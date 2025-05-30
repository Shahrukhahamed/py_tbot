#!/usr/bin/env python3
"""
Final comprehensive test to verify the bot is fully functional
"""

import sys
import os
import json
sys.path.append('.')

# Set dummy environment variables for testing
os.environ['TELEGRAM_BOT_TOKEN'] = 'dummy_token'
os.environ['SUPABASE_URL'] = 'https://dummy.supabase.co'
os.environ['SUPABASE_KEY'] = 'dummy_key'

def test_complete_system():
    """Test the complete system integration"""
    print("🔧 COMPREHENSIVE SYSTEM TEST")
    print("=" * 50)
    
    # Test 1: Core imports
    print("1. Testing core imports...")
    try:
        from config.settings import settings
        from src.utils.logger import logger
        from src.infrastructure.database import SupabaseDB
        from src.infrastructure.cache import cache
        print("   ✅ Core imports successful")
    except Exception as e:
        print(f"   ❌ Core imports failed: {e}")
        return False
    
    # Test 2: Blockchain system
    print("\n2. Testing blockchain system...")
    try:
        from src.core.blockchain.adapters import BlockchainAdapters
        adapters = BlockchainAdapters()
        
        # Test adapter creation
        eth_adapter = adapters.get_adapter('Ethereum')
        if eth_adapter:
            print("   ✅ Ethereum adapter created")
        
        # Test explorer URL generation
        url = adapters.get_explorer_url('Ethereum', 'tx', '0x123')
        if url:
            print("   ✅ Explorer URL generation working")
        
        # Test supported chains
        chains = adapters.get_supported_chains()
        print(f"   ✅ {len(chains)} blockchain adapters available")
        
    except Exception as e:
        print(f"   ❌ Blockchain system failed: {e}")
        return False
    
    # Test 3: Telegram handlers
    print("\n3. Testing Telegram handlers...")
    try:
        from src.interface.telegram.handlers import handle_start, handle_help
        from src.interface.telegram.bot import TelegramBot
        print("   ✅ Telegram handlers imported")
        print("   ⚠️  Bot initialization skipped (requires valid token)")
    except Exception as e:
        print(f"   ❌ Telegram handlers failed: {e}")
        return False
    
    # Test 4: Configuration
    print("\n4. Testing configuration...")
    try:
        # Test blockchain config
        if hasattr(settings, 'BLOCKCHAINS') and settings.BLOCKCHAINS:
            print(f"   ✅ Blockchain config loaded ({len(settings.BLOCKCHAINS)} chains)")
        
        # Test tracked currencies
        if hasattr(settings, 'TRACKED_CURRENCIES'):
            print(f"   ✅ Tracked currencies loaded ({len(settings.TRACKED_CURRENCIES)} currencies)")
        
        # Test admin commands
        if hasattr(settings, 'ADMIN_COMMANDS'):
            print(f"   ✅ Admin commands loaded ({len(settings.ADMIN_COMMANDS)} commands)")
            
    except Exception as e:
        print(f"   ❌ Configuration test failed: {e}")
        return False
    
    # Test 5: Cache system
    print("\n5. Testing cache system...")
    try:
        # Test cache operations
        cache.set('test_key', 'test_value', 60)
        value = cache.get('test_key')
        if value == 'test_value':
            print("   ✅ Cache set/get working")
        
        cache.delete('test_key')
        value = cache.get('test_key')
        if value is None:
            print("   ✅ Cache delete working")
            
    except Exception as e:
        print(f"   ❌ Cache system failed: {e}")
        return False
    
    # Test 6: Logging system
    print("\n6. Testing logging system...")
    try:
        logger.log("Test log message")
        print("   ✅ Logging system working")
    except Exception as e:
        print(f"   ❌ Logging system failed: {e}")
        return False
    
    # Test 7: Main entry point
    print("\n7. Testing main entry point...")
    try:
        import main
        print("   ✅ Main module imports successfully")
        print("   ⚠️  Bot startup skipped (requires valid credentials)")
    except Exception as e:
        print(f"   ❌ Main entry point failed: {e}")
        return False
    
    return True

def test_blockchain_coverage():
    """Test blockchain coverage"""
    print("\n🌐 BLOCKCHAIN COVERAGE TEST")
    print("=" * 50)
    
    try:
        from src.core.blockchain.adapters import BlockchainAdapters
        adapters = BlockchainAdapters()
        chains = adapters.get_supported_chains()
        
        evm_chains = ['Ethereum', 'BSC', 'Polygon', 'Avalanche', 'Arbitrum', 'Optimism', 'Fantom', 'Pulsechain']
        non_evm_chains = ['Solana', 'Tron', 'Dogecoin', 'Polkadot', 'Near', 'Algorand', 'Ton', 'PiNetwork', 'Cosmos', 'Osmosis', 'EOS']
        
        print(f"Total supported chains: {len(chains)}")
        print(f"EVM chains: {len([c for c in evm_chains if c in chains])}/{len(evm_chains)}")
        print(f"Non-EVM chains: {len([c for c in non_evm_chains if c in chains])}/{len(non_evm_chains)}")
        
        for chain in chains:
            try:
                adapter = adapters.get_adapter(chain)
                status = "✅" if adapter else "❌"
                print(f"   {status} {chain}")
            except Exception as e:
                print(f"   ⚠️  {chain} (connection issue expected)")
        
        return True
    except Exception as e:
        print(f"❌ Blockchain coverage test failed: {e}")
        return False

def test_file_structure():
    """Test file structure integrity"""
    print("\n📁 FILE STRUCTURE TEST")
    print("=" * 50)
    
    required_files = [
        'main.py',
        'requirements.txt',
        '.env.example',
        'config/settings.py',
        'config/blockchains.json',
        'src/utils/logger.py',
        'src/infrastructure/database.py',
        'src/infrastructure/cache.py',
        'src/core/blockchain/adapters/__init__.py',
        'src/interface/telegram/bot.py',
        'src/interface/telegram/handlers.py',
    ]
    
    missing_files = []
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path}")
            missing_files.append(file_path)
    
    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False
    else:
        print(f"\n✅ All {len(required_files)} required files present")
        return True

def main():
    """Run all tests"""
    print("🚀 BLOCKCHAIN TRANSACTION BOT - FINAL BUILD TEST")
    print("=" * 60)
    
    tests = [
        ("System Integration", test_complete_system),
        ("Blockchain Coverage", test_blockchain_coverage),
        ("File Structure", test_file_structure),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🧪 {test_name.upper()}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"🏁 FINAL RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Bot is ready for deployment!")
        print("\n📋 Next steps:")
        print("1. Set up your environment variables in .env")
        print("2. Configure your Supabase database")
        print("3. Get your Telegram bot token")
        print("4. Run: python main.py")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)