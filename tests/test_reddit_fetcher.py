"""Unit tests for ``wallpaper_randomizer.reddit_fetcher.RedditFetcher``.

All Reddit network access is mocked: ``praw.Reddit.subreddit`` is replaced
with a stub returning fake submissions built by ``make_submission``, and the
instance's ``fetch_image_posts`` is patched where the selection/caching logic
of ``get_random_wallpaper_url`` is under test. Constructing ``praw.Reddit``
with fake credentials makes no network calls, so everything runs fully
offline and deterministically.
"""

import pytest

import wallpaper_randomizer.reddit_fetcher as reddit_fetcher_module
from wallpaper_randomizer.reddit_fetcher import RedditFetcher

from .helpers import make_submission

FAKE_CREDS = {
    "client_id": "x",
    "client_secret": "y",
    "user_agent": "z",
}


class FakeSubreddit:
    """Stand-in for a PRAW subreddit object.

    Every listing method returns the same preset post list and records the
    keyword arguments it received, so tests can assert pass-through of
    ``limit`` / ``time_filter``.
    """

    def __init__(self, posts):
        self.posts = list(posts)
        self.calls = {}

    def _record(self, method, **kwargs):
        self.calls[method] = kwargs

    def hot(self, limit=100):
        self._record("hot", limit=limit)
        return list(self.posts)

    def new(self, limit=100):
        self._record("new", limit=limit)
        return list(self.posts)

    def top(self, time_filter="month", limit=100):
        self._record("top", time_filter=time_filter, limit=limit)
        return list(self.posts)

    def controversial(self, time_filter="month", limit=100):
        self._record("controversial", time_filter=time_filter, limit=limit)
        return list(self.posts)

    def rising(self, limit=100):
        self._record("rising", limit=limit)
        return list(self.posts)


@pytest.fixture
def fetcher():
    """A RedditFetcher built with fake credentials (no network access)."""
    return RedditFetcher(dict(FAKE_CREDS))


def _stub_subreddit(monkeypatch, fetcher, posts):
    """Replace the reddit client's ``subreddit`` helper with a stub.

    In praw 8 ``subreddit`` is an *instance* attribute of the ``praw.Reddit``
    client (a ``SubredditHelper``), so it is patched on the client instance;
    monkeypatch restores the original helper after the test.
    """
    sub = FakeSubreddit(posts)
    monkeypatch.setattr(fetcher.reddit, "subreddit", lambda name: sub)
    return sub


def _pin_random_choice(monkeypatch):
    """Make the module's ``random.choice`` always pick the first element.

    ``reddit_fetcher`` does ``import random``, so patching ``choice`` on that
    shared module makes random-mode selection exact and deterministic.
    """
    monkeypatch.setattr(
        reddit_fetcher_module.random, "choice", lambda seq: seq[0])


def _mixed_posts():
    """A post list exercising every branch of ``_is_image_post`` + NSFW."""
    return [
        make_submission(url="https://i.imgur.com/aaaa.jpg",
                        title="direct jpg", post_hint="image"),
        make_submission(url="https://imgur.com/abcdef",
                        title="imgur link", post_hint="link"),
        make_submission(url="https://example.com/page",
                        title="plain link", post_hint="link"),
        make_submission(url="https://example.com/p2",
                        title="nsfw image", over_18=True, post_hint="image"),
        make_submission(url="https://imgur.com/nsfw/",
                        title="nsfw imgur", over_18=True, post_hint="link"),
    ]


def _three_posts(subreddit="wallpaper"):
    """A fixed, ordered list of image posts."""
    return [
        make_submission(url=f"https://i.imgur.com/post{i}.png",
                        title=f"post {i}", subreddit=subreddit,
                        permalink=f"/r/{subreddit}/comments/i{i}/")
        for i in range(3)
    ]


def _patch_fetch(monkeypatch, fetcher, posts_by_subreddit):
    """Install a counting stub for the instance's ``fetch_image_posts``.

    The stub matches the real method's signature minus ``self`` (it is set as
    an instance attribute, so it is not bound and receives ``subreddit_name``
    as its first argument). Returns a list recording one entry per call.
    """
    calls = []

    def fake_fetch(subreddit_name, sort="top", time_filter="month",
                   limit=100, filter_nsfw=True):
        calls.append(subreddit_name)
        return posts_by_subreddit.get(subreddit_name, [])

    monkeypatch.setattr(fetcher, "fetch_image_posts", fake_fetch)
    return calls


# ---------------------------------------------------------------------------
# Construction
# ---------------------------------------------------------------------------

def test_constructor_creates_praw_client_with_empty_cache(fetcher):
    assert isinstance(fetcher.reddit, reddit_fetcher_module.praw.Reddit)
    assert fetcher._cached_posts is None
    assert fetcher._cache_key is None


# ---------------------------------------------------------------------------
# _is_image_post
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ext", [".jpg", ".jpeg", ".png", ".webp", ".gif"])
def test_is_image_post_direct_image_extensions(fetcher, ext):
    post = make_submission(url=f"https://example.com/wallpaper{ext}",
                           post_hint="link")
    assert fetcher._is_image_post(post) is True


def test_is_image_post_imgur_link_without_trailing_slash(fetcher):
    # No known extension and not a Reddit-hosted image: only the imgur rule
    # can match.
    post = make_submission(url="https://i.imgur.com/abcdefg", post_hint="link")
    assert fetcher._is_image_post(post) is True


def test_is_image_post_post_hint_image(fetcher):
    post = make_submission(url="https://example.com/page", post_hint="image")
    assert fetcher._is_image_post(post) is True


def test_is_image_post_rejects_plain_link(fetcher):
    post = make_submission(url="https://example.com/page", post_hint="link")
    assert fetcher._is_image_post(post) is False


def test_is_image_post_rejects_imgur_with_trailing_slash(fetcher):
    post = make_submission(url="https://imgur.com/a/somegallery/",
                           post_hint="link")
    assert fetcher._is_image_post(post) is False


# ---------------------------------------------------------------------------
# fetch_image_posts
# ---------------------------------------------------------------------------

def test_fetch_image_posts_filters_nsfw_and_non_images(monkeypatch, fetcher):
    _stub_subreddit(monkeypatch, fetcher, _mixed_posts())

    result = fetcher.fetch_image_posts("wallpaper", sort="top",
                                       filter_nsfw=True)

    assert [p.title for p in result] == ["direct jpg", "imgur link"]


def test_fetch_image_posts_keeps_nsfw_when_disabled(monkeypatch, fetcher):
    _stub_subreddit(monkeypatch, fetcher, _mixed_posts())

    result = fetcher.fetch_image_posts("wallpaper", sort="top",
                                       filter_nsfw=False)

    assert [p.title for p in result] == ["direct jpg", "imgur link",
                                         "nsfw image"]


@pytest.mark.parametrize(
    ("sort", "time_filter"),
    [
        ("hot", "month"),
        ("new", "month"),
        ("top", "month"),
        ("controversial", "week"),
        ("rising", "month"),
    ],
)
def test_fetch_image_posts_calls_matching_listing(
        monkeypatch, fetcher, sort, time_filter):
    sub = _stub_subreddit(monkeypatch, fetcher, _mixed_posts())

    fetcher.fetch_image_posts("wallpaper", sort=sort, time_filter=time_filter,
                              limit=42)

    assert list(sub.calls) == [sort]
    if sort in ("top", "controversial"):
        assert sub.calls[sort] == {"time_filter": time_filter, "limit": 42}
    else:
        assert sub.calls[sort] == {"limit": 42}


def test_fetch_image_posts_invalid_sort_raises(monkeypatch, fetcher):
    _stub_subreddit(monkeypatch, fetcher, [])

    with pytest.raises(ValueError, match="Invalid sort method"):
        fetcher.fetch_image_posts("wallpaper", sort="wibble")


# ---------------------------------------------------------------------------
# get_random_wallpaper_url
# ---------------------------------------------------------------------------

def test_get_random_wallpaper_url_random_mode_returns_post_dict(
        monkeypatch, fetcher):
    posts = _three_posts()
    _patch_fetch(monkeypatch, fetcher, {"wallpaper": posts})
    _pin_random_choice(monkeypatch)

    result = fetcher.get_random_wallpaper_url(["wallpaper"])

    assert result == {
        "url": posts[0].url,
        "title": posts[0].title,
        "subreddit": "wallpaper",
        "permalink": f"https://reddit.com{posts[0].permalink}",
        "index": 0,
    }


def test_get_random_wallpaper_url_respects_exclude_indices(monkeypatch, fetcher):
    posts = _three_posts()
    _patch_fetch(monkeypatch, fetcher, {"wallpaper": posts})
    _pin_random_choice(monkeypatch)

    result = fetcher.get_random_wallpaper_url(["wallpaper"],
                                              exclude_indices={0, 2})

    assert result is not None
    assert result["index"] == 1
    assert result["url"] == posts[1].url


def test_get_random_wallpaper_url_excludes_everything_returns_none(
        monkeypatch, fetcher):
    posts = _three_posts()
    _patch_fetch(monkeypatch, fetcher, {"wallpaper": posts})
    _pin_random_choice(monkeypatch)

    result = fetcher.get_random_wallpaper_url(
        ["wallpaper"], exclude_indices={0, 1, 2})

    assert result is None


def test_get_random_wallpaper_url_first_mode_skip_count(monkeypatch, fetcher):
    posts = _three_posts()
    _patch_fetch(monkeypatch, fetcher, {"wallpaper": posts})

    result = fetcher.get_random_wallpaper_url(["wallpaper"],
                                              selection_mode="first",
                                              skip_count=2)

    assert result is not None
    assert result["index"] == 2
    assert result["url"] == posts[2].url
    assert result["title"] == posts[2].title


@pytest.mark.parametrize("skip_count", [3, 10])
def test_get_random_wallpaper_url_first_mode_skip_out_of_range(
        monkeypatch, fetcher, skip_count):
    posts = _three_posts()
    _patch_fetch(monkeypatch, fetcher, {"wallpaper": posts})

    result = fetcher.get_random_wallpaper_url(["wallpaper"],
                                              selection_mode="first",
                                              skip_count=skip_count)

    assert result is None


def test_get_random_wallpaper_url_no_posts_returns_none(monkeypatch, fetcher):
    _patch_fetch(monkeypatch, fetcher, {"wallpaper": []})

    assert fetcher.get_random_wallpaper_url(["wallpaper"]) is None


def test_get_random_wallpaper_url_skips_failing_subreddit(monkeypatch, fetcher):
    def fake_fetch(subreddit_name, sort="top", time_filter="month",
                   limit=100, filter_nsfw=True):
        if subreddit_name == "broken":
            raise RuntimeError("network down")
        return _three_posts(subreddit_name)

    monkeypatch.setattr(fetcher, "fetch_image_posts", fake_fetch)
    _pin_random_choice(monkeypatch)

    result = fetcher.get_random_wallpaper_url(["broken", "wallpaper"])

    assert result is not None
    assert result["subreddit"] == "wallpaper"


# ---------------------------------------------------------------------------
# Post caching
# ---------------------------------------------------------------------------

def test_post_cache_same_params_fetches_once(monkeypatch, fetcher):
    posts = _three_posts()
    calls = _patch_fetch(monkeypatch, fetcher, {"wallpaper": posts})
    _pin_random_choice(monkeypatch)

    first = fetcher.get_random_wallpaper_url(["wallpaper"])
    second = fetcher.get_random_wallpaper_url(["wallpaper"])

    assert calls == ["wallpaper"]  # underlying fetch happened only once
    assert first == second
    assert fetcher._cached_posts == posts


def test_post_cache_different_subreddits_refetches(monkeypatch, fetcher):
    calls = _patch_fetch(
        monkeypatch, fetcher,
        {"wallpaper": _three_posts(), "wallpapers": _three_posts("wallpapers")})
    _pin_random_choice(monkeypatch)

    first = fetcher.get_random_wallpaper_url(["wallpaper"])
    second = fetcher.get_random_wallpaper_url(["wallpapers"])

    assert calls == ["wallpaper", "wallpapers"]
    assert first["subreddit"] == "wallpaper"
    assert second["subreddit"] == "wallpapers"


def test_post_cache_different_limit_refetches(monkeypatch, fetcher):
    calls = _patch_fetch(monkeypatch, fetcher, {"wallpaper": _three_posts()})
    _pin_random_choice(monkeypatch)

    fetcher.get_random_wallpaper_url(["wallpaper"], limit=10)
    fetcher.get_random_wallpaper_url(["wallpaper"], limit=20)

    assert len(calls) == 2


def test_clear_post_cache_forces_refetch(monkeypatch, fetcher):
    posts = _three_posts()
    calls = _patch_fetch(monkeypatch, fetcher, {"wallpaper": posts})
    _pin_random_choice(monkeypatch)

    fetcher.get_random_wallpaper_url(["wallpaper"])
    fetcher.get_random_wallpaper_url(["wallpaper"])
    assert len(calls) == 1

    fetcher.clear_post_cache()
    assert fetcher._cached_posts is None
    assert fetcher._cache_key is None

    fetcher.get_random_wallpaper_url(["wallpaper"])
    assert len(calls) == 2