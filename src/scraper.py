"""Web scraper for DTU course registration system."""
import time
import logging
from typing import List, Optional
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common. by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from . models import Course

logger = logging. getLogger(__name__)

# Table structure constants
MIN_REQUIRED_CELLS = 10  # Minimum cells needed for valid course row


class CourseScraper: 
    """Scraper for DTU course information."""
    
    def __init__(self, config: dict):
        """Initialize scraper with configuration."""
        self.config = config
        self.driver: Optional[webdriver.Chrome] = None
        self.timeout = config.get('timeout', 30)
        
    def _init_driver(self):
        """Initialize Chrome webdriver."""
        chrome_options = Options()
        
        if self.config.get('headless', True):
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
        
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.implicitly_wait(10)
        
        logger.info("Chrome WebDriver initialized")
        
    def scrape_courses(self) -> List[Course]:
        """Scrape all monitored courses."""
        all_courses = []
        
        try: 
            self._init_driver()
            
            courses_config = self.config.get('courses_to_monitor', [])
            
            if not courses_config:
                logger.warning("No courses to monitor!")
                return []
            
            logger.info(f"Monitoring {len(courses_config)} courses")
            
            for course_config in courses_config:
                code = course_config['code']
                url = course_config['url']
                name = course_config.get('name', '')
                
                logger.info(f"Scraping {code} - {name}")
                logger.info(f"URL: {url}")
                
                try:
                    # Go directly to detail page
                    self.driver. get(url)
                    time.sleep(3)
                    
                    # Parse the class table
                    courses = self._parse_course_detail(code, name)
                    
                    if courses:
                        all_courses.extend(courses)
                        logger.info(f"Found {len(courses)} classes with seats for {code}")
                    else: 
                        logger.info(f"No available seats for {code}")
                        
                except Exception as e: 
                    logger.error(f" Error scraping {code}: {e}")
                    continue
        
            logger.info(f"Total classes with seats: {len(all_courses)}")
            
        except Exception as e:
            logger.error(f"Scraping failed: {e}")
            
        finally:
            if self. driver:
                self.driver. quit()
                logger.info("Chrome WebDriver closed")
        
        return all_courses
    
    def _parse_course_detail(self, course_code:  str, course_name: str) -> List[Course]:
        """Parse course detail page table."""
        courses = []
        
        try: 
            # Wait for table
            wait = WebDriverWait(self. driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
            
            # Find all table rows with td elements
            rows = self. driver.find_elements(By. XPATH, "//table//tr[td]")
            
            logger.info(f"📊 Found {len(rows)} rows")
            
            for row in rows:
                try:
                    cells = row. find_elements(By.TAG_NAME, "td")
                    
                    # Need at least MIN_REQUIRED_CELLS for valid row
                    if len(cells) < MIN_REQUIRED_CELLS:
                        continue
                    
                    # Extract basic info
                    class_name = cells[0].text.strip()
                    registration_code = cells[1].text.strip()
                    
                    if not class_name or not registration_code:
                        continue
                    
                    # KEY:  Check column 3 for "Số chỗ Còn lại"
                    seats_cell = cells[3]
                    seats_text = seats_cell. text.strip()
                    
                    # If "Hết chỗ" → SKIP!
                    if "Hết chỗ" in seats_text:
                        logger. info(f"{class_name}: Hết chỗ (skipped)")
                        continue
                    
                    # If empty seats_text → SKIP!
                    if not seats_text:
                        logger.info(f"{class_name}: Empty seats info (skipped)")
                        continue
                    
                    # No "Hết chỗ" AND has text → HAS SEATS!
                    logger.info(f"{class_name}: CÓ CHỖ!  ({seats_text})")
                    
                    # Extract other data
                    schedule = cells[6].text.strip() if len(cells) > 6 else ""  # Giờ học
                    room = cells[7].text.strip() if len(cells) > 7 else ""      # Phòng
                    location = cells[8].text.strip() if len(cells) > 8 else ""  # Địa điểm
                    instructor = cells[9].text.strip() if len(cells) > 9 else "" # Giảng viên
                    
                    # Try to parse seat number
                    if seats_text.isdigit():
                        available_seats = int(seats_text)
                    else:
                        # Has non-numeric text (but not "Hết chỗ"), default to 1
                        available_seats = 1
                    
                    course = Course(
                        code=course_code,
                        name=f"{course_code} - {course_name}",
                        class_name=class_name,
                        registration_code=registration_code,
                        available_seats=available_seats,
                        total_seats=0,
                        schedule=schedule,
                        room=room,
                        location=location,
                        instructor=instructor,
                        registration_status=""
                    )
                    
                    courses.append(course)
                    
                except Exception as e:
                    logger.error(f"Error parsing row: {e}")
                    continue
            
            logger.info(f"Parsed {len(courses)} classes with available seats")
            
        except Exception as e:
            logger.error(f"Error in _parse_course_detail: {e}")
            import traceback
            traceback.print_exc()
        
        return courses
