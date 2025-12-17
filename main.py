#!/usr/bin/env python3
"""Main entry point for the Class Seat Monitor application."""

import sys
import logging
import signal
from pathlib import Path
import argparse

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent))

from src.monitor import SeatMonitor


def setup_logging(log_file: str = "logs/monitor.log", log_level: str = "INFO"):
    """Set up logging configuration.
    
    Args:
        log_file: Path to log file
        log_level: Logging level
    """
    # Create logs directory if it doesn't exist
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    print("\n\n🛑 Shutting down gracefully...")
    sys.exit(0)


def cmd_start(args):
    """Start the monitoring system.
    
    Args:
        args: Command line arguments
    """
    print("🚀 Starting Class Seat Monitor...")
    print(f"Configuration: {args.config}")
    print()
    
    monitor = SeatMonitor(args.config)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start monitoring
    monitor.start()


def cmd_add_course(args):
    """Add a course to the monitoring watchlist.
    
    Args:
        args: Command line arguments
    """
    monitor = SeatMonitor(args.config)
    monitor.add_course(args.course_code, args.threshold)


def cmd_list(args):
    """List all monitored courses.
    
    Args:
        args: Command line arguments
    """
    monitor = SeatMonitor(args.config)
    monitor.list_monitored_courses()


def cmd_test_scraper(args):
    """Test the scraper functionality.
    
    Args:
        args: Command line arguments
    """
    monitor = SeatMonitor(args.config)
    monitor.test_scraper()


def cmd_test_telegram(args):
    """Test Telegram notifications.
    
    Args:
        args: Command line arguments
    """
    monitor = SeatMonitor(args.config)
    monitor.test_telegram()


def cmd_summary(args):
    """Send a monitoring summary.
    
    Args:
        args: Command line arguments
    """
    monitor = SeatMonitor(args.config)
    monitor.send_summary()


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description='Class Seat Monitor - Track course seat availability',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py start                           # Start monitoring
  python main.py add-course "CS 403"             # Add course to watchlist
  python main.py add-course "CS 100" -t 5        # Add with threshold
  python main.py list                            # List monitored courses
  python main.py test-scraper                    # Test scraper
  python main.py test-telegram                   # Test Telegram bot
  python main.py summary                         # Send summary
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '-l', '--log-level',
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Set logging level (default: INFO)'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    parser_start = subparsers.add_parser('start', help='Start monitoring')
    parser_start.set_defaults(func=cmd_start)
    
    # Add course command
    parser_add = subparsers.add_parser('add-course', help='Add course to watchlist')
    parser_add.add_argument('course_code', help='Course code (e.g., "CS 403")')
    parser_add.add_argument(
        '-t', '--threshold',
        type=int,
        default=0,
        help='Notify when seats > threshold (default: 0)'
    )
    parser_add.set_defaults(func=cmd_add_course)
    
    # List command
    parser_list = subparsers.add_parser('list', help='List monitored courses')
    parser_list.set_defaults(func=cmd_list)
    
    # Test scraper command
    parser_test_scraper = subparsers.add_parser('test-scraper', help='Test scraper')
    parser_test_scraper.set_defaults(func=cmd_test_scraper)
    
    # Test Telegram command
    parser_test_telegram = subparsers.add_parser('test-telegram', help='Test Telegram bot')
    parser_test_telegram.set_defaults(func=cmd_test_telegram)
    
    # Summary command
    parser_summary = subparsers.add_parser('summary', help='Send monitoring summary')
    parser_summary.set_defaults(func=cmd_summary)
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    
    # Execute command
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
