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
            Desktop environment name ('gnome', 'kde', 'i3', 'sway', 'hyprland', etc.) or None
        """
        # Check for window managers via environment variables
        desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
        session = os.environ.get('DESKTOP_SESSION', '').lower()
        wayland_display = os.environ.get('WAYLAND_DISPLAY', '')

        # Check for sway (Wayland compositor)
        if 'sway' in desktop or 'sway' in session or os.environ.get('SWAYSOCK'):
            return 'sway'

        # Check for hyprland (Wayland compositor)
        if 'hyprland' in desktop or 'hyprland' in session or os.environ.get('HYPRLAND_INSTANCE_SIGNATURE'):
            return 'hyprland'

        # Check for i3 (X11 window manager)
        if 'i3' in desktop or 'i3' in session:
            return 'i3'

        # Check for traditional desktop environments
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
            if 'sway' in processes and wayland_display:
                return 'sway'
            elif 'Hyprland' in processes and wayland_display:
                return 'hyprland'
            elif 'i3' in processes:
                return 'i3'
            elif 'gnome-shell' in processes:
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
        # Set wallpaper and picture options to fill screen (option 2)
        # Options: 0=Automatic, 1=Stretch, 2=Fill, 3=Fit, 4=Center, 5=Tile
        script = f'''
        tell application "System Events"
            tell every desktop
                set picture to "{image_path}"
                set picture rotation to 0
            end tell
        end tell
        
        tell application "System Events"
            tell current desktop
                -- Try to set fill mode (may not work on all macOS versions)
                try
                    set picture options to {{class:picture options, fill screen:true}}
                end try
            end tell
        end tell
        '''

        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully set wallpaper on macOS (fill screen mode)")
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
        if self.desktop_env == 'i3':
            return self._set_i3_wallpaper(image_path)
        elif self.desktop_env == 'sway':
            return self._set_sway_wallpaper(image_path)
        elif self.desktop_env == 'hyprland':
            return self._set_hyprland_wallpaper(image_path)
        elif self.desktop_env == 'gnome':
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

        # Set picture options to 'zoom' to fill screen while maintaining aspect ratio
        subprocess.run(
            ['gsettings', 'set', 'org.gnome.desktop.background',
                'picture-options', 'zoom'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully set wallpaper on GNOME (zoom mode)")
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
                # Set fill mode using qdbus
                self._set_kde_fill_mode()
                print(f"Successfully set wallpaper on KDE Plasma (zoom mode)")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback to qdbus method
        try:
            # Get all desktops and set wallpaper with zoom fill mode
            # FillMode 2 = Scaled and Cropped (zoom to fill screen while maintaining aspect ratio)
            script = f"""
            const allDesktops = desktops();
            for (const desktop of allDesktops) {{
                desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
                desktop.writeConfig("Image", "file://{image_path}");
                desktop.writeConfig("FillMode", "2");
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
                print(f"Successfully set wallpaper on KDE Plasma (zoom mode)")
                return True
            else:
                print(f"Failed to set wallpaper: {result.stderr}")
                return False
        except Exception as e:
            print(f"Error setting KDE wallpaper: {e}")
            return False

    def _set_kde_fill_mode(self) -> None:
        """Set KDE wallpaper fill mode to zoom (scaled and cropped)."""
        try:
            script = """
            const allDesktops = desktops();
            for (const desktop of allDesktops) {
                desktop.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
                desktop.writeConfig("FillMode", "2");
            }
            """
            subprocess.run(
                ['qdbus', 'org.kde.plasmashell', '/PlasmaShell',
                 'org.kde.PlasmaShell.evaluateScript', script],
                capture_output=True,
                text=True,
                timeout=5
            )
        except:
            pass

    def _set_xfce_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on XFCE.

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        # Set the image
        result = subprocess.run(
            ['xfconf-query', '-c', 'xfce4-desktop', '-p',
             '/backdrop/screen0/monitor0/workspace0/last-image', '-s', str(image_path)],
            capture_output=True,
            text=True
        )

        # Set image style to 5 (zoomed) to fill screen while maintaining aspect ratio
        subprocess.run(
            ['xfconf-query', '-c', 'xfce4-desktop', '-p',
             '/backdrop/screen0/monitor0/workspace0/image-style', '-s', '5'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully set wallpaper on XFCE (zoom mode)")
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

        # Set picture options to 'zoom' to fill screen while maintaining aspect ratio
        subprocess.run(
            ['gsettings', 'set', 'org.mate.background',
                'picture-options', 'zoom'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully set wallpaper on MATE (zoom mode)")
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

        # Set picture options to 'zoom' to fill screen while maintaining aspect ratio
        subprocess.run(
            ['gsettings', 'set', 'org.cinnamon.desktop.background',
                'picture-options', 'zoom'],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print(f"Successfully set wallpaper on Cinnamon (zoom mode)")
            return True
        else:
            print(f"Failed to set wallpaper: {result.stderr}")
            return False

    def _command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH.

        Args:
            command: Command name to check

        Returns:
            True if command exists, False otherwise
        """
        try:
            result = subprocess.run(
                ['which', command],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False

    def _set_i3_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on i3 window manager.

        Tries tools in priority order: feh, nitrogen, xwallpaper

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        # Try feh first (most common for i3)
        if self._command_exists('feh'):
            try:
                result = subprocess.run(
                    ['feh', '--bg-fill', str(image_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"Successfully set wallpaper on i3 using feh (fill mode)")
                    return True
            except Exception as e:
                print(f"feh failed: {e}")

        # Try nitrogen
        if self._command_exists('nitrogen'):
            try:
                result = subprocess.run(
                    ['nitrogen', '--set-zoom-fill', str(image_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(
                        f"Successfully set wallpaper on i3 using nitrogen (zoom-fill mode)")
                    return True
            except Exception as e:
                print(f"nitrogen failed: {e}")

        # Try xwallpaper
        if self._command_exists('xwallpaper'):
            try:
                result = subprocess.run(
                    ['xwallpaper', '--zoom', str(image_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(
                        f"Successfully set wallpaper on i3 using xwallpaper (zoom mode)")
                    return True
            except Exception as e:
                print(f"xwallpaper failed: {e}")

        print("Failed to set wallpaper on i3: no compatible tool found")
        print("Please install one of: feh, nitrogen, or xwallpaper")
        return False

    def _set_sway_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on sway compositor.

        Tries tools in priority order: swaybg, swayimg
        Note: swaybg runs as a background process and needs to be killed first

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        # Kill any existing swaybg processes
        try:
            subprocess.run(['pkill', 'swaybg'], capture_output=True)
        except:
            pass

        # Try swaybg (most common for sway)
        if self._command_exists('swaybg'):
            try:
                # Start swaybg in background with fill mode
                subprocess.Popen(
                    ['swaybg', '-i', str(image_path), '-m', 'fill'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"Successfully set wallpaper on sway using swaybg (fill mode)")
                return True
            except Exception as e:
                print(f"swaybg failed: {e}")

        # Try swayimg
        if self._command_exists('swayimg'):
            try:
                result = subprocess.run(
                    ['swayimg', '--bg', str(image_path)],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    print(f"Successfully set wallpaper on sway using swayimg")
                    return True
            except Exception as e:
                print(f"swayimg failed: {e}")

        print("Failed to set wallpaper on sway: no compatible tool found")
        print("Please install swaybg (recommended) or swayimg")
        return False

    def _set_hyprland_wallpaper(self, image_path: Path) -> bool:
        """Set wallpaper on hyprland compositor.

        Tries tools in priority order: hyprpaper, swaybg

        Args:
            image_path: Path to image

        Returns:
            True if successful
        """
        # Try hyprpaper first (native hyprland tool)
        if self._command_exists('hyprctl'):
            try:
                # hyprpaper requires configuration, try using hyprctl to set wallpaper
                # First, preload the image
                subprocess.run(
                    ['hyprctl', 'hyprpaper', 'preload', str(image_path)],
                    capture_output=True,
                    text=True
                )
                # Then set it for all monitors
                result = subprocess.run(
                    ['hyprctl', 'hyprpaper', 'wallpaper', f',{image_path}'],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0 or 'ok' in result.stdout.lower():
                    print(f"Successfully set wallpaper on hyprland using hyprpaper")
                    return True
            except Exception as e:
                print(f"hyprpaper failed: {e}")

        # Try swaybg as fallback (works on most Wayland compositors)
        if self._command_exists('swaybg'):
            try:
                # Kill any existing swaybg processes
                subprocess.run(['pkill', 'swaybg'], capture_output=True)
                # Start swaybg in background with fill mode
                subprocess.Popen(
                    ['swaybg', '-i', str(image_path), '-m', 'fill'],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                print(f"Successfully set wallpaper on hyprland using swaybg (fill mode)")
                return True
            except Exception as e:
                print(f"swaybg failed: {e}")

        print("Failed to set wallpaper on hyprland: no compatible tool found")
        print("Please install hyprpaper (recommended) or swaybg")
        return False
