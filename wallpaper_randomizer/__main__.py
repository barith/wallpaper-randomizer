"""Main CLI entry point for wallpaper randomizer."""

import sys
import argparse
from pathlib import Path

from .config import Config
from .reddit_fetcher import RedditFetcher
from .image_handler import ImageHandler
from .wallpaper_setter import WallpaperSetter
from .wallpaper_fetcher import fetch_wallpaper_with_retry
from .gui import launch_gui


def cmd_init(args):
    """Initialize configuration file."""
    try:
        Config.create_default_config(args.config)
        print("\nNext steps:")
        print("1. Go to https://www.reddit.com/prefs/apps")
        print("2. Click 'Create App' or 'Create Another App'")
        print("3. Select 'script' as the app type")
        print("4. Fill in the form (redirect uri can be http://localhost:8080)")
        print("5. Copy client_id and client_secret to config.yaml")
        return 0
    except FileExistsError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"Error creating config: {e}")
        return 1


def cmd_test_config(args):
    """Test configuration validity."""
    try:
        config = Config(args.config)
        print("✓ Configuration file loaded successfully")
        print(f"✓ Subreddits: {', '.join(config.get_subreddits())}")
        print(
            f"✓ Minimum resolution: {config.get_min_resolution()[0]}x{config.get_min_resolution()[1]}")
        print(f"✓ Post filter: {config.get_post_filter()['sort']}", end='')
        if config.get_post_filter()['sort'] in ['top', 'controversial']:
            print(
                f" (time: {config.get_post_filter().get('time_filter', 'month')})")
        else:
            print()
        print(f"✓ Cache directory: {config.get_cache_dir()}")
        print("\nConfiguration is valid!")
        return 0
    except Exception as e:
        print(f"✗ Configuration error: {e}")
        return 1


def cmd_clear_cache(args):
    """Clear image cache."""
    try:
        config = Config(args.config)
        cache_dir = config.get_cache_dir()

        if not cache_dir.exists():
            print("Cache directory doesn't exist")
            return 0

        image_handler = ImageHandler(cache_dir, (0, 0))
        count = image_handler.clear_cache()
        print(f"Removed {count} cached images")
        return 0
    except Exception as e:
        print(f"Error clearing cache: {e}")
        return 1


def cmd_gui(args):
    """Launch the GUI application."""
    try:
        launch_gui(args.config)
        return 0
    except Exception as e:
        print(f"Error launching GUI: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_set_wallpaper(args):
    """Set a random wallpaper."""
    try:
        # Load configuration
        print("Loading configuration...")
        config = Config(args.config)

        # Initialize components
        reddit_fetcher = RedditFetcher(config.get_reddit_credentials())
        image_handler = ImageHandler(
            config.get_cache_dir(),
            config.get_min_resolution()
        )
        wallpaper_setter = WallpaperSetter()

        # Fetch wallpaper with retry logic using shared function
        result = fetch_wallpaper_with_retry(
            config=config,
            reddit_fetcher=reddit_fetcher,
            image_handler=image_handler,
            status_callback=print
        )

        if not result:
            return 1

        image_path, wallpaper_info = result

        # Set wallpaper
        print(f"\nSetting wallpaper...")
        if wallpaper_setter.set_wallpaper(image_path):
            print("\n✓ Wallpaper set successfully!")

            # Clean up old cache if needed
            max_cache_mb = config.get_max_cache_size_mb()
            current_cache_mb = image_handler.get_cache_size_mb()
            print(f"\nCache size: {current_cache_mb:.1f}MB / {max_cache_mb}MB")

            if current_cache_mb > max_cache_mb:
                deleted = image_handler.cleanup_old_cache(max_cache_mb)
                print(f"Cleaned up {deleted} old images")

            return 0
        else:
            print("\n✗ Failed to set wallpaper")
            return 1

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Set random wallpapers from Reddit',
        prog='wallpaper-randomizer'
    )
    parser.add_argument(
        '-c', '--config',
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # init command
    parser_init = subparsers.add_parser(
        'init', help='Initialize configuration file')
    parser_init.set_defaults(func=cmd_init)

    # test-config command
    parser_test = subparsers.add_parser(
        'test-config', help='Validate configuration')
    parser_test.set_defaults(func=cmd_test_config)

    # clear-cache command
    parser_clear = subparsers.add_parser(
        'clear-cache', help='Clear image cache')
    parser_clear.set_defaults(func=cmd_clear_cache)

    # gui command
    parser_gui = subparsers.add_parser('gui', help='Launch GUI application')
    parser_gui.set_defaults(func=cmd_gui)

    # set command (default)
    parser_set = subparsers.add_parser('set', help='Set random wallpaper')
    parser_set.set_defaults(func=cmd_set_wallpaper)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == '__main__':
    sys.exit(main())
