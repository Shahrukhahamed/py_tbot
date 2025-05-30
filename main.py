#!/usr/bin/env python3
"""
Main entry point for the Blockchain Transaction Tracking Bot
"""

import asyncio
import threading
import signal
import sys
from src.interface.telegram.bot import TelegramBot
from src.core.blockchain.manager import BlockchainTracker
from src.utils.logger import logger
from config.settings import settings


class BotApplication:
    """Main application class that coordinates all components"""
    
    def __init__(self):
        self.telegram_bot = None
        self.blockchain_tracker = None
        self.tracker_thread = None
        self.running = False
    
    async def start(self):
        """Start the bot application"""
        try:
            logger.log("Starting Blockchain Transaction Tracking Bot...")
            
            # Initialize Telegram bot
            self.telegram_bot = TelegramBot()
            
            # Initialize blockchain tracker
            self.blockchain_tracker = BlockchainTracker()
            
            # Start blockchain tracker in a separate thread
            self.tracker_thread = threading.Thread(
                target=self.blockchain_tracker.start,
                daemon=True
            )
            self.tracker_thread.start()
            
            # Start Telegram bot
            self.running = True
            logger.log("Bot started successfully!")
            await self.telegram_bot.start()
            
        except Exception as e:
            logger.log(f"Error starting bot: {e}")
            await self.stop()
    
    async def stop(self):
        """Stop the bot application"""
        try:
            logger.log("Stopping bot...")
            self.running = False
            
            if self.blockchain_tracker:
                self.blockchain_tracker.active = False
            
            if self.telegram_bot:
                await self.telegram_bot.stop()
            
            logger.log("Bot stopped successfully!")
            
        except Exception as e:
            logger.log(f"Error stopping bot: {e}")


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.log(f"Received signal {signum}, shutting down...")
    sys.exit(0)


async def main():
    """Main function"""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create and start the application
    app = BotApplication()
    
    try:
        await app.start()
    except KeyboardInterrupt:
        logger.log("Received keyboard interrupt")
    except Exception as e:
        logger.log(f"Unexpected error: {e}")
    finally:
        await app.stop()


if __name__ == "__main__":
    # Check if required environment variables are set
    required_vars = ['TELEGRAM_BOT_TOKEN', 'SUPABASE_URL', 'SUPABASE_KEY']
    missing_vars = [var for var in required_vars if not getattr(settings, var, None)]
    
    if missing_vars:
        logger.log(f"Missing required environment variables: {', '.join(missing_vars)}")
        logger.log("Please set these variables in your .env file or environment")
        sys.exit(1)
    
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.log("Bot shutdown by user")
    except Exception as e:
        logger.log(f"Fatal error: {e}")
        sys.exit(1)