#!/usr/bin/env python3
"""
Custom Blockchain Integration Test Suite
Tests the new custom EVM and Web3 blockchain integration features
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_custom_evm_adapter():
    """Test Custom EVM Adapter functionality"""
    print("🔧 Testing Custom EVM Adapter...")
    
    try:
        from src.core.blockchain.adapters.custom_evm_adapter import CustomEVMAdapter
        
        # Test configuration
        config = {
            "name": "Test EVM Chain",
            "rpc_url": "https://rpc.test-chain.com",
            "chain_id": 12345,
            "symbol": "TEST",
            "explorer_url": "https://explorer.test-chain.com",
            "gas_price_multiplier": 1.2,
            "block_time": 3,
            "confirmations": 6,
            "token_contracts": {
                "USDT": "0x1234567890123456789012345678901234567890",
                "USDC": "0x0987654321098765432109876543210987654321"
            }
        }
        
        # Initialize adapter
        adapter = CustomEVMAdapter(config)
        
        # Test basic functionality
        chain_info = adapter.get_chain_info()
        assert chain_info['name'] == "Test EVM Chain"
        assert chain_info['chain_id'] == 12345
        assert chain_info['symbol'] == "TEST"
        assert chain_info['type'] == "Custom EVM"
        
        # Test token contracts
        supported_tokens = adapter.get_supported_tokens()
        assert "USDT" in supported_tokens
        assert "USDC" in supported_tokens
        
        # Test explorer URL generation
        tx_url = adapter.get_explorer_url('tx', '0xabcdef')
        assert "explorer.test-chain.com" in tx_url
        assert "0xabcdef" in tx_url
        
        # Test address validation (basic format)
        assert adapter.validate_address("0x1234567890123456789012345678901234567890") == True
        assert adapter.validate_address("invalid_address") == False
        
        print("✅ Custom EVM Adapter tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Custom EVM Adapter test failed: {e}")
        return False

def test_custom_web3_adapter():
    """Test Custom Web3 Adapter functionality"""
    print("🌐 Testing Custom Web3 Adapter...")
    
    try:
        from src.core.blockchain.adapters.custom_web3_adapter import CustomWeb3Adapter
        
        # Test Substrate configuration
        substrate_config = {
            "name": "Test Substrate Chain",
            "chain_type": "substrate",
            "rpc_url": "wss://rpc.test-substrate.com",
            "symbol": "DOT",
            "decimals": 10,
            "explorer_url": "https://explorer.test-substrate.com",
            "block_time": 6,
            "address_format": r'^[1-9A-HJ-NP-Za-km-z]{47,48}$',
            "rpc_methods": {
                "get_block_number": "chain_getHeader",
                "get_block": "chain_getBlock",
                "get_balance": "system_account"
            }
        }
        
        # Initialize adapter
        adapter = CustomWeb3Adapter(substrate_config)
        
        # Test basic functionality
        chain_info = adapter.get_chain_info()
        assert chain_info['name'] == "Test Substrate Chain"
        assert chain_info['type'] == "Custom Web3 (substrate)"
        assert chain_info['symbol'] == "DOT"
        assert chain_info['decimals'] == 10
        
        # Test network info
        network_info = adapter.get_network_info()
        assert network_info['chain_name'] == "Test Substrate Chain"
        assert network_info['chain_type'] == "substrate"
        assert network_info['symbol'] == "DOT"
        
        # Test explorer URL generation
        tx_url = adapter.get_explorer_url('tx', 'test_extrinsic_hash')
        assert "explorer.test-substrate.com" in tx_url
        assert "extrinsic" in tx_url
        
        # Test custom method addition
        adapter.add_custom_method("get_runtime_version", "state_getRuntimeVersion")
        assert "get_runtime_version" in adapter.rpc_methods
        
        print("✅ Custom Web3 Adapter tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Custom Web3 Adapter test failed: {e}")
        return False

def test_custom_integration_manager():
    """Test Custom Blockchain Integration Manager"""
    print("🏗️ Testing Custom Integration Manager...")
    
    try:
        from src.core.blockchain.custom_integration import CustomBlockchainManager
        
        # Initialize manager
        manager = CustomBlockchainManager("test_custom_blockchains.json")
        
        # Test EVM chain addition
        evm_config = {
            "name": "Test EVM",
            "type": "evm",
            "rpc_url": "https://rpc.test-evm.com",
            "chain_id": 99999,
            "symbol": "TEVM",
            "explorer_url": "https://explorer.test-evm.com",
            "enabled": True
        }
        
        success = manager.add_custom_chain("test_evm", evm_config, save=False)
        assert success == True
        
        # Test Web3 chain addition
        web3_config = {
            "name": "Test Web3",
            "type": "web3",
            "chain_type": "cosmos",
            "rpc_url": "https://rpc.test-cosmos.com",
            "symbol": "TCOSM",
            "decimals": 6,
            "enabled": True
        }
        
        success = manager.add_custom_chain("test_web3", web3_config, save=False)
        assert success == True
        
        # Test chain listing
        chains = manager.list_custom_chains()
        assert "test_evm" in chains
        assert "test_web3" in chains
        
        # Test chain retrieval
        evm_adapter = manager.get_custom_chain("test_evm")
        assert evm_adapter is not None
        
        web3_adapter = manager.get_custom_chain("test_web3")
        assert web3_adapter is not None
        
        # Test statistics
        stats = manager.get_chain_stats()
        assert stats['total_chains'] >= 2
        assert stats['evm_chains'] >= 1
        assert stats['web3_chains'] >= 1
        
        # Test templates
        evm_template = manager.create_evm_chain_template()
        assert "rpc_url" in evm_template
        assert "chain_id" in evm_template
        
        web3_template = manager.create_web3_chain_template("substrate")
        assert "rpc_url" in web3_template
        assert "chain_type" in web3_template
        
        # Test chain removal
        success = manager.remove_custom_chain("test_evm", save=False)
        assert success == True
        
        success = manager.remove_custom_chain("test_web3", save=False)
        assert success == True
        
        print("✅ Custom Integration Manager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Custom Integration Manager test failed: {e}")
        return False

def test_blockchain_adapters_integration():
    """Test BlockchainAdapters integration with custom chains"""
    print("🔗 Testing BlockchainAdapters Integration...")
    
    try:
        from src.core.blockchain.adapters import BlockchainAdapters
        
        # Initialize adapters
        adapters = BlockchainAdapters()
        
        # Test built-in chains
        supported_chains = adapters.get_supported_chains()
        assert len(supported_chains) > 0
        assert "Ethereum" in supported_chains
        
        # Test EVM template creation
        evm_template = adapters.create_evm_template()
        assert isinstance(evm_template, dict)
        assert "rpc_url" in evm_template
        
        # Test Web3 template creation
        web3_template = adapters.create_web3_template("substrate")
        assert isinstance(web3_template, dict)
        assert "chain_type" in web3_template
        
        # Test custom chain stats
        stats = adapters.get_custom_chain_stats()
        assert isinstance(stats, dict)
        assert "total_chains" in stats
        
        print("✅ BlockchainAdapters Integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ BlockchainAdapters Integration test failed: {e}")
        return False

def test_telegram_handlers_import():
    """Test that new Telegram handlers can be imported"""
    print("📱 Testing Telegram Handlers Import...")
    
    try:
        from src.interface.telegram.handlers import (
            add_custom_evm_chain,
            add_custom_web3_chain,
            remove_custom_chain,
            list_custom_chains,
            test_custom_chain,
            get_evm_template,
            get_web3_template
        )
        
        # Check that handlers are callable
        assert callable(add_custom_evm_chain)
        assert callable(add_custom_web3_chain)
        assert callable(remove_custom_chain)
        assert callable(list_custom_chains)
        assert callable(test_custom_chain)
        assert callable(get_evm_template)
        assert callable(get_web3_template)
        
        print("✅ Telegram Handlers Import tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Telegram Handlers Import test failed: {e}")
        return False

def test_configuration_files():
    """Test configuration file handling"""
    print("📄 Testing Configuration Files...")
    
    try:
        # Test that config directory can be created
        config_dir = Path("config")
        config_dir.mkdir(exist_ok=True)
        
        # Test custom blockchain config creation
        from src.core.blockchain.custom_integration import CustomBlockchainManager
        
        test_config_file = "test_config.json"
        manager = CustomBlockchainManager(test_config_file)
        
        # Clean up test file
        if os.path.exists(test_config_file):
            os.remove(test_config_file)
        
        print("✅ Configuration Files tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration Files test failed: {e}")
        return False

def main():
    """Run all custom integration tests"""
    print("🚀 Starting Custom Blockchain Integration Tests...\n")
    
    tests = [
        test_custom_evm_adapter,
        test_custom_web3_adapter,
        test_custom_integration_manager,
        test_blockchain_adapters_integration,
        test_telegram_handlers_import,
        test_configuration_files
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            failed += 1
        print()
    
    print("=" * 60)
    print(f"🏁 CUSTOM INTEGRATION TEST RESULTS:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All custom blockchain integration tests passed!")
        print("🚀 Custom EVM and Web3 blockchain integration features are ready!")
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)