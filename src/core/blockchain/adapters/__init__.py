from .base_chain_adapter import BaseChainAdapter
from .ethereum_adapter import EthereumAdapter
from .bsc_adapter import BSCAdapter
from .polygon_adapter import PolygonAdapter
from .avalanche_adapter import AvalancheAdapter
from .arbitrum_adapter import ArbitrumAdapter
from .optimism_adapter import OptimismAdapter
from .fantom_adapter import FantomAdapter
from .pulsechain_adapter import PulsechainAdapter
from .solana_adapter import SolanaAdapter
from .tron_adapter import TronAdapter
from .dogecoin_adapter import DogecoinAdapter
from .polkadot_adapter import PolkadotAdapter
from .near_adapter import NearAdapter
from .algorand_adapter import AlgorandAdapter
from .ton_adapter import TonAdapter
from .pi_network_adapter import PiNetworkAdapter
from .cosmos_adapter import CosmosAdapter
from .osmosis_adapter import OsmosisAdapter
from .eos_adapter import EOSAdapter
from .custom_evm_adapter import CustomEVMAdapter
from .custom_web3_adapter import CustomWeb3Adapter

from config.settings import settings
from src.utils.logger import logger


class BlockchainAdapters:
    """Factory class for blockchain adapters with custom integration support"""
    
    _adapters = {
        'Ethereum': EthereumAdapter,
        'Binance Smart Chain': BSCAdapter,
        'Polygon': PolygonAdapter,
        'Avalanche': AvalancheAdapter,
        'Arbitrum': ArbitrumAdapter,
        'Optimism': OptimismAdapter,
        'Fantom': FantomAdapter,
        'PulseChain': PulsechainAdapter,
        'Solana': SolanaAdapter,
        'Tron': TronAdapter,
        'Dogecoin': DogecoinAdapter,
        'Polkadot': PolkadotAdapter,
        'Near': NearAdapter,
        'Algorand': AlgorandAdapter,
        'Ton': TonAdapter,
        'Pi Network': PiNetworkAdapter,
        'Cosmos': CosmosAdapter,
        'Osmosis': OsmosisAdapter,
        'EOS': EOSAdapter,
    }
    
    def __init__(self):
        """Initialize with custom blockchain integration support"""
        self.custom_adapters = {}
        self._load_custom_integrations()
    
    _explorer_urls = {
        'Ethereum': 'https://etherscan.io/tx/',
        'Binance Smart Chain': 'https://bscscan.com/tx/',
        'Polygon': 'https://polygonscan.com/tx/',
        'Avalanche': 'https://snowtrace.io/tx/',
        'Arbitrum': 'https://arbiscan.io/tx/',
        'Optimism': 'https://optimistic.etherscan.io/tx/',
        'Fantom': 'https://ftmscan.com/tx/',
        'PulseChain': 'https://scan.pulsechain.com/tx/',
        'Solana': 'https://solscan.io/tx/',
        'Tron': 'https://tronscan.org/#/transaction/',
        'Dogecoin': 'https://dogechain.info/tx/',
        'Polkadot': 'https://polkadot.subscan.io/extrinsic/',
        'Near': 'https://explorer.near.org/transactions/',
        'Algorand': 'https://algoexplorer.io/tx/',
        'Ton': 'https://tonscan.org/tx/',
        'Pi Network': 'https://blockexplorer.pi/',
        'Cosmos': 'https://www.mintscan.io/cosmos/txs/',
        'Osmosis': 'https://www.mintscan.io/osmosis/txs/',
        'EOS': 'https://bloks.io/transaction/',
    }
    
    def _load_custom_integrations(self):
        """Load custom blockchain integrations"""
        try:
            from ..custom_integration import custom_blockchain_manager
            self.custom_manager = custom_blockchain_manager
            self.custom_adapters = custom_blockchain_manager.get_all_custom_chains()
            logger.log(f"Loaded {len(self.custom_adapters)} custom blockchain integrations")
        except Exception as e:
            logger.log(f"Error loading custom integrations: {e}")
            self.custom_manager = None
    
    def get_adapter(self, chain_name: str):
        """Get adapter instance for a blockchain"""
        # Check custom adapters first
        if hasattr(self, 'custom_adapters') and chain_name in self.custom_adapters:
            return self.custom_adapters[chain_name]
        
        # Check built-in adapters
        if chain_name not in self._adapters:
            raise ValueError(f"Unsupported blockchain: {chain_name}")
        
        adapter_class = self._adapters[chain_name]
        blockchain_config = settings.BLOCKCHAINS.get('blockchains', {}).get(chain_name)
        
        if not blockchain_config:
            # Try to create adapter without config for basic functionality
            try:
                return adapter_class()
            except Exception as e:
                logger.log(f"Warning: Failed to initialize {chain_name} adapter: {e}")
                return None
        
        return adapter_class(blockchain_config)
    
    def get_explorer_url(self, chain_name: str, url_type: str = 'tx', identifier: str = '') -> str:
        """Get explorer URL for a blockchain transaction or address"""
        # Check custom adapters first
        if hasattr(self, 'custom_adapters') and chain_name in self.custom_adapters:
            adapter = self.custom_adapters[chain_name]
            if hasattr(adapter, 'get_explorer_url'):
                return adapter.get_explorer_url(url_type, identifier)
        
        # Check built-in explorer URLs
        base_url = self._explorer_urls.get(chain_name, '')
        if not base_url:
            return ''
        
        if url_type == 'tx':
            return f"{base_url}{identifier}"
        elif url_type == 'address':
            return base_url.replace('/tx/', '/address/') + identifier
        elif url_type == 'block':
            return base_url.replace('/tx/', '/block/') + identifier
        else:
            return base_url
    
    def get_supported_chains(self) -> list:
        """Get list of supported blockchain names including custom chains"""
        chains = list(self._adapters.keys())
        if hasattr(self, 'custom_adapters'):
            chains.extend(self.custom_adapters.keys())
        return chains
    
    def add_custom_evm_chain(self, chain_name: str, config: dict) -> bool:
        """Add a custom EVM-compatible blockchain"""
        if not hasattr(self, 'custom_manager') or not self.custom_manager:
            return False
        
        config['type'] = 'evm'
        success = self.custom_manager.add_custom_chain(chain_name, config)
        if success:
            self.custom_adapters = self.custom_manager.get_all_custom_chains()
        return success
    
    def add_custom_web3_chain(self, chain_name: str, config: dict) -> bool:
        """Add a custom Web3-compatible blockchain"""
        if not hasattr(self, 'custom_manager') or not self.custom_manager:
            return False
        
        config['type'] = 'web3'
        success = self.custom_manager.add_custom_chain(chain_name, config)
        if success:
            self.custom_adapters = self.custom_manager.get_all_custom_chains()
        return success
    
    def remove_custom_chain(self, chain_name: str) -> bool:
        """Remove a custom blockchain"""
        if not hasattr(self, 'custom_manager') or not self.custom_manager:
            return False
        
        success = self.custom_manager.remove_custom_chain(chain_name)
        if success:
            self.custom_adapters = self.custom_manager.get_all_custom_chains()
        return success
    
    def test_custom_chain(self, chain_name: str) -> dict:
        """Test connection to a custom blockchain"""
        if not hasattr(self, 'custom_manager') or not self.custom_manager:
            return {'success': False, 'error': 'Custom integration manager not available'}
        
        return self.custom_manager.test_chain_connection(chain_name)
    
    def get_custom_chain_stats(self) -> dict:
        """Get statistics for custom blockchains"""
        if not hasattr(self, 'custom_manager') or not self.custom_manager:
            return {'total_chains': 0, 'enabled_chains': 0}
        
        return self.custom_manager.get_chain_stats()
    
    def create_evm_template(self) -> dict:
        """Create a template for EVM chain configuration"""
        if not hasattr(self, 'custom_manager') or not self.custom_manager:
            return {}
        
        return self.custom_manager.create_evm_chain_template()
    
    def create_web3_template(self, chain_type: str = "substrate") -> dict:
        """Create a template for Web3 chain configuration"""
        if not hasattr(self, 'custom_manager') or not self.custom_manager:
            return {}
        
        return self.custom_manager.create_web3_chain_template(chain_type)