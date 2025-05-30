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

from config.settings import settings


class BlockchainAdapters:
    """Factory class for blockchain adapters"""
    
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
    
    @classmethod
    def get_adapter(cls, chain_name: str):
        """Get adapter instance for a blockchain"""
        if chain_name not in cls._adapters:
            raise ValueError(f"Unsupported blockchain: {chain_name}")
        
        adapter_class = cls._adapters[chain_name]
        blockchain_config = settings.BLOCKCHAINS['blockchains'].get(chain_name)
        
        if not blockchain_config:
            raise ValueError(f"No configuration found for blockchain: {chain_name}")
        
        return adapter_class(blockchain_config)
    
    @classmethod
    def get_explorer_url(cls, chain_name: str, url_type: str = 'tx', identifier: str = '') -> str:
        """Get explorer URL for a blockchain transaction or address"""
        base_url = cls._explorer_urls.get(chain_name, '')
        if not base_url:
            return ''
        
        if url_type == 'tx':
            return f"{base_url}/tx/{identifier}"
        elif url_type == 'address':
            return f"{base_url}/address/{identifier}"
        else:
            return base_url
    
    @classmethod
    def get_supported_chains(cls) -> list:
        """Get list of supported blockchain names"""
        return list(cls._adapters.keys())