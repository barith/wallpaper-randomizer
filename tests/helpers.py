"""Pure helper functions shared across the wallpaper_randomizer test suite.

These are plain functions (NOT pytest fixtures) so they can be called directly
inside tests, e.g.::

    from .helpers import valid_config_dict, make_submission, make_png

Keep this module dependency-light: it only needs the stdlib, Pillow and PyYAML.
It must never import ``wallpaper_randomizer.gui`` (needs Tk) or any module that
transitively requires a display.
"""

from pathlib import Path
from types import SimpleNamespace

from PIL import Image


def valid_config_dict() -> dict:
    """Return a fully valid config dict that passes ``Config._validate_config``.

    Uses fake (but non-placeholder) Reddit credentials so validation passes
    without any real API access. Copy and mutate the result to build specific
    invalid-config cases in tests.
    """
    return {
        "subreddits": ["wallpaper", "wallpapers"],
        "min_resolution": {"width": 1920, "height": 1080},
        "post_filter": {
            "sort": "top",
            "time_filter": "month",
            "limit": 100,
            "selection_mode": "random",
            "retry_count": 5,
            "filter_nsfw": True,
        },
        "reddit": {
            "client_id": "FAKE_CLIENT_ID",
            "client_secret": "FAKE_CLIENT_SECRET",
            "user_agent": "wallpaper-randomizer-test/1.0",
        },
        "cache_dir": "/tmp/wallpaper-randomizer-test-cache",
        "max_cache_size_mb": 500,
    }


def make_submission(
    url: str = "https://i.imgur.com/abcdefg.jpg",
    title: str = "a test post",
    over_18: bool = False,
    post_hint: str = "image",
    subreddit: str = "wallpaper",
    permalink: str = "/r/wallpaper/comments/abcdefg/a_test_post/",
):
    """Build a minimal stand-in for a ``praw.models.Submission``.

    Only the attributes the code under test actually touches are set:
    ``url``, ``title``, ``over_18``, ``post_hint``, ``permalink`` and
    ``subreddit.display_name``. This is enough for ``RedditFetcher`` and
    ``wallpaper_fetcher`` without a live PRAW client.
    """
    return SimpleNamespace(
        url=url,
        title=title,
        over_18=over_18,
        post_hint=post_hint,
        permalink=permalink,
        subreddit=SimpleNamespace(display_name=subreddit),
    )


def make_png(path, width: int, height: int, color=(0, 128, 255)) -> Path:
    """Create a solid-color PNG of the given size on disk; return its ``Path``.

    Useful for exercising ``ImageHandler`` resolution validation and cache
    size/cleanup logic with real (tiny) image files.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (width, height), color).save(path)
    return path
