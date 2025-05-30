from web3 import Web3
from typing import List, Dict, Any
from .base_chain_adapter import BaseChainAdapter
from src.utils.logger import logger


class FantomAdapter(BaseChainAdapter):
    """Fantom blockchain adapter"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if not self.w3.is_connected():
                raise ConnectionError(f"Failed to connect to Fantom RPC: {self.rpc_url}")
        except Exception as e:
            logger.log(f"Error initializing Fantom adapter: {e}")
            raise
    
    def get_current_block(self) -> int:
        try:
            return self.w3.eth.block_number
        except Exception as e:
            logger.log(f"Error getting current block: {e}")
            return 0
    
    def get_transactions(self, start_block: int, end_block: int) -> List[Dict[str, Any]]:
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
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            return self._format_ethereum_transaction(tx)
        except Exception as e:
            logger.log(f"Error getting transaction details: {e}")
            return {}
    
    def _format_ethereum_transaction(self, tx) -> Dict[str, Any]:
        try:
            return {
                'hash': tx['hash'].hex() if hasattr(tx['hash'], 'hex') else str(tx['hash']),
                'to': tx.get('to', ''),
                'from': tx.get('from', ''),
                'value': float(self.w3.from_wei(tx.get('value', 0), 'ether')),
                'currency': self._detect_token_currency(tx),
                'block': tx.get('blockNumber', 0),
                'timestamp': 0
            }
        except Exception as e:
            logger.log(f"Error formatting transaction: {e}")
            return {}
