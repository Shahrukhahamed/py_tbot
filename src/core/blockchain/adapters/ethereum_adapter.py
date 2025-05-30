from web3 import Web3
from typing import List, Dict, Any
from .base_chain_adapter import BaseChainAdapter
from src.utils.logger import logger


class EthereumAdapter(BaseChainAdapter):
    """Ethereum blockchain adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.w3 = None
        self.connection_error = None
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if not self.w3.is_connected():
                self.connection_error = f"Failed to connect to Ethereum RPC: {self.rpc_url}"
                logger.log(f"Warning: {self.connection_error}")
            else:
                logger.log("Ethereum adapter initialized successfully")
        except Exception as e:
            self.connection_error = f"Error initializing Ethereum adapter: {e}"
            logger.log(f"Warning: {self.connection_error}")
    
    def get_current_block(self) -> int:
        """Get the current block number"""
        if self.connection_error or not self.w3:
            logger.log(f"Cannot get current block: {self.connection_error}")
            return 0
        try:
            return self.w3.eth.block_number
        except Exception as e:
            logger.log(f"Error getting current block: {e}")
            return 0
    
    def get_transactions(self, start_block: int, end_block: int) -> List[Dict[str, Any]]:
        """Get transactions between block range"""
        if self.connection_error or not self.w3:
            logger.log(f"Cannot get transactions: {self.connection_error}")
            return []
        
        transactions = []
        try:
            for block_num in range(start_block, end_block + 1):
                block = self.w3.eth.get_block(block_num, full_transactions=True)
                for tx in block.transactions:
                    formatted_tx = self._format_ethereum_transaction(tx)
                    transactions.append(formatted_tx)
        except Exception as e:
            logger.log(f"Error getting transactions: {e}")
        
        return transactions
    
    def get_transaction_details(self, tx_hash: str) -> Dict[str, Any]:
        """Get detailed transaction information"""
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            return self._format_ethereum_transaction(tx)
        except Exception as e:
            logger.log(f"Error getting transaction details: {e}")
            return {}
    
    def _format_ethereum_transaction(self, tx) -> Dict[str, Any]:
        """Format Ethereum transaction to standard format"""
        try:
            return {
                'hash': tx['hash'].hex() if hasattr(tx['hash'], 'hex') else str(tx['hash']),
                'to': tx.get('to', ''),
                'from': tx.get('from', ''),
                'value': float(self.w3.from_wei(tx.get('value', 0), 'ether')),
                'currency': self._detect_token_currency(tx),
                'block': tx.get('blockNumber', 0),
                'timestamp': 0  # Would need to get from block
            }
        except Exception as e:
            logger.log(f"Error formatting transaction: {e}")
            return {}