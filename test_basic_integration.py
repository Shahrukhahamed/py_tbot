#!/usr/bin/env python3
"""
Basic Custom Blockchain Integration Test
Tests the core functionality without complex dependencies
"""

import sys
import os
import json
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_imports():
    """Test that all custom integration modules can be imported"""
    print("📦 Testing Module Imports...")
    
    try:
        # Test custom adapters
        from src.core.blockchain.adapters.custom_evm_adapter import CustomEVMAdapter
        from src.core.blockchain.adapters.custom_web3_adapter import CustomWeb3Adapter
        from src.core.blockchain.custom_integration import CustomBlockchainManager
        
        print("✅ Custom adapters imported successfully")
        
        # Test enhanced adapters factory
        from src.core.blockchain.adapters import BlockchainAdapters
        print("✅ Enhanced BlockchainAdapters imported successfully")
        
        # Test telegram handlers
        from src.interface.telegram.handlers import (
            add_custom_evm_chain,
            add_custom_web3_chain,
            remove_custom_chain,
            list_custom_chains,
            test_custom_chain,
            get_evm_template,
            get_web3_template
        )
        print("✅ Custom blockchain Telegram handlers imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        return False

def test_custom_evm_adapter_basic():
    """Test basic CustomEVMAdapter functionality"""
    print("🔧 Testing CustomEVMAdapter Basic Functionality...")
    
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
                "USDT": "0x1234567890123456789012345678901234567890"
            },
            "enabled": True
        }
        
        # Initialize adapter
        adapter = CustomEVMAdapter(config)
        
        # Test basic methods
        chain_info = adapter.get_chain_info()
        assert chain_info['name'] == "Test EVM Chain"
        assert chain_info['chain_id'] == 12345
        assert chain_info['symbol'] == "TEST"
        
        # Test token contracts
        supported_tokens = adapter.get_supported_tokens()
        assert "USDT" in supported_tokens
        
        # Test explorer URL generation
        tx_url = adapter.get_explorer_url('tx', '0xabcdef')
        assert "explorer.test-chain.com" in tx_url
        
        # Test address validation
        assert adapter.validate_address("0x1234567890123456789012345678901234567890") == True
        assert adapter.validate_address("invalid_address") == False
        
        print("✅ CustomEVMAdapter basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ CustomEVMAdapter basic test failed: {e}")
        return False

def test_custom_web3_adapter_basic():
    """Test basic CustomWeb3Adapter functionality"""
    print("🌐 Testing CustomWeb3Adapter Basic Functionality...")
    
    try:
        from src.core.blockchain.adapters.custom_web3_adapter import CustomWeb3Adapter
        
        # Test configuration
        config = {
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
                "get_block": "chain_getBlock"
            },
            "enabled": True
        }
        
        # Initialize adapter
        adapter = CustomWeb3Adapter(config)
        
        # Test basic methods
        chain_info = adapter.get_chain_info()
        assert chain_info['name'] == "Test Substrate Chain"
        assert chain_info['symbol'] == "DOT"
        assert chain_info['decimals'] == 10
        
        # Test network info
        network_info = adapter.get_network_info()
        assert network_info['chain_name'] == "Test Substrate Chain"
        assert network_info['chain_type'] == "substrate"
        
        # Test explorer URL generation
        tx_url = adapter.get_explorer_url('tx', 'test_hash')
        assert "explorer.test-substrate.com" in tx_url
        
        # Test custom method addition
        adapter.add_custom_method("get_runtime_version", "state_getRuntimeVersion")
        assert "get_runtime_version" in adapter.rpc_methods
        
        print("✅ CustomWeb3Adapter basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ CustomWeb3Adapter basic test failed: {e}")
        return False

def test_custom_integration_manager_basic():
    """Test basic CustomBlockchainManager functionality"""
    print("🏗️ Testing CustomBlockchainManager Basic Functionality...")
    
    try:
        from src.core.blockchain.custom_integration import CustomBlockchainManager
        
        # Initialize manager with test file
        test_config_file = "test_custom_chains.json"
        manager = CustomBlockchainManager(test_config_file)
        
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
        
        # Clean up test file
        if os.path.exists(test_config_file):
            os.remove(test_config_file)
        
        print("✅ CustomBlockchainManager basic tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ CustomBlockchainManager basic test failed: {e}")
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
        
        # Test template creation
        evm_template = adapters.create_evm_template()
        assert isinstance(evm_template, dict)
        assert "rpc_url" in evm_template
        
        web3_template = adapters.create_web3_template("substrate")
        assert isinstance(web3_template, dict)
        assert "chain_type" in web3_template
        
        # Test custom chain stats
        stats = adapters.get_custom_chain_stats()
        assert isinstance(stats, dict)
        assert "total_chains" in stats
        
        print("✅ BlockchainAdapters integration tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ BlockchainAdapters integration test failed: {e}")
        return False

def test_configuration_handling():
    """Test configuration file handling"""
    print("📄 Testing Configuration Handling...")
    
    try:
        from src.core.blockchain.custom_integration import CustomBlockchainManager
        
        # Test configuration creation and loading
        test_config_file = "test_config_handling.json"
        manager = CustomBlockchainManager(test_config_file)
        
        # Add a test chain
        test_config = {
            "name": "Config Test Chain",
            "type": "evm",
            "rpc_url": "https://test.com",
            "chain_id": 1234,
            "symbol": "TEST",
            "enabled": True
        }
        
        # Test saving and loading
        manager.add_custom_chain("config_test", test_config, save=True)
        
        # Create new manager instance to test loading
        manager2 = CustomBlockchainManager(test_config_file)
        chains = manager2.list_custom_chains()
        assert "config_test" in chains
        
        # Clean up
        if os.path.exists(test_config_file):
            os.remove(test_config_file)
        
        print("✅ Configuration handling tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Configuration handling test failed: {e}")
        return False

def main():
    """Run all basic integration tests"""
    print("🚀 Starting Basic Custom Blockchain Integration Tests...\n")
    
    tests = [
        test_imports,
        test_custom_evm_adapter_basic,
        test_custom_web3_adapter_basic,
        test_custom_integration_manager_basic,
        test_blockchain_adapters_integration,
        test_configuration_handling
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
    print(f"🏁 BASIC INTEGRATION TEST RESULTS:")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {passed + failed}")
    
    if failed == 0:
        print("\n🎉 All basic integration tests passed!")
        print("🚀 Custom blockchain integration features are working correctly!")
        
        # Show feature summary
        print("\n📋 CUSTOM BLOCKCHAIN INTEGRATION FEATURES:")
        print("🔗 Custom EVM Chain Integration")
        print("🌐 Custom Web3 Chain Integration (Substrate, Cosmos, Custom)")
        print("🏗️ Dynamic Blockchain Management")
        print("📱 Telegram Bot Commands for Custom Chains")
        print("🔧 Configuration Templates")
        print("📊 Chain Statistics and Monitoring")
        print("🧪 Connection Testing")
        
        return True
    else:
        print(f"\n⚠️ {failed} test(s) failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)