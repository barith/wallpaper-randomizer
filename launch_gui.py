#!/usr/bin/env python3
"""
Launcher script for Wallpaper Randomizer GUI.
This is the entry point for the PyInstaller-built executable.
"""

import sys
from wallpaper_randomizer.gui import launch_gui

if __name__ == '__main__':
    # Look for config.yaml in the same directory as the executable
    config_path = 'config.yaml'
    launch_gui(config_path)
    sys.exit(0)
