"""Unit tests for ``wallpaper_randomizer.image_handler.ImageHandler``.

All HTTP access is mocked by patching ``requests.get`` on the module under
test, so the tests run fully offline and deterministically. Real image files
are produced with the shared ``make_png`` helper into the ``cache_dir``
fixture (a fresh temp directory).
"""

import hashlib
import os

import pytest
import requests

import wallpaper_randomizer.image_handler as image_handler
from wallpaper_randomizer.image_handler import ImageHandler

from .helpers import make_png

MIN_W, MIN_H = 1920, 1080

KNOWN_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp", ".gif"]


class _FakeResponse:
    """Minimal stand-in for ``requests.Response`` (content + status check)."""

    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        # No-op: simulates a 2xx response.
        pass


@pytest.fixture
def handler(cache_dir):
    """An ImageHandler with a demanding minimum resolution."""
    return ImageHandler(cache_dir, (MIN_W, MIN_H))


def _png_bytes(tmp_path, width, height) -> bytes:
    """Bytes of a real solid-color PNG, built via the shared helper."""
    return make_png(tmp_path / "source.png", width, height).read_bytes()


# ---------------------------------------------------------------------------
# _get_extension_from_url
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("ext", KNOWN_EXTENSIONS)
def test_get_extension_from_url_recognizes_extension(handler, ext):
    url = f"https://example.com/image{ext}"
    assert handler._get_extension_from_url(url) == ext


@pytest.mark.parametrize("ext", KNOWN_EXTENSIONS)
def test_get_extension_from_url_is_case_insensitive(handler, ext):
    # Uppercase and mixed-case extensions must map to the lowercase form.
    assert handler._get_extension_from_url(f"https://example.com/image{ext.upper()}") == ext
    upper = ext.upper()
    mixed = ext[0] + upper[1:]
    assert handler._get_extension_from_url(f"https://example.com/image{mixed}") == ext


@pytest.mark.parametrize(
    "url",
    [
        "https://i.imgur.com/abcdef",          # no extension at all
        "https://example.com/image",           # bare name
        "https://example.com/image.jpg?w=100", # extension hidden by a query string
    ],
)
def test_get_extension_from_url_defaults_to_jpg(handler, url):
    assert handler._get_extension_from_url(url) == ".jpg"


# ---------------------------------------------------------------------------
# _validate_resolution
# ---------------------------------------------------------------------------

def test_validate_resolution_accepts_sufficient_image(handler, cache_dir):
    path = make_png(cache_dir / "ok.png", MIN_W, MIN_H)
    assert handler._validate_resolution(path) is True


def test_validate_resolution_accepts_image_exceeding_minimum(handler, cache_dir):
    path = make_png(cache_dir / "big.png", MIN_W + 100, MIN_H + 50)
    assert handler._validate_resolution(path) is True


def test_validate_resolution_rejects_width_shortfall(handler, cache_dir):
    # Width below the minimum, height fine.
    path = make_png(cache_dir / "short_w.png", MIN_W - 1, MIN_H)
    assert handler._validate_resolution(path) is False


def test_validate_resolution_rejects_height_shortfall(handler, cache_dir):
    # Height below the minimum, width fine.
    path = make_png(cache_dir / "short_h.png", MIN_W, MIN_H - 1)
    assert handler._validate_resolution(path) is False


def test_validate_resolution_rejects_corrupt_file(handler, cache_dir):
    # A .png-named file with junk bytes: the exception must be caught.
    path = cache_dir / "corrupt.png"
    path.write_bytes(b"this is definitely not a png")
    assert handler._validate_resolution(path) is False


# ---------------------------------------------------------------------------
# download_image
# ---------------------------------------------------------------------------

def test_download_image_happy_path_saves_and_validates(handler, cache_dir, tmp_path, monkeypatch):
    content = _png_bytes(tmp_path, MIN_W, MIN_H)
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeResponse(content)

    monkeypatch.setattr(image_handler.requests, "get", fake_get)

    result = handler.download_image("https://example.com/wall.jpg")

    assert result is not None
    assert result.parent == cache_dir
    assert result.exists()
    assert handler._validate_resolution(result)
    assert calls == ["https://example.com/wall.jpg"]


def test_download_image_below_min_returns_none_and_unlinks(handler, cache_dir, tmp_path, monkeypatch):
    content = _png_bytes(tmp_path, 640, 480)
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeResponse(content)

    monkeypatch.setattr(image_handler.requests, "get", fake_get)

    result = handler.download_image("https://example.com/too-small.png")

    assert result is None
    assert len(calls) == 1
    # The too-small file must have been removed from the cache.
    assert list(cache_dir.iterdir()) == []


def test_download_image_imgur_url_without_extension_gets_jpg(handler, cache_dir, tmp_path, monkeypatch):
    content = _png_bytes(tmp_path, MIN_W, MIN_H)

    def fake_get(url, **kwargs):
        return _FakeResponse(content)

    monkeypatch.setattr(image_handler.requests, "get", fake_get)

    url = "https://imgur.com/abcdef"
    result = handler.download_image(url)

    assert result is not None
    expected_name = hashlib.md5(url.encode() + b".jpg").hexdigest() + ".jpg"
    assert result.name == expected_name
    assert result.suffix == ".jpg"
    assert sorted(p.name for p in cache_dir.iterdir()) == [expected_name]


def test_download_image_returns_cached_file_without_redownloading(handler, tmp_path, monkeypatch):
    content = _png_bytes(tmp_path, MIN_W, MIN_H)
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeResponse(content)

    monkeypatch.setattr(image_handler.requests, "get", fake_get)

    first = handler.download_image("https://example.com/wall.jpg")
    second = handler.download_image("https://example.com/wall.jpg")

    assert first is not None
    assert first == second
    assert calls == ["https://example.com/wall.jpg"], "second call must be served from cache"


def test_download_image_cached_but_too_small_returns_none(handler, cache_dir, tmp_path, monkeypatch):
    # Pre-seed the cache with the hash-named file of a URL whose content is
    # below the minimum resolution; the cached copy must be rejected and no
    # download should happen.
    url = "https://example.com/wall.jpg"
    expected_name = hashlib.md5(url.encode()).hexdigest() + ".jpg"
    make_png(cache_dir / expected_name, 320, 240)

    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return _FakeResponse(_png_bytes(tmp_path, MIN_W, MIN_H))

    monkeypatch.setattr(image_handler.requests, "get", fake_get)

    result = handler.download_image(url)

    assert result is None
    assert calls == []


def test_download_image_http_error_returns_none_gracefully(handler, cache_dir, monkeypatch):
    def fake_get(url, **kwargs):
        raise requests.HTTPError("simulated 500 Server Error")

    monkeypatch.setattr(image_handler.requests, "get", fake_get)

    result = handler.download_image("https://example.com/broken.png")

    assert result is None
    assert list(cache_dir.iterdir()) == []


# ---------------------------------------------------------------------------
# get_cache_size_mb
# ---------------------------------------------------------------------------

def test_get_cache_size_mb_empty_cache_is_zero(handler):
    assert handler.get_cache_size_mb() == 0.0


def test_get_cache_size_mb_sums_file_sizes(handler, cache_dir):
    big = cache_dir / "big.bin"
    big.write_bytes(b"\x00" * (1024 * 1024))
    medium = cache_dir / "medium.bin"
    medium.write_bytes(b"\x00" * (512 * 1024))
    tiny_text = cache_dir / "notes.txt"
    tiny_text.write_bytes(b"hello wallpaper")
    png = make_png(cache_dir / "img.png", 8, 8)

    total_bytes = sum(
        p.stat().st_size for p in (big, medium, tiny_text, png)
    )
    expected_mb = total_bytes / (1024 * 1024)

    assert handler.get_cache_size_mb() == pytest.approx(expected_mb, rel=1e-9)


# ---------------------------------------------------------------------------
# clear_cache
# ---------------------------------------------------------------------------

def test_clear_cache_deletes_all_files_and_returns_count(handler, cache_dir):
    files = [
        make_png(cache_dir / "one.png", 40, 40),
        make_png(cache_dir / "two.png", 41, 41),
        make_png(cache_dir / "three.png", 42, 42),
    ]
    extra = cache_dir / "loose.bin"
    extra.write_bytes(b"abc")
    files.append(extra)

    deleted = handler.clear_cache()

    assert deleted == len(files)
    assert list(cache_dir.iterdir()) == []


# ---------------------------------------------------------------------------
# cleanup_old_cache
# ---------------------------------------------------------------------------

def _create_aged_pngs(cache_dir, count: int):
    """Create *count* PNGs with distinct mtimes; index 0 is the oldest."""
    base_mtime = 1_600_000_000.0
    files = []
    for i in range(count):
        path = make_png(cache_dir / f"aged_{i}.png", 50 + 10 * i, 50 + 10 * i)
        mtime = base_mtime + i * 100
        os.utime(path, (mtime, mtime))
        files.append(path)
    return files


def test_cleanup_old_cache_deletes_oldest_first_until_under_limit(handler, cache_dir):
    files = _create_aged_pngs(cache_dir, 4)
    sizes = [p.stat().st_size for p in files]
    newest_two_bytes = sizes[2] + sizes[3]
    # A limit just above the size of the two newest files forces exactly the
    # two oldest to be deleted.
    max_size_mb = (newest_two_bytes / (1024 * 1024)) * 1.01

    deleted = handler.cleanup_old_cache(max_size_mb)

    assert deleted == 2
    remaining = sorted(p.name for p in cache_dir.iterdir())
    assert remaining == sorted(p.name for p in files[2:])


def test_cleanup_old_cache_under_limit_deletes_nothing(handler, cache_dir):
    files = _create_aged_pngs(cache_dir, 4)

    deleted = handler.cleanup_old_cache(max_size_mb=1000)

    assert deleted == 0
    remaining = sorted(p.name for p in cache_dir.iterdir())
    assert remaining == sorted(p.name for p in files)