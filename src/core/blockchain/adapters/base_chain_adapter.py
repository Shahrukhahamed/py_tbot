from abc import ABC, abstractmethod
from typing import List, Dict, Any
from .token_methods import TokenMethodsMixin


class BaseChainAdapter(ABC, TokenMethodsMixin):
    """Base class for all blockchain adapters with token tracking support"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rpc_url = config.get('rpc_url')
        self.native_token = config.get('native_token')
        self.tokens = config.get('tokens', {})
        self.chain_name = config.get('name', 'unknown')
    
    @abstractmethod
    def get_current_block(self) -> int:
        """Get the current block number"""
        pass
    
    @abstractmethod
    def get_transactions(self, start_block: int, end_block: int) -> List[Dict[str, Any]]:
        """Get transactions between block range"""
        pass
    
    @abstractmethod
    def get_transaction_details(self, tx_hash: str) -> Dict[str, Any]:
        """Get detailed transaction information"""
        pass
    
    def _detect_token_currency(self, tx: Dict[str, Any]) -> str:
        """Detect the currency/token type from transaction"""
        to_addr = (tx.get('to') or '').lower()
        
        for token_name, contract_addr in self.tokens.items():
            if to_addr == contract_addr.lower():
                return token_name
        
        return self.native_token
    
    def _format_transaction(self, tx: Dict[str, Any]) -> Dict[str, Any]:
        """Format transaction data to standard format"""
        return {
            'hash': tx.get('hash', ''),
            'to': tx.get('to', ''),
            'from': tx.get('from', ''),
            'value': tx.get('value', 0),
            'currency': self._detect_token_currency(tx),
            'block': tx.get('blockNumber', 0),
            'timestamp': tx.get('timestamp', 0)
        }