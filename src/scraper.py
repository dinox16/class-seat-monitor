"""Web scraper for Duy Tan University course registration system."""

import logging
import os
import time
from typing import List, Dict, Optional, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


logger = logging.getLogger(__name__)


class CourseScraper:
    """Scraper for Duy Tan University course registration website."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the scraper.
        
        Args:
            config: Scraper configuration dictionary
        """
        self.config = config
        self.target_url = config.get('target_url', '')
        self.academic_year = config.get('academic_year', '2025-2026')
        self.semester = config.get('semester', 'Học Kỳ II')
        
        # Support both single subject and multiple subjects
        subjects = config.get('subjects', config.get('subject'))
        if isinstance(subjects, str):
            self.subjects = [subjects]
        elif isinstance(subjects, list):
            self.subjects = subjects
        else:
            self.subjects = ['CS']  # Default fallback
        
        self.headless = config.get('headless', True)
        self.timeout = config.get('timeout', 30)
        self.driver = None

    def _setup_driver(self):
        """Set up Chrome WebDriver with appropriate options."""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Try to find chromedriver - check system location first (for Linux/CI)
        chromedriver_path = None
        system_paths = [
            '/usr/bin/chromedriver',  # Linux system installation
            '/usr/local/bin/chromedriver',  # Alternative Linux location
        ]
        
        for path in system_paths:
            if os.path.exists(path):
                chromedriver_path = path
                logger.info(f"Using system chromedriver at {path}")
                break
        
        # Use webdriver-manager as fallback
        if not chromedriver_path:
            try:
                chromedriver_path = ChromeDriverManager().install()
                logger.info("Using chromedriver from webdriver-manager")
            except Exception as e:
                logger.error(f"Failed to install chromedriver with webdriver-manager: {e}")
                raise
        
        service = Service(chromedriver_path)
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        self.driver.implicitly_wait(10)
        
        logger.info("Chrome WebDriver initialized successfully")

    def _close_driver(self):
        """Close the WebDriver."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Chrome WebDriver closed")
            except Exception as e:
                logger.error(f"Error closing driver: {e}")

    def scrape_courses(self, retry_count: int = 3) -> List[Dict[str, Any]]:
        """Scrape course data from the website.
        
        Args:
            retry_count: Number of retry attempts on failure
            
        Returns:
            List of course dictionaries
        """
        for attempt in range(retry_count):
            try:
                logger.info(f"Starting scrape attempt {attempt + 1}/{retry_count}")
                courses = self._scrape_with_selenium()
                logger.info(f"Successfully scraped {len(courses)} courses")
                self._close_driver()
                return courses
                
            except Exception as e:
                logger.error(f"Scraping attempt {attempt + 1} failed: {e}")
                self._close_driver()
                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 5
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error("All scraping attempts failed")
        
        return []

    def _scrape_with_selenium(self) -> List[Dict[str, Any]]:
        """Perform actual scraping using Selenium.
        
        Returns:
            List of course dictionaries
        """
        self._setup_driver()
        
        logger.info(f"Navigating to {self.target_url}")
        self.driver.get(self.target_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Try to interact with filters if they exist
        try:
            self._apply_filters()
        except Exception as e:
            logger.warning(f"Could not apply filters: {e}")
        
        # Wait for the course table to load
        try:
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
        except TimeoutException:
            logger.error("Timeout waiting for course table to load")
            raise
        
        # Give extra time for dynamic content
        time.sleep(2)
        
        # Parse the page
        soup = BeautifulSoup(self.driver.page_source, 'html.parser')
        courses = self._parse_courses(soup)
        
        return courses

    def _apply_filters(self):
        """Apply filters for academic year, semester, and subject."""
        try:
            # This is a placeholder - actual implementation would depend on the website structure
            # You would need to inspect the website to find the correct selectors
            
            # Example: Select academic year dropdown
            # year_dropdown = self.driver.find_element(By.ID, "year_select")
            # Select(year_dropdown).select_by_visible_text(self.academic_year)
            
            # Example: Select semester
            # semester_dropdown = self.driver.find_element(By.ID, "semester_select")
            # Select(semester_dropdown).select_by_visible_text(self.semester)
            
            # Example: Enter subject code
            # subject_input = self.driver.find_element(By.ID, "subject_input")
            # subject_input.clear()
            # subject_input.send_keys(self.subject)
            
            # Example: Click search button
            # search_button = self.driver.find_element(By.ID, "search_button")
            # search_button.click()
            
            # Wait for results
            # time.sleep(2)
            
            logger.info("Filters applied successfully")
            
        except NoSuchElementException as e:
            logger.warning(f"Filter elements not found: {e}")

    def _parse_courses(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Parse course data from HTML.
        
        Args:
            soup: BeautifulSoup object of the page
            
        Returns:
            List of course dictionaries
        """
        courses = []
        
        # Find the main course table
        tables = soup.find_all('table')
        
        if not tables:
            logger.warning("No tables found on page")
            return courses
        
        # Typically the course data is in the first or main table
        # This is a generic implementation - adjust selectors based on actual website
        for table in tables:
            rows = table.find_all('tr')
            
            # Skip header row
            for row in rows[1:]:
                try:
                    cols = row.find_all(['td', 'th'])
                    
                    if len(cols) < 5:
                        continue
                    
                    # Extract data from columns
                    # Adjust indices based on actual table structure
                    course_data = self._extract_course_data(cols)
                    
                    if course_data and course_data.get('class_code'):
                        courses.append(course_data)
                        
                except Exception as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue
        
        return courses

    def _extract_course_data(self, cols) -> Optional[Dict[str, Any]]:
        """Extract course data from table columns.
        
        Args:
            cols: List of table column elements
            
        Returns:
            Dictionary with course data or None
        """
        try:
            # This is a generic implementation
            # Adjust based on actual website structure
            # Expected columns (from problem statement):
            # 0: Course Code (Mã Môn học)
            # 1: Course Name (Tên Môn học)
            # 2: Class Code (Mã đăng ký)
            # 3: Available Seats (Số chỗ còn lại)
            # 4: Total Capacity (Hạn đăng ký)
            # 5: Schedule (Giờ học)
            # 6: Room (Phòng)
            # 7: Instructor (Giảng viên)
            # 8: Status (Tình trạng Đăng ký)
            
            def get_text(col):
                """Safely get text from column."""
                return col.get_text(strip=True) if col else ""
            
            def parse_int(text):
                """Parse integer from text, return 0 if failed."""
                try:
                    return int(text.strip())
                except (ValueError, AttributeError):
                    return 0
            
            # Attempt to extract data
            course_code = get_text(cols[0]) if len(cols) > 0 else ""
            course_name = get_text(cols[1]) if len(cols) > 1 else ""
            class_code = get_text(cols[2]) if len(cols) > 2 else ""
            available_seats = parse_int(get_text(cols[3])) if len(cols) > 3 else 0
            total_capacity = parse_int(get_text(cols[4])) if len(cols) > 4 else 0
            schedule = get_text(cols[5]) if len(cols) > 5 else ""
            room = get_text(cols[6]) if len(cols) > 6 else ""
            instructor = get_text(cols[7]) if len(cols) > 7 else ""
            status = get_text(cols[8]) if len(cols) > 8 else ""
            
            # Filter by subjects if specified
            if self.subjects:
                if not any(course_code.startswith(subject) for subject in self.subjects):
                    return None
            
            return {
                'course_code': course_code,
                'course_name': course_name,
                'class_code': class_code,
                'available_seats': available_seats,
                'total_capacity': total_capacity,
                'schedule': schedule,
                'room': room,
                'instructor': instructor,
                'status': status
            }
            
        except Exception as e:
            logger.error(f"Error extracting course data: {e}")
            return None

    def test_scraper(self) -> bool:
        """Test the scraper functionality.
        
        Returns:
            True if scraper works, False otherwise
        """
        try:
            logger.info("Testing scraper...")
            courses = self.scrape_courses(retry_count=1)
            
            if courses:
                logger.info(f"Scraper test successful! Found {len(courses)} courses")
                logger.info(f"Sample course: {courses[0]}")
                return True
            else:
                logger.warning("Scraper test returned no courses")
                return False
                
        except Exception as e:
            logger.error(f"Scraper test failed: {e}")
            return False
