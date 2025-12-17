"""Configuration management for the Class Seat Monitor."""

import os
import yaml
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv


class Config:
    """Configuration handler for the monitoring system."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration.
        
        Args:
            config_path: Path to the YAML configuration file
        """
        # Load environment variables from .env file
        load_dotenv()
        
        self.config_path = Path(config_path)
        self.config_data = self._load_config()
        self._apply_env_overrides()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file.
        
        Returns:
            Dictionary containing configuration data
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        
        with open(self.config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config

    def _apply_env_overrides(self):
        """Apply environment variable overrides to configuration."""
        # Telegram configuration
        if os.getenv('TELEGRAM_BOT_TOKEN'):
            self.config_data['telegram']['bot_token'] = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if os.getenv('TELEGRAM_CHAT_IDS'):
            chat_ids = os.getenv('TELEGRAM_CHAT_IDS').split(',')
            self.config_data['telegram']['chat_ids'] = [int(id.strip()) for id in chat_ids]
        
        # Monitoring configuration
        if os.getenv('MONITORING_INTERVAL_MINUTES'):
            self.config_data['monitoring']['interval_minutes'] = int(os.getenv('MONITORING_INTERVAL_MINUTES'))
        
        # Database configuration
        if os.getenv('DATABASE_PATH'):
            self.config_data['database']['path'] = os.getenv('DATABASE_PATH')
        
        # Logging configuration
        if os.getenv('LOG_LEVEL'):
            self.config_data['logging']['level'] = os.getenv('LOG_LEVEL')
        
        if os.getenv('LOG_FILE'):
            self.config_data['logging']['file'] = os.getenv('LOG_FILE')
        
        # Scraper configuration
        if os.getenv('SCRAPER_HEADLESS'):
            self.config_data['scraper']['headless'] = os.getenv('SCRAPER_HEADLESS').lower() == 'true'
        
        if os.getenv('SCRAPER_TIMEOUT'):
            self.config_data['scraper']['timeout'] = int(os.getenv('SCRAPER_TIMEOUT'))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key.
        
        Args:
            key: Configuration key (supports nested keys with dot notation)
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value

    @property
    def telegram_bot_token(self) -> str:
        """Get Telegram bot token."""
        token = self.get('telegram.bot_token', '')
        # Replace ${VAR} syntax with environment variables
        if token.startswith('${') and token.endswith('}'):
            var_name = token[2:-1]
            return os.getenv(var_name, '')
        return token

    @property
    def telegram_chat_ids(self) -> List[int]:
        """Get list of Telegram chat IDs."""
        return self.get('telegram.chat_ids', [])

    @property
    def monitoring_interval(self) -> int:
        """Get monitoring interval in minutes."""
        return self.get('monitoring.interval_minutes', 5)

    @property
    def target_url(self) -> str:
        """Get target URL for scraping."""
        return self.get('monitoring.target_url', '')

    @property
    def courses_to_monitor(self) -> List[Dict[str, Any]]:
        """Get list of courses to monitor."""
        return self.get('courses_to_monitor', [])

    @property
    def scraper_config(self) -> Dict[str, Any]:
        """Get scraper configuration."""
        return self.get('scraper', {})

    @property
    def database_path(self) -> str:
        """Get database file path."""
        return self.get('database.path', 'data/courses.db')

    @property
    def log_level(self) -> str:
        """Get logging level."""
        return self.get('logging.level', 'INFO')

    @property
    def log_file(self) -> str:
        """Get log file path."""
        return self.get('logging.file', 'logs/monitor.log')
