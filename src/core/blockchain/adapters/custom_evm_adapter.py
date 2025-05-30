"""
Custom EVM Blockchain Adapter
Allows dynamic integration of any EVM-compatible blockchain
"""

from typing import Dict, List, Optional, Any
from .base_chain_adapter import BaseChainAdapter
from src.utils.logger import logger

class CustomEVMAdapter(BaseChainAdapter):
    """
    Custom EVM Blockchain Adapter for dynamic EVM chain integration
    Supports any EVM-compatible blockchain with custom configuration
    """
    
    def __init__(self, chain_config: Dict[str, Any]):
        """
        Initialize custom EVM adapter with dynamic configuration
        
        Args:
            chain_config: Dictionary containing:
                - name: Chain name
                - rpc_url: RPC endpoint URL
                - chain_id: Network chain ID
                - symbol: Native token symbol
                - explorer_url: Block explorer URL
                - gas_price_multiplier: Optional gas price multiplier
                - block_time: Average block time in seconds
                - confirmations: Required confirmations
        """
        super().__init__(chain_config)
        self.chain_name = chain_config.get('name', 'Custom EVM Chain')
        self.chain_id = chain_config.get('chain_id')
        self.symbol = chain_config.get('symbol', 'ETH')
        self.explorer_url = chain_config.get('explorer_url', '')
        self.gas_price_multiplier = chain_config.get('gas_price_multiplier', 1.0)
        self.block_time = chain_config.get('block_time', 15)  # seconds
        self.confirmations = chain_config.get('confirmations', 12)
        
        # Token contracts for stablecoins
        self.token_contracts = chain_config.get('token_contracts', {})
        
        # Initialize Web3 connection
        self.web3 = None
        self._initialize_connection()
        
        logger.log(f"Custom EVM adapter initialized for {self.chain_name} (Chain ID: {self.chain_id})")
    
    def _initialize_connection(self):
        """Initialize Web3 connection to the custom EVM chain"""
        try:
            from web3 import Web3
            
            if not self.rpc_url:
                logger.log(f"No RPC URL provided for {self.chain_name}")
                return
            
            if self.rpc_url.startswith('wss://') or self.rpc_url.startswith('ws://'):
                from web3.providers import WebsocketProvider
                provider = WebsocketProvider(self.rpc_url)
            else:
                from web3.providers import HTTPProvider
                # Set a short timeout for HTTP requests
                provider = HTTPProvider(self.rpc_url, request_kwargs={'timeout': 3})
            
            self.web3 = Web3(provider)
            
            # Test connection
            try:
                is_connected = self.web3.is_connected()
                if is_connected:
                    logger.log(f"Successfully connected to {self.chain_name} at {self.rpc_url}")
                    # Verify chain ID if provided
                    if self.chain_id:
                        try:
                            actual_chain_id = self.web3.eth.chain_id
                            if actual_chain_id != self.chain_id:
                                logger.log(f"Warning: Chain ID mismatch for {self.chain_name}. Expected: {self.chain_id}, Actual: {actual_chain_id}")
                        except Exception as e:
                            logger.log(f"Could not verify chain ID for {self.chain_name}: {e}")
                else:
                    logger.log(f"Failed to connect to {self.chain_name} at {self.rpc_url}")
            except Exception as e:
                logger.log(f"Failed to connect to {self.chain_name} at {self.rpc_url}")
                self.web3 = None
                
        except Exception as e:
            logger.log(f"Error initializing connection to {self.chain_name}: {e}")
            self.web3 = None
    
    def get_chain_info(self) -> Dict[str, Any]:
        """Get comprehensive chain information"""
        return {
            'name': self.chain_name,
            'chain_id': self.chain_id,
            'symbol': self.symbol,
            'type': 'Custom EVM',
            'rpc_url': self.rpc_url,
            'explorer_url': self.explorer_url,
            'block_time': self.block_time,
            'confirmations': self.confirmations,
            'gas_price_multiplier': self.gas_price_multiplier,
            'supported_tokens': list(self.token_contracts.keys())
        }
    
    def get_current_block(self) -> int:
        """Get current block number"""
        try:
            if not self.web3 or not self.web3.is_connected():
                logger.log(f"Warning: Not connected to {self.chain_name} RPC")
                return 0
            
            block_number = self.web3.eth.block_number
            logger.log(f"{self.chain_name} current block: {block_number}")
            return block_number
        except Exception as e:
            logger.log(f"Error getting current block for {self.chain_name}: {e}")
            return 0
    
    def get_transactions(self, start_block: int, end_block: int) -> List[Dict]:
        """Get transactions in block range"""
        try:
            if not self.web3 or not self.web3.is_connected():
                logger.log(f"Warning: Not connected to {self.chain_name} RPC")
                return []
            
            transactions = []
            for block_num in range(start_block, min(end_block + 1, start_block + 10)):
                try:
                    block = self.web3.eth.get_block(block_num, full_transactions=True)
                    for tx in block.transactions:
                        tx_data = {
                            'hash': tx.hash.hex(),
                            'from': tx['from'],
                            'to': tx.get('to', ''),
                            'value': str(tx.value),
                            'gas': tx.gas,
                            'gas_price': str(tx.gasPrice),
                            'block_number': block_num,
                            'block_hash': block.hash.hex(),
                            'transaction_index': tx.transactionIndex,
                            'chain_id': self.chain_id,
                            'chain_name': self.chain_name
                        }
                        transactions.append(tx_data)
                except Exception as e:
                    logger.log(f"Error processing block {block_num} on {self.chain_name}: {e}")
                    continue
            
            return transactions
        except Exception as e:
            logger.log(f"Error getting transactions for {self.chain_name}: {e}")
            return []
    
    def get_transaction_details(self, tx_hash: str) -> Optional[Dict]:
        """Get detailed transaction information"""
        try:
            if not self.web3 or not self.web3.is_connected():
                logger.log(f"Warning: Not connected to {self.chain_name} RPC")
                return None
            
            tx = self.web3.eth.get_transaction(tx_hash)
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            
            return {
                'hash': tx.hash.hex(),
                'from': tx['from'],
                'to': tx.get('to', ''),
                'value': str(tx.value),
                'gas': tx.gas,
                'gas_price': str(tx.gasPrice),
                'gas_used': receipt.gasUsed,
                'status': receipt.status,
                'block_number': receipt.blockNumber,
                'block_hash': receipt.blockHash.hex(),
                'transaction_index': receipt.transactionIndex,
                'chain_id': self.chain_id,
                'chain_name': self.chain_name,
                'confirmations': self.get_current_block() - receipt.blockNumber
            }
        except Exception as e:
            logger.log(f"Error getting transaction details for {tx_hash} on {self.chain_name}: {e}")
            return None
    
    def get_token_balance(self, address: str, token_contract: str) -> float:
        """Get token balance for an address"""
        try:
            if not self.web3 or not self.web3.is_connected():
                return 0.0
            
            # Standard ERC-20 ABI for balanceOf function
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [{"name": "_owner", "type": "address"}],
                    "name": "balanceOf",
                    "outputs": [{"name": "balance", "type": "uint256"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                }
            ]
            
            contract = self.web3.eth.contract(
                address=self.web3.to_checksum_address(token_contract),
                abi=erc20_abi
            )
            
            balance = contract.functions.balanceOf(
                self.web3.to_checksum_address(address)
            ).call()
            
            decimals = contract.functions.decimals().call()
            return balance / (10 ** decimals)
            
        except Exception as e:
            logger.log(f"Error getting token balance on {self.chain_name}: {e}")
            return 0.0
    
    def get_native_balance(self, address: str) -> float:
        """Get native token balance"""
        try:
            if not self.web3 or not self.web3.is_connected():
                return 0.0
            
            balance_wei = self.web3.eth.get_balance(
                self.web3.to_checksum_address(address)
            )
            return self.web3.from_wei(balance_wei, 'ether')
            
        except Exception as e:
            logger.log(f"Error getting native balance on {self.chain_name}: {e}")
            return 0.0
    
    def estimate_gas_price(self) -> int:
        """Estimate current gas price"""
        try:
            if not self.web3 or not self.web3.is_connected():
                return 0
            
            gas_price = self.web3.eth.gas_price
            return int(gas_price * self.gas_price_multiplier)
            
        except Exception as e:
            logger.log(f"Error estimating gas price on {self.chain_name}: {e}")
            return 0
    
    def validate_address(self, address: str) -> bool:
        """Validate if address is valid for this chain"""
        try:
            if not self.web3:
                return False
            
            checksum_address = self.web3.to_checksum_address(address)
            return self.web3.is_address(checksum_address)
            
        except Exception:
            return False
    
    def get_explorer_url(self, url_type: str, identifier: str) -> str:
        """Get explorer URL for transaction, address, or block"""
        if not self.explorer_url:
            return ""
        
        base_url = self.explorer_url.rstrip('/')
        
        if url_type == 'tx':
            return f"{base_url}/tx/{identifier}"
        elif url_type == 'address':
            return f"{base_url}/address/{identifier}"
        elif url_type == 'block':
            return f"{base_url}/block/{identifier}"
        else:
            return base_url
    
    def get_supported_tokens(self) -> Dict[str, str]:
        """Get supported token contracts"""
        return self.token_contracts.copy()
    
    def add_token_contract(self, symbol: str, contract_address: str):
        """Add a new token contract"""
        self.token_contracts[symbol.upper()] = contract_address
        logger.log(f"Added {symbol} token contract to {self.chain_name}: {contract_address}")
    
    def remove_token_contract(self, symbol: str):
        """Remove a token contract"""
        if symbol.upper() in self.token_contracts:
            del self.token_contracts[symbol.upper()]
            logger.log(f"Removed {symbol} token contract from {self.chain_name}")
    
    def update_rpc_url(self, new_rpc_url: str):
        """Update RPC URL and reconnect"""
        self.rpc_url = new_rpc_url
        self._initialize_web3()
        logger.log(f"Updated RPC URL for {self.chain_name}: {new_rpc_url}")
    
    def get_network_stats(self) -> Dict[str, Any]:
        """Get network statistics"""
        try:
            if not self.web3 or not self.web3.is_connected():
                return {}
            
            current_block = self.get_current_block()
            gas_price = self.estimate_gas_price()
            
            return {
                'current_block': current_block,
                'gas_price': gas_price,
                'gas_price_gwei': self.web3.from_wei(gas_price, 'gwei') if gas_price > 0 else 0,
                'chain_id': self.chain_id,
                'connected': True,
                'block_time': self.block_time,
                'confirmations_required': self.confirmations
            }
            
        except Exception as e:
            logger.log(f"Error getting network stats for {self.chain_name}: {e}")
            return {'connected': False, 'error': str(e)}