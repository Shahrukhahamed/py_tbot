"""
Custom Blockchain Integration Manager
Handles dynamic addition and management of custom blockchain integrations
"""

import json
import os
from typing import Dict, List, Optional, Any, Union
from .adapters.custom_evm_adapter import CustomEVMAdapter
from .adapters.custom_web3_adapter import CustomWeb3Adapter
from .adapters.base_chain_adapter import BaseChainAdapter
from src.utils.logger import logger

class CustomBlockchainManager:
    """
    Manager for custom blockchain integrations
    Supports both EVM and non-EVM blockchain integration
    """
    
    def __init__(self, config_file: str = "config/custom_blockchains.json"):
        self.config_file = config_file
        self.custom_chains: Dict[str, BaseChainAdapter] = {}
        self.chain_configs: Dict[str, Dict] = {}
        self.load_custom_chains()
    
    def load_custom_chains(self):
        """Load custom blockchain configurations from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    configs = json.load(f)
                
                for chain_name, config in configs.items():
                    self.add_custom_chain(chain_name, config, save=False)
                
                logger.log(f"Loaded {len(self.custom_chains)} custom blockchain configurations")
            else:
                logger.log("No custom blockchain configuration file found, creating default")
                self.create_default_config()
                
        except Exception as e:
            logger.log(f"Error loading custom blockchain configurations: {e}")
    
    def create_default_config(self):
        """Create default custom blockchain configuration file"""
        default_config = {
            "example_evm_chain": {
                "name": "Example EVM Chain",
                "type": "evm",
                "rpc_url": "https://rpc.example-evm-chain.com",
                "chain_id": 12345,
                "symbol": "EXAMPLE",
                "explorer_url": "https://explorer.example-evm-chain.com",
                "gas_price_multiplier": 1.2,
                "block_time": 3,
                "confirmations": 6,
                "token_contracts": {
                    "USDT": "0x...",
                    "USDC": "0x..."
                },
                "enabled": False
            },
            "example_substrate_chain": {
                "name": "Example Substrate Chain",
                "type": "web3",
                "chain_type": "substrate",
                "rpc_url": "wss://rpc.example-substrate.com",
                "symbol": "SUB",
                "explorer_url": "https://explorer.example-substrate.com",
                "decimals": 12,
                "block_time": 6,
                "address_format": "^[1-9A-HJ-NP-Za-km-z]{47,48}$",
                "rpc_methods": {
                    "get_block_number": "chain_getHeader",
                    "get_block": "chain_getBlock",
                    "get_balance": "system_account"
                },
                "enabled": False
            },
            "example_cosmos_chain": {
                "name": "Example Cosmos Chain",
                "type": "web3",
                "chain_type": "cosmos",
                "rpc_url": "https://rpc.example-cosmos.com",
                "symbol": "ATOM",
                "explorer_url": "https://explorer.example-cosmos.com",
                "decimals": 6,
                "block_time": 7,
                "address_format": "^cosmos[0-9a-z]{39}$",
                "rpc_methods": {
                    "get_block_number": "status",
                    "get_block": "block",
                    "get_balance": "bank/balances"
                },
                "enabled": False
            }
        }
        
        try:
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.log(f"Created default custom blockchain configuration: {self.config_file}")
        except Exception as e:
            logger.log(f"Error creating default configuration: {e}")
    
    def add_custom_chain(self, chain_name: str, config: Dict[str, Any], save: bool = True) -> bool:
        """
        Add a custom blockchain integration
        
        Args:
            chain_name: Unique name for the blockchain
            config: Configuration dictionary
            save: Whether to save to configuration file
        
        Returns:
            bool: Success status
        """
        try:
            if not config.get('enabled', True):
                logger.log(f"Custom chain {chain_name} is disabled, skipping")
                return False
            
            chain_type = config.get('type', 'web3').lower()
            
            if chain_type == 'evm':
                adapter = CustomEVMAdapter(config)
            elif chain_type == 'web3':
                adapter = CustomWeb3Adapter(config)
            else:
                logger.log(f"Unknown chain type: {chain_type}")
                return False
            
            self.custom_chains[chain_name] = adapter
            self.chain_configs[chain_name] = config
            
            if save:
                self.save_configuration()
            
            logger.log(f"Added custom blockchain: {chain_name} ({chain_type})")
            return True
            
        except Exception as e:
            logger.log(f"Error adding custom chain {chain_name}: {e}")
            return False
    
    def remove_custom_chain(self, chain_name: str, save: bool = True) -> bool:
        """Remove a custom blockchain integration"""
        try:
            if chain_name in self.custom_chains:
                del self.custom_chains[chain_name]
            
            if chain_name in self.chain_configs:
                del self.chain_configs[chain_name]
            
            if save:
                self.save_configuration()
            
            logger.log(f"Removed custom blockchain: {chain_name}")
            return True
            
        except Exception as e:
            logger.log(f"Error removing custom chain {chain_name}: {e}")
            return False
    
    def get_custom_chain(self, chain_name: str) -> Optional[BaseChainAdapter]:
        """Get a custom blockchain adapter"""
        return self.custom_chains.get(chain_name)
    
    def list_custom_chains(self) -> List[str]:
        """List all custom blockchain names"""
        return list(self.custom_chains.keys())
    
    def get_all_custom_chains(self) -> Dict[str, BaseChainAdapter]:
        """Get all custom blockchain adapters"""
        return self.custom_chains.copy()
    
    def save_configuration(self):
        """Save current configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.chain_configs, f, indent=2)
            logger.log("Saved custom blockchain configuration")
        except Exception as e:
            logger.log(f"Error saving configuration: {e}")
    
    def update_chain_config(self, chain_name: str, updates: Dict[str, Any]) -> bool:
        """Update configuration for a custom chain"""
        try:
            if chain_name not in self.chain_configs:
                logger.log(f"Custom chain {chain_name} not found")
                return False
            
            self.chain_configs[chain_name].update(updates)
            
            # Recreate adapter with new config
            config = self.chain_configs[chain_name]
            if config.get('enabled', True):
                self.add_custom_chain(chain_name, config, save=False)
            
            self.save_configuration()
            logger.log(f"Updated configuration for {chain_name}")
            return True
            
        except Exception as e:
            logger.log(f"Error updating chain config for {chain_name}: {e}")
            return False
    
    def enable_chain(self, chain_name: str) -> bool:
        """Enable a custom chain"""
        return self.update_chain_config(chain_name, {'enabled': True})
    
    def disable_chain(self, chain_name: str) -> bool:
        """Disable a custom chain"""
        if chain_name in self.custom_chains:
            del self.custom_chains[chain_name]
        return self.update_chain_config(chain_name, {'enabled': False})
    
    def test_chain_connection(self, chain_name: str) -> Dict[str, Any]:
        """Test connection to a custom chain"""
        try:
            adapter = self.get_custom_chain(chain_name)
            if not adapter:
                return {'success': False, 'error': 'Chain not found'}
            
            # Test basic functionality
            current_block = adapter.get_current_block()
            
            if hasattr(adapter, 'get_network_info'):
                network_info = adapter.get_network_info()
            elif hasattr(adapter, 'get_network_stats'):
                network_info = adapter.get_network_stats()
            else:
                network_info = {'current_block': current_block}
            
            return {
                'success': True,
                'chain_name': chain_name,
                'current_block': current_block,
                'network_info': network_info
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_chain_stats(self) -> Dict[str, Any]:
        """Get statistics for all custom chains"""
        stats = {
            'total_chains': len(self.custom_chains),
            'enabled_chains': len([c for c in self.chain_configs.values() if c.get('enabled', True)]),
            'evm_chains': len([c for c in self.chain_configs.values() if c.get('type') == 'evm']),
            'web3_chains': len([c for c in self.chain_configs.values() if c.get('type') == 'web3']),
            'chains': {}
        }
        
        for chain_name, adapter in self.custom_chains.items():
            try:
                current_block = adapter.get_current_block()
                stats['chains'][chain_name] = {
                    'type': self.chain_configs[chain_name].get('type', 'unknown'),
                    'current_block': current_block,
                    'connected': current_block > 0
                }
            except Exception as e:
                stats['chains'][chain_name] = {
                    'type': self.chain_configs[chain_name].get('type', 'unknown'),
                    'connected': False,
                    'error': str(e)
                }
        
        return stats
    
    def create_evm_chain_template(self) -> Dict[str, Any]:
        """Create a template for EVM chain configuration"""
        return {
            "name": "New EVM Chain",
            "type": "evm",
            "rpc_url": "https://rpc.your-chain.com",
            "chain_id": 1,
            "symbol": "ETH",
            "explorer_url": "https://explorer.your-chain.com",
            "gas_price_multiplier": 1.0,
            "block_time": 15,
            "confirmations": 12,
            "token_contracts": {
                "USDT": "0x...",
                "USDC": "0x...",
                "DAI": "0x..."
            },
            "enabled": True
        }
    
    def create_web3_chain_template(self, chain_type: str = "substrate") -> Dict[str, Any]:
        """Create a template for Web3 chain configuration"""
        templates = {
            "substrate": {
                "name": "New Substrate Chain",
                "type": "web3",
                "chain_type": "substrate",
                "rpc_url": "wss://rpc.your-substrate-chain.com",
                "symbol": "DOT",
                "explorer_url": "https://explorer.your-substrate-chain.com",
                "decimals": 10,
                "block_time": 6,
                "address_format": "^[1-9A-HJ-NP-Za-km-z]{47,48}$",
                "rpc_methods": {
                    "get_block_number": "chain_getHeader",
                    "get_block": "chain_getBlock",
                    "get_balance": "system_account"
                },
                "enabled": True
            },
            "cosmos": {
                "name": "New Cosmos Chain",
                "type": "web3",
                "chain_type": "cosmos",
                "rpc_url": "https://rpc.your-cosmos-chain.com",
                "symbol": "ATOM",
                "explorer_url": "https://explorer.your-cosmos-chain.com",
                "decimals": 6,
                "block_time": 7,
                "address_format": "^cosmos[0-9a-z]{39}$",
                "rpc_methods": {
                    "get_block_number": "status",
                    "get_block": "block",
                    "get_balance": "bank/balances"
                },
                "enabled": True
            }
        }
        
        return templates.get(chain_type, templates["substrate"])

# Global instance
custom_blockchain_manager = CustomBlockchainManager()