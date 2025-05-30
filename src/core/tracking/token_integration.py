"""
Token Integration System for All Blockchains
Supports automatic token discovery and integration across all supported blockchains
"""

import json
import asyncio
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from src.utils.logger import get_logger
from src.core.blockchain.adapters import BlockchainAdapters
from src.core.blockchain.custom_integration import CustomBlockchainManager
from src.infrastructure.cache import CacheManager
from .models import TokenInfo

logger = get_logger(__name__)

@dataclass
class TokenContract:
    """Token contract information"""
    address: str
    blockchain: str
    symbol: str
    name: str
    decimals: int
    total_supply: Optional[int] = None
    verified: bool = False
    contract_type: str = "ERC20"  # ERC20, BEP20, SPL, etc.
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()

@dataclass
class TokenMetadata:
    """Extended token metadata"""
    contract: TokenContract
    price_usd: Optional[float] = None
    market_cap: Optional[float] = None
    volume_24h: Optional[float] = None
    holders_count: Optional[int] = None
    liquidity_usd: Optional[float] = None
    website: Optional[str] = None
    twitter: Optional[str] = None
    telegram: Optional[str] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []

class TokenIntegrationManager:
    """Manages token integration across all blockchains"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.blockchain_adapters = BlockchainAdapters()
        self.custom_manager = CustomBlockchainManager()
        
        # Token registries
        self.token_contracts: Dict[str, TokenContract] = {}
        self.token_metadata: Dict[str, TokenMetadata] = {}
        self.popular_tokens: Dict[str, List[str]] = {}  # blockchain -> token addresses
        
        # Load existing data
        self._load_token_contracts()
        self._load_token_metadata()
        self._load_popular_tokens()
    
    def _get_token_id(self, blockchain: str, address: str) -> str:
        """Generate unique token ID"""
        return f"{blockchain}:{address.lower()}"
    
    def _load_token_contracts(self):
        """Load token contracts from cache"""
        try:
            contracts_data = self.cache.get("token_contracts")
            if contracts_data:
                contracts = json.loads(contracts_data)
                for token_id, contract_data in contracts.items():
                    self.token_contracts[token_id] = TokenContract(**contract_data)
                logger.info(f"Loaded {len(self.token_contracts)} token contracts")
        except Exception as e:
            logger.error(f"Error loading token contracts: {e}")
    
    def _save_token_contracts(self):
        """Save token contracts to cache"""
        try:
            contracts_data = {}
            for token_id, contract in self.token_contracts.items():
                contracts_data[token_id] = asdict(contract)
            
            self.cache.set("token_contracts", json.dumps(contracts_data))
            logger.info(f"Saved {len(self.token_contracts)} token contracts")
        except Exception as e:
            logger.error(f"Error saving token contracts: {e}")
    
    def _load_token_metadata(self):
        """Load token metadata from cache"""
        try:
            metadata_data = self.cache.get("token_metadata")
            if metadata_data:
                metadata = json.loads(metadata_data)
                for token_id, meta_data in metadata.items():
                    # Reconstruct TokenContract from nested data
                    contract_data = meta_data.pop('contract')
                    contract = TokenContract(**contract_data)
                    meta_data['contract'] = contract
                    self.token_metadata[token_id] = TokenMetadata(**meta_data)
                logger.info(f"Loaded {len(self.token_metadata)} token metadata entries")
        except Exception as e:
            logger.error(f"Error loading token metadata: {e}")
    
    def _save_token_metadata(self):
        """Save token metadata to cache"""
        try:
            metadata_data = {}
            for token_id, metadata in self.token_metadata.items():
                meta_dict = asdict(metadata)
                metadata_data[token_id] = meta_dict
            
            self.cache.set("token_metadata", json.dumps(metadata_data))
            logger.info(f"Saved {len(self.token_metadata)} token metadata entries")
        except Exception as e:
            logger.error(f"Error saving token metadata: {e}")
    
    def _load_popular_tokens(self):
        """Load popular tokens list"""
        try:
            popular_data = self.cache.get("popular_tokens")
            if popular_data:
                self.popular_tokens = json.loads(popular_data)
                logger.info(f"Loaded popular tokens for {len(self.popular_tokens)} blockchains")
        except Exception as e:
            logger.error(f"Error loading popular tokens: {e}")
    
    def _save_popular_tokens(self):
        """Save popular tokens list"""
        try:
            self.cache.set("popular_tokens", json.dumps(self.popular_tokens))
            logger.info(f"Saved popular tokens for {len(self.popular_tokens)} blockchains")
        except Exception as e:
            logger.error(f"Error saving popular tokens: {e}")
    
    async def add_token(self, blockchain: str, address: str, **kwargs) -> bool:
        """Add a new token to the system"""
        try:
            token_id = self._get_token_id(blockchain, address)
            
            # Check if token already exists
            if token_id in self.token_contracts:
                logger.info(f"Token {token_id} already exists")
                return True
            
            # Get adapter for blockchain
            adapter = self.blockchain_adapters.get_adapter(blockchain)
            if not adapter:
                # Try custom blockchain
                custom_adapters = self.custom_manager.get_all_adapters()
                if blockchain in custom_adapters:
                    adapter = custom_adapters[blockchain]
                else:
                    logger.error(f"No adapter found for blockchain: {blockchain}")
                    return False
            
            # Fetch token information
            token_info = await self._fetch_token_contract_info(adapter, address, blockchain)
            if not token_info:
                # Create basic token info from provided data
                token_info = TokenContract(
                    address=address.lower(),
                    blockchain=blockchain,
                    symbol=kwargs.get('symbol', 'UNKNOWN'),
                    name=kwargs.get('name', 'Unknown Token'),
                    decimals=kwargs.get('decimals', 18),
                    verified=kwargs.get('verified', False)
                )
            
            # Store token contract
            self.token_contracts[token_id] = token_info
            
            # Create metadata if additional info provided
            if any(key in kwargs for key in ['price_usd', 'market_cap', 'website', 'description']):
                metadata = TokenMetadata(
                    contract=token_info,
                    price_usd=kwargs.get('price_usd'),
                    market_cap=kwargs.get('market_cap'),
                    volume_24h=kwargs.get('volume_24h'),
                    website=kwargs.get('website'),
                    twitter=kwargs.get('twitter'),
                    telegram=kwargs.get('telegram'),
                    description=kwargs.get('description'),
                    logo_url=kwargs.get('logo_url'),
                    tags=kwargs.get('tags', [])
                )
                self.token_metadata[token_id] = metadata
            
            # Save to cache
            self._save_token_contracts()
            if token_id in self.token_metadata:
                self._save_token_metadata()
            
            logger.info(f"Added token {token_info.symbol} on {blockchain}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding token {blockchain}:{address}: {e}")
            return False
    
    async def _fetch_token_contract_info(self, adapter, address: str, blockchain: str) -> Optional[TokenContract]:
        """Fetch token contract information from blockchain"""
        try:
            if hasattr(adapter, 'get_token_contract_info'):
                info = await adapter.get_token_contract_info(address)
                if info:
                    return TokenContract(
                        address=address.lower(),
                        blockchain=blockchain,
                        symbol=info.get('symbol', 'UNKNOWN'),
                        name=info.get('name', 'Unknown Token'),
                        decimals=info.get('decimals', 18),
                        total_supply=info.get('total_supply'),
                        verified=info.get('verified', False),
                        contract_type=info.get('contract_type', 'ERC20')
                    )
            
            # Fallback: try basic token info methods
            if hasattr(adapter, 'get_token_info'):
                info = await adapter.get_token_info(address)
                if info:
                    return TokenContract(
                        address=address.lower(),
                        blockchain=blockchain,
                        symbol=info.get('symbol', 'UNKNOWN'),
                        name=info.get('name', 'Unknown Token'),
                        decimals=info.get('decimals', 18),
                        verified=info.get('verified', False)
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching token contract info: {e}")
            return None
    
    def get_token(self, blockchain: str, address: str) -> Optional[TokenContract]:
        """Get token contract information"""
        token_id = self._get_token_id(blockchain, address)
        return self.token_contracts.get(token_id)
    
    def get_token_metadata(self, blockchain: str, address: str) -> Optional[TokenMetadata]:
        """Get token metadata"""
        token_id = self._get_token_id(blockchain, address)
        return self.token_metadata.get(token_id)
    
    def search_tokens(self, query: str, blockchain: Optional[str] = None) -> List[TokenContract]:
        """Search tokens by symbol, name, or address"""
        query = query.lower()
        results = []
        
        for token_id, contract in self.token_contracts.items():
            if blockchain and contract.blockchain != blockchain:
                continue
            
            if (query in contract.symbol.lower() or 
                query in contract.name.lower() or 
                query in contract.address.lower()):
                results.append(contract)
        
        return results[:50]  # Limit results
    
    def get_tokens_by_blockchain(self, blockchain: str) -> List[TokenContract]:
        """Get all tokens for a specific blockchain"""
        return [contract for contract in self.token_contracts.values() 
                if contract.blockchain == blockchain]
    
    def get_popular_tokens(self, blockchain: str) -> List[TokenContract]:
        """Get popular tokens for a blockchain"""
        if blockchain not in self.popular_tokens:
            return []
        
        popular_addresses = self.popular_tokens[blockchain]
        tokens = []
        
        for address in popular_addresses:
            token_id = self._get_token_id(blockchain, address)
            if token_id in self.token_contracts:
                tokens.append(self.token_contracts[token_id])
        
        return tokens
    
    def add_to_popular(self, blockchain: str, address: str):
        """Add token to popular list"""
        if blockchain not in self.popular_tokens:
            self.popular_tokens[blockchain] = []
        
        if address.lower() not in self.popular_tokens[blockchain]:
            self.popular_tokens[blockchain].append(address.lower())
            self._save_popular_tokens()
    
    def remove_from_popular(self, blockchain: str, address: str):
        """Remove token from popular list"""
        if blockchain in self.popular_tokens:
            try:
                self.popular_tokens[blockchain].remove(address.lower())
                self._save_popular_tokens()
            except ValueError:
                pass
    
    async def update_token_metadata(self, blockchain: str, address: str, **kwargs) -> bool:
        """Update token metadata"""
        try:
            token_id = self._get_token_id(blockchain, address)
            
            if token_id not in self.token_contracts:
                logger.error(f"Token {token_id} not found")
                return False
            
            contract = self.token_contracts[token_id]
            
            # Get existing metadata or create new
            if token_id in self.token_metadata:
                metadata = self.token_metadata[token_id]
            else:
                metadata = TokenMetadata(contract=contract)
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(metadata, key):
                    setattr(metadata, key, value)
            
            self.token_metadata[token_id] = metadata
            self._save_token_metadata()
            
            logger.info(f"Updated metadata for {token_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating token metadata: {e}")
            return False
    
    async def discover_tokens(self, blockchain: str, limit: int = 100) -> List[TokenContract]:
        """Discover new tokens on a blockchain"""
        try:
            adapter = self.blockchain_adapters.get_adapter(blockchain)
            if not adapter:
                # Try custom blockchain
                custom_adapters = self.custom_manager.get_all_adapters()
                if blockchain in custom_adapters:
                    adapter = custom_adapters[blockchain]
                else:
                    logger.error(f"No adapter found for blockchain: {blockchain}")
                    return []
            
            discovered_tokens = []
            
            if hasattr(adapter, 'discover_tokens'):
                tokens = await adapter.discover_tokens(limit)
                for token_data in tokens:
                    token_id = self._get_token_id(blockchain, token_data['address'])
                    if token_id not in self.token_contracts:
                        contract = TokenContract(
                            address=token_data['address'].lower(),
                            blockchain=blockchain,
                            symbol=token_data.get('symbol', 'UNKNOWN'),
                            name=token_data.get('name', 'Unknown Token'),
                            decimals=token_data.get('decimals', 18),
                            verified=token_data.get('verified', False)
                        )
                        self.token_contracts[token_id] = contract
                        discovered_tokens.append(contract)
            
            if discovered_tokens:
                self._save_token_contracts()
                logger.info(f"Discovered {len(discovered_tokens)} new tokens on {blockchain}")
            
            return discovered_tokens
            
        except Exception as e:
            logger.error(f"Error discovering tokens on {blockchain}: {e}")
            return []
    
    def get_supported_blockchains(self) -> List[str]:
        """Get list of supported blockchains for token integration"""
        supported = list(self.blockchain_adapters.get_supported_chains())
        
        # Add custom blockchains
        custom_adapters = self.custom_manager.get_all_adapters()
        supported.extend(custom_adapters.keys())
        
        return sorted(set(supported))
    
    def get_integration_stats(self) -> Dict:
        """Get token integration statistics"""
        blockchain_counts = {}
        verified_count = 0
        
        for contract in self.token_contracts.values():
            blockchain_counts[contract.blockchain] = blockchain_counts.get(contract.blockchain, 0) + 1
            if contract.verified:
                verified_count += 1
        
        return {
            'total_tokens': len(self.token_contracts),
            'verified_tokens': verified_count,
            'blockchain_distribution': blockchain_counts,
            'metadata_entries': len(self.token_metadata),
            'popular_tokens_count': sum(len(tokens) for tokens in self.popular_tokens.values()),
            'supported_blockchains': len(self.get_supported_blockchains())
        }
    
    async def validate_token_address(self, blockchain: str, address: str) -> bool:
        """Validate if a token address is valid for the blockchain"""
        try:
            adapter = self.blockchain_adapters.get_adapter(blockchain)
            if not adapter:
                # Try custom blockchain
                custom_adapters = self.custom_manager.get_all_adapters()
                if blockchain in custom_adapters:
                    adapter = custom_adapters[blockchain]
                else:
                    return False
            
            if hasattr(adapter, 'validate_address'):
                return await adapter.validate_address(address)
            
            # Basic validation for common address formats
            if blockchain in ['ethereum', 'bsc', 'polygon', 'avalanche', 'arbitrum', 'optimism', 'fantom']:
                return len(address) == 42 and address.startswith('0x')
            elif blockchain == 'solana':
                return 32 <= len(address) <= 44
            elif blockchain == 'tron':
                return len(address) == 34 and address.startswith('T')
            
            return True  # Default to valid for unknown blockchains
            
        except Exception as e:
            logger.error(f"Error validating address {address} on {blockchain}: {e}")
            return False
    
    def export_tokens(self, blockchain: Optional[str] = None) -> Dict:
        """Export token data"""
        tokens_data = {}
        
        for token_id, contract in self.token_contracts.items():
            if blockchain and contract.blockchain != blockchain:
                continue
            
            token_data = asdict(contract)
            
            # Add metadata if available
            if token_id in self.token_metadata:
                metadata = self.token_metadata[token_id]
                token_data['metadata'] = asdict(metadata)
                # Remove duplicate contract data
                del token_data['metadata']['contract']
            
            tokens_data[token_id] = token_data
        
        return tokens_data
    
    async def import_tokens(self, tokens_data: Dict) -> int:
        """Import token data"""
        imported_count = 0
        
        try:
            for token_id, token_data in tokens_data.items():
                # Extract metadata if present
                metadata_data = token_data.pop('metadata', None)
                
                # Create contract
                contract = TokenContract(**token_data)
                self.token_contracts[token_id] = contract
                
                # Create metadata if present
                if metadata_data:
                    metadata_data['contract'] = contract
                    metadata = TokenMetadata(**metadata_data)
                    self.token_metadata[token_id] = metadata
                
                imported_count += 1
            
            # Save to cache
            self._save_token_contracts()
            if any(token_id in self.token_metadata for token_id in tokens_data.keys()):
                self._save_token_metadata()
            
            logger.info(f"Imported {imported_count} tokens")
            return imported_count
            
        except Exception as e:
            logger.error(f"Error importing tokens: {e}")
            return imported_count