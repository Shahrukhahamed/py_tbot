"""
Comprehensive tests for token tracking system
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from src.core.tracking.token_tracker import TokenTracker, TrackingMode, TokenInfo, TrackingConfig
from src.core.tracking.token_integration import TokenIntegrationManager, TokenContract, TokenMetadata
from src.infrastructure.cache import CacheManager

class TestTokenTracker:
    """Test token tracking functionality"""
    
    @pytest.fixture
    def cache_manager(self):
        """Mock cache manager"""
        cache = Mock(spec=CacheManager)
        cache.get.return_value = None
        cache.set.return_value = None
        return cache
    
    @pytest.fixture
    def token_tracker(self, cache_manager):
        """Create token tracker instance"""
        return TokenTracker(cache_manager)
    
    def test_tracking_id_generation(self, token_tracker):
        """Test tracking ID generation"""
        tracking_id = token_tracker._get_tracking_id("ethereum", "0x1234567890abcdef")
        assert tracking_id == "ethereum:0x1234567890abcdef"
    
    def test_add_tracking_config(self, token_tracker):
        """Test adding tracking configuration"""
        user_id = "123456789"
        blockchain = "ethereum"
        token_address = "0x1234567890abcdef"
        mode = TrackingMode.BOTH
        
        success = token_tracker.add_tracking(user_id, blockchain, token_address, mode)
        assert success is True
        
        # Check if tracking was added
        trackings = token_tracker.get_user_trackings(user_id)
        assert len(trackings) == 1
        assert trackings[0]['blockchain'] == blockchain
        assert trackings[0]['token_address'] == token_address.lower()
        assert trackings[0]['mode'] == mode.value
    
    def test_remove_tracking_config(self, token_tracker):
        """Test removing tracking configuration"""
        user_id = "123456789"
        blockchain = "ethereum"
        token_address = "0x1234567890abcdef"
        mode = TrackingMode.BUY_ONLY
        
        # Add tracking first
        token_tracker.add_tracking(user_id, blockchain, token_address, mode)
        assert len(token_tracker.get_user_trackings(user_id)) == 1
        
        # Remove tracking
        success = token_tracker.remove_tracking(user_id, blockchain, token_address)
        assert success is True
        assert len(token_tracker.get_user_trackings(user_id)) == 0
    
    def test_tracking_stats(self, token_tracker):
        """Test tracking statistics"""
        # Add some trackings
        token_tracker.add_tracking("user1", "ethereum", "0x1111", TrackingMode.BUY_ONLY)
        token_tracker.add_tracking("user1", "bsc", "0x2222", TrackingMode.SELL_ONLY)
        token_tracker.add_tracking("user2", "polygon", "0x3333", TrackingMode.BOTH)
        
        stats = token_tracker.get_tracking_stats()
        
        assert stats['total_trackings'] == 3
        assert stats['total_subscribers'] == 2
        assert stats['mode_distribution']['buy_only'] == 1
        assert stats['mode_distribution']['sell_only'] == 1
        assert stats['mode_distribution']['both'] == 1

class TestTokenIntegration:
    """Test token integration functionality"""
    
    @pytest.fixture
    def cache_manager(self):
        """Mock cache manager"""
        cache = Mock(spec=CacheManager)
        cache.get.return_value = None
        cache.set.return_value = None
        return cache
    
    @pytest.fixture
    def token_integration(self, cache_manager):
        """Create token integration instance"""
        return TokenIntegrationManager(cache_manager)
    
    def test_search_tokens(self, token_integration):
        """Test token search functionality"""
        # Add some tokens
        token1 = TokenContract(
            address="0x1111", blockchain="ethereum", 
            symbol="USDT", name="Tether USD", decimals=6
        )
        token2 = TokenContract(
            address="0x2222", blockchain="ethereum", 
            symbol="USDC", name="USD Coin", decimals=6
        )
        
        token_integration.token_contracts["ethereum:0x1111"] = token1
        token_integration.token_contracts["ethereum:0x2222"] = token2
        
        # Search by symbol
        results = token_integration.search_tokens("USD")
        assert len(results) == 2
        
        # Search by blockchain
        results = token_integration.search_tokens("USD", "ethereum")
        assert len(results) == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])