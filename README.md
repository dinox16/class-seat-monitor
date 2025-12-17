# 🎓 Class Seat Monitor

Monitor class seat availability on Duy Tan University course registration system with real-time Telegram notifications.

## 📋 Overview

This application automatically monitors course seat availability on the [Duy Tan University course registration website](https://courses.duytan.edu.vn/Sites/Home_ChuongTrinhDaoTao.aspx?p=home_coursesearch) and sends instant Telegram notifications when seats become available.

### ✨ Features

- 🔍 **Automated Web Scraping**: Uses Selenium to scrape course data from JavaScript-rendered pages
- 💾 **Database Tracking**: SQLite database tracks seat changes over time
- 📱 **Telegram Notifications**: Instant alerts when seats become available
- ⚙️ **Configurable Monitoring**: Set thresholds and filters for specific courses
- 🐳 **Docker Support**: Easy deployment with Docker and docker-compose
- 🔄 **Automatic Scheduling**: Configurable check intervals (default: 5 minutes)
- 📊 **Summary Reports**: Get periodic summaries of monitoring status
- 🛡️ **Error Handling**: Retry logic and error notifications

## 🏗️ Architecture

```
class-seat-monitor/
├── src/
│   ├── __init__.py
│   ├── config.py          # Configuration management
│   ├── database.py        # SQLite database layer
│   ├── scraper.py         # Web scraper using Selenium
│   ├── notifier.py        # Telegram bot integration
│   └── monitor.py         # Main monitoring logic
├── data/                  # Database storage
├── logs/                  # Application logs
├── main.py               # CLI entry point
├── config.yaml           # Configuration file
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Docker compose configuration
├── setup.sh            # Setup automation script
└── README.md           # Documentation
```

## 🚀 Installation

### Prerequisites

- Python 3.9 or higher
- Google Chrome or Chromium (for Selenium)
- Telegram account
- (Optional) Docker and Docker Compose

### Option 1: Local Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dinox16/class-seat-monitor.git
   cd class-seat-monitor
   ```

2. **Run the setup script**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

   The setup script will:
   - Check Python version
   - Create virtual environment
   - Install dependencies
   - Create necessary directories
   - Copy `.env.example` to `.env`

3. **Configure your environment**
   
   Edit `.env` file:
   ```bash
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_IDS=123456789,987654321
   ```

4. **Configure courses to monitor**
   
   Edit `config.yaml` to add courses you want to monitor:
   ```yaml
   courses_to_monitor:
     - course_code: "CS 403"
       notify_when_seats_gt: 0
     - course_code: "CS 100"
       notify_when_seats_gt: 5
   ```

### Option 2: Docker Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/dinox16/class-seat-monitor.git
   cd class-seat-monitor
   ```

2. **Create `.env` file**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Build and run with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **View logs**
   ```bash
   docker-compose logs -f
   ```

## 🔧 Configuration

### Telegram Bot Setup

1. **Create a Telegram Bot**
   - Open Telegram and search for [@BotFather](https://t.me/BotFather)
   - Send `/newbot` command
   - Follow instructions to create your bot
   - Copy the bot token provided

2. **Get Your Chat ID**
   - Send a message to your bot
   - Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
   - Find your `chat_id` in the response
   - Alternatively, use [@userinfobot](https://t.me/userinfobot)

3. **Configure the Application**
   - Add bot token to `.env` file
   - Add chat ID(s) to `.env` file

### Configuration File (config.yaml)

```yaml
# Telegram configuration
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  chat_ids:
    - 123456789

# Monitoring settings
monitoring:
  interval_minutes: 5
  target_url: "https://courses.duytan.edu.vn/Sites/Home_ChuongTrinhDaoTao.aspx?p=home_coursesearch"

# Courses to monitor
courses_to_monitor:
  - course_code: "CS 403"
    notify_when_seats_gt: 0
  - course_code: "CS 100"
    notify_when_seats_gt: 5

# Scraper settings
scraper:
  academic_year: "2025-2026"
  semester: "Học Kỳ II"
  subject: "CS"
  headless: true
  timeout: 30

# Database settings
database:
  path: "data/courses.db"

# Logging settings
logging:
  level: "INFO"
  file: "logs/monitor.log"
```

## 💻 Usage

### Command Line Interface

#### Start Monitoring
```bash
python main.py start
```

#### Add Course to Watchlist
```bash
# Add with default threshold (0)
python main.py add-course "CS 403"

# Add with custom threshold
python main.py add-course "CS 100" --threshold 5
```

#### List Monitored Courses
```bash
python main.py list
```

#### Test Scraper
```bash
python main.py test-scraper
```

#### Test Telegram Notifications
```bash
python main.py test-telegram
```

#### Send Summary
```bash
python main.py summary
```

#### View Help
```bash
python main.py --help
```

### Docker Usage

```bash
# Start the monitor
docker-compose up -d

# View logs
docker-compose logs -f seat-monitor

# Stop the monitor
docker-compose down

# Restart the monitor
docker-compose restart

# Rebuild after changes
docker-compose up -d --build
```

## 📱 Notification Examples

### Seat Availability Alert
```
🎓 Seat Available Alert!

Course: CS 403 - Advanced Algorithms
Class Code: CS403202502003

📊 Seat Update:
  • Previous: 0
  • Current: 5
  • Added: +5
  • Capacity: 50

🕐 Schedule: T3, T5 (7:00-9:30)
🏫 Room: H201
👨‍🏫 Instructor: Dr. Nguyen Van A
📝 Status: Đang Đăng Ký

⏰ Detected at: 2025-12-17 10:30:15
```

### Monitoring Summary
```
📋 Monitoring Summary

🔍 Monitored Courses: 2
📚 Total Courses Found: 5
🔔 Changes Detected: 1
⏰ Last Check: 2025-12-17 10:30:00

Course Details:
  • CS 403: 5 seats
  • CS 100: 12 seats
```

## 🔍 Troubleshooting

### Common Issues

1. **Chrome/ChromeDriver Issues**
   - The application uses `webdriver-manager` to automatically download ChromeDriver
   - If issues persist, ensure Chrome/Chromium is installed:
     ```bash
     # Ubuntu/Debian
     sudo apt-get install chromium-browser
     
     # macOS
     brew install chromium
     ```

2. **Telegram Bot Not Responding**
   - Verify bot token is correct
   - Check that you've sent `/start` to your bot
   - Confirm chat ID is correct
   - Test with: `python main.py test-telegram`

3. **No Courses Found**
   - Website structure may have changed
   - Check logs for scraping errors
   - Verify target URL is accessible
   - Test with: `python main.py test-scraper`

4. **Database Locked**
   - Ensure only one instance is running
   - Check file permissions on `data/` directory

### Logs

Logs are stored in `logs/monitor.log`:
```bash
# View logs
tail -f logs/monitor.log

# View last 100 lines
tail -n 100 logs/monitor.log
```

## 🛠️ Development

### Project Structure

- **src/config.py**: Configuration management with YAML and environment variables
- **src/database.py**: SQLite database operations
- **src/scraper.py**: Web scraping with Selenium and BeautifulSoup
- **src/notifier.py**: Telegram bot integration
- **src/monitor.py**: Main monitoring loop with APScheduler
- **main.py**: CLI interface with argparse

### Running Tests

```bash
# Test scraper
python main.py test-scraper

# Test Telegram
python main.py test-telegram

# Test monitoring cycle (run once)
python -c "from src.monitor import SeatMonitor; m = SeatMonitor(); m.check_and_notify()"
```

### Database Schema

**courses** table:
- id, course_code, course_name, class_code
- available_seats, total_capacity
- schedule, room, instructor, status
- last_updated

**seat_history** table:
- id, class_code, available_seats, total_capacity, timestamp

**monitored_courses** table:
- id, course_code, notify_when_seats_gt, is_active, added_at

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational purposes only. Please ensure you comply with Duy Tan University's terms of service and website usage policies. Be respectful with scraping frequency to avoid overloading the server.

## 📞 Support

If you encounter any issues or have questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review logs for error details

## 🎯 Future Enhancements

- [ ] Web dashboard for monitoring status
- [ ] Support for multiple universities
- [ ] Email notifications
- [ ] Mobile app
- [ ] Course availability predictions
- [ ] Advanced filtering options
- [ ] Multi-language support

## 🙏 Acknowledgments

- Duy Tan University for the course registration system
- Python community for excellent libraries
- Contributors and testers

---

Made with ❤️ by the Class Seat Monitor team
