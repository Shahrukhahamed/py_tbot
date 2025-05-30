from telegram import Update
from telegram.ext import ContextTypes
from src.utils.validator import BlockchainValidator
from src.utils.logger import logger

# Initialize database lazily to avoid connection errors during import
_db = None

def get_db():
    """Get database instance, initialize if needed"""
    global _db
    if _db is None:
        try:
            from src.infrastructure.database import SupabaseDB
            _db = SupabaseDB()
        except Exception as e:
            logger.log(f"Database initialization failed: {e}")
            _db = None
    return _db

# Constants
AUTH_ERROR = "⛔ Admin authorization required"
SYSTEM_ERROR = "❌ Authorization system error"

def admin_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            db = get_db()
            if not db:
                await update.message.reply_text(SYSTEM_ERROR)
                return
            
            result = db.execute('settings', 'select', {'key': 'admin_id'})
            if not result or not result.data:
                raise ValueError("Admin ID not found")

            admin_id = result.data[0]['value']
            if str(update.effective_user.id) != admin_id:
                await update.message.reply_text(AUTH_ERROR)
                return

            return await func(update, context)
        except Exception as e:
            logger.log(f"Authorization error: {e}")
            await update.message.reply_text(SYSTEM_ERROR)
    return wrapper


@admin_required
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Crypto Tracker Bot is online!")


@admin_required
async def handle_add_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        address, blockchain = context.args[:2]
        if not BlockchainValidator.validate_address(address, blockchain):
            return await update.message.reply_text("❌ Invalid address format")

        get_db().execute('wallets', 'insert', {
            'address': address,
            'blockchain': blockchain
        })
        await update.message.reply_text(f"✅ Wallet `{address}` added", parse_mode="Markdown")
    except (ValueError, IndexError):
        await update.message.reply_text("Usage: /add_wallet <address> <blockchain>")


@admin_required
async def handle_remove_wallet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        address = context.args[0]
        get_db().execute('wallets', 'delete', {'address': address})
        await update.message.reply_text(f"🗑️ Wallet `{address}` removed", parse_mode="Markdown")
    except IndexError:
        await update.message.reply_text("Usage: /remove_wallet <address>")


@admin_required
async def handle_add_blockchain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name, rpc, explorer, currency = context.args[:4]
        get_db().execute('blockchains', 'insert', {
            'name': name,
            'rpc': rpc,
            'explorer': explorer,
            'currency': currency
        })
        await update.message.reply_text(f"⛓️ Blockchain `{name}` added", parse_mode="Markdown")
    except (ValueError, IndexError):
        await update.message.reply_text("Usage: /add_blockchain <name> <rpc> <explorer> <currency>")


@admin_required
async def handle_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📚 *Available Commands:*

**Basic Commands:**
/start - Initialize the bot
/help - Show this help message
/status - Show bot status

**Wallet Management:**
/add_wallet <address> <blockchain>
/remove_wallet <address>
/pause_tracking
/resume_tracking
/start_tracking
/stop_tracking

**Currency Management:**
/add_currency <symbol> <name>
/remove_currency <symbol>
/update_rate <symbol> <rate>

**Blockchain Management:**
/add_blockchain <name> <rpc> <explorer> <currency>
/remove_blockchain <name>
/set_rpc_url <blockchain> <url>
/fallback_rpc <blockchain> <fallback_url>

**🚀 Custom Blockchain Integration:**
/add_custom_evm_chain <name> <rpc_url> <chain_id> <symbol> [explorer_url]
/add_custom_web3_chain <name> <chain_type> <rpc_url> <symbol> <decimals> [explorer_url]
/remove_custom_chain <chain_name>
/list_custom_chains - List all custom blockchains
/test_custom_chain <chain_name> - Test custom blockchain connection
/get_evm_template - Get EVM chain configuration template
/get_web3_template [chain_type] - Get Web3 chain configuration template

**🪙 Token Tracking & Integration:**
/setup_tracking - Interactive token tracking setup
/track_token <blockchain> <address> <mode> - Quick track token
/untrack_token <blockchain> <address> - Stop tracking token
/my_trackings - View your active trackings
/tracking_stats - View tracking statistics

**🔍 Token Management:**
/add_token <blockchain> <address> [symbol] [name] - Add token to system
/search_tokens <query> [blockchain] - Search for tokens
/popular_tokens [blockchain] - View popular tokens
/discover_tokens <blockchain> [limit] - Discover new tokens
/token_info <blockchain> <address> - Get token details
/supported_chains - List supported blockchains

**Tracking Modes:**
- buy_only: Track only buy transactions
- sell_only: Track only sell transactions  
- both: Track both buy and sell transactions

**System Configuration:**
/set_message_format <template>
/clear_cache
/set_group_id <id>
/set_admin_id <id>
/set_media <media_url>

**Supported Chain Types for Web3:**
- substrate (Polkadot/Kusama ecosystem)
- cosmos (Cosmos ecosystem)
- custom (Generic Web3 chains)
    """
    await update.message.reply_text(help_text, parse_mode="Markdown")


@admin_required
async def handle_pause_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_db().execute('settings', 'upsert', {'key': 'tracking_paused', 'value': 'true'})
    await update.message.reply_text("⏸️ Transaction tracking paused")


@admin_required
async def handle_resume_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    get_db().execute('settings', 'upsert', {'key': 'tracking_paused', 'value': 'false'})
    await update.message.reply_text("▶️ Transaction tracking resumed")


@admin_required
async def handle_start_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        blockchain = context.args[0] if context.args else "all"
        get_db().execute('settings', 'upsert', {'key': f'tracking_{blockchain}', 'value': 'true'})
        await update.message.reply_text(f"🚀 Started tracking for {blockchain}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


@admin_required
async def handle_stop_tracking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        blockchain = context.args[0] if context.args else "all"
        get_db().execute('settings', 'upsert', {'key': f'tracking_{blockchain}', 'value': 'false'})
        await update.message.reply_text(f"🛑 Stopped tracking for {blockchain}")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


@admin_required
async def handle_remove_blockchain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name = context.args[0]
        get_db().execute('blockchains', 'delete', {'name': name})
        await update.message.reply_text(f"🗑️ Blockchain `{name}` removed", parse_mode="Markdown")
    except IndexError:
        await update.message.reply_text("Usage: /remove_blockchain <name>")


@admin_required
async def handle_add_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol, name = context.args[:2]
        get_db().execute('currencies', 'insert', {
            'ticker': symbol.upper(),
            'name': name
        })
        await update.message.reply_text(f"💰 Currency `{symbol.upper()}` added", parse_mode="Markdown")
    except (ValueError, IndexError):
        await update.message.reply_text("Usage: /add_currency <symbol> <name>")


@admin_required
async def handle_remove_currency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol = context.args[0].upper()
        get_db().execute('currencies', 'delete', {'ticker': symbol})
        await update.message.reply_text(f"🗑️ Currency `{symbol}` removed", parse_mode="Markdown")
    except IndexError:
        await update.message.reply_text("Usage: /remove_currency <symbol>")


@admin_required
async def handle_update_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        symbol, rate = context.args[:2]
        get_db().execute('settings', 'upsert', {'key': f'rate_{symbol.upper()}', 'value': rate})
        await update.message.reply_text(f"💱 Rate for `{symbol.upper()}` updated to ${rate}", parse_mode="Markdown")
    except (ValueError, IndexError):
        await update.message.reply_text("Usage: /update_rate <symbol> <rate>")


@admin_required
async def handle_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Get tracking status
        tracking_status = get_db().execute('settings', 'select', {'key': 'tracking_paused'})
        is_paused = tracking_status.data[0]['value'] == 'true' if tracking_status.data else False
        
        # Get wallet count
        wallets = get_db().execute('wallets', 'select')
        wallet_count = len(wallets.data) if wallets.data else 0
        
        # Get blockchain count
        blockchains = get_db().execute('blockchains', 'select')
        blockchain_count = len(blockchains.data) if blockchains.data else 0
        
        status_text = f"""
📊 *Bot Status:*
🔄 Tracking: {'Paused' if is_paused else 'Active'}
👛 Wallets: {wallet_count}
⛓️ Blockchains: {blockchain_count}
        """
        await update.message.reply_text(status_text, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error getting status: {str(e)}")


@admin_required
async def handle_set_message_format(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        template = " ".join(context.args)
        if not template:
            raise ValueError("Template cannot be empty")
        
        get_db().execute('settings', 'upsert', {'key': 'message_format', 'value': template})
        await update.message.reply_text("📝 Message format updated")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


@admin_required
async def handle_clear_cache(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        from src.infrastructure.cache import cache
        cache.clear_all()
        await update.message.reply_text("🧹 Cache cleared")
    except Exception as e:
        await update.message.reply_text(f"❌ Error clearing cache: {str(e)}")


@admin_required
async def handle_set_group_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        group_id = context.args[0]
        get_db().execute('settings', 'upsert', {'key': 'group_id', 'value': group_id})
        await update.message.reply_text(f"👥 Group ID set to `{group_id}`", parse_mode="Markdown")
    except IndexError:
        await update.message.reply_text("Usage: /set_group_id <id>")


@admin_required
async def handle_set_admin_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        admin_id = context.args[0]
        get_db().execute('settings', 'upsert', {'key': 'admin_id', 'value': admin_id})
        await update.message.reply_text(f"👤 Admin ID set to `{admin_id}`", parse_mode="Markdown")
    except IndexError:
        await update.message.reply_text("Usage: /set_admin_id <id>")


@admin_required
async def handle_set_rpc_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        blockchain, url = context.args[:2]
        get_db().execute('settings', 'upsert', {'key': f'rpc_{blockchain}', 'value': url})
        await update.message.reply_text(f"🔗 RPC URL for `{blockchain}` updated", parse_mode="Markdown")
    except (ValueError, IndexError):
        await update.message.reply_text("Usage: /set_rpc_url <blockchain> <url>")


@admin_required
async def handle_fallback_rpc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        blockchain, fallback_url = context.args[:2]
        get_db().execute('settings', 'upsert', {'key': f'fallback_rpc_{blockchain}', 'value': fallback_url})
        await update.message.reply_text(f"🔄 Fallback RPC for `{blockchain}` set", parse_mode="Markdown")
    except (ValueError, IndexError):
        await update.message.reply_text("Usage: /fallback_rpc <blockchain> <fallback_url>")


@admin_required
async def handle_set_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        media_url = context.args[0] if context.args else None
        if not media_url:
            await update.message.reply_text("Usage: /set_media <media_url>")
            return
            
        get_db().execute('settings', 'upsert', {'key': 'notification_media', 'value': media_url})
        await update.message.reply_text(f"🖼️ Notification media set", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")


# Custom Blockchain Integration Handlers

@admin_required
async def add_custom_evm_chain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a custom EVM-compatible blockchain"""
    try:
        if len(context.args) < 4:
            await update.message.reply_text(
                "Usage: /add_custom_evm_chain <name> <rpc_url> <chain_id> <symbol> [explorer_url]\n"
                "Example: /add_custom_evm_chain \"My Chain\" https://rpc.mychain.com 12345 MYC https://explorer.mychain.com"
            )
            return
        
        from src.core.blockchain.adapters import BlockchainAdapters
        adapters = BlockchainAdapters()
        
        chain_name = context.args[0]
        rpc_url = context.args[1]
        chain_id = int(context.args[2])
        symbol = context.args[3]
        explorer_url = context.args[4] if len(context.args) > 4 else ""
        
        config = {
            "name": chain_name,
            "rpc_url": rpc_url,
            "chain_id": chain_id,
            "symbol": symbol,
            "explorer_url": explorer_url,
            "gas_price_multiplier": 1.0,
            "block_time": 15,
            "confirmations": 12,
            "token_contracts": {},
            "enabled": True
        }
        
        success = adapters.add_custom_evm_chain(chain_name, config)
        
        if success:
            await update.message.reply_text(
                f"✅ Custom EVM chain added successfully!\n"
                f"🔗 Name: {chain_name}\n"
                f"🌐 RPC: {rpc_url}\n"
                f"🆔 Chain ID: {chain_id}\n"
                f"💰 Symbol: {symbol}"
            )
        else:
            await update.message.reply_text("❌ Failed to add custom EVM chain")
        
    except Exception as e:
        logger.log(f"Error adding custom EVM chain: {e}")
        await update.message.reply_text(f"❌ Error adding custom EVM chain: {str(e)}")


@admin_required
async def add_custom_web3_chain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Add a custom Web3-compatible blockchain"""
    try:
        if len(context.args) < 5:
            await update.message.reply_text(
                "Usage: /add_custom_web3_chain <name> <chain_type> <rpc_url> <symbol> <decimals> [explorer_url]\n"
                "Chain types: substrate, cosmos, custom\n"
                "Example: /add_custom_web3_chain \"My Substrate\" substrate wss://rpc.mychain.com DOT 10 https://explorer.mychain.com"
            )
            return
        
        from src.core.blockchain.adapters import BlockchainAdapters
        adapters = BlockchainAdapters()
        
        chain_name = context.args[0]
        chain_type = context.args[1]
        rpc_url = context.args[2]
        symbol = context.args[3]
        decimals = int(context.args[4])
        explorer_url = context.args[5] if len(context.args) > 5 else ""
        
        config = {
            "name": chain_name,
            "chain_type": chain_type,
            "rpc_url": rpc_url,
            "symbol": symbol,
            "decimals": decimals,
            "explorer_url": explorer_url,
            "block_time": 6,
            "address_format": r'^[a-zA-Z0-9]+$',
            "rpc_methods": {},
            "enabled": True
        }
        
        success = adapters.add_custom_web3_chain(chain_name, config)
        
        if success:
            await update.message.reply_text(
                f"✅ Custom Web3 chain added successfully!\n"
                f"🔗 Name: {chain_name}\n"
                f"🔧 Type: {chain_type}\n"
                f"🌐 RPC: {rpc_url}\n"
                f"💰 Symbol: {symbol}\n"
                f"🔢 Decimals: {decimals}"
            )
        else:
            await update.message.reply_text("❌ Failed to add custom Web3 chain")
        
    except Exception as e:
        logger.log(f"Error adding custom Web3 chain: {e}")
        await update.message.reply_text(f"❌ Error adding custom Web3 chain: {str(e)}")


@admin_required
async def remove_custom_chain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove a custom blockchain"""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /remove_custom_chain <chain_name>")
            return
        
        from src.core.blockchain.adapters import BlockchainAdapters
        adapters = BlockchainAdapters()
        
        chain_name = context.args[0]
        success = adapters.remove_custom_chain(chain_name)
        
        if success:
            await update.message.reply_text(f"✅ Custom chain '{chain_name}' removed successfully!")
        else:
            await update.message.reply_text(f"❌ Failed to remove custom chain '{chain_name}'")
        
    except Exception as e:
        logger.log(f"Error removing custom chain: {e}")
        await update.message.reply_text(f"❌ Error removing custom chain: {str(e)}")


@admin_required
async def list_custom_chains(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all custom blockchains"""
    try:
        from src.core.blockchain.adapters import BlockchainAdapters
        adapters = BlockchainAdapters()
        
        stats = adapters.get_custom_chain_stats()
        
        message = f"📊 Custom Blockchain Statistics:\n\n"
        message += f"📈 Total Custom Chains: {stats.get('total_chains', 0)}\n"
        message += f"✅ Enabled Chains: {stats.get('enabled_chains', 0)}\n"
        message += f"🔗 EVM Chains: {stats.get('evm_chains', 0)}\n"
        message += f"🌐 Web3 Chains: {stats.get('web3_chains', 0)}\n\n"
        
        chains = stats.get('chains', {})
        if chains:
            message += "🔗 Custom Chains:\n"
            for chain_name, info in chains.items():
                status = "🟢" if info.get('connected', False) else "🔴"
                chain_type = info.get('type', 'unknown')
                current_block = info.get('current_block', 0)
                message += f"{status} {chain_name} ({chain_type}) - Block: {current_block}\n"
        else:
            message += "No custom chains configured."
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.log(f"Error listing custom chains: {e}")
        await update.message.reply_text(f"❌ Error listing custom chains: {str(e)}")


@admin_required
async def test_custom_chain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Test connection to a custom blockchain"""
    try:
        if not context.args:
            await update.message.reply_text("Usage: /test_custom_chain <chain_name>")
            return
        
        from src.core.blockchain.adapters import BlockchainAdapters
        adapters = BlockchainAdapters()
        
        chain_name = context.args[0]
        result = adapters.test_custom_chain(chain_name)
        
        if result.get('success', False):
            network_info = result.get('network_info', {})
            current_block = result.get('current_block', 0)
            
            message = f"✅ Custom chain '{chain_name}' test successful!\n\n"
            message += f"📊 Current Block: {current_block}\n"
            
            if 'connected' in network_info:
                status = "🟢 Connected" if network_info['connected'] else "🔴 Disconnected"
                message += f"🔗 Status: {status}\n"
            
            if 'gas_price' in network_info:
                message += f"⛽ Gas Price: {network_info['gas_price']}\n"
            
            if 'chain_id' in network_info:
                message += f"🆔 Chain ID: {network_info['chain_id']}\n"
        else:
            message = f"❌ Custom chain '{chain_name}' test failed!\n"
            message += f"Error: {result.get('error', 'Unknown error')}"
        
        await update.message.reply_text(message)
        
    except Exception as e:
        logger.log(f"Error testing custom chain: {e}")
        await update.message.reply_text(f"❌ Error testing custom chain: {str(e)}")


@admin_required
async def get_evm_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get EVM chain configuration template"""
    try:
        from src.core.blockchain.adapters import BlockchainAdapters
        adapters = BlockchainAdapters()
        
        template = adapters.create_evm_template()
        
        if template:
            import json
            message = "📋 EVM Chain Configuration Template:\n\n"
            message += f"```json\n{json.dumps(template, indent=2)}\n```"
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Failed to get EVM template")
        
    except Exception as e:
        logger.log(f"Error getting EVM template: {e}")
        await update.message.reply_text(f"❌ Error getting EVM template: {str(e)}")


@admin_required
async def get_web3_template(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get Web3 chain configuration template"""
    try:
        chain_type = context.args[0] if context.args else "substrate"
        
        from src.core.blockchain.adapters import BlockchainAdapters
        adapters = BlockchainAdapters()
        
        template = adapters.create_web3_template(chain_type)
        
        if template:
            import json
            message = f"📋 Web3 Chain Configuration Template ({chain_type}):\n\n"
            message += f"```json\n{json.dumps(template, indent=2)}\n```"
            await update.message.reply_text(message, parse_mode='Markdown')
        else:
            await update.message.reply_text("❌ Failed to get Web3 template")
        
    except Exception as e:
        logger.log(f"Error getting Web3 template: {e}")
        await update.message.reply_text(f"❌ Error getting Web3 template: {str(e)}")