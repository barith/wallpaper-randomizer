"""Shared wallpaper fetching logic with retry mechanism."""

from pathlib import Path
from typing import Optional, Callable, Dict, Any

from .config import Config
from .reddit_fetcher import RedditFetcher
from .image_handler import ImageHandler


def fetch_wallpaper_with_retry(
    config: Config,
    reddit_fetcher: RedditFetcher,
    image_handler: ImageHandler,
    status_callback: Optional[Callable[[str], None]] = None
) -> Optional[Path]:
    """Fetch and download a wallpaper with retry logic.

    This function implements the retry mechanism that attempts to fetch
    a valid wallpaper multiple times if the first attempt fails due to
    resolution mismatch or download errors.

    Args:
        config: Configuration object
        reddit_fetcher: RedditFetcher instance for fetching posts
        image_handler: ImageHandler instance for downloading and validating images
        status_callback: Optional callback function for status updates

    Returns:
        Path to the downloaded image file, or None if all attempts failed
    """
    def log(message: str):
        """Log a status message via callback if provided."""
        if status_callback:
            status_callback(message)

    # Get configuration settings
    post_filter = config.get_post_filter()
    selection_mode = config.get_selection_mode()
    retry_count = config.get_retry_count()

    # Fetch wallpaper with retry logic
    log("Fetching posts from Reddit...")
    image_path = None
    tried_indices = set()

    for attempt in range(retry_count):
        # Determine parameters based on selection mode
        if selection_mode == 'first':
            skip_count = attempt
            exclude_indices = None
        else:
            skip_count = 0
            exclude_indices = tried_indices

        # Fetch wallpaper
        wallpaper_info = reddit_fetcher.get_random_wallpaper_url(
            config.get_subreddits(),
            sort=post_filter['sort'],
            time_filter=post_filter.get('time_filter', 'month'),
            limit=post_filter.get('limit', 100),
            selection_mode=selection_mode,
            skip_count=skip_count,
            exclude_indices=exclude_indices,
            filter_nsfw=config.get_filter_nsfw()
        )

        if not wallpaper_info:
            if attempt == 0:
                log("Failed to find any suitable wallpapers")
                return None
            else:
                log(
                    f"No more wallpapers to try (attempt {attempt + 1}/{retry_count})")
                break

        log(f"\nAttempt {attempt + 1}/{retry_count}:")
        log(f"  Title: {wallpaper_info['title']}")
        log(f"  Subreddit: r/{wallpaper_info['subreddit']}")
        log(f"  URL: {wallpaper_info['url']}")

        # Track tried indices for random mode
        if selection_mode == 'random':
            tried_indices.add(wallpaper_info['index'])

        # Download and validate image
        image_path = image_handler.download_image(
            wallpaper_info['url'],
            wallpaper_info['title']
        )

        if image_path:
            # Successfully downloaded and validated
            break
        else:
            if attempt < retry_count - 1:
                log("Failed to download or validate image, trying next wallpaper...")
            else:
                log("Failed to download or validate image")

    if not image_path:
        log(f"\nFailed to get a valid wallpaper after {retry_count} attempts")
        return None

    return image_path
