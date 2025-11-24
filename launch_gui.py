#!/usr/bin/env python3
"""
Launcher script for Wallpaper Randomizer GUI.
This is the entry point for the PyInstaller-built executable.
"""

import sys
from wallpaper_randomizer.config import Config
from wallpaper_randomizer.gui import launch_gui

if __name__ == '__main__':
    # Use platform-specific config path
    config_path = str(Config.get_default_config_path())
    launch_gui(config_path)
    sys.exit(0)
