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
/start - Initialize the bot
/add_wallet <address> <blockchain>
/remove_wallet <address>
/pause_tracking
/resume_tracking
/start_tracking
/stop_tracking
/add_currency <symbol> <name>
/remove_currency <symbol>
/update_rate <symbol> <rate>
/status
/add_blockchain <name> <rpc> <explorer> <currency>
/remove_blockchain <name>
/set_message_format <template>
/clear_cache
/set_group_id <id>
/set_admin_id <id>
/set_rpc_url <blockchain> <url>
/fallback_rpc <blockchain> <fallback_url>
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