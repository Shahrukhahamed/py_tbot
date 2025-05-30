import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from src.interface.telegram.handlers import *
from src.infrastructure.database import SupabaseDB
from src.utils.logger import logger


class TelegramBot:
    def __init__(self):
        token = os.getenv("TELEGRAM_TOKEN")
        if not token:
            raise EnvironmentError("TELEGRAM_TOKEN is not set in environment variables.")

        self.db = SupabaseDB()
        self.app = ApplicationBuilder().token(token).build()
        self._register_handlers()

    def _register_handlers(self):
        """Register all command and event handlers for the Telegram bot."""
        command_handlers = {
            'start': handle_start,
            'pause_tracking': handle_pause_tracking,
            'resume_tracking': handle_resume_tracking,
            'start_tracking': handle_start_tracking,
            'stop_tracking': handle_stop_tracking,
            'add_wallet': handle_add_wallet,
            'remove_wallet': handle_remove_wallet,
            'add_currency': handle_add_currency,
            'remove_currency': handle_remove_currency,
            'update_rate': handle_update_rate,
            'help': handle_help,
            'status': handle_status,
            'add_blockchain': handle_add_blockchain,
            'remove_blockchain': handle_remove_blockchain,
            'set_message_format': handle_set_message_format,
            'clear_cache': handle_clear_cache,
            'set_group_id': handle_set_group_id,
            'set_admin_id': handle_set_admin_id,
            'set_rpc_url': handle_set_rpc_url,
            'fallback_rpc': handle_fallback_rpc,
            'set_media': handle_set_media,
            # Custom Blockchain Integration Commands
            'add_custom_evm_chain': add_custom_evm_chain,
            'add_custom_web3_chain': add_custom_web3_chain,
            'remove_custom_chain': remove_custom_chain,
            'list_custom_chains': list_custom_chains,
            'test_custom_chain': test_custom_chain,
            'get_evm_template': get_evm_template,
            'get_web3_template': get_web3_template,
        }

        for command, handler in command_handlers.items():
            self.app.add_handler(CommandHandler(command, handler))

        # Handle when bot is added to a group
        self.app.add_handler(MessageHandler(
            filters.StatusUpdate.NEW_CHAT_MEMBERS,
            self._on_bot_added_to_group
        ))

    async def _on_bot_added_to_group(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Triggered when bot is added to a new group. Stores group/admin IDs in settings table."""
        for user in update.message.new_chat_members:
            if user.is_bot and user.username == context.bot.username:
                admin_id = str(update.effective_user.id)
                group_id = str(update.effective_chat.id)

                self.db.execute('settings', 'upsert', {'key': 'admin_id', 'value': admin_id})
                self.db.execute('settings', 'upsert', {'key': 'group_id', 'value': group_id})

                logger.log(f"Bot added to group {group_id} by admin {admin_id}")

                await context.bot.send_message(
                    chat_id=group_id,
                    text="✅ Bot activated! Use /help to see available commands."
                )

    def run(self):
        """Starts polling for updates."""
        logger.log("Telegram bot started.")
        self.app.run_polling()