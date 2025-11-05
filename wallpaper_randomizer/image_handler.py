"""Image downloading and validation."""

import os
import requests
from pathlib import Path
from PIL import Image
from typing import Optional, Tuple
import hashlib


class ImageHandler:
    """Handle image downloading and validation."""

    def __init__(self, cache_dir: Path, min_resolution: Tuple[int, int]):
        """Initialize image handler.

        Args:
            cache_dir: Directory to cache downloaded images
            min_resolution: Minimum (width, height) required
        """
        self.cache_dir = cache_dir
        self.min_width, self.min_height = min_resolution
        self._ensure_cache_dir()

    def _ensure_cache_dir(self) -> None:
        """Create cache directory if it doesn't exist."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def download_image(self, url: str, title: str = None) -> Optional[Path]:
        """Download an image and validate its resolution.

        Args:
            url: URL of the image to download
            title: Optional title for naming the file

        Returns:
            Path to downloaded image if successful and meets requirements, None otherwise
        """
        try:
            # Handle imgur URLs
            if 'imgur.com' in url and not url.endswith(('.jpg', '.jpeg', '.png', '.webp', '.gif')):
                # Add .jpg extension for imgur links without extension
                if not url.endswith('/'):
                    url = url + '.jpg'

            # Generate filename from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()
            extension = self._get_extension_from_url(url)
            filename = f"{url_hash}{extension}"
            filepath = self.cache_dir / filename

            # Check if already cached
            if filepath.exists():
                print(f"Image already cached: {filepath.name}")
                if self._validate_resolution(filepath):
                    return filepath
                else:
                    print(f"Cached image doesn't meet resolution requirements")
                    return None

            # Download image
            print(f"Downloading image from {url}...")
            response = requests.get(url, timeout=30, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            response.raise_for_status()

            # Save to cache
            with open(filepath, 'wb') as f:
                f.write(response.content)

            print(f"Downloaded to: {filepath}")

            # Validate resolution
            if self._validate_resolution(filepath):
                return filepath
            else:
                print(f"Image resolution too small, removing...")
                filepath.unlink()
                return None

        except Exception as e:
            print(f"Error downloading image: {e}")
            return None

    def _get_extension_from_url(self, url: str) -> str:
        """Extract file extension from URL.

        Args:
            url: Image URL

        Returns:
            File extension including dot (e.g., '.jpg')
        """
        url_lower = url.lower()
        for ext in ['.jpg', '.jpeg', '.png', '.webp', '.gif']:
            if url_lower.endswith(ext):
                return ext
        # Default to .jpg if no extension found
        return '.jpg'

    def _validate_resolution(self, filepath: Path) -> bool:
        """Check if image meets minimum resolution requirements.

        Args:
            filepath: Path to image file

        Returns:
            True if image meets minimum resolution
        """
        try:
            with Image.open(filepath) as img:
                width, height = img.size
                print(
                    f"Image resolution: {width}x{height} (minimum: {self.min_width}x{self.min_height})")

                if width >= self.min_width and height >= self.min_height:
                    return True
                else:
                    return False

        except Exception as e:
            print(f"Error validating image: {e}")
            return False

    def get_cache_size_mb(self) -> float:
        """Get total size of cached images in MB.

        Returns:
            Size in megabytes
        """
        total_size = 0
        for file in self.cache_dir.glob('*'):
            if file.is_file():
                total_size += file.stat().st_size
        return total_size / (1024 * 1024)

    def clear_cache(self) -> int:
        """Remove all cached images.

        Returns:
            Number of files deleted
        """
        count = 0
        for file in self.cache_dir.glob('*'):
            if file.is_file():
                file.unlink()
                count += 1
        return count

    def cleanup_old_cache(self, max_size_mb: int) -> int:
        """Remove oldest cached images if cache exceeds size limit.

        Args:
            max_size_mb: Maximum cache size in MB

        Returns:
            Number of files deleted
        """
        current_size = self.get_cache_size_mb()
        if current_size <= max_size_mb:
            return 0

        # Get all files sorted by modification time (oldest first)
        files = sorted(
            [f for f in self.cache_dir.glob('*') if f.is_file()],
            key=lambda x: x.stat().st_mtime
        )

        deleted = 0
        for file in files:
            if current_size <= max_size_mb:
                break

            file_size_mb = file.stat().st_size / (1024 * 1024)
            file.unlink()
            current_size -= file_size_mb
            deleted += 1

        return deleted
