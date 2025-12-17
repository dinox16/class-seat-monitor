#!/usr/bin/env python3
"""Single monitoring check script for scheduled execution (e.g., GitHub Actions)."""

import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config import Config
from src.monitor import SeatMonitor
from src.notifier import TelegramNotifier, send_notification_sync


def setup_logging():
    """Set up basic logging configuration."""
    # Create logs directory if it doesn't exist
    log_path = Path("logs")
    log_path.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("logs/monitor.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Run a single monitoring check."""
    # Setup logging first (before any exceptions can occur)
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("=" * 60)
        logger.info("Starting single monitoring check")
        logger.info("=" * 60)
        
        # Initialize monitor
        monitor = SeatMonitor("config.yaml")
        
        # Run single check
        monitor.check_once()
        
        logger.info("=" * 60)
        logger.info("Monitoring check completed successfully")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error during monitoring check: {e}", exc_info=True)
        
        # Try to send error notification
        try:
            config = Config("config.yaml")
            notifier = TelegramNotifier(
                config.telegram_bot_token,
                config.telegram_chat_ids
            )
            send_notification_sync(
                notifier,
                'send_error_notification',
                "Fatal monitoring error",
                str(e)
            )
        except Exception as notify_error:
            logger.error(f"Failed to send error notification: {notify_error}")
        
        return 1


if __name__ == '__main__':
    sys.exit(main())
