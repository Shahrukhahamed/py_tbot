from telegram import Update
from telegram.ext import ContextTypes
from src.infrastructure.database import SupabaseDB
from src.utils.validator import BlockchainValidator
from src.utils.logger import logger

db = SupabaseDB()

# Constants
AUTH_ERROR = "⛔ Admin authorization required"
SYSTEM_ERROR = "❌ Authorization system error"

def admin_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
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

        db.execute('wallets', 'insert', {
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
        db.execute('wallets', 'delete', {'address': address})
        await update.message.reply_text(f"🗑️ Wallet `{address}` removed", parse_mode="Markdown")
    except IndexError:
        await update.message.reply_text("Usage: /remove_wallet <address>")


@admin_required
async def handle_add_blockchain(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        name, rpc, explorer, currency = context.args[:4]
        db.execute('blockchains', 'insert', {
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