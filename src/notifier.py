"""Telegram notification handler for seat availability alerts."""

import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError


logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Handle Telegram bot notifications for course seat changes."""

    def __init__(self, bot_token: str, chat_ids: List[int]):
        """Initialize the Telegram notifier.
        
        Args:
            bot_token: Telegram bot token from BotFather
            chat_ids: List of chat IDs to send notifications to
        """
        self.bot_token = bot_token
        self.chat_ids = chat_ids
        self.bot = None
        
        if not self.bot_token or self.bot_token.startswith('${'):
            logger.warning("Invalid Telegram bot token - notifications disabled")
            self.enabled = False
        else:
            self.bot = Bot(token=self.bot_token)
            self.enabled = True
            logger.info(f"Telegram notifier initialized for {len(chat_ids)} chat(s)")

    async def send_seat_alert(self, course_data: Dict[str, Any], 
                             seat_change: Dict[str, Any]) -> bool:
        """Send alert when seats become available.
        
        Args:
            course_data: Dictionary with course information
            seat_change: Dictionary with seat change details
            
        Returns:
            True if notification sent successfully
        """
        if not self.enabled:
            logger.warning("Notifications disabled - skipping alert")
            return False
        
        try:
            message = self._format_seat_alert(course_data, seat_change)
            
            success = True
            for chat_id in self.chat_ids:
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    logger.info(f"Seat alert sent to chat {chat_id}")
                except TelegramError as e:
                    logger.error(f"Failed to send alert to chat {chat_id}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending seat alert: {e}")
            return False

    def _format_seat_alert(self, course_data: Dict[str, Any], 
                          seat_change: Dict[str, Any]) -> str:
        """Format seat availability alert message.
        
        Args:
            course_data: Course information
            seat_change: Seat change details
            
        Returns:
            Formatted message string
        """
        previous_seats = seat_change.get('previous_seats', 0)
        current_seats = seat_change.get('current_seats', 0)
        seats_added = current_seats - previous_seats
        
        message = "🎓 <b>Seat Available Alert!</b>\n\n"
        message += f"<b>Course:</b> {course_data.get('course_code', 'N/A')} - {course_data.get('course_name', 'N/A')}\n"
        message += f"<b>Class Code:</b> <code>{course_data.get('class_code', 'N/A')}</code>\n\n"
        
        message += f"📊 <b>Seat Update:</b>\n"
        message += f"  • Previous: {previous_seats}\n"
        message += f"  • Current: <b>{current_seats}</b>\n"
        message += f"  • Added: <b>+{seats_added}</b>\n"
        message += f"  • Capacity: {course_data.get('total_capacity', 'N/A')}\n\n"
        
        if course_data.get('schedule'):
            message += f"🕐 <b>Schedule:</b> {course_data.get('schedule')}\n"
        
        if course_data.get('room'):
            message += f"🏫 <b>Room:</b> {course_data.get('room')}\n"
        
        if course_data.get('instructor'):
            message += f"👨‍🏫 <b>Instructor:</b> {course_data.get('instructor')}\n"
        
        if course_data.get('status'):
            message += f"📝 <b>Status:</b> {course_data.get('status')}\n"
        
        message += f"\n⏰ <i>Detected at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
        
        return message

    async def send_summary(self, summary_data: Dict[str, Any]) -> bool:
        """Send periodic summary of monitoring status.
        
        Args:
            summary_data: Dictionary with summary information
            
        Returns:
            True if notification sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            message = self._format_summary(summary_data)
            
            success = True
            for chat_id in self.chat_ids:
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    logger.info(f"Summary sent to chat {chat_id}")
                except TelegramError as e:
                    logger.error(f"Failed to send summary to chat {chat_id}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending summary: {e}")
            return False

    def _format_summary(self, summary_data: Dict[str, Any]) -> str:
        """Format summary message.
        
        Args:
            summary_data: Summary information
            
        Returns:
            Formatted message string
        """
        message = "📋 <b>Monitoring Summary</b>\n\n"
        
        monitored_count = summary_data.get('monitored_courses', 0)
        total_courses = summary_data.get('total_courses', 0)
        changes_detected = summary_data.get('changes_detected', 0)
        last_check = summary_data.get('last_check', 'N/A')
        
        message += f"🔍 <b>Monitored Courses:</b> {monitored_count}\n"
        message += f"📚 <b>Total Courses Found:</b> {total_courses}\n"
        message += f"🔔 <b>Changes Detected:</b> {changes_detected}\n"
        message += f"⏰ <b>Last Check:</b> {last_check}\n"
        
        if summary_data.get('courses'):
            message += "\n<b>Course Details:</b>\n"
            for course in summary_data.get('courses', [])[:10]:
                message += f"  • {course.get('course_code', 'N/A')}: {course.get('available_seats', 0)} seats\n"
        
        return message

    async def send_error_notification(self, error_message: str, 
                                      error_details: Optional[str] = None) -> bool:
        """Send error notification to admin.
        
        Args:
            error_message: Main error message
            error_details: Additional error details
            
        Returns:
            True if notification sent successfully
        """
        if not self.enabled:
            return False
        
        try:
            message = "⚠️ <b>Error Alert</b>\n\n"
            message += f"<b>Error:</b> {error_message}\n"
            
            if error_details:
                message += f"\n<b>Details:</b>\n<code>{error_details}</code>\n"
            
            message += f"\n⏰ <i>{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>"
            
            success = True
            for chat_id in self.chat_ids:
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=message,
                        parse_mode='HTML'
                    )
                    logger.info(f"Error notification sent to chat {chat_id}")
                except TelegramError as e:
                    logger.error(f"Failed to send error to chat {chat_id}: {e}")
                    success = False
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending error notification: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test Telegram bot connection.
        
        Returns:
            True if connection successful
        """
        if not self.enabled:
            logger.warning("Telegram notifications disabled")
            return False
        
        try:
            bot_info = await self.bot.get_me()
            logger.info(f"Connected to Telegram bot: @{bot_info.username}")
            
            # Send test message
            test_message = "✅ <b>Test Message</b>\n\nTelegram notification system is working!"
            
            for chat_id in self.chat_ids:
                try:
                    await self.bot.send_message(
                        chat_id=chat_id,
                        text=test_message,
                        parse_mode='HTML'
                    )
                    logger.info(f"Test message sent to chat {chat_id}")
                except TelegramError as e:
                    logger.error(f"Failed to send test message to chat {chat_id}: {e}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Telegram connection test failed: {e}")
            return False


def send_notification_sync(notifier: TelegramNotifier, method: str, *args, **kwargs) -> bool:
    """Synchronous wrapper for async notification methods.
    
    Args:
        notifier: TelegramNotifier instance
        method: Method name to call
        *args: Positional arguments for the method
        **kwargs: Keyword arguments for the method
        
    Returns:
        Result from the async method
    """
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    method_func = getattr(notifier, method)
    return loop.run_until_complete(method_func(*args, **kwargs))
