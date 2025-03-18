from tronapi import Tron
from tronapi.exceptions import TronAPIException
from config.settings import settings
from functools import lru_cache
from tenacity import retry, wait_exponential, stop_after_attempt
import logging

logger = logging.getLogger(__name__)

# Define the token contract addresses for Tron (TRC20 tokens)
USDT_CONTRACT = "TXYZ... (USDT contract address)"
USDC_CONTRACT = "TABC... (USDC contract address)"
DAI_CONTRACT = "TDEF... (DAI contract address)"

class TronAdapter:
    """Optimized Tron blockchain adapter with error handling and connection management"""
    
    _instance = None  # Singleton instance
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(TronAdapter, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Lazy initialization of Tron connection"""
        self._connect()
        self.last_block = 0  # Track last processed block
        
    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        reraise=True
    )
    def _connect(self):
        """Establish connection with retry logic"""
        try:
            self.tron = Tron(
                full_node=settings.BLOCKCHAINS['Tron']['rpc'],
                timeout=settings.BLOCKCHAINS['Tron'].get('timeout', 10),
                retries=3
            )
            logger.info("Successfully connected to Tron node")
        except TronAPIException as e:
            logger.error(f"Connection failed: {str(e)}")
            raise

    def get_transactions(self, start_block: int, end_block: int):
        """Optimized transaction fetching with block range validation"""
        try:
            # Validate block range
            if start_block > end_block:
                logger.warning(f"Invalid block range: {start_block}-{end_block}")
                return []
                
            # Use generator to reduce memory footprint
            return self._process_blocks(start_block, end_block)
            
        except TronAPIException as e:
            logger.error(f"API Error: {str(e)}")
            self._connect()  # Reconnect on failure
            return []
        except Exception as e:
            logger.critical(f"Unexpected error: {str(e)}", exc_info=True)
            return []

    def _process_blocks(self, start_block: int, end_block: int):
        """Process blocks using generator for memory efficiency"""
        for block_num in range(start_block, end_block + 1):
            yield from self._get_block_transactions(block_num)
            
    @lru_cache(maxsize=128)
    def _get_block_transactions(self, block_num: int):
        """Cached block processing with transaction extraction"""
        try:
            block = self.tron.trx.get_block(block_num)
            return [self._format_transaction(tx) for tx in block.get('transactions', [])]
        except TronAPIException as e:
            logger.warning(f"Failed to get block {block_num}: {str(e)}")
            return []

    def _format_transaction(self, tx: dict):
        """Standardized transaction formatting"""
        currency = self._detect_token_currency(tx)  # Detect the token
        return {
            'hash': tx.get('txID'),
            'from': tx.get('ownerAddress'),
            'to': self._get_recipient(tx),
            'value': int(tx.get('value', 0)),
            'currency': currency,  # This will now include USDT, USDC, DAI, or TRX
            'block': tx.get('blockNumber'),
            'timestamp': tx.get('timestamp'),
            'status': tx.get('ret')[0].get('contractRet') if tx.get('ret') else None
        }

    def _detect_token_currency(self, tx: dict) -> str:
        """Detect token type based on contract address"""
        contract_data = tx.get('raw_data', {}).get('contract', [{}])[0]
        if contract_data.get('type') == 'TransferContract':
            token_address = contract_data.get('parameter', {}).get('value', {}).get('to_address')
            
            if token_address == USDT_CONTRACT:
                return 'USDT'
            elif token_address == USDC_CONTRACT:
                return 'USDC'
            elif token_address == DAI_CONTRACT:
                return 'DAI'
        return 'TRX'  # Default is TRX if no token detected

    def _get_recipient(self, tx: dict) -> str:
        """Extract recipient address with fallback"""
        contract_data = tx.get('raw_data', {}).get('contract', [{}])[0]
        return contract_data.get('parameter', {}).get('value', {}).get('to_address') or ''