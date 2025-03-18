from telegram import Bot
from telegram.constants import ParseMode
from config.settings import settings
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    def __init__(self):
        self.bot = Bot(token=settings.TELEGRAM_TOKEN)

    async def send_alert(self, chat_id: int, message: str):
        try:
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode=ParseMode.MARKDOWN_V2
            )
            logger.info(f"Message sent successfully to {chat_id}")
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {str(e)}")
    
    async def send_bulk_alert(self, chat_ids: list, message: str):
        """Send a message to multiple chat IDs."""
        for chat_id in chat_ids:
            await self.send_alert(chat_id, message)