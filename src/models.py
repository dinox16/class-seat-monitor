"""Data models for course information."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Course:
    """Course class information."""
    
    code: str  # Course code (e.g., "CS 403")
    name: str  # Full course name
    class_name: str  # Class name/section
    registration_code: str  # Registration code for the class
    available_seats: int  # Number of available seats
    total_seats: int  # Total capacity
    schedule: str  # Class schedule
    room: str  # Room number/location
    location: str  # Campus/building location
    instructor: str  # Instructor name
    registration_status: str  # Registration status
    
    def to_dict(self) -> dict:
        """Convert Course to dictionary for database storage."""
        return {
            'course_code': self.code,
            'course_name': self.name,
            'class_name': self.class_name,
            'class_code': self.registration_code,
            'available_seats': self.available_seats,
            'total_capacity': self.total_seats,
            'has_seats': self.available_seats > 0,
            'seats_available_text': str(self.available_seats) if self.available_seats > 0 else "Hết chỗ",
            'schedule': self.schedule,
            'room': self.room,
            'location': self.location,
            'instructor': self.instructor,
            'status': self.registration_status
        }
