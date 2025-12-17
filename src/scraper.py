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
        subjects = config.get('subjects') or config.get('subject')
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
        
        logger.info("🤖 Starting monitoring check")
        logger.info(f"📡 Navigating to DTU website...")
        self.driver.get(self.target_url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Apply filters to search for courses
        try:
            self._apply_filters()
        except Exception as e:
            logger.error(f"Failed to apply filters: {e}")
            raise
        
        # Get course links from search results
        course_links = self._get_course_links()
        
        if not course_links:
            logger.warning("No courses found in search results")
            return []
        
        logger.info(f"✅ Found {len(course_links)} course(s) to check")
        
        # Visit each course detail page and parse classes
        all_courses = []
        for course_code, course_url in course_links.items():
            try:
                logger.info(f"🔗 Opening detail page for {course_code}...")
                courses = self._scrape_course_detail_page(course_code, course_url)
                all_courses.extend(courses)
            except Exception as e:
                logger.error(f"Error scraping {course_code}: {e}")
                continue
        
        logger.info(f"✅ Successfully scraped {len(all_courses)} classes total")
        return all_courses

    def _apply_filters(self):
        """Apply filters for academic year, semester, and subject."""
        from selenium.webdriver.support.ui import Select
        
        try:
            # Wait for page elements to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "select"))
            )
            time.sleep(2)
            
            # Find and select academic year dropdown
            year_selects = self.driver.find_elements(By.TAG_NAME, "select")
            for select_element in year_selects:
                try:
                    select = Select(select_element)
                    options_text = [opt.text for opt in select.options]
                    if any(self.academic_year in opt for opt in options_text):
                        select.select_by_visible_text(self.academic_year)
                        logger.info(f"Selected academic year: {self.academic_year}")
                        time.sleep(1)
                        break
                except:
                    continue
            
            # Find and select semester dropdown
            for select_element in year_selects:
                try:
                    select = Select(select_element)
                    options_text = [opt.text for opt in select.options]
                    if any(self.semester in opt for opt in options_text):
                        select.select_by_visible_text(self.semester)
                        logger.info(f"Selected semester: {self.semester}")
                        time.sleep(1)
                        break
                except:
                    continue
            
            # Find subject input field and enter first subject
            subject_to_search = self.subjects[0] if self.subjects else "CS"
            logger.info(f"🔍 Searching for {subject_to_search} courses...")
            
            # Try to find the subject input by common input attributes
            inputs = self.driver.find_elements(By.TAG_NAME, "input")
            for input_elem in inputs:
                input_type = input_elem.get_attribute('type')
                if input_type == 'text':
                    try:
                        input_elem.clear()
                        input_elem.send_keys(subject_to_search)
                        logger.info(f"Entered subject code: {subject_to_search}")
                        break
                    except:
                        continue
            
            time.sleep(1)
            
            # Find and click search button - look for button with "TÌM KIẾM" text
            buttons = self.driver.find_elements(By.TAG_NAME, "input")
            buttons.extend(self.driver.find_elements(By.TAG_NAME, "button"))
            
            for button in buttons:
                button_text = button.get_attribute('value') or button.text
                if button_text and ('TÌM' in button_text.upper() or 'SEARCH' in button_text.upper()):
                    button.click()
                    logger.info("✅ Clicked search button")
                    time.sleep(3)  # Wait for search results
                    break
            
            logger.info("Filters applied successfully")
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            raise

    def _get_course_links(self) -> Dict[str, str]:
        """Extract course links from search results page.
        
        Returns:
            Dictionary mapping course codes to their detail page URLs
        """
        course_links = {}
        
        try:
            # Wait for results to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "a"))
            )
            
            # Parse the current page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find all links that might be course links
            # Looking for links with courseid parameter
            links = soup.find_all('a', href=True)
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Look for course detail links (containing courseid parameter)
                if 'courseid=' in href and text:
                    # Extract course code from link text
                    # The course code should match our monitored courses
                    for subject in self.subjects:
                        if text.startswith(subject):
                            # Make absolute URL if relative
                            if not href.startswith('http'):
                                base_url = self.target_url.split('?')[0]
                                href = base_url + '?' + href.split('?')[1] if '?' in href else base_url + href
                            
                            course_links[text] = href
                            logger.info(f"✅ Found course: {text}")
                            break
            
        except Exception as e:
            logger.error(f"Error extracting course links: {e}")
        
        return course_links
    
    def _scrape_course_detail_page(self, course_code: str, course_url: str) -> List[Dict[str, Any]]:
        """Scrape a single course detail page for class information.
        
        Args:
            course_code: Course code (e.g., "CS 403")
            course_url: URL to the course detail page
            
        Returns:
            List of class dictionaries for this course
        """
        classes = []
        
        try:
            # Navigate to course detail page
            self.driver.get(course_url)
            time.sleep(3)
            
            # Wait for table to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "table"))
            )
            
            # Parse the page
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Find the class table and parse it
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                # Skip if too few rows (not a class table)
                if len(rows) < 2:
                    continue
                
                # Check header row to identify class table
                header_row = rows[0]
                header_cells = header_row.find_all(['th', 'td'])
                header_text = ' '.join([cell.get_text(strip=True) for cell in header_cells])
                
                # Look for key Vietnamese column names in header
                if 'Tên lớp' in header_text or 'Mã đăng ký' in header_text or 'Còn lại' in header_text:
                    # This is the class table
                    logger.info(f"✅ Found class table with {len(rows)-1} row(s)")
                    
                    # Parse each class row (skip header)
                    for row in rows[1:]:
                        class_data = self._parse_class_row(row, course_code)
                        if class_data:
                            classes.append(class_data)
                    
                    break
            
            if classes:
                logger.info(f"✅ Found {len(classes)} class(es): {', '.join([c['class_name'] for c in classes])}")
            else:
                logger.warning(f"No classes found for {course_code}")
                
        except Exception as e:
            logger.error(f"Error scraping course detail page: {e}")
        
        return classes
    
    def _parse_class_row(self, row, course_code: str) -> Optional[Dict[str, Any]]:
        """Parse a single class row from the detail table.
        
        Args:
            row: BeautifulSoup row element
            course_code: Course code for this class
            
        Returns:
            Dictionary with class data or None
        """
        try:
            cols = row.find_all(['td', 'th'])
            
            if len(cols) < 4:
                return None
            
            def get_text(col):
                """Safely get text from column."""
                return col.get_text(strip=True) if col else ""
            
            # Parse columns based on the table structure from problem statement:
            # 0: Tên lớp (Class Name)
            # 1: Mã đăng ký (Registration Code)
            # 2: Loại hình (Type)
            # 3: Số chỗ Còn lại (Seats Available) - THIS IS KEY!
            # 4: Hạn đăng ký (Registration Deadline)
            # 5: Tuần học (Week)
            # 6: Giờ học (Schedule)
            # 7: Phòng (Room)
            # 8: Địa điểm (Location)
            # 9: Giảng viên (Instructor)
            # 10: Tình trạng Đăng ký (Registration Status)
            # 11: Tình trạng Triển khai (Deployment Status)
            
            class_name = get_text(cols[0]) if len(cols) > 0 else ""
            class_code = get_text(cols[1]) if len(cols) > 1 else ""
            class_type = get_text(cols[2]) if len(cols) > 2 else ""
            seats_available_text = get_text(cols[3]) if len(cols) > 3 else ""
            registration_deadline = get_text(cols[4]) if len(cols) > 4 else ""
            week = get_text(cols[5]) if len(cols) > 5 else ""
            schedule = get_text(cols[6]) if len(cols) > 6 else ""
            room = get_text(cols[7]) if len(cols) > 7 else ""
            location = get_text(cols[8]) if len(cols) > 8 else ""
            instructor = get_text(cols[9]) if len(cols) > 9 else ""
            registration_status = get_text(cols[10]) if len(cols) > 10 else ""
            deployment_status = get_text(cols[11]) if len(cols) > 11 else ""
            
            # Check if seats are available (NOT "Hết chỗ")
            has_seats = seats_available_text != "Hết chỗ"
            
            # Try to parse the number of seats
            available_seats = 0
            if has_seats:
                try:
                    # Try to extract number from text
                    available_seats = int(''.join(filter(str.isdigit, seats_available_text)))
                except:
                    # If not a number but not "Hết chỗ", consider as having seats
                    available_seats = 1
            
            logger.info(f"📊 {class_name}: {seats_available_text} {'(NOTIFY!)' if has_seats else '(skipped)'}")
            
            return {
                'course_code': course_code,
                'course_name': course_code,  # Will be updated if we can extract full name
                'class_name': class_name,
                'class_code': class_code,
                'class_type': class_type,
                'available_seats': available_seats,
                'seats_available_text': seats_available_text,
                'has_seats': has_seats,
                'total_capacity': 0,  # Not directly available
                'schedule': schedule,
                'room': room,
                'location': location,
                'instructor': instructor,
                'status': registration_status,
                'registration_deadline': registration_deadline,
                'week': week,
                'deployment_status': deployment_status
            }
            
        except Exception as e:
            logger.error(f"Error parsing class row: {e}")
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
