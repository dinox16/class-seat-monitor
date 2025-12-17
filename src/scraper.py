"""Web scraper for DTU course registration system."""
import time
import logging
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium. webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
from selenium. common.exceptions import TimeoutException, NoSuchElementException
from . models import Course

logger = logging.getLogger(__name__)


class CourseScraper:
    """Scraper for DTU course information."""
    
    BASE_URL = "https://courses.duytan.edu.vn/Sites/Home_ChuongTrinhDaoTao. aspx"
    SEARCH_URL = f"{BASE_URL}?p=home_coursesearch"
    
    def __init__(self, config: dict):
        """Initialize scraper with configuration."""
        self. config = config
        self.driver:  Optional[webdriver.Chrome] = None
        self.academic_year = config.get('academic_year', '2025-2026')
        self.semester = config.get('semester', 'Học Kỳ II')
        self.timeout = config.get('timeout', 60)
        
    def _init_driver(self):
        """Initialize Chrome webdriver."""
        chrome_options = Options()
        
        if self.config.get('headless', True):
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
        
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options. add_argument('--disable-blink-features=AutomationControlled')
        chrome_options. add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver. Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
        logger.info(" Chrome WebDriver initialized")
        
    def scrape_courses(self) -> List[Course]:
        """Scrape all monitored courses."""
        all_courses = []
        
        try:
            self._init_driver()
            
            # Get list of courses to monitor from config
            courses_to_monitor = self.config.get('courses_to_monitor', [])
            
            if not courses_to_monitor:
                logger.warning(" No courses to monitor in config!")
                return []
            
            logger.info(f" Monitoring {len(courses_to_monitor)} courses: {courses_to_monitor}")
            
            # Scrape each course
            for course_code in courses_to_monitor: 
                logger.info(f" Scraping {course_code}...")
                
                try:
                    # Extract subject prefix (e.g., "CS" from "CS 403")
                    subject = course_code.split()[0] if ' ' in course_code else course_code[: 3]
                    
                    courses = self._scrape_course(course_code, subject)
                    
                    if courses: 
                        all_courses.extend(courses)
                        logger.info(f" Found {len(courses)} classes for {course_code}")
                    else:
                        logger.warning(f" No classes found for {course_code}")
                        
                except Exception as e:
                    logger. error(f" Error scraping {course_code}: {e}")
                    continue
                    
            logger.info(f"Total courses scraped: {len(all_courses)}")
            
        except Exception as e:
            logger.error(f" Scraping failed: {e}")
            
        finally:
            if self. driver:
                self.driver. quit()
                logger.info(" Chrome WebDriver closed")
                
        return all_courses
    
    def _scrape_course(self, course_code: str, subject: str) -> List[Course]:
        """Scrape a specific course."""
        courses = []
        
        try: 
            # Navigate to search page
            logger.info(f" Navigating to search page...")
            self.driver.get(self.SEARCH_URL)
            time.sleep(3)
            
            # Select academic year
            logger.info(f" Selecting academic year:  {self.academic_year}")
            year_select = Select(self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ctl00_ddlNamHoc"))
            year_select.select_by_visible_text(self.academic_year)
            time.sleep(1)
            
            # Select semester
            logger. info(f"Selecting semester: {self. semester}")
            semester_select = Select(self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ctl00_ddlHocKy"))
            semester_select. select_by_visible_text(self.semester)
            time.sleep(1)
            
            # Select subject
            logger.info(f" Selecting subject: {subject}")
            subject_select = Select(self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ctl00_ddlKhoa"))
            subject_select.select_by_visible_text(subject)
            time.sleep(1)
            
            # Enter course code in search box (optional)
            search_box = self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ctl00_txtMaMonHoc")
            search_box.clear()
            time.sleep(0.5)
            
            # Click search button
            logger.info(f" Clicking search button...")
            search_btn = self.driver.find_element(By.ID, "ctl00_ContentPlaceHolder1_ctl00_btnTimKiem")
            search_btn.click()
            time.sleep(3)
            
            # Find the course link in results
            logger.info(f" Looking for course:  {course_code}")
            course_links = self.driver.find_elements(By.XPATH, f"//a[contains(text(), '{course_code}')]")
            
            if not course_links:
                logger.warning(f" Course {course_code} not found in search results")
                return []
            
            # Click on the first matching course
            logger.info(f"📖 Opening course detail page...")
            course_links[0].click()
            time.sleep(3)
            
            # Parse course detail page
            courses = self._parse_course_detail(course_code)
            
        except Exception as e:
            logger.error(f" Error in _scrape_course: {e}")
            import traceback
            traceback.print_exc()
            
        return courses
    
    def _parse_course_detail(self, course_code: str) -> List[Course]:
        """Parse course detail page to extract class information."""
        courses = []
        
        try:
            # Wait for table to load
            wait = WebDriverWait(self. driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            
            # Find all class rows (rows with class information)
            rows = self.driver.find_elements(By. XPATH, "//table//tr[contains(@class, 'lichthi')]")
            
            if not rows:
                # Try alternative xpath
                rows = self.driver.find_elements(By.XPATH, "//table//tr[td[contains(@class, 'tenmonhoc')]]")
            
            if not rows:
                logger.warning(f" No class rows found for {course_code}")
                return []
            
            logger.info(f" Found {len(rows)} potential class rows")
            
            for row in rows:
                try:
                    cells = row.find_elements(By.TAG_NAME, "td")
                    
                    if len(cells) < 10:
                        continue
                    
                    # Extract data from cells
                    class_name = cells[0].text.strip()
                    registration_code = cells[1].text.strip()
                    class_type = cells[2].text.strip()
                    seats_text = cells[3].text.strip()  # "Hết chỗ" or number
                    schedule = cells[6].text.strip()
                    room = cells[7].text.strip()
                    location = cells[8].text.strip()
                    instructor = cells[9].text.strip()
                    registration_status = cells[10].text.strip() if len(cells) > 10 else ""
                    
                    # CHECK:  If NOT "Hết chỗ" → HAS SEATS! 
                    has_seats = "Hết chỗ" not in seats_text
                    
                    if not has_seats:
                        logger.info(f"    {class_name}:  Hết chỗ (skipped)")
                        continue
                    
                    # Try to parse number of seats
                    available_seats = 1  # Default to 1 if not "Hết chỗ"
                    if seats_text and seats_text.isdigit():
                        available_seats = int(seats_text)
                    
                    logger.info(f"    {class_name}: CÓ CHỖ!  ({seats_text})")
                    
                    # Create Course object
                    course = Course(
                        code=course_code,
                        name=f"{course_code} - {class_name}",
                        class_name=class_name,
                        registration_code=registration_code,
                        available_seats=available_seats,
                        total_seats=0,  # Not available on website
                        schedule=schedule,
                        room=room,
                        location=location,
                        instructor=instructor,
                        registration_status=registration_status
                    )
                    
                    courses.append(course)
                    
                except Exception as e:
                    logger.error(f" Error parsing row: {e}")
                    continue
            
            logger.info(f" Parsed {len(courses)} classes with available seats")
            
        except Exception as e:
            logger.error(f" Error in _parse_course_detail: {e}")
            import traceback
            traceback.print_exc()
            
        return courses
