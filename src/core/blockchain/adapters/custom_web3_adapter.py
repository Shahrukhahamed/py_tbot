"""
Custom Web3 Blockchain Adapter
Allows dynamic integration of any Web3-compatible blockchain (including non-EVM)
"""

import json
import requests
from typing import Dict, List, Optional, Any, Callable
from .base_chain_adapter import BaseChainAdapter
from src.utils.logger import logger

class CustomWeb3Adapter(BaseChainAdapter):
    """
    Custom Web3 Blockchain Adapter for dynamic blockchain integration
    Supports any Web3-compatible blockchain with custom RPC methods
    """
    
    def __init__(self, chain_config: Dict[str, Any]):
        """
        Initialize custom Web3 adapter with dynamic configuration
        
        Args:
            chain_config: Dictionary containing:
                - name: Chain name
                - rpc_url: RPC endpoint URL
                - chain_type: Type of blockchain (e.g., 'substrate', 'cosmos', 'solana')
                - symbol: Native token symbol
                - explorer_url: Block explorer URL
                - rpc_methods: Custom RPC method mappings
                - address_format: Address format validation regex
                - decimals: Native token decimals
                - block_time: Average block time in seconds
        """
        super().__init__(chain_config)
        self.chain_name = chain_config.get('name', 'Custom Web3 Chain')
        self.chain_type = chain_config.get('chain_type', 'custom')
        self.symbol = chain_config.get('symbol', 'CUSTOM')
        self.explorer_url = chain_config.get('explorer_url', '')
        self.decimals = chain_config.get('decimals', 18)
        self.block_time = chain_config.get('block_time', 6)  # seconds
        
        # Custom RPC method mappings
        self.rpc_methods = chain_config.get('rpc_methods', {
            'get_block_number': 'chain_getBlockNumber',
            'get_block': 'chain_getBlock',
            'get_transaction': 'chain_getTransaction',
            'get_balance': 'system_accountBalance',
            'get_transaction_receipt': 'chain_getTransactionReceipt'
        })
        
        # Address format validation
        self.address_format = chain_config.get('address_format', r'^[a-zA-Z0-9]+$')
        
        # Custom parsers for different response formats
        self.response_parsers = chain_config.get('response_parsers', {})
        
        # Initialize without web3 for non-EVM chains
        self.web3 = None
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
        logger.log(f"Custom Web3 adapter initialized for {self.chain_name} ({self.chain_type})")
    
    def _make_rpc_call(self, method: str, params: List = None) -> Optional[Dict]:
        """Make a custom RPC call"""
        try:
            if params is None:
                params = []
            
            payload = {
                'jsonrpc': '2.0',
                'method': method,
                'params': params,
                'id': 1
            }
            
            response = self.session.post(self.rpc_url, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if 'error' in data:
                logger.log(f"RPC error for {self.chain_name}: {data['error']}")
                return None
            
            return data.get('result')
            
        except Exception as e:
            logger.log(f"RPC call failed for {self.chain_name}: {e}")
            return None
    
    def get_chain_info(self) -> Dict[str, Any]:
        """Get comprehensive chain information"""
        return {
            'name': self.chain_name,
            'type': f'Custom Web3 ({self.chain_type})',
            'symbol': self.symbol,
            'rpc_url': self.rpc_url,
            'explorer_url': self.explorer_url,
            'decimals': self.decimals,
            'block_time': self.block_time,
            'address_format': self.address_format,
            'supported_methods': list(self.rpc_methods.keys())
        }
    
    def get_current_block(self) -> int:
        """Get current block number using custom RPC method"""
        try:
            method = self.rpc_methods.get('get_block_number', 'chain_getBlockNumber')
            result = self._make_rpc_call(method)
            
            if result is None:
                return 0
            
            # Handle different response formats
            if isinstance(result, dict):
                # Substrate-style response
                block_number = result.get('number', result.get('blockNumber', 0))
            elif isinstance(result, str):
                # Hex string response
                block_number = int(result, 16) if result.startswith('0x') else int(result)
            else:
                # Direct integer response
                block_number = int(result)
            
            logger.log(f"{self.chain_name} current block: {block_number}")
            return block_number
            
        except Exception as e:
            logger.log(f"Error getting current block for {self.chain_name}: {e}")
            return 0
    
    def get_transactions(self, start_block: int, end_block: int) -> List[Dict]:
        """Get transactions in block range using custom RPC methods"""
        try:
            transactions = []
            method = self.rpc_methods.get('get_block', 'chain_getBlock')
            
            for block_num in range(start_block, min(end_block + 1, start_block + 5)):
                try:
                    # Get block with transactions
                    block_result = self._make_rpc_call(method, [block_num, True])
                    
                    if not block_result:
                        continue
                    
                    # Parse block based on chain type
                    block_txs = self._parse_block_transactions(block_result, block_num)
                    transactions.extend(block_txs)
                    
                except Exception as e:
                    logger.log(f"Error processing block {block_num} on {self.chain_name}: {e}")
                    continue
            
            return transactions
            
        except Exception as e:
            logger.log(f"Error getting transactions for {self.chain_name}: {e}")
            return []
    
    def _parse_block_transactions(self, block_data: Dict, block_num: int) -> List[Dict]:
        """Parse transactions from block data based on chain type"""
        transactions = []
        
        try:
            # Handle different block formats
            if self.chain_type == 'substrate':
                # Substrate/Polkadot format
                extrinsics = block_data.get('block', {}).get('extrinsics', [])
                for i, ext in enumerate(extrinsics):
                    tx_data = {
                        'hash': ext.get('hash', f"block_{block_num}_tx_{i}"),
                        'from': ext.get('signer', ''),
                        'to': self._extract_destination(ext),
                        'value': self._extract_value(ext),
                        'block_number': block_num,
                        'transaction_index': i,
                        'chain_name': self.chain_name,
                        'chain_type': self.chain_type
                    }
                    transactions.append(tx_data)
                    
            elif self.chain_type == 'cosmos':
                # Cosmos format
                txs = block_data.get('block', {}).get('data', {}).get('txs', [])
                for i, tx in enumerate(txs):
                    tx_data = {
                        'hash': tx.get('txhash', f"block_{block_num}_tx_{i}"),
                        'from': self._extract_cosmos_sender(tx),
                        'to': self._extract_cosmos_recipient(tx),
                        'value': self._extract_cosmos_amount(tx),
                        'block_number': block_num,
                        'transaction_index': i,
                        'chain_name': self.chain_name,
                        'chain_type': self.chain_type
                    }
                    transactions.append(tx_data)
                    
            else:
                # Generic format
                txs = block_data.get('transactions', block_data.get('txs', []))
                for i, tx in enumerate(txs):
                    tx_data = {
                        'hash': tx.get('hash', tx.get('txid', f"block_{block_num}_tx_{i}")),
                        'from': tx.get('from', tx.get('sender', '')),
                        'to': tx.get('to', tx.get('recipient', '')),
                        'value': str(tx.get('value', tx.get('amount', 0))),
                        'block_number': block_num,
                        'transaction_index': i,
                        'chain_name': self.chain_name,
                        'chain_type': self.chain_type
                    }
                    transactions.append(tx_data)
            
        except Exception as e:
            logger.log(f"Error parsing block transactions for {self.chain_name}: {e}")
        
        return transactions
    
    def get_transaction_details(self, tx_hash: str) -> Optional[Dict]:
        """Get detailed transaction information"""
        try:
            method = self.rpc_methods.get('get_transaction', 'chain_getTransaction')
            tx_result = self._make_rpc_call(method, [tx_hash])
            
            if not tx_result:
                return None
            
            # Parse transaction based on chain type
            return self._parse_transaction_details(tx_result, tx_hash)
            
        except Exception as e:
            logger.log(f"Error getting transaction details for {tx_hash} on {self.chain_name}: {e}")
            return None
    
    def _parse_transaction_details(self, tx_data: Dict, tx_hash: str) -> Dict:
        """Parse transaction details based on chain type"""
        try:
            if self.chain_type == 'substrate':
                return {
                    'hash': tx_hash,
                    'from': tx_data.get('signer', ''),
                    'to': self._extract_destination(tx_data),
                    'value': self._extract_value(tx_data),
                    'block_number': tx_data.get('blockNumber', 0),
                    'status': 'success' if tx_data.get('success', True) else 'failed',
                    'chain_name': self.chain_name,
                    'chain_type': self.chain_type
                }
            elif self.chain_type == 'cosmos':
                return {
                    'hash': tx_hash,
                    'from': self._extract_cosmos_sender(tx_data),
                    'to': self._extract_cosmos_recipient(tx_data),
                    'value': self._extract_cosmos_amount(tx_data),
                    'block_number': tx_data.get('height', 0),
                    'status': 'success' if tx_data.get('code', 0) == 0 else 'failed',
                    'chain_name': self.chain_name,
                    'chain_type': self.chain_type
                }
            else:
                return {
                    'hash': tx_hash,
                    'from': tx_data.get('from', tx_data.get('sender', '')),
                    'to': tx_data.get('to', tx_data.get('recipient', '')),
                    'value': str(tx_data.get('value', tx_data.get('amount', 0))),
                    'block_number': tx_data.get('blockNumber', tx_data.get('height', 0)),
                    'status': tx_data.get('status', 'unknown'),
                    'chain_name': self.chain_name,
                    'chain_type': self.chain_type
                }
        except Exception as e:
            logger.log(f"Error parsing transaction details for {self.chain_name}: {e}")
            return {'hash': tx_hash, 'error': str(e)}
    
    def get_balance(self, address: str) -> float:
        """Get native token balance"""
        try:
            method = self.rpc_methods.get('get_balance', 'system_accountBalance')
            result = self._make_rpc_call(method, [address])
            
            if not result:
                return 0.0
            
            # Parse balance based on chain type
            if isinstance(result, dict):
                balance = result.get('free', result.get('balance', result.get('amount', 0)))
            else:
                balance = result
            
            # Convert to float considering decimals
            if isinstance(balance, str):
                balance = int(balance, 16) if balance.startswith('0x') else int(balance)
            
            return float(balance) / (10 ** self.decimals)
            
        except Exception as e:
            logger.log(f"Error getting balance for {address} on {self.chain_name}: {e}")
            return 0.0
    
    def validate_address(self, address: str) -> bool:
        """Validate address format"""
        import re
        try:
            return bool(re.match(self.address_format, address))
        except Exception:
            return False
    
    def get_explorer_url(self, url_type: str, identifier: str) -> str:
        """Get explorer URL for transaction, address, or block"""
        if not self.explorer_url:
            return ""
        
        base_url = self.explorer_url.rstrip('/')
        
        # Handle different explorer URL formats
        if self.chain_type == 'substrate':
            if url_type == 'tx':
                return f"{base_url}/extrinsic/{identifier}"
            elif url_type == 'address':
                return f"{base_url}/account/{identifier}"
            elif url_type == 'block':
                return f"{base_url}/block/{identifier}"
        elif self.chain_type == 'cosmos':
            if url_type == 'tx':
                return f"{base_url}/tx/{identifier}"
            elif url_type == 'address':
                return f"{base_url}/account/{identifier}"
            elif url_type == 'block':
                return f"{base_url}/blocks/{identifier}"
        else:
            # Generic format
            if url_type == 'tx':
                return f"{base_url}/tx/{identifier}"
            elif url_type == 'address':
                return f"{base_url}/address/{identifier}"
            elif url_type == 'block':
                return f"{base_url}/block/{identifier}"
        
        return base_url
    
    def _extract_destination(self, tx_data: Dict) -> str:
        """Extract destination address from transaction data"""
        # Handle different transaction formats
        call = tx_data.get('call', {})
        if isinstance(call, dict):
            args = call.get('args', {})
            return args.get('dest', args.get('to', ''))
        return ''
    
    def _extract_value(self, tx_data: Dict) -> str:
        """Extract value from transaction data"""
        call = tx_data.get('call', {})
        if isinstance(call, dict):
            args = call.get('args', {})
            return str(args.get('value', args.get('amount', 0)))
        return '0'
    
    def _extract_cosmos_sender(self, tx_data: Dict) -> str:
        """Extract sender from Cosmos transaction"""
        msgs = tx_data.get('tx', {}).get('body', {}).get('messages', [])
        if msgs:
            return msgs[0].get('from_address', '')
        return ''
    
    def _extract_cosmos_recipient(self, tx_data: Dict) -> str:
        """Extract recipient from Cosmos transaction"""
        msgs = tx_data.get('tx', {}).get('body', {}).get('messages', [])
        if msgs:
            return msgs[0].get('to_address', '')
        return ''
    
    def _extract_cosmos_amount(self, tx_data: Dict) -> str:
        """Extract amount from Cosmos transaction"""
        msgs = tx_data.get('tx', {}).get('body', {}).get('messages', [])
        if msgs:
            amount = msgs[0].get('amount', [])
            if amount:
                return amount[0].get('amount', '0')
        return '0'
    
    def update_rpc_url(self, new_rpc_url: str):
        """Update RPC URL"""
        self.rpc_url = new_rpc_url
        logger.log(f"Updated RPC URL for {self.chain_name}: {new_rpc_url}")
    
    def add_custom_method(self, method_name: str, rpc_method: str):
        """Add custom RPC method mapping"""
        self.rpc_methods[method_name] = rpc_method
        logger.log(f"Added custom method {method_name} -> {rpc_method} for {self.chain_name}")
    
    def get_network_info(self) -> Dict[str, Any]:
        """Get network information"""
        try:
            current_block = self.get_current_block()
            
            return {
                'chain_name': self.chain_name,
                'chain_type': self.chain_type,
                'current_block': current_block,
                'symbol': self.symbol,
                'decimals': self.decimals,
                'block_time': self.block_time,
                'connected': current_block > 0,
                'rpc_url': self.rpc_url
            }
            
        except Exception as e:
            logger.log(f"Error getting network info for {self.chain_name}: {e}")
            return {'connected': False, 'error': str(e)}