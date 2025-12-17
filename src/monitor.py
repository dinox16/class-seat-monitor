"""Core monitoring logic for seat availability tracking."""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from .config import Config
from .database import Database
from .scraper import CourseScraper
from .notifier import TelegramNotifier, send_notification_sync


logger = logging.getLogger(__name__)


class SeatMonitor:
    """Main monitoring system for course seat availability."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the monitor.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = Config(config_path)
        self.db = Database(self.config.database_path)
        
        # Initialize scraper
        scraper_config = {
            'target_url': self.config.target_url,
            'academic_year': self.config.scraper_config.get('academic_year', '2025-2026'),
            'semester': self.config.scraper_config.get('semester', 'Học Kỳ II'),
            'subjects': self.config.scraper_config.get('subjects', self.config.scraper_config.get('subject', 'CS')),
            'headless': self.config.scraper_config.get('headless', True),
            'timeout': self.config.scraper_config.get('timeout', 30)
        }
        self.scraper = CourseScraper(scraper_config)
        
        # Initialize notifier
        self.notifier = TelegramNotifier(
            self.config.telegram_bot_token,
            self.config.telegram_chat_ids
        )
        
        # Initialize scheduler
        self.scheduler = BlockingScheduler()
        self.is_running = False
        
        # Add configured courses to monitoring
        self._initialize_monitored_courses()
        
        logger.info("SeatMonitor initialized successfully")

    def _initialize_monitored_courses(self):
        """Add courses from configuration to monitoring list."""
        for course in self.config.courses_to_monitor:
            course_code = course.get('course_code')
            threshold = course.get('notify_when_seats_gt', 0)
            
            if course_code:
                self.db.add_monitored_course(course_code, threshold)
                logger.info(f"Added {course_code} to monitoring (threshold: {threshold})")

    def _process_course(self, course: Dict[str, Any], monitored: List[Dict[str, Any]]) -> bool:
        """Process a single course for monitoring.
        
        Args:
            course: Course data dictionary
            monitored: List of monitored courses
            
        Returns:
            True if notification was sent, False otherwise
        """
        # Save course data and check for changes
        self.db.save_course_data(course)
        
        # Check if this course is monitored
        course_code = course.get('course_code')
        class_code = course.get('class_code')
        
        monitored_course = next(
            (m for m in monitored if m['course_code'] == course_code),
            None
        )
        
        if not monitored_course:
            return False
        
        # Check for seat changes
        seat_change = self.db.get_latest_seat_change(class_code)
        
        if seat_change:
            # Check if change meets notification threshold
            threshold = monitored_course.get('notify_when_seats_gt', 0)
            current_seats = seat_change.get('current_seats', 0)
            
            if current_seats > threshold:
                logger.info(f"Seat change detected for {course_code}: "
                          f"{seat_change['previous_seats']} -> {current_seats}")
                
                # Send notification
                send_notification_sync(
                    self.notifier,
                    'send_seat_alert',
                    course,
                    seat_change
                )
                
                return True
        
        return False

    def check_once(self):
        """Run a single monitoring check (for scheduled tasks)."""
        logger.info("Running single monitoring check")
        
        # Get monitored courses
        monitored = self.db.get_monitored_courses()
        
        if not monitored:
            logger.warning("No courses being monitored")
            return
        
        logger.info(f"Monitoring {len(monitored)} courses")
        
        # Scrape current data
        courses = self.scraper.scrape_courses()
        
        if not courses:
            logger.warning("No courses scraped")
            return
        
        logger.info(f"Scraped {len(courses)} courses")
        
        # Process each course
        changes_detected = 0
        for course in courses:
            if self._process_course(course, monitored):
                changes_detected += 1
        
        logger.info(f"Check complete. Changes detected: {changes_detected}")

    def check_and_notify(self):
        """Main monitoring cycle - scrape, compare, and notify."""
        try:
            logger.info("Starting monitoring cycle...")
            
            # Get monitored courses
            monitored = self.db.get_monitored_courses()
            
            if not monitored:
                logger.warning("No courses being monitored")
                return
            
            logger.info(f"Monitoring {len(monitored)} courses")
            
            # Scrape current data
            logger.info("Scraping course data...")
            courses = self.scraper.scrape_courses()
            
            if not courses:
                logger.warning("No courses scraped - website may be down")
                send_notification_sync(
                    self.notifier,
                    'send_error_notification',
                    "No courses scraped",
                    "The website may be down or the scraper needs updating"
                )
                return
            
            logger.info(f"Scraped {len(courses)} courses")
            
            # Process each course
            changes_detected = 0
            for course in courses:
                if self._process_course(course, monitored):
                    changes_detected += 1
            
            logger.info(f"Monitoring cycle complete. Changes detected: {changes_detected}")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}", exc_info=True)
            send_notification_sync(
                self.notifier,
                'send_error_notification',
                "Monitoring cycle error",
                str(e)
            )

    def start(self):
        """Start the monitoring scheduler."""
        if self.is_running:
            logger.warning("Monitor is already running")
            return
        
        interval = self.config.monitoring_interval
        logger.info(f"Starting monitor with {interval} minute interval")
        
        # Run immediately on start
        self.check_and_notify()
        
        # Schedule regular checks
        self.scheduler.add_job(
            self.check_and_notify,
            trigger=IntervalTrigger(minutes=interval),
            id='seat_monitor',
            name='Course Seat Monitor',
            replace_existing=True
        )
        
        self.is_running = True
        
        try:
            logger.info("Monitor started - press Ctrl+C to stop")
            self.scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Monitor stopped by user")
            self.stop()

    def stop(self):
        """Stop the monitoring scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Monitor stopped")
        
        self.is_running = False

    def send_summary(self):
        """Send a summary of current monitoring status."""
        try:
            monitored = self.db.get_monitored_courses()
            
            summary_data = {
                'monitored_courses': len(monitored),
                'total_courses': 0,
                'changes_detected': 0,
                'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'courses': []
            }
            
            # Get current data for monitored courses
            for monitored_course in monitored:
                course_code = monitored_course['course_code']
                courses = self.db.get_courses_by_code(course_code)
                
                summary_data['total_courses'] += len(courses)
                
                for course in courses:
                    summary_data['courses'].append({
                        'course_code': course['course_code'],
                        'class_code': course['class_code'],
                        'available_seats': course['available_seats'],
                        'total_capacity': course['total_capacity']
                    })
            
            send_notification_sync(
                self.notifier,
                'send_summary',
                summary_data
            )
            
            logger.info("Summary sent successfully")
            
        except Exception as e:
            logger.error(f"Error sending summary: {e}")

    def add_course(self, course_code: str, threshold: int = 0):
        """Add a course to the monitoring list.
        
        Args:
            course_code: Course code to monitor
            threshold: Notification threshold
        """
        success = self.db.add_monitored_course(course_code, threshold)
        
        if success:
            logger.info(f"Added course {course_code} to monitoring")
            print(f"✅ Added {course_code} to monitoring list")
        else:
            logger.error(f"Failed to add course {course_code}")
            print(f"❌ Failed to add {course_code}")

    def list_monitored_courses(self):
        """List all monitored courses."""
        monitored = self.db.get_monitored_courses()
        
        if not monitored:
            print("No courses are currently being monitored")
            return
        
        print(f"\n📋 Monitored Courses ({len(monitored)}):")
        print("-" * 60)
        
        for course in monitored:
            print(f"  • {course['course_code']}")
            print(f"    Threshold: {course['notify_when_seats_gt']} seats")
            print(f"    Added: {course['added_at']}")
            
            # Get current data
            courses = self.db.get_courses_by_code(course['course_code'])
            if courses:
                total_seats = sum(c['available_seats'] for c in courses)
                print(f"    Current: {len(courses)} class(es), {total_seats} available seats")
            print()

    def test_scraper(self):
        """Test the scraper functionality."""
        print("🔍 Testing scraper...")
        success = self.scraper.test_scraper()
        
        if success:
            print("✅ Scraper test passed!")
        else:
            print("❌ Scraper test failed")

    def test_telegram(self):
        """Test Telegram notifications."""
        print("📱 Testing Telegram connection...")
        success = send_notification_sync(self.notifier, 'test_connection')
        
        if success:
            print("✅ Telegram test passed!")
        else:
            print("❌ Telegram test failed")
