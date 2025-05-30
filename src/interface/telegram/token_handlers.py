"""
Telegram Bot Handlers for Token Tracking
Multi-blockchain token tracking with buy/sell filtering
"""

import asyncio
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, ConversationHandler, MessageHandler, filters

from src.utils.logger import get_logger
from src.core.tracking import TokenTracker, TrackingMode, TokenIntegrationManager
from src.infrastructure.cache import CacheManager

logger = get_logger(__name__)

# Conversation states
SELECTING_BLOCKCHAIN, ENTERING_ADDRESS, SELECTING_MODE, SETTING_FILTERS = range(4)

class TokenTrackingHandlers:
    """Telegram handlers for token tracking functionality"""
    
    def __init__(self, cache_manager: CacheManager):
        self.cache = cache_manager
        self.token_tracker = TokenTracker(cache_manager)
        self.token_integration = TokenIntegrationManager(cache_manager)
        
        # Start tracking on initialization
        asyncio.create_task(self.token_tracker.start_all_tracking())
    
    def get_handlers(self) -> List:
        """Get all token tracking handlers"""
        return [
            # Token tracking commands
            CommandHandler("track_token", self.track_token_command),
            CommandHandler("untrack_token", self.untrack_token_command),
            CommandHandler("my_trackings", self.my_trackings_command),
            CommandHandler("tracking_stats", self.tracking_stats_command),
            
            # Token integration commands
            CommandHandler("add_token", self.add_token_command),
            CommandHandler("search_tokens", self.search_tokens_command),
            CommandHandler("popular_tokens", self.popular_tokens_command),
            CommandHandler("discover_tokens", self.discover_tokens_command),
            CommandHandler("token_info", self.token_info_command),
            CommandHandler("supported_chains", self.supported_chains_command),
            
            # Conversation handler for tracking setup
            ConversationHandler(
                entry_points=[CommandHandler("setup_tracking", self.setup_tracking_start)],
                states={
                    SELECTING_BLOCKCHAIN: [CallbackQueryHandler(self.setup_blockchain_selected)],
                    ENTERING_ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.setup_address_entered)],
                    SELECTING_MODE: [CallbackQueryHandler(self.setup_mode_selected)],
                    SETTING_FILTERS: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.setup_filters_entered)]
                },
                fallbacks=[CommandHandler("cancel", self.setup_cancel)]
            ),
            
            # Callback query handlers
            CallbackQueryHandler(self.handle_tracking_callback, pattern="^track_"),
            CallbackQueryHandler(self.handle_token_callback, pattern="^token_"),
        ]
    
    async def track_token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Quick track token command"""
        try:
            user_id = str(update.effective_user.id)
            args = context.args
            
            if len(args) < 3:
                await update.message.reply_text(
                    "❌ Usage: /track_token <blockchain> <token_address> <mode>\n\n"
                    "Modes: buy_only, sell_only, both\n"
                    "Example: /track_token ethereum 0x1234... both"
                )
                return
            
            blockchain = args[0].lower()
            token_address = args[1]
            mode_str = args[2].lower()
            
            # Validate mode
            try:
                mode = TrackingMode(mode_str)
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid mode. Use: buy_only, sell_only, or both"
                )
                return
            
            # Validate token address
            is_valid = await self.token_integration.validate_token_address(blockchain, token_address)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ Invalid token address for {blockchain}"
                )
                return
            
            # Add tracking
            success = self.token_tracker.add_tracking(user_id, blockchain, token_address, mode)
            
            if success:
                # Get token info
                token_info = await self.token_tracker.get_token_info(blockchain, token_address)
                symbol = token_info.symbol if token_info else "UNKNOWN"
                
                await update.message.reply_text(
                    f"✅ **Tracking Started**\n\n"
                    f"🔗 Blockchain: {blockchain.title()}\n"
                    f"🪙 Token: {symbol}\n"
                    f"📍 Address: `{token_address}`\n"
                    f"📊 Mode: {mode.value.replace('_', ' ').title()}\n\n"
                    f"You'll receive notifications for {mode.value.replace('_', ' ')} transactions!",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Failed to start tracking")
                
        except Exception as e:
            logger.error(f"Error in track_token_command: {e}")
            await update.message.reply_text("❌ An error occurred while setting up tracking")
    
    async def untrack_token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Untrack token command"""
        try:
            user_id = str(update.effective_user.id)
            args = context.args
            
            if len(args) < 2:
                await update.message.reply_text(
                    "❌ Usage: /untrack_token <blockchain> <token_address>\n"
                    "Example: /untrack_token ethereum 0x1234..."
                )
                return
            
            blockchain = args[0].lower()
            token_address = args[1]
            
            success = self.token_tracker.remove_tracking(user_id, blockchain, token_address)
            
            if success:
                await update.message.reply_text(
                    f"✅ **Tracking Stopped**\n\n"
                    f"🔗 Blockchain: {blockchain.title()}\n"
                    f"📍 Address: `{token_address}`\n\n"
                    f"You'll no longer receive notifications for this token.",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Failed to stop tracking or token not found")
                
        except Exception as e:
            logger.error(f"Error in untrack_token_command: {e}")
            await update.message.reply_text("❌ An error occurred while stopping tracking")
    
    async def my_trackings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user's active trackings"""
        try:
            user_id = str(update.effective_user.id)
            trackings = self.token_tracker.get_user_trackings(user_id)
            
            if not trackings:
                await update.message.reply_text(
                    "📭 **No Active Trackings**\n\n"
                    "You're not tracking any tokens yet.\n"
                    "Use /setup_tracking to start tracking tokens!"
                )
                return
            
            message = "📊 **Your Active Token Trackings**\n\n"
            
            for i, tracking in enumerate(trackings, 1):
                status = "🟢" if tracking['enabled'] else "🔴"
                message += f"{status} **{i}. {tracking['token_symbol']}**\n"
                message += f"   🔗 {tracking['blockchain'].title()}\n"
                message += f"   📊 Mode: {tracking['mode'].replace('_', ' ').title()}\n"
                message += f"   📍 `{tracking['token_address']}`\n\n"
            
            # Add inline keyboard for management
            keyboard = [
                [InlineKeyboardButton("🔄 Refresh", callback_data="track_refresh")],
                [InlineKeyboardButton("➕ Add New", callback_data="track_add_new")],
                [InlineKeyboardButton("📈 Statistics", callback_data="track_stats")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in my_trackings_command: {e}")
            await update.message.reply_text("❌ An error occurred while fetching your trackings")
    
    async def tracking_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show tracking statistics"""
        try:
            stats = self.token_tracker.get_tracking_stats()
            integration_stats = self.token_integration.get_integration_stats()
            
            message = "📊 **Token Tracking Statistics**\n\n"
            
            # Tracking stats
            message += f"🎯 **Active Tracking**\n"
            message += f"   • Total Trackings: {stats['total_trackings']}\n"
            message += f"   • Active Tasks: {stats['active_trackings']}\n"
            message += f"   • Total Users: {stats['total_subscribers']}\n\n"
            
            # Mode distribution
            if stats['mode_distribution']:
                message += f"📈 **Tracking Modes**\n"
                for mode, count in stats['mode_distribution'].items():
                    message += f"   • {mode.replace('_', ' ').title()}: {count}\n"
                message += "\n"
            
            # Blockchain distribution
            if stats['blockchain_distribution']:
                message += f"🔗 **Blockchains**\n"
                for blockchain, count in stats['blockchain_distribution'].items():
                    message += f"   • {blockchain.title()}: {count}\n"
                message += "\n"
            
            # Integration stats
            message += f"🪙 **Token Integration**\n"
            message += f"   • Total Tokens: {integration_stats['total_tokens']}\n"
            message += f"   • Verified Tokens: {integration_stats['verified_tokens']}\n"
            message += f"   • Supported Chains: {integration_stats['supported_blockchains']}\n"
            message += f"   • Popular Tokens: {integration_stats['popular_tokens_count']}\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in tracking_stats_command: {e}")
            await update.message.reply_text("❌ An error occurred while fetching statistics")
    
    async def add_token_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Add token to integration system"""
        try:
            args = context.args
            
            if len(args) < 2:
                await update.message.reply_text(
                    "❌ Usage: /add_token <blockchain> <token_address> [symbol] [name]\n"
                    "Example: /add_token ethereum 0x1234... USDT \"Tether USD\""
                )
                return
            
            blockchain = args[0].lower()
            token_address = args[1]
            symbol = args[2] if len(args) > 2 else None
            name = args[3] if len(args) > 3 else None
            
            # Validate address
            is_valid = await self.token_integration.validate_token_address(blockchain, token_address)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ Invalid token address for {blockchain}"
                )
                return
            
            # Add token
            kwargs = {}
            if symbol:
                kwargs['symbol'] = symbol
            if name:
                kwargs['name'] = name
            
            success = await self.token_integration.add_token(blockchain, token_address, **kwargs)
            
            if success:
                token = self.token_integration.get_token(blockchain, token_address)
                await update.message.reply_text(
                    f"✅ **Token Added Successfully**\n\n"
                    f"🪙 Symbol: {token.symbol}\n"
                    f"📝 Name: {token.name}\n"
                    f"🔗 Blockchain: {token.blockchain.title()}\n"
                    f"📍 Address: `{token.address}`\n"
                    f"🔢 Decimals: {token.decimals}\n\n"
                    f"You can now track this token using /track_token!",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text("❌ Failed to add token")
                
        except Exception as e:
            logger.error(f"Error in add_token_command: {e}")
            await update.message.reply_text("❌ An error occurred while adding the token")
    
    async def search_tokens_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Search for tokens"""
        try:
            args = context.args
            
            if not args:
                await update.message.reply_text(
                    "❌ Usage: /search_tokens <query> [blockchain]\n"
                    "Example: /search_tokens USDT ethereum"
                )
                return
            
            query = args[0]
            blockchain = args[1].lower() if len(args) > 1 else None
            
            tokens = self.token_integration.search_tokens(query, blockchain)
            
            if not tokens:
                await update.message.reply_text(
                    f"🔍 **No tokens found for '{query}'**\n\n"
                    f"Try a different search term or add the token using /add_token"
                )
                return
            
            message = f"🔍 **Search Results for '{query}'**\n\n"
            
            for i, token in enumerate(tokens[:10], 1):  # Limit to 10 results
                message += f"**{i}. {token.symbol}** - {token.name}\n"
                message += f"   🔗 {token.blockchain.title()}\n"
                message += f"   📍 `{token.address}`\n"
                if token.verified:
                    message += f"   ✅ Verified\n"
                message += "\n"
            
            if len(tokens) > 10:
                message += f"... and {len(tokens) - 10} more results\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in search_tokens_command: {e}")
            await update.message.reply_text("❌ An error occurred while searching tokens")
    
    async def popular_tokens_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show popular tokens for a blockchain"""
        try:
            args = context.args
            
            if not args:
                # Show all blockchains with popular tokens
                supported_chains = self.token_integration.get_supported_blockchains()
                
                message = "🌟 **Popular Tokens by Blockchain**\n\n"
                message += "Select a blockchain to see popular tokens:\n\n"
                
                keyboard = []
                for i in range(0, len(supported_chains), 2):
                    row = []
                    for j in range(2):
                        if i + j < len(supported_chains):
                            chain = supported_chains[i + j]
                            row.append(InlineKeyboardButton(
                                chain.title(), 
                                callback_data=f"token_popular_{chain}"
                            ))
                    keyboard.append(row)
                
                reply_markup = InlineKeyboardMarkup(keyboard)
                await update.message.reply_text(message, parse_mode='Markdown', reply_markup=reply_markup)
                return
            
            blockchain = args[0].lower()
            popular_tokens = self.token_integration.get_popular_tokens(blockchain)
            
            if not popular_tokens:
                await update.message.reply_text(
                    f"🌟 **No popular tokens found for {blockchain.title()}**\n\n"
                    f"Popular tokens will appear here as they're added to the system."
                )
                return
            
            message = f"🌟 **Popular Tokens on {blockchain.title()}**\n\n"
            
            for i, token in enumerate(popular_tokens, 1):
                message += f"**{i}. {token.symbol}** - {token.name}\n"
                message += f"   📍 `{token.address}`\n"
                if token.verified:
                    message += f"   ✅ Verified\n"
                message += "\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in popular_tokens_command: {e}")
            await update.message.reply_text("❌ An error occurred while fetching popular tokens")
    
    async def discover_tokens_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Discover new tokens on a blockchain"""
        try:
            args = context.args
            
            if not args:
                await update.message.reply_text(
                    "❌ Usage: /discover_tokens <blockchain> [limit]\n"
                    "Example: /discover_tokens ethereum 50"
                )
                return
            
            blockchain = args[0].lower()
            limit = int(args[1]) if len(args) > 1 else 20
            limit = min(limit, 100)  # Max 100 tokens
            
            await update.message.reply_text(
                f"🔍 **Discovering tokens on {blockchain.title()}...**\n\n"
                f"This may take a moment..."
            )
            
            discovered_tokens = await self.token_integration.discover_tokens(blockchain, limit)
            
            if not discovered_tokens:
                await update.message.reply_text(
                    f"🔍 **No new tokens discovered on {blockchain.title()}**\n\n"
                    f"All recent tokens may already be in the system."
                )
                return
            
            message = f"🔍 **Discovered {len(discovered_tokens)} new tokens on {blockchain.title()}**\n\n"
            
            for i, token in enumerate(discovered_tokens[:10], 1):
                message += f"**{i}. {token.symbol}** - {token.name}\n"
                message += f"   📍 `{token.address}`\n\n"
            
            if len(discovered_tokens) > 10:
                message += f"... and {len(discovered_tokens) - 10} more tokens added to the system\n"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in discover_tokens_command: {e}")
            await update.message.reply_text("❌ An error occurred while discovering tokens")
    
    async def token_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Get detailed token information"""
        try:
            args = context.args
            
            if len(args) < 2:
                await update.message.reply_text(
                    "❌ Usage: /token_info <blockchain> <token_address>\n"
                    "Example: /token_info ethereum 0x1234..."
                )
                return
            
            blockchain = args[0].lower()
            token_address = args[1]
            
            # Get token contract info
            token = self.token_integration.get_token(blockchain, token_address)
            if not token:
                await update.message.reply_text(
                    f"❌ Token not found in system. Add it first using /add_token"
                )
                return
            
            # Get metadata
            metadata = self.token_integration.get_token_metadata(blockchain, token_address)
            
            message = f"🪙 **Token Information**\n\n"
            message += f"**{token.symbol}** - {token.name}\n"
            message += f"🔗 Blockchain: {token.blockchain.title()}\n"
            message += f"📍 Address: `{token.address}`\n"
            message += f"🔢 Decimals: {token.decimals}\n"
            
            if token.verified:
                message += f"✅ Verified Token\n"
            
            if token.total_supply:
                message += f"💰 Total Supply: {token.total_supply:,}\n"
            
            if metadata:
                message += f"\n📊 **Market Data**\n"
                if metadata.price_usd:
                    message += f"💵 Price: ${metadata.price_usd:.6f}\n"
                if metadata.market_cap:
                    message += f"📈 Market Cap: ${metadata.market_cap:,.2f}\n"
                if metadata.volume_24h:
                    message += f"📊 24h Volume: ${metadata.volume_24h:,.2f}\n"
                if metadata.holders_count:
                    message += f"👥 Holders: {metadata.holders_count:,}\n"
                
                if metadata.website or metadata.twitter or metadata.telegram:
                    message += f"\n🔗 **Links**\n"
                    if metadata.website:
                        message += f"🌐 Website: {metadata.website}\n"
                    if metadata.twitter:
                        message += f"🐦 Twitter: {metadata.twitter}\n"
                    if metadata.telegram:
                        message += f"💬 Telegram: {metadata.telegram}\n"
                
                if metadata.description:
                    message += f"\n📝 **Description**\n{metadata.description[:200]}...\n"
            
            # Add tracking button
            keyboard = [[
                InlineKeyboardButton(
                    "📊 Track This Token", 
                    callback_data=f"token_track_{blockchain}_{token_address}"
                )
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
        except Exception as e:
            logger.error(f"Error in token_info_command: {e}")
            await update.message.reply_text("❌ An error occurred while fetching token information")
    
    async def supported_chains_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show supported blockchains"""
        try:
            supported_chains = self.token_integration.get_supported_blockchains()
            
            message = "🔗 **Supported Blockchains for Token Tracking**\n\n"
            
            # Group chains by type
            evm_chains = []
            non_evm_chains = []
            custom_chains = []
            
            for chain in supported_chains:
                if chain in ['ethereum', 'bsc', 'polygon', 'avalanche', 'arbitrum', 'optimism', 'fantom']:
                    evm_chains.append(chain)
                elif 'custom' in chain or 'evm' in chain:
                    custom_chains.append(chain)
                else:
                    non_evm_chains.append(chain)
            
            if evm_chains:
                message += "⚡ **EVM Compatible**\n"
                for chain in sorted(evm_chains):
                    message += f"   • {chain.title()}\n"
                message += "\n"
            
            if non_evm_chains:
                message += "🌐 **Non-EVM Blockchains**\n"
                for chain in sorted(non_evm_chains):
                    message += f"   • {chain.title()}\n"
                message += "\n"
            
            if custom_chains:
                message += "🔧 **Custom Integrations**\n"
                for chain in sorted(custom_chains):
                    message += f"   • {chain.title()}\n"
                message += "\n"
            
            message += f"**Total: {len(supported_chains)} blockchains supported**\n\n"
            message += "Use /setup_tracking to start tracking tokens on any of these chains!"
            
            await update.message.reply_text(message, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error in supported_chains_command: {e}")
            await update.message.reply_text("❌ An error occurred while fetching supported chains")
    
    # Conversation handlers for setup tracking
    async def setup_tracking_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Start tracking setup conversation"""
        try:
            supported_chains = self.token_integration.get_supported_blockchains()
            
            message = "🎯 **Setup Token Tracking**\n\n"
            message += "Select a blockchain to track tokens on:\n"
            
            keyboard = []
            for i in range(0, len(supported_chains), 2):
                row = []
                for j in range(2):
                    if i + j < len(supported_chains):
                        chain = supported_chains[i + j]
                        row.append(InlineKeyboardButton(
                            chain.title(), 
                            callback_data=f"setup_blockchain_{chain}"
                        ))
                keyboard.append(row)
            
            keyboard.append([InlineKeyboardButton("❌ Cancel", callback_data="setup_cancel")])
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message, 
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            return SELECTING_BLOCKCHAIN
            
        except Exception as e:
            logger.error(f"Error in setup_tracking_start: {e}")
            await update.message.reply_text("❌ An error occurred while starting setup")
            return ConversationHandler.END
    
    async def setup_blockchain_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle blockchain selection"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "setup_cancel":
                await query.edit_message_text("❌ Setup cancelled")
                return ConversationHandler.END
            
            blockchain = query.data.replace("setup_blockchain_", "")
            context.user_data['setup_blockchain'] = blockchain
            
            await query.edit_message_text(
                f"🔗 **Selected: {blockchain.title()}**\n\n"
                f"📍 Please enter the token address you want to track:\n\n"
                f"Example addresses:\n"
                f"• Ethereum: 0x1234567890abcdef...\n"
                f"• Solana: 32-44 character string\n"
                f"• Tron: T1234567890abcdef...\n\n"
                f"Send /cancel to abort setup.",
                parse_mode='Markdown'
            )
            
            return ENTERING_ADDRESS
            
        except Exception as e:
            logger.error(f"Error in setup_blockchain_selected: {e}")
            await query.edit_message_text("❌ An error occurred")
            return ConversationHandler.END
    
    async def setup_address_entered(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle token address entry"""
        try:
            token_address = update.message.text.strip()
            blockchain = context.user_data['setup_blockchain']
            
            # Validate address
            is_valid = await self.token_integration.validate_token_address(blockchain, token_address)
            if not is_valid:
                await update.message.reply_text(
                    f"❌ Invalid token address for {blockchain}.\n"
                    f"Please enter a valid address or send /cancel to abort."
                )
                return ENTERING_ADDRESS
            
            context.user_data['setup_token_address'] = token_address
            
            # Try to get token info
            token_info = await self.token_tracker.get_token_info(blockchain, token_address)
            if token_info:
                symbol = token_info.symbol
                name = token_info.name
            else:
                symbol = "UNKNOWN"
                name = "Unknown Token"
            
            message = f"🪙 **Token Found**\n\n"
            message += f"Symbol: {symbol}\n"
            message += f"Name: {name}\n"
            message += f"Address: `{token_address}`\n\n"
            message += f"📊 **Select tracking mode:**"
            
            keyboard = [
                [InlineKeyboardButton("🟢 Buy Orders Only", callback_data="setup_mode_buy_only")],
                [InlineKeyboardButton("🔴 Sell Orders Only", callback_data="setup_mode_sell_only")],
                [InlineKeyboardButton("🔄 Both Buy & Sell", callback_data="setup_mode_both")],
                [InlineKeyboardButton("❌ Cancel", callback_data="setup_cancel")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                message,
                parse_mode='Markdown',
                reply_markup=reply_markup
            )
            
            return SELECTING_MODE
            
        except Exception as e:
            logger.error(f"Error in setup_address_entered: {e}")
            await update.message.reply_text("❌ An error occurred while validating the address")
            return ConversationHandler.END
    
    async def setup_mode_selected(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle tracking mode selection"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "setup_cancel":
                await query.edit_message_text("❌ Setup cancelled")
                return ConversationHandler.END
            
            mode_str = query.data.replace("setup_mode_", "")
            mode = TrackingMode(mode_str)
            context.user_data['setup_mode'] = mode
            
            # Complete setup
            user_id = str(update.effective_user.id)
            blockchain = context.user_data['setup_blockchain']
            token_address = context.user_data['setup_token_address']
            
            success = self.token_tracker.add_tracking(user_id, blockchain, token_address, mode)
            
            if success:
                token_info = await self.token_tracker.get_token_info(blockchain, token_address)
                symbol = token_info.symbol if token_info else "UNKNOWN"
                
                await query.edit_message_text(
                    f"✅ **Tracking Setup Complete!**\n\n"
                    f"🪙 Token: {symbol}\n"
                    f"🔗 Blockchain: {blockchain.title()}\n"
                    f"📊 Mode: {mode.value.replace('_', ' ').title()}\n"
                    f"📍 Address: `{token_address}`\n\n"
                    f"🔔 You'll receive notifications for {mode.value.replace('_', ' ')} transactions!\n\n"
                    f"Use /my_trackings to manage your active trackings.",
                    parse_mode='Markdown'
                )
            else:
                await query.edit_message_text("❌ Failed to setup tracking")
            
            return ConversationHandler.END
            
        except Exception as e:
            logger.error(f"Error in setup_mode_selected: {e}")
            await query.edit_message_text("❌ An error occurred while setting up tracking")
            return ConversationHandler.END
    
    async def setup_cancel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel setup conversation"""
        await update.message.reply_text("❌ Setup cancelled")
        return ConversationHandler.END
    
    async def handle_tracking_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle tracking-related callback queries"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data == "track_refresh":
                # Refresh trackings list
                user_id = str(update.effective_user.id)
                trackings = self.token_tracker.get_user_trackings(user_id)
                
                if not trackings:
                    await query.edit_message_text("📭 No active trackings found")
                    return
                
                message = "📊 **Your Active Token Trackings** (Refreshed)\n\n"
                
                for i, tracking in enumerate(trackings, 1):
                    status = "🟢" if tracking['enabled'] else "🔴"
                    message += f"{status} **{i}. {tracking['token_symbol']}**\n"
                    message += f"   🔗 {tracking['blockchain'].title()}\n"
                    message += f"   📊 Mode: {tracking['mode'].replace('_', ' ').title()}\n"
                    message += f"   📍 `{tracking['token_address']}`\n\n"
                
                keyboard = [
                    [InlineKeyboardButton("🔄 Refresh", callback_data="track_refresh")],
                    [InlineKeyboardButton("➕ Add New", callback_data="track_add_new")],
                    [InlineKeyboardButton("📈 Statistics", callback_data="track_stats")]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await query.edit_message_text(
                    message,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
            
            elif query.data == "track_add_new":
                await query.edit_message_text(
                    "➕ **Add New Tracking**\n\n"
                    "Use /setup_tracking to add a new token tracking configuration."
                )
            
            elif query.data == "track_stats":
                stats = self.token_tracker.get_tracking_stats()
                
                message = "📈 **Your Tracking Statistics**\n\n"
                user_id = str(update.effective_user.id)
                user_trackings = len(self.token_tracker.get_user_trackings(user_id))
                
                message += f"🎯 Your Active Trackings: {user_trackings}\n"
                message += f"🌐 Total System Trackings: {stats['total_trackings']}\n"
                message += f"⚡ Active Tasks: {stats['active_trackings']}\n"
                message += f"👥 Total Users: {stats['total_subscribers']}\n"
                
                await query.edit_message_text(message, parse_mode='Markdown')
                
        except Exception as e:
            logger.error(f"Error in handle_tracking_callback: {e}")
            await query.edit_message_text("❌ An error occurred")
    
    async def handle_token_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle token-related callback queries"""
        try:
            query = update.callback_query
            await query.answer()
            
            if query.data.startswith("token_popular_"):
                blockchain = query.data.replace("token_popular_", "")
                popular_tokens = self.token_integration.get_popular_tokens(blockchain)
                
                if not popular_tokens:
                    await query.edit_message_text(
                        f"🌟 **No popular tokens found for {blockchain.title()}**\n\n"
                        f"Popular tokens will appear here as they're added to the system."
                    )
                    return
                
                message = f"🌟 **Popular Tokens on {blockchain.title()}**\n\n"
                
                for i, token in enumerate(popular_tokens, 1):
                    message += f"**{i}. {token.symbol}** - {token.name}\n"
                    message += f"   📍 `{token.address}`\n"
                    if token.verified:
                        message += f"   ✅ Verified\n"
                    message += "\n"
                
                await query.edit_message_text(message, parse_mode='Markdown')
            
            elif query.data.startswith("token_track_"):
                parts = query.data.replace("token_track_", "").split("_", 1)
                if len(parts) == 2:
                    blockchain, token_address = parts
                    
                    await query.edit_message_text(
                        f"📊 **Track Token**\n\n"
                        f"To track this token, use:\n"
                        f"`/track_token {blockchain} {token_address} both`\n\n"
                        f"Or use /setup_tracking for guided setup.",
                        parse_mode='Markdown'
                    )
                
        except Exception as e:
            logger.error(f"Error in handle_token_callback: {e}")
            await query.edit_message_text("❌ An error occurred")