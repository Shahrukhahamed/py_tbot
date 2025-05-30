"""
Token tracking methods for blockchain adapters
Extends adapters with token-specific functionality
"""

import asyncio
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from web3 import Web3
from web3.exceptions import ContractLogicError

from src.utils.logger import get_logger
from src.core.tracking.models import Transaction, TransactionType

logger = get_logger(__name__)

class TokenMethodsMixin:
    """Mixin class to add token tracking methods to blockchain adapters"""
    
    async def get_token_info(self, token_address: str) -> Optional[Dict]:
        """Get basic token information"""
        try:
            if hasattr(self, 'web3') and self.web3:
                return await self._get_erc20_token_info(token_address)
            else:
                return await self._get_generic_token_info(token_address)
        except Exception as e:
            logger.error(f"Error getting token info for {token_address}: {e}")
            return None
    
    async def _get_erc20_token_info(self, token_address: str) -> Optional[Dict]:
        """Get ERC20 token information using Web3"""
        try:
            # ERC20 ABI for basic functions
            erc20_abi = [
                {
                    "constant": True,
                    "inputs": [],
                    "name": "name",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "symbol",
                    "outputs": [{"name": "", "type": "string"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "decimals",
                    "outputs": [{"name": "", "type": "uint8"}],
                    "type": "function"
                },
                {
                    "constant": True,
                    "inputs": [],
                    "name": "totalSupply",
                    "outputs": [{"name": "", "type": "uint256"}],
                    "type": "function"
                }
            ]
            
            contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=erc20_abi
            )
            
            # Get token information
            try:
                name = contract.functions.name().call()
            except:
                name = "Unknown Token"
            
            try:
                symbol = contract.functions.symbol().call()
            except:
                symbol = "UNKNOWN"
            
            try:
                decimals = contract.functions.decimals().call()
            except:
                decimals = 18
            
            try:
                total_supply = contract.functions.totalSupply().call()
            except:
                total_supply = None
            
            return {
                'name': name,
                'symbol': symbol,
                'decimals': decimals,
                'total_supply': total_supply,
                'verified': True,
                'contract_type': 'ERC20'
            }
            
        except Exception as e:
            logger.error(f"Error getting ERC20 token info: {e}")
            return None
    
    async def _get_generic_token_info(self, token_address: str) -> Optional[Dict]:
        """Get generic token information for non-EVM chains"""
        try:
            # This would be implemented differently for each blockchain
            # For now, return basic info
            return {
                'name': 'Unknown Token',
                'symbol': 'UNKNOWN',
                'decimals': 18,
                'verified': False
            }
        except Exception as e:
            logger.error(f"Error getting generic token info: {e}")
            return None
    
    async def get_token_contract_info(self, token_address: str) -> Optional[Dict]:
        """Get detailed token contract information"""
        try:
            basic_info = await self.get_token_info(token_address)
            if not basic_info:
                return None
            
            # Add contract-specific information
            if hasattr(self, 'web3') and self.web3:
                # Get contract code to verify it's a contract
                try:
                    code = self.web3.eth.get_code(Web3.to_checksum_address(token_address))
                    basic_info['is_contract'] = len(code) > 0
                except:
                    basic_info['is_contract'] = False
            
            return basic_info
            
        except Exception as e:
            logger.error(f"Error getting token contract info: {e}")
            return None
    
    async def get_token_transactions(self, token_address: str, from_block: int = 0) -> List[Transaction]:
        """Get token transactions from a specific block"""
        try:
            if hasattr(self, 'web3') and self.web3:
                return await self._get_erc20_transactions(token_address, from_block)
            else:
                return await self._get_generic_token_transactions(token_address, from_block)
        except Exception as e:
            logger.error(f"Error getting token transactions: {e}")
            return []
    
    async def _get_erc20_transactions(self, token_address: str, from_block: int) -> List[Transaction]:
        """Get ERC20 token transactions"""
        try:
            # ERC20 Transfer event ABI
            transfer_abi = {
                "anonymous": False,
                "inputs": [
                    {"indexed": True, "name": "from", "type": "address"},
                    {"indexed": True, "name": "to", "type": "address"},
                    {"indexed": False, "name": "value", "type": "uint256"}
                ],
                "name": "Transfer",
                "type": "event"
            }
            
            contract = self.web3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=[transfer_abi]
            )
            
            # Get latest block
            latest_block = self.web3.eth.block_number
            to_block = min(from_block + 1000, latest_block)  # Limit to 1000 blocks
            
            # Get transfer events
            transfer_filter = contract.events.Transfer.create_filter(
                fromBlock=from_block,
                toBlock=to_block
            )
            
            events = transfer_filter.get_all_entries()
            transactions = []
            
            # Get token info for decimals
            token_info = await self.get_token_info(token_address)
            decimals = token_info.get('decimals', 18) if token_info else 18
            symbol = token_info.get('symbol', 'UNKNOWN') if token_info else 'UNKNOWN'
            
            for event in events:
                try:
                    # Get transaction details
                    tx_hash = event['transactionHash'].hex()
                    tx_receipt = self.web3.eth.get_transaction_receipt(tx_hash)
                    tx_details = self.web3.eth.get_transaction(tx_hash)
                    block = self.web3.eth.get_block(event['blockNumber'])
                    
                    # Calculate amount
                    raw_amount = event['args']['value']
                    amount = raw_amount / (10 ** decimals)
                    
                    # Determine transaction type
                    from_addr = event['args']['from']
                    to_addr = event['args']['to']
                    
                    # Simple heuristic for buy/sell detection
                    # This would need to be enhanced with DEX detection
                    tx_type = TransactionType.TRANSFER
                    if self._is_dex_address(to_addr):
                        tx_type = TransactionType.SELL
                    elif self._is_dex_address(from_addr):
                        tx_type = TransactionType.BUY
                    
                    transaction = Transaction(
                        hash=tx_hash,
                        blockchain=self.chain_name,
                        token_address=token_address,
                        token_symbol=symbol,
                        transaction_type=tx_type,
                        from_address=from_addr,
                        to_address=to_addr,
                        amount=amount,
                        amount_usd=None,  # Would need price data
                        price=None,
                        timestamp=datetime.fromtimestamp(block['timestamp']),
                        block_number=event['blockNumber'],
                        gas_used=tx_receipt['gasUsed'],
                        gas_price=tx_details['gasPrice'],
                        is_whale=amount > 100000,  # Simple whale detection
                        dex_name=self._get_dex_name(from_addr, to_addr)
                    )
                    
                    transactions.append(transaction)
                    
                except Exception as e:
                    logger.error(f"Error processing transaction event: {e}")
                    continue
            
            return transactions
            
        except Exception as e:
            logger.error(f"Error getting ERC20 transactions: {e}")
            return []
    
    async def _get_generic_token_transactions(self, token_address: str, from_block: int) -> List[Transaction]:
        """Get token transactions for non-EVM chains"""
        try:
            # This would be implemented differently for each blockchain
            # For now, return empty list
            return []
        except Exception as e:
            logger.error(f"Error getting generic token transactions: {e}")
            return []
    
    def _is_dex_address(self, address: str) -> bool:
        """Check if address is a known DEX"""
        # Known DEX addresses (this would be expanded)
        dex_addresses = {
            # Uniswap V2
            '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D',
            # Uniswap V3
            '0xE592427A0AEce92De3Edee1F18E0157C05861564',
            # SushiSwap
            '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F',
            # PancakeSwap
            '0x10ED43C718714eb63d5aA57B78B54704E256024E',
        }
        
        return address.lower() in [addr.lower() for addr in dex_addresses]
    
    def _get_dex_name(self, from_addr: str, to_addr: str) -> Optional[str]:
        """Get DEX name from addresses"""
        dex_mapping = {
            '0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D': 'Uniswap V2',
            '0xE592427A0AEce92De3Edee1F18E0157C05861564': 'Uniswap V3',
            '0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F': 'SushiSwap',
            '0x10ED43C718714eb63d5aA57B78B54704E256024E': 'PancakeSwap',
        }
        
        for addr in [from_addr, to_addr]:
            if addr.lower() in [k.lower() for k in dex_mapping.keys()]:
                return dex_mapping.get(addr)
        
        return None
    
    async def discover_tokens(self, limit: int = 100) -> List[Dict]:
        """Discover new tokens on the blockchain"""
        try:
            if hasattr(self, 'web3') and self.web3:
                return await self._discover_erc20_tokens(limit)
            else:
                return await self._discover_generic_tokens(limit)
        except Exception as e:
            logger.error(f"Error discovering tokens: {e}")
            return []
    
    async def _discover_erc20_tokens(self, limit: int) -> List[Dict]:
        """Discover ERC20 tokens by scanning recent blocks"""
        try:
            discovered_tokens = []
            latest_block = self.web3.eth.block_number
            
            # Scan last 100 blocks for token transfers
            for block_num in range(latest_block - 100, latest_block):
                try:
                    block = self.web3.eth.get_block(block_num, full_transactions=True)
                    
                    for tx in block['transactions']:
                        try:
                            # Check if transaction is to a contract
                            if tx['to']:
                                code = self.web3.eth.get_code(tx['to'])
                                if len(code) > 0:  # It's a contract
                                    # Try to get token info
                                    token_info = await self.get_token_info(tx['to'])
                                    if token_info and token_info['symbol'] != 'UNKNOWN':
                                        token_data = {
                                            'address': tx['to'],
                                            'symbol': token_info['symbol'],
                                            'name': token_info['name'],
                                            'decimals': token_info['decimals'],
                                            'verified': True
                                        }
                                        
                                        # Check if already discovered
                                        if not any(t['address'].lower() == tx['to'].lower() 
                                                 for t in discovered_tokens):
                                            discovered_tokens.append(token_data)
                                            
                                            if len(discovered_tokens) >= limit:
                                                return discovered_tokens
                        except:
                            continue
                except:
                    continue
            
            return discovered_tokens
            
        except Exception as e:
            logger.error(f"Error discovering ERC20 tokens: {e}")
            return []
    
    async def _discover_generic_tokens(self, limit: int) -> List[Dict]:
        """Discover tokens for non-EVM chains"""
        try:
            # This would be implemented differently for each blockchain
            return []
        except Exception as e:
            logger.error(f"Error discovering generic tokens: {e}")
            return []
    
    async def validate_address(self, address: str) -> bool:
        """Validate if an address is valid for this blockchain"""
        try:
            if hasattr(self, 'web3') and self.web3:
                # EVM address validation
                try:
                    Web3.to_checksum_address(address)
                    return True
                except:
                    return False
            else:
                # Generic validation - override in specific adapters
                return len(address) > 20  # Basic length check
        except Exception as e:
            logger.error(f"Error validating address: {e}")
            return False