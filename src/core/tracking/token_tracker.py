"""
Multi-Blockchain Token Tracking System
Supports tracking multiple tokens across all blockchains with buy/sell filtering
"""

import asyncio
import json
import time
from typing import Dict, List, Optional, Set, Any
from dataclasses import asdict
from datetime import datetime, timedelta

from src.utils.logger import get_logger
from src.core.blockchain.adapters import BlockchainAdapters
from src.infrastructure.cache import CacheManager
from .models import TrackingMode, TransactionType, TokenInfo, TrackingConfig, Transaction

logger = get_logger(__name__)

class TokenTracker:
    """Multi-blockchain token tracking system"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.blockchain_adapters = BlockchainAdapters()
        self.tracking_configs: Dict[str, TrackingConfig] = {}
        self.token_cache: Dict[str, TokenInfo] = {}
        self.active_trackers: Dict[str, asyncio.Task] = {}
        self.subscribers: Dict[str, Set[str]] = {}  # user_id -> set of tracking_ids
        
        # Load existing configurations
        self._load_tracking_configs()
        self._load_token_cache()
        self._load_subscribers()
    
    def _get_tracking_id(self, blockchain: str, token_address: str) -> str:
        """Generate unique tracking ID"""
        return f"{blockchain}:{token_address.lower()}"
    
    def _load_tracking_configs(self):
        """Load tracking configurations from cache"""
        try:
            configs_data = self.cache.get("token_tracking_configs")
            if configs_data:
                configs = json.loads(configs_data)
                for tracking_id, config_data in configs.items():
                    config_data['mode'] = TrackingMode(config_data['mode'])
                    self.tracking_configs[tracking_id] = TrackingConfig(**config_data)
                logger.info(f"Loaded {len(self.tracking_configs)} tracking configurations")
        except Exception as e:
            logger.error(f"Error loading tracking configs: {e}")
    
    def _save_tracking_configs(self):
        """Save tracking configurations to cache"""
        try:
            configs_data = {}
            for tracking_id, config in self.tracking_configs.items():
                config_dict = asdict(config)
                config_dict['mode'] = config.mode.value
                configs_data[tracking_id] = config_dict
            
            self.cache.set("token_tracking_configs", json.dumps(configs_data))
            logger.info(f"Saved {len(self.tracking_configs)} tracking configurations")
        except Exception as e:
            logger.error(f"Error saving tracking configs: {e}")
    
    def _load_token_cache(self):
        """Load token information cache"""
        try:
            token_data = self.cache.get("token_info_cache")
            if token_data:
                tokens = json.loads(token_data)
                for token_id, token_info in tokens.items():
                    self.token_cache[token_id] = TokenInfo(**token_info)
                logger.info(f"Loaded {len(self.token_cache)} tokens from cache")
        except Exception as e:
            logger.error(f"Error loading token cache: {e}")
    
    def _save_token_cache(self):
        """Save token information cache"""
        try:
            tokens_data = {}
            for token_id, token_info in self.token_cache.items():
                tokens_data[token_id] = asdict(token_info)
            
            self.cache.set("token_info_cache", json.dumps(tokens_data))
            logger.info(f"Saved {len(self.token_cache)} tokens to cache")
        except Exception as e:
            logger.error(f"Error saving token cache: {e}")
    
    async def get_token_info(self, blockchain: str, token_address: str) -> Optional[TokenInfo]:
        """Get token information from blockchain or cache"""
        token_id = f"{blockchain}:{token_address.lower()}"
        
        # Check cache first
        if token_id in self.token_cache:
            return self.token_cache[token_id]
        
        try:
            adapter = self.blockchain_adapters.get_adapter(blockchain)
            if not adapter:
                logger.error(f"No adapter found for blockchain: {blockchain}")
                return None
            
            # Get token info from blockchain
            token_info = await self._fetch_token_info(adapter, token_address, blockchain)
            if token_info:
                self.token_cache[token_id] = token_info
                self._save_token_cache()
                return token_info
                
        except Exception as e:
            logger.error(f"Error getting token info for {blockchain}:{token_address}: {e}")
        
        return None
    
    async def _fetch_token_info(self, adapter, token_address: str, blockchain: str) -> Optional[TokenInfo]:
        """Fetch token information from blockchain adapter"""
        try:
            # Try to get token info using adapter methods
            if hasattr(adapter, 'get_token_info'):
                info = await adapter.get_token_info(token_address)
                if info:
                    return TokenInfo(
                        address=token_address,
                        symbol=info.get('symbol', 'UNKNOWN'),
                        name=info.get('name', 'Unknown Token'),
                        decimals=info.get('decimals', 18),
                        blockchain=blockchain,
                        verified=info.get('verified', False)
                    )
            
            # Fallback: create basic token info
            return TokenInfo(
                address=token_address,
                symbol='UNKNOWN',
                name='Unknown Token',
                decimals=18,
                blockchain=blockchain,
                verified=False
            )
            
        except Exception as e:
            logger.error(f"Error fetching token info: {e}")
            return None
    
    def add_tracking(self, user_id: str, blockchain: str, token_address: str, 
                    mode: TrackingMode, **kwargs) -> bool:
        """Add token tracking configuration"""
        try:
            tracking_id = self._get_tracking_id(blockchain, token_address)
            
            # Create tracking config
            config = TrackingConfig(
                token_address=token_address.lower(),
                blockchain=blockchain,
                mode=mode,
                min_amount=kwargs.get('min_amount'),
                max_amount=kwargs.get('max_amount'),
                whale_threshold=kwargs.get('whale_threshold')
            )
            
            self.tracking_configs[tracking_id] = config
            
            # Add user subscription
            if user_id not in self.subscribers:
                self.subscribers[user_id] = set()
            self.subscribers[user_id].add(tracking_id)
            
            # Save configurations
            self._save_tracking_configs()
            self._save_subscribers()
            
            # Start tracking if not already active
            if tracking_id not in self.active_trackers:
                self._start_tracking(tracking_id)
            
            logger.info(f"Added tracking for {blockchain}:{token_address} (mode: {mode.value})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding tracking: {e}")
            return False
    
    def remove_tracking(self, user_id: str, blockchain: str, token_address: str) -> bool:
        """Remove token tracking for user"""
        try:
            tracking_id = self._get_tracking_id(blockchain, token_address)
            
            # Remove user subscription
            if user_id in self.subscribers and tracking_id in self.subscribers[user_id]:
                self.subscribers[user_id].remove(tracking_id)
                if not self.subscribers[user_id]:
                    del self.subscribers[user_id]
            
            # Check if any users still subscribed
            still_subscribed = any(tracking_id in subs for subs in self.subscribers.values())
            
            if not still_subscribed:
                # Stop tracking and remove config
                if tracking_id in self.active_trackers:
                    self.active_trackers[tracking_id].cancel()
                    del self.active_trackers[tracking_id]
                
                if tracking_id in self.tracking_configs:
                    del self.tracking_configs[tracking_id]
            
            self._save_tracking_configs()
            self._save_subscribers()
            
            logger.info(f"Removed tracking for {blockchain}:{token_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error removing tracking: {e}")
            return False
    
    def get_user_trackings(self, user_id: str) -> List[Dict]:
        """Get all trackings for a user"""
        if user_id not in self.subscribers:
            return []
        
        trackings = []
        for tracking_id in self.subscribers[user_id]:
            if tracking_id in self.tracking_configs:
                config = self.tracking_configs[tracking_id]
                token_id = f"{config.blockchain}:{config.token_address}"
                token_info = self.token_cache.get(token_id)
                
                tracking_data = {
                    'tracking_id': tracking_id,
                    'blockchain': config.blockchain,
                    'token_address': config.token_address,
                    'mode': config.mode.value,
                    'enabled': config.enabled,
                    'token_symbol': token_info.symbol if token_info else 'UNKNOWN',
                    'token_name': token_info.name if token_info else 'Unknown Token'
                }
                trackings.append(tracking_data)
        
        return trackings
    
    def _start_tracking(self, tracking_id: str):
        """Start tracking task for a token"""
        if tracking_id in self.active_trackers:
            return
        
        config = self.tracking_configs.get(tracking_id)
        if not config or not config.enabled:
            return
        
        try:
            task = asyncio.create_task(self._track_token(tracking_id))
            self.active_trackers[tracking_id] = task
            logger.info(f"Started tracking task for {tracking_id}")
        except RuntimeError:
            # No event loop running - this is expected in tests
            logger.info(f"No event loop for tracking {tracking_id} - will start when bot runs")
    
    async def _track_token(self, tracking_id: str):
        """Main tracking loop for a token"""
        config = self.tracking_configs.get(tracking_id)
        if not config:
            return
        
        adapter = self.blockchain_adapters.get_adapter(config.blockchain)
        if not adapter:
            logger.error(f"No adapter for blockchain: {config.blockchain}")
            return
        
        last_block = await self._get_last_processed_block(tracking_id)
        
        while config.enabled:
            try:
                # Get latest transactions
                transactions = await self._get_token_transactions(
                    adapter, config.token_address, last_block
                )
                
                for tx in transactions:
                    if self._should_notify_transaction(tx, config):
                        await self._notify_subscribers(tracking_id, tx)
                
                # Update last processed block
                if transactions:
                    latest_block = max(tx.block_number for tx in transactions)
                    await self._save_last_processed_block(tracking_id, latest_block)
                
                # Wait before next check
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in tracking loop for {tracking_id}: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _get_token_transactions(self, adapter, token_address: str, 
                                    from_block: int) -> List[Transaction]:
        """Get token transactions from blockchain"""
        try:
            if hasattr(adapter, 'get_token_transactions'):
                return await adapter.get_token_transactions(token_address, from_block)
            else:
                # Fallback implementation
                return await self._fallback_get_transactions(adapter, token_address, from_block)
        except Exception as e:
            logger.error(f"Error getting token transactions: {e}")
            return []
    
    async def _fallback_get_transactions(self, adapter, token_address: str, 
                                       from_block: int) -> List[Transaction]:
        """Fallback method to get transactions"""
        # This would implement basic transaction fetching
        # For now, return empty list
        return []
    
    def _should_notify_transaction(self, transaction: Transaction, config: TrackingConfig) -> bool:
        """Check if transaction should trigger notification"""
        # Check tracking mode
        if config.mode == TrackingMode.BUY_ONLY and transaction.transaction_type != TransactionType.BUY:
            return False
        if config.mode == TrackingMode.SELL_ONLY and transaction.transaction_type != TransactionType.SELL:
            return False
        
        # Check amount filters
        if config.min_amount and transaction.amount < config.min_amount:
            return False
        if config.max_amount and transaction.amount > config.max_amount:
            return False
        
        return True
    
    async def _notify_subscribers(self, tracking_id: str, transaction: Transaction):
        """Notify all subscribers about transaction"""
        # Get subscribers for this tracking
        subscribers = [user_id for user_id, subs in self.subscribers.items() 
                      if tracking_id in subs]
        
        if not subscribers:
            return
        
        # Format notification message
        message = self._format_transaction_message(transaction)
        
        # Send notifications (this would integrate with Telegram bot)
        for user_id in subscribers:
            await self._send_notification(user_id, message)
    
    def _format_transaction_message(self, tx: Transaction) -> str:
        """Format transaction for notification"""
        emoji = "🟢" if tx.transaction_type == TransactionType.BUY else "🔴"
        whale_emoji = "🐋" if tx.is_whale else ""
        
        message = f"{emoji}{whale_emoji} **{tx.transaction_type.value.upper()}** on {tx.blockchain}\n"
        message += f"Token: {tx.token_symbol}\n"
        message += f"Amount: {tx.amount:,.2f} {tx.token_symbol}\n"
        
        if tx.amount_usd:
            message += f"Value: ${tx.amount_usd:,.2f}\n"
        
        if tx.price:
            message += f"Price: ${tx.price:.6f}\n"
        
        if tx.dex_name:
            message += f"DEX: {tx.dex_name}\n"
        
        message += f"Hash: `{tx.hash}`\n"
        message += f"Time: {tx.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        
        return message
    
    async def _send_notification(self, user_id: str, message: str):
        """Send notification to user (placeholder)"""
        # This would integrate with the Telegram bot
        logger.info(f"Notification for {user_id}: {message}")
    
    async def _get_last_processed_block(self, tracking_id: str) -> int:
        """Get last processed block for tracking"""
        try:
            key = f"last_block:{tracking_id}"
            block_data = self.cache.get(key)
            return int(block_data) if block_data else 0
        except:
            return 0
    
    async def _save_last_processed_block(self, tracking_id: str, block_number: int):
        """Save last processed block"""
        try:
            key = f"last_block:{tracking_id}"
            self.cache.set(key, str(block_number))
        except Exception as e:
            logger.error(f"Error saving last block: {e}")
    
    def _save_subscribers(self):
        """Save subscriber data"""
        try:
            subscribers_data = {}
            for user_id, tracking_ids in self.subscribers.items():
                subscribers_data[user_id] = list(tracking_ids)
            
            self.cache.set("token_tracking_subscribers", json.dumps(subscribers_data))
        except Exception as e:
            logger.error(f"Error saving subscribers: {e}")
    
    def _load_subscribers(self):
        """Load subscriber data"""
        try:
            subscribers_data = self.cache.get("token_tracking_subscribers")
            if subscribers_data:
                data = json.loads(subscribers_data)
                for user_id, tracking_ids in data.items():
                    self.subscribers[user_id] = set(tracking_ids)
        except Exception as e:
            logger.error(f"Error loading subscribers: {e}")
    
    def get_tracking_stats(self) -> Dict:
        """Get tracking statistics"""
        total_trackings = len(self.tracking_configs)
        active_trackings = len(self.active_trackers)
        total_subscribers = len(self.subscribers)
        
        mode_counts = {}
        blockchain_counts = {}
        
        for config in self.tracking_configs.values():
            mode_counts[config.mode.value] = mode_counts.get(config.mode.value, 0) + 1
            blockchain_counts[config.blockchain] = blockchain_counts.get(config.blockchain, 0) + 1
        
        return {
            'total_trackings': total_trackings,
            'active_trackings': active_trackings,
            'total_subscribers': total_subscribers,
            'mode_distribution': mode_counts,
            'blockchain_distribution': blockchain_counts,
            'cached_tokens': len(self.token_cache)
        }
    
    async def start_all_tracking(self):
        """Start all enabled tracking tasks"""
        for tracking_id, config in self.tracking_configs.items():
            if config.enabled and tracking_id not in self.active_trackers:
                self._start_tracking(tracking_id)
        
        logger.info(f"Started {len(self.active_trackers)} tracking tasks")
    
    async def stop_all_tracking(self):
        """Stop all tracking tasks"""
        for task in self.active_trackers.values():
            task.cancel()
        
        self.active_trackers.clear()
        logger.info("Stopped all tracking tasks")