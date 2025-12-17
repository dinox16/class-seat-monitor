"""Database layer for storing course information and tracking changes."""

import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any


logger = logging.getLogger(__name__)


class Database:
    """SQLite database handler for course monitoring."""

    def __init__(self, db_path: str = "data/courses.db"):
        """Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection.
        
        Returns:
            SQLite connection object
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self):
        """Initialize database schema."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Create courses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT NOT NULL,
                course_name TEXT,
                class_name TEXT,
                class_code TEXT UNIQUE NOT NULL,
                available_seats INTEGER,
                seats_available_text TEXT,
                has_seats BOOLEAN,
                total_capacity INTEGER,
                schedule TEXT,
                room TEXT,
                location TEXT,
                instructor TEXT,
                status TEXT,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create seat history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS seat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_code TEXT NOT NULL,
                available_seats INTEGER NOT NULL,
                total_capacity INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (class_code) REFERENCES courses(class_code)
            )
        """)
        
        # Create monitored courses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS monitored_courses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_code TEXT UNIQUE NOT NULL,
                notify_when_seats_gt INTEGER DEFAULT 0,
                is_active BOOLEAN DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create notification tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notification_tracking (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                class_code TEXT UNIQUE NOT NULL,
                last_notified_at TIMESTAMP,
                last_seats_status TEXT,
                notification_sent BOOLEAN DEFAULT 0
            )
        """)
        
        # Create index for faster queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_class_code 
            ON courses(class_code)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_seat_history_class_code 
            ON seat_history(class_code)
        """)
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")

    def save_course_data(self, course_data: Dict[str, Any]) -> bool:
        """Save or update course information.
        
        Args:
            course_data: Dictionary containing course information
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Check if course exists
            cursor.execute(
                "SELECT available_seats FROM courses WHERE class_code = ?",
                (course_data['class_code'],)
            )
            existing = cursor.fetchone()
            
            if existing:
                # Update existing course
                cursor.execute("""
                    UPDATE courses 
                    SET course_code = ?, course_name = ?, class_name = ?,
                        available_seats = ?, seats_available_text = ?, has_seats = ?,
                        total_capacity = ?, schedule = ?, room = ?, location = ?,
                        instructor = ?, status = ?, last_updated = ?
                    WHERE class_code = ?
                """, (
                    course_data.get('course_code'),
                    course_data.get('course_name'),
                    course_data.get('class_name'),
                    course_data.get('available_seats'),
                    course_data.get('seats_available_text'),
                    course_data.get('has_seats', False),
                    course_data.get('total_capacity'),
                    course_data.get('schedule'),
                    course_data.get('room'),
                    course_data.get('location'),
                    course_data.get('instructor'),
                    course_data.get('status'),
                    datetime.now(),
                    course_data['class_code']
                ))
                
                # Record in history if seats changed
                if existing[0] != course_data.get('available_seats'):
                    cursor.execute("""
                        INSERT INTO seat_history (class_code, available_seats, total_capacity)
                        VALUES (?, ?, ?)
                    """, (
                        course_data['class_code'],
                        course_data.get('available_seats'),
                        course_data.get('total_capacity')
                    ))
            else:
                # Insert new course
                cursor.execute("""
                    INSERT INTO courses 
                    (course_code, course_name, class_name, class_code, available_seats,
                     seats_available_text, has_seats, total_capacity, schedule, room,
                     location, instructor, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    course_data.get('course_code'),
                    course_data.get('course_name'),
                    course_data.get('class_name'),
                    course_data['class_code'],
                    course_data.get('available_seats'),
                    course_data.get('seats_available_text'),
                    course_data.get('has_seats', False),
                    course_data.get('total_capacity'),
                    course_data.get('schedule'),
                    course_data.get('room'),
                    course_data.get('location'),
                    course_data.get('instructor'),
                    course_data.get('status')
                ))
                
                # Record initial state in history
                cursor.execute("""
                    INSERT INTO seat_history (class_code, available_seats, total_capacity)
                    VALUES (?, ?, ?)
                """, (
                    course_data['class_code'],
                    course_data.get('available_seats'),
                    course_data.get('total_capacity')
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving course data: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_seat_changes(self, class_code: str) -> List[Dict[str, Any]]:
        """Get seat availability changes for a course.
        
        Args:
            class_code: Class registration code
            
        Returns:
            List of seat change records
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT available_seats, total_capacity, timestamp
            FROM seat_history
            WHERE class_code = ?
            ORDER BY timestamp DESC
            LIMIT 10
        """, (class_code,))
        
        changes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return changes

    def get_latest_seat_change(self, class_code: str) -> Optional[Dict[str, Any]]:
        """Get the most recent seat change for a course.
        
        Args:
            class_code: Class registration code
            
        Returns:
            Dictionary with seat change information or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Get last two entries to compare
        cursor.execute("""
            SELECT available_seats, total_capacity, timestamp
            FROM seat_history
            WHERE class_code = ?
            ORDER BY timestamp DESC
            LIMIT 2
        """, (class_code,))
        
        results = cursor.fetchall()
        conn.close()
        
        if len(results) < 2:
            return None
        
        current = dict(results[0])
        previous = dict(results[1])
        
        # Only return if seats increased
        if current['available_seats'] > previous['available_seats']:
            return {
                'class_code': class_code,
                'previous_seats': previous['available_seats'],
                'current_seats': current['available_seats'],
                'total_capacity': current['total_capacity'],
                'timestamp': current['timestamp']
            }
        
        return None

    def add_monitored_course(self, course_code: str, notify_threshold: int = 0) -> bool:
        """Add a course to the monitoring watchlist.
        
        Args:
            course_code: Course code to monitor
            notify_threshold: Minimum seats required for notification
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO monitored_courses 
                (course_code, notify_when_seats_gt, is_active)
                VALUES (?, ?, 1)
            """, (course_code, notify_threshold))
            
            conn.commit()
            logger.info(f"Added course {course_code} to monitoring list")
            return True
            
        except Exception as e:
            logger.error(f"Error adding monitored course: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def remove_monitored_course(self, course_code: str) -> bool:
        """Remove a course from the monitoring watchlist.
        
        Args:
            course_code: Course code to remove
            
        Returns:
            True if successful, False otherwise
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                DELETE FROM monitored_courses WHERE course_code = ?
            """, (course_code,))
            
            conn.commit()
            logger.info(f"Removed course {course_code} from monitoring list")
            return True
            
        except Exception as e:
            logger.error(f"Error removing monitored course: {e}")
            return False
        finally:
            if conn:
                conn.close()

    def get_monitored_courses(self) -> List[Dict[str, Any]]:
        """Get list of monitored courses.
        
        Returns:
            List of monitored course records
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT course_code, notify_when_seats_gt, is_active, added_at
            FROM monitored_courses
            WHERE is_active = 1
            ORDER BY added_at DESC
        """)
        
        courses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return courses

    def get_course_info(self, class_code: str) -> Optional[Dict[str, Any]]:
        """Get detailed course information.
        
        Args:
            class_code: Class registration code
            
        Returns:
            Dictionary with course information or None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM courses WHERE class_code = ?
        """, (class_code,))
        
        result = cursor.fetchone()
        conn.close()
        
        return dict(result) if result else None

    def get_courses_by_code(self, course_code: str) -> List[Dict[str, Any]]:
        """Get all classes for a given course code.
        
        Args:
            course_code: Course code (e.g., "CS 403")
            
        Returns:
            List of course records
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM courses 
            WHERE course_code = ?
            ORDER BY last_updated DESC
        """, (course_code,))
        
        courses = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return courses
    
    def should_send_notification(self, class_code: str, has_seats: bool) -> bool:
        """Check if notification should be sent for this class.
        
        Args:
            class_code: Class registration code
            has_seats: Whether the class currently has seats
            
        Returns:
            True if notification should be sent
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # Get notification tracking record
            cursor.execute("""
                SELECT last_seats_status, notification_sent
                FROM notification_tracking
                WHERE class_code = ?
            """, (class_code,))
            
            result = cursor.fetchone()
            
            if result:
                last_status = result[0]
                notification_sent = result[1]
                
                # Send notification if:
                # 1. Current status is "has seats" AND
                # 2. Either no notification was sent OR last status was "no seats"
                if has_seats and (not notification_sent or last_status == "Hết chỗ"):
                    return True
                else:
                    return False
            else:
                # First time seeing this class, send notification if has seats
                return has_seats
                
        except Exception as e:
            logger.error(f"Error checking notification status: {e}")
            return False
        finally:
            if conn:
                conn.close()
    
    def mark_notification_sent(self, class_code: str, seats_status: str):
        """Mark that notification was sent for this class.
        
        Args:
            class_code: Class registration code
            seats_status: Current seats status text
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO notification_tracking
                (class_code, last_notified_at, last_seats_status, notification_sent)
                VALUES (?, ?, ?, ?)
            """, (
                class_code,
                datetime.now(),
                seats_status,
                1 if seats_status != "Hết chỗ" else 0
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error marking notification sent: {e}")
        finally:
            if conn:
                conn.close()
    
    def update_notification_status(self, class_code: str, seats_status: str):
        """Update notification status without sending notification.
        
        Args:
            class_code: Class registration code
            seats_status: Current seats status text
        """
        conn = None
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT OR REPLACE INTO notification_tracking
                (class_code, last_seats_status, notification_sent)
                VALUES (?, ?, ?)
            """, (
                class_code,
                seats_status,
                0 if seats_status == "Hết chỗ" else 1
            ))
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error updating notification status: {e}")
        finally:
            if conn:
                conn.close()
