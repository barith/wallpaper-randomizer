"""Tests for ``wallpaper_randomizer.wallpaper_fetcher.fetch_wallpaper_with_retry``.

The RedditFetcher and ImageHandler collaborators are replaced by small hand-
rolled stubs (no praw client, no HTTP), so every test is deterministic and runs
fully offline. A real ``Config`` is built from a temp YAML file via the shared
``write_config`` fixture, with ``selection_mode`` / ``retry_count`` mutated as
needed.
"""

from pathlib import Path

import pytest

from wallpaper_randomizer.config import Config
from wallpaper_randomizer.wallpaper_fetcher import fetch_wallpaper_with_retry

from .helpers import make_png, valid_config_dict


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

class StubRedditFetcher:
    """Stand-in for ``RedditFetcher``: records every call, returns canned info.

    ``info`` may be a wallpaper-info dict (returned on every attempt), ``None``
    (no wallpapers at all), or a callable ``info(attempt) -> dict | None``.
    Note: ``exclude_indices`` is copied at call time because the code under test
    passes the same mutable set object across attempts.
    """

    def __init__(self, info):
        self._info = info
        self.calls = []

    def get_random_wallpaper_url(self, subreddits, **kwargs):
        call = {"subreddits": subreddits, **kwargs}
        if call.get("exclude_indices") is not None:
            call["exclude_indices"] = set(call["exclude_indices"])
        self.calls.append(call)
        if callable(self._info):
            return self._info(len(self.calls) - 1)
        return self._info


class StubImageHandler:
    """Stand-in for ``ImageHandler.download_image``.

    ``results`` may be a single value (returned every time) or a sequence of
    return values, one per call; after the sequence is exhausted the last value
    is repeated (so ``[None]`` means "always fails").
    """

    def __init__(self, results):
        self._results = list(results) if isinstance(results, (list, tuple)) else [results]
        self.calls = []

    def download_image(self, url, title):
        self.calls.append((url, title))
        i = len(self.calls) - 1
        if i < len(self._results):
            return self._results[i]
        return self._results[-1]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_wallpaper_info(index=0):
    """A canned wallpaper-info dict as returned by the (real) RedditFetcher."""
    return {
        "url": f"https://i.imgur.com/img{index}.jpg",
        "title": f"Test wallpaper {index}",
        "subreddit": "wallpaper",
        "permalink": f"/r/wallpaper/comments/img{index}/test_wallpaper_{index}/",
        "index": index,
    }


def build_config(write_config, selection_mode="random", retry_count=3):
    """Build a real ``Config`` from a temp YAML file with controlled settings."""
    data = valid_config_dict()
    data["post_filter"]["selection_mode"] = selection_mode
    data["post_filter"]["retry_count"] = retry_count
    return Config(write_config(data))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_success_on_first_attempt(write_config, cache_dir):
    cfg = build_config(write_config, retry_count=3)
    info = make_wallpaper_info(0)
    png = make_png(Path(cache_dir) / "out.png", 1920, 1080)

    result = fetch_wallpaper_with_retry(cfg, StubRedditFetcher(info), StubImageHandler(png))

    assert result is not None
    path, returned_info = result
    assert path == png
    assert returned_info == info


def test_retry_then_success(write_config, cache_dir):
    cfg = build_config(write_config, retry_count=5)
    info = make_wallpaper_info(0)
    png = make_png(Path(cache_dir) / "out.png", 1920, 1080)
    # Fail the first two downloads, succeed on the third.
    handler = StubImageHandler([None, None, png])

    result = fetch_wallpaper_with_retry(cfg, StubRedditFetcher(info), handler)

    assert result is not None
    assert result == (png, info)
    assert handler.calls == [(info["url"], info["title"])] * 3
    assert len(handler.calls) == 3


def test_exhausts_retries_returns_none(write_config):
    cfg = build_config(write_config, retry_count=3)
    info = make_wallpaper_info(0)
    handler = StubImageHandler(None)  # every download fails

    result = fetch_wallpaper_with_retry(cfg, StubRedditFetcher(info), handler)

    assert result is None
    assert len(handler.calls) == 3  # exactly retry_count attempts


def test_no_wallpapers_on_first_attempt(write_config):
    cfg = build_config(write_config, retry_count=3)
    handler = StubImageHandler(None)

    result = fetch_wallpaper_with_retry(cfg, StubRedditFetcher(None), handler)

    assert result is None
    assert handler.calls == []  # download never attempted


def test_no_wallpapers_on_later_attempt(write_config, cache_dir):
    cfg = build_config(write_config, retry_count=3)
    png = make_png(Path(cache_dir) / "out.png", 1920, 1080)
    fetcher = StubRedditFetcher(lambda attempt: make_wallpaper_info(attempt) if attempt == 0 else None)
    handler = StubImageHandler(None)
    messages = []

    result = fetch_wallpaper_with_retry(cfg, fetcher, handler, status_callback=messages.append)

    assert result is None
    assert len(fetcher.calls) == 2
    assert len(handler.calls) == 1  # only the first attempt found a wallpaper
    assert any("No more wallpapers to try (attempt 2/3)" in m for m in messages)


def test_first_mode_increments_skip_count(write_config):
    cfg = build_config(write_config, selection_mode="first", retry_count=4)
    fetcher = StubRedditFetcher(lambda attempt: make_wallpaper_info(attempt))
    handler = StubImageHandler(None)  # keep failing so all attempts run

    result = fetch_wallpaper_with_retry(cfg, fetcher, handler)

    assert result is None
    assert [call["skip_count"] for call in fetcher.calls] == [0, 1, 2, 3]
    assert all(call["exclude_indices"] is None for call in fetcher.calls)
    assert all(call["selection_mode"] == "first" for call in fetcher.calls)


def test_random_mode_grows_excluded_indices(write_config):
    cfg = build_config(write_config, selection_mode="random", retry_count=4)
    fetcher = StubRedditFetcher(lambda attempt: make_wallpaper_info(attempt))
    handler = StubImageHandler(None)

    result = fetch_wallpaper_with_retry(cfg, fetcher, handler)

    assert result is None
    # Each attempt receives the set of indices already tried (copied at call time).
    assert [call["exclude_indices"] for call in fetcher.calls] == [
        set(), {0}, {0, 1}, {0, 1, 2}
    ]
    assert all(call["skip_count"] == 0 for call in fetcher.calls)
    assert all(call["selection_mode"] == "random" for call in fetcher.calls)


def test_fetch_call_matches_config_settings(write_config, cache_dir):
    cfg = build_config(write_config, selection_mode="random", retry_count=1)
    info = make_wallpaper_info(0)
    png = make_png(Path(cache_dir) / "out.png", 1920, 1080)
    fetcher = StubRedditFetcher(info)

    result = fetch_wallpaper_with_retry(cfg, fetcher, StubImageHandler(png))

    assert result == (png, info)
    (call,) = fetcher.calls
    assert call["subreddits"] == ["wallpaper", "wallpapers"]
    assert call["sort"] == "top"
    assert call["time_filter"] == "month"
    assert call["limit"] == 100
    assert call["selection_mode"] == "random"
    assert call["skip_count"] == 0
    assert call["exclude_indices"] == set()
    assert call["filter_nsfw"] is True


def test_status_callback_receives_success_messages(write_config, cache_dir):
    cfg = build_config(write_config, retry_count=3)
    info = make_wallpaper_info(0)
    png = make_png(Path(cache_dir) / "out.png", 1920, 1080)
    messages = []

    result = fetch_wallpaper_with_retry(
        cfg, StubRedditFetcher(info), StubImageHandler(png), status_callback=messages.append
    )

    assert result == (png, info)
    assert messages[0] == "Fetching posts from Reddit..."
    assert any("Attempt 1/3:" in m for m in messages)
    assert any("Title: Test wallpaper 0" in m for m in messages)
    assert any("Subreddit: r/wallpaper" in m for m in messages)
    assert any("URL: https://i.imgur.com/img0.jpg" in m for m in messages)


def test_status_callback_receives_failure_messages(write_config):
    cfg = build_config(write_config, retry_count=3)
    fetcher = StubRedditFetcher(lambda attempt: make_wallpaper_info(attempt))
    messages = []

    result = fetch_wallpaper_with_retry(
        cfg, fetcher, StubImageHandler(None), status_callback=messages.append
    )

    assert result is None
    # Intermediate failures get the "trying next" suffix; the final one does not.
    assert any(
        m == "Failed to download or validate image, trying next wallpaper..." for m in messages
    )
    assert any(m == "Failed to download or validate image" for m in messages)
    # Note: the source prefixes this message with a leading newline.
    assert any(
        m == "\nFailed to get a valid wallpaper after 3 attempts" for m in messages
    )