"""Live integration test against the real Reddit API.

Skipped automatically unless ``REDDIT_CLIENT_ID`` and ``REDDIT_CLIENT_SECRET``
are present in the environment (e.g. injected from GitHub secrets by the
``live-integration`` CI job). This exercises the real end-to-end path that the
unit tests mock out: fetching posts through PRAW and downloading a real image.
It deliberately does NOT apply a wallpaper (CI is headless).
"""

import os

import pytest
import yaml
from PIL import Image

from .helpers import valid_config_dict
from wallpaper_randomizer.config import Config
from wallpaper_randomizer.image_handler import ImageHandler
from wallpaper_randomizer.reddit_fetcher import RedditFetcher

LIVE = pytest.mark.skipif(
    not (os.environ.get("REDDIT_CLIENT_ID") and os.environ.get("REDDIT_CLIENT_SECRET")),
    reason="REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET not set",
)


@LIVE
def test_live_fetch_and_download(tmp_path):
    """Fetch real posts from r/wallpaper and download one image."""
    creds = {
        "client_id": os.environ["REDDIT_CLIENT_ID"],
        "client_secret": os.environ["REDDIT_CLIENT_SECRET"],
        "user_agent": "wallpaper-randomizer-ci/1.0",
    }

    config_data = valid_config_dict()
    config_data["subreddits"] = ["wallpaper"]
    config_data["post_filter"]["limit"] = 5  # keep the API call small
    config_path = tmp_path / "config.yaml"
    config_path.write_text(yaml.safe_dump(config_data))
    config = Config(str(config_path))

    fetcher = RedditFetcher(creds)
    info = fetcher.get_random_wallpaper_url(
        config.get_subreddits(),
        sort="top",
        time_filter="month",
        limit=5,
    )
    assert info is not None, "no image posts returned from live fetch"

    # (0, 0) min resolution: we only care that the download itself works,
    # not that the live image meets a specific size.
    handler = ImageHandler(tmp_path / "cache", (0, 0))
    path = handler.download_image(info["url"], info["title"])
    assert path is not None, f"could not download {info['url']}"
    assert path.exists() and path.stat().st_size > 0

    with Image.open(path) as img:
        img.verify()  # raises if the downloaded bytes are not a valid image
