# Wallpaper Fill Modes

The application automatically sets wallpapers in "zoom" or "fill" mode across all supported platforms. This ensures that:

1. **Aspect ratio is maintained** - Images are never stretched or distorted
2. **Screen is completely filled** - No black bars or gaps
3. **Maximum image visibility** - Images are scaled to show as much as possible while filling the screen

## Platform-Specific Implementation

### Linux - GNOME
- Uses `gsettings` to set `picture-options` to `zoom`
- This fills the screen while maintaining aspect ratio
- Works for both light and dark mode wallpapers

### Linux - KDE Plasma
- Sets `FillMode` to `2` (Scaled and Cropped)
- This is the "zoom to fill" mode in KDE
- Maintains aspect ratio while filling the entire screen

### Linux - XFCE
- Sets `image-style` to `5` (zoomed)
- Fills screen while maintaining aspect ratio

### Linux - MATE
- Uses `gsettings` to set `picture-options` to `zoom`
- Same behavior as GNOME

### Linux - Cinnamon
- Uses `gsettings` to set `picture-options` to `zoom`
- Same behavior as GNOME

### macOS
- Attempts to set `fill screen` mode via AppleScript
- Maintains aspect ratio while filling the screen

### Windows
- Windows API sets the wallpaper
- The fill mode is typically controlled by Windows settings
- Users may need to adjust "Choose a fit" in Windows Settings > Personalization > Background

## What This Means

When an image is set as wallpaper:

- **If image is wider than screen**: Top and bottom are cropped slightly
- **If image is taller than screen**: Left and right are cropped slightly
- **If aspect ratios match**: No cropping needed, entire image is shown

This is the most common and visually pleasing way to display wallpapers, ensuring no black bars appear around your wallpaper.

## Alternative Modes

If you prefer different behavior (like seeing the entire image with black bars), you would need to manually adjust your desktop environment's wallpaper settings after running the tool.

Common alternatives include:
- **Fit/Contain**: Shows entire image, may leave black bars
- **Stretch**: Distorts image to fill screen (not recommended)
- **Center**: Shows image at original size, centered
- **Tile**: Repeats image to fill screen
