"""Configuration management for wallpaper randomizer."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class Config:
    """Configuration manager."""

    DEFAULT_CONFIG_PATH = "config.yaml"
    TEMPLATE_PATH = "config.yaml.template"

    def __init__(self, config_path: str = None):
        """Initialize configuration.

        Args:
            config_path: Path to config file. Defaults to config.yaml in current directory.
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file.

        Returns:
            Configuration dictionary.

        Raises:
            FileNotFoundError: If config file doesn't exist.
            ValueError: If config is invalid.
        """
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Run 'python -m wallpaper_randomizer init' to create one."
            )

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        self._validate_config(config)
        return config

    def _validate_config(self, config: Dict[str, Any]) -> None:
        """Validate configuration structure and values.

        Args:
            config: Configuration dictionary to validate.

        Raises:
            ValueError: If configuration is invalid.
        """
        # Check required sections
        required_sections = ['subreddits', 'min_resolution',
                             'post_filter', 'reddit', 'cache_dir']
        for section in required_sections:
            if section not in config:
                raise ValueError(
                    f"Missing required configuration section: {section}")

        # Validate subreddits
        if not isinstance(config['subreddits'], list) or len(config['subreddits']) == 0:
            raise ValueError("'subreddits' must be a non-empty list")

        # Validate min_resolution
        if 'width' not in config['min_resolution'] or 'height' not in config['min_resolution']:
            raise ValueError(
                "'min_resolution' must contain 'width' and 'height'")
        if config['min_resolution']['width'] <= 0 or config['min_resolution']['height'] <= 0:
            raise ValueError(
                "Resolution width and height must be positive integers")

        # Validate post_filter
        valid_sorts = ['hot', 'new', 'top', 'controversial', 'rising']
        if config['post_filter']['sort'] not in valid_sorts:
            raise ValueError(
                f"'sort' must be one of: {', '.join(valid_sorts)}")

        if config['post_filter']['sort'] in ['top', 'controversial']:
            valid_time_filters = ['hour', 'day',
                                  'week', 'month', 'year', 'all']
            time_filter = config['post_filter'].get('time_filter', 'month')
            if time_filter not in valid_time_filters:
                raise ValueError(
                    f"'time_filter' must be one of: {', '.join(valid_time_filters)}")

        # Validate Reddit credentials
        if not config['reddit'].get('client_id') or config['reddit']['client_id'] == 'YOUR_CLIENT_ID_HERE':
            raise ValueError(
                "Reddit client_id not configured. Please add your Reddit API credentials.")
        if not config['reddit'].get('client_secret') or config['reddit']['client_secret'] == 'YOUR_CLIENT_SECRET_HERE':
            raise ValueError(
                "Reddit client_secret not configured. Please add your Reddit API credentials.")

    @staticmethod
    def create_default_config(config_path: str = None) -> None:
        """Create a default configuration file from template.

        Args:
            config_path: Where to create the config file.
        """
        config_path = config_path or Config.DEFAULT_CONFIG_PATH

        if os.path.exists(config_path):
            raise FileExistsError(
                f"Configuration file already exists: {config_path}")

        # Copy template to config path
        template_path = Config.TEMPLATE_PATH
        if not os.path.exists(template_path):
            raise FileNotFoundError(
                f"Template file not found: {template_path}")

        with open(template_path, 'r') as src:
            content = src.read()

        with open(config_path, 'w') as dst:
            dst.write(content)

        print(f"Created configuration file: {config_path}")
        print("Please edit it to add your Reddit API credentials.")

    def get_cache_dir(self) -> Path:
        """Get the cache directory path, expanding ~ if necessary.

        Returns:
            Path object for cache directory.
        """
        cache_dir = self.data['cache_dir']
        return Path(os.path.expanduser(cache_dir))

    def get_subreddits(self) -> list:
        """Get list of subreddits."""
        return self.data['subreddits']

    def get_min_resolution(self) -> tuple:
        """Get minimum resolution as (width, height)."""
        return (
            self.data['min_resolution']['width'],
            self.data['min_resolution']['height']
        )

    def get_post_filter(self) -> Dict[str, Any]:
        """Get post filter settings."""
        return self.data['post_filter']

    def get_reddit_credentials(self) -> Dict[str, str]:
        """Get Reddit API credentials."""
        return self.data['reddit']

    def get_max_cache_size_mb(self) -> int:
        """Get maximum cache size in MB."""
        return self.data.get('max_cache_size_mb', 500)

    def get_wallpaper_tool(self) -> Optional[str]:
        """Get optional wallpaper tool override.

        Returns:
            Tool name if specified in config, None otherwise.
        """
        wallpaper_tool = self.data.get('wallpaper_tool')
        if wallpaper_tool and isinstance(wallpaper_tool, dict):
            return wallpaper_tool.get('tool')
        return None
