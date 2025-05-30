#!/usr/bin/env python3
"""
Test script to verify the bot can be built and imported correctly
"""

import sys
import os
sys.path.append('.')

# Set dummy environment variables for testing
os.environ['TELEGRAM_BOT_TOKEN'] = 'dummy_token'
os.environ['SUPABASE_URL'] = 'https://dummy.supabase.co'
os.environ['SUPABASE_KEY'] = 'dummy_key'

def test_imports():
    """Test all critical imports"""
    print("Testing imports...")
    
    try:
        from config.settings import settings
        print("✓ Settings imported successfully")
    except Exception as e:
        print(f"✗ Settings import failed: {e}")
        return False
    
    try:
        from src.utils.logger import logger
        print("✓ Logger imported successfully")
    except Exception as e:
        print(f"✗ Logger import failed: {e}")
        return False
    
    try:
        from src.infrastructure.database import SupabaseDB
        print("✓ Database imported successfully")
    except Exception as e:
        print(f"✗ Database import failed: {e}")
        return False
    
    try:
        from src.infrastructure.cache import cache
        print("✓ Cache imported successfully")
    except Exception as e:
        print(f"✗ Cache import failed: {e}")
        return False
    
    try:
        from src.core.blockchain.adapters import BlockchainAdapters
        print("✓ Blockchain adapters imported successfully")
    except Exception as e:
        print(f"✗ Blockchain adapters import failed: {e}")
        return False
    
    try:
        from src.interface.telegram.handlers import handle_start
        print("✓ Telegram handlers imported successfully")
    except Exception as e:
        print(f"✗ Telegram handlers import failed: {e}")
        # This is expected if database credentials are not set
        if "Invalid API key" in str(e):
            print("  (This is expected without valid database credentials)")
        else:
            return False
    
    return True

def test_adapter_creation():
    """Test adapter creation"""
    print("\nTesting adapter creation...")
    
    try:
        from src.core.blockchain.adapters import BlockchainAdapters
        adapters = BlockchainAdapters()
        
        # Test getting an adapter
        eth_adapter = adapters.get_adapter('Ethereum')
        if eth_adapter:
            print("✓ Ethereum adapter created successfully")
        else:
            print("✗ Failed to create Ethereum adapter")
            return False
        
        # Test getting explorer URL
        explorer_url = adapters.get_explorer_url('Ethereum', 'tx', '0x123')
        if explorer_url:
            print("✓ Explorer URL generation works")
        else:
            print("✗ Explorer URL generation failed")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Adapter creation failed: {e}")
        return False

def test_configuration():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from config.settings import settings
        
        # Test blockchain config loading
        if hasattr(settings, 'BLOCKCHAINS') and settings.BLOCKCHAINS:
            print(f"✓ Loaded {len(settings.BLOCKCHAINS)} blockchain configurations")
        else:
            print("✗ Failed to load blockchain configurations")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("=" * 50)
    print("BLOCKCHAIN TRANSACTION BOT - BUILD TEST")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_configuration,
        test_adapter_creation,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("✓ All tests passed! Bot is ready to build.")
        return True
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)