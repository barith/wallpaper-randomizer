"""Cross-platform wallpaper setting functionality."""

import os
import sys
import subprocess
import platform
from pathlib import Path
from typing import Optional


class WallpaperSetter:
    """Set wallpaper across different operating systems and desktop environments."""

    def __init__(self):
        """Initialize wallpaper setter and detect platform."""
        self.system = platform.system()
        self.desktop_env = None
        if self.system == 'Linux':
            self.desktop_env = self._detect_desktop_environment()

    def _detect_desktop_environment(self) -> Optional[str]:
        """Detect the desktop environment on Linux.

        Returns:
            Desktop environment name ('gnome', 'kde', etc.) or None
        """
        # Check common environment variables
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()

        if 'gnome' in desktop or desktop == 'ubuntu':
            return 'gnome'
        elif 'kde' in desktop or 'plasma' in desktop:
            return 'kde'
        elif 'xfce' in desktop:
            return 'xfce'
        elif 'mate' in desktop:
            return 'mate'
        elif 'cinnamon' in desktop:
            return 'cinnamon'

        # Fallback: check running processes
        try:
            processes = subprocess.check_output(['ps', '-A'], text=True)
            if 'gnome-shell' in processes:
                return 'gnome'
            elif 'plasmashell' in processes or 'kwin' in processes:
                return 'kde'
            elif 'xfce' in processes:
                return 'xfce'
        except:
            pass

        return None

    def set_wallpaper(self, image_path: Path) -> bool:
        """Set the desktop wallpaper.

        Args:
            image_path: Path to the image file

        Returns:
            True if successful, False otherwise
        """
        if not image_path.exists():
            print(f"Error: Image file not found: {image_path}")
            return False

        # Convert to absolute path
        image_path = image_path.absolute()

        try:
            if self.system == 'Darwin':  # macOS
                return self._set_macos_wallpaper(image_path)
            elif self.system == 'Windows':
                return self._set_windows_wallpaper(image_path)
            elif self.system == 'Linux':
                return self._set_linux_wallpaper(image_path)
            else:
                print(f"Unsupported operating system: {self.system}")
                return False
        except Exception as e:
            print(f"Error setting wallpaper: {e}")
            return False

    def _set_macos_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on macOS using osascript.

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        script = f'''
        tell application "System Events"
            tell every desktop
                set picture to "{image_path}"
            end tell
        end tell
        '''

        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully set wallpaper on macOS")
            return True
        else:
            print(f"Failed to set wallpaper: {result.stderr}")
            return False

    def _set_windows_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on Windows using ctypes.

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        import ctypes

        # Constants for Windows API
        SPI_SETDESKWALLPAPER = 20
        SPIF_UPDATEINIFILE = 0x01
        SPIF_SENDCHANGE = 0x02

        result = ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER,
            0,
            str(image_path),
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )

        if result:
            print(f"Successfully set wallpaper on Windows")
            return True
        else:
            print(f"Failed to set wallpaper on Windows")
            return False

    def _set_linux_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on Linux based on desktop environment.

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        if self.desktop_env == 'gnome':
            return self._set_gnome_wallpaper(image_path)
        elif self.desktop_env == 'kde':
            return self._set_kde_wallpaper(image_path)
        elif self.desktop_env == 'xfce':
            return self._set_xfce_wallpaper(image_path)
        elif self.desktop_env == 'mate':
            return self._set_mate_wallpaper(image_path)
        elif self.desktop_env == 'cinnamon':
            return self._set_cinnamon_wallpaper(image_path)
        else:
            print(
                f"Unsupported or unknown desktop environment: {self.desktop_env}")
            print("Trying GNOME method as fallback...")
            return self._set_gnome_wallpaper(image_path)

    def _set_gnome_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on GNOME using gsettings.

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        uri = f"file://{image_path}"

        result = subprocess.run(
            ['gsettings', 'set', 'org.gnome.desktop.background', 'picture-uri', uri],
            capture_output=True,
            text=True
        )

        # Also set for dark mode
        subprocess.run(
            ['gsettings', 'set', 'org.gnome.desktop.background',
                'picture-uri-dark', uri],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully set wallpaper on GNOME")
            return True
        else:
            print(f"Failed to set wallpaper: {result.stderr}")
            return False

    def _set_kde_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on KDE Plasma.

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        # Try plasma-apply-wallpaperimage first (newer KDE)
        try:
            result = subprocess.run(
                ['plasma-apply-wallpaperimage', str(image_path)],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                print(f"Successfully set wallpaper on KDE Plasma")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback to qdbus method
        try:
            # Get all desktops
            script = f"""
            const allDesktops = desktops();
            for (const desktop of allDesktops) {{
                desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
                desktop.writeConfig("Image", "file://{image_path}");
            }}
            """

            result = subprocess.run(
                ['qdbus', 'org.kde.plasmashell', '/PlasmaShell',
                 'org.kde.PlasmaShell.evaluateScript', script],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"Successfully set wallpaper on KDE Plasma (qdbus)")
                return True
            else:
                print(f"Failed to set wallpaper: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error setting KDE wallpaper: {e}")
            return False

    def _set_xfce_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on XFCE.

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        result = subprocess.run(
            ['xfconf-query', '-c', 'xfce4-desktop', '-p',
             '/backdrop/screen0/monitor0/workspace0/last-image', '-s', str(image_path)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully set wallpaper on XFCE")
            return True
        else:
            print(f"Failed to set wallpaper: {result.stderr}")
            return False

    def _set_mate_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on MATE.

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        result = subprocess.run(
            ['gsettings', 'set', 'org.mate.background',
                'picture-filename', str(image_path)],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully set wallpaper on MATE")
            return True
        else:
            print(f"Failed to set wallpaper: {result.stderr}")
            return False

    def _set_cinnamon_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on Cinnamon.

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        result = subprocess.run(
            ['gsettings', 'set', 'org.cinnamon.desktop.background', 'picture-uri',
             f"file://{image_path}"],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully set wallpaper on Cinnamon")
            return True
        else:
            print(f"Failed to set wallpaper: {result.stderr}")
            return False
