# Usage Examples

## Quick Start

1. **Initialize configuration**
```bash
python -m wallpaper_randomizer init
```

2. **Edit config.yaml** to add your Reddit API credentials (see README.md for details)

3. **Test your configuration**
```bash
python -m wallpaper_randomizer test-config
```

4. **Set a random wallpaper**
```bash
python -m wallpaper_randomizer set
```

## Configuration Examples

### High-Resolution Wallpapers
```yaml
min_resolution:
  width: 3840
  height: 2160
```

### Different Post Sources

**Hot posts:**
```yaml
post_filter:
  sort: "hot"
  limit: 50
```

**Top posts from the past week:**
```yaml
post_filter:
  sort: "top"
  time_filter: "week"
  limit: 100
```

**New posts:**
```yaml
post_filter:
  sort: "new"
  limit: 100
```

### Custom Subreddits

**For nature wallpapers:**
```yaml
subreddits:
  - EarthPorn
  - NaturePorn
  - SkyPorn
  - LakePorn
```

**For minimal designs:**
```yaml
subreddits:
  - MinimalistWallpaper
  - Minimalwallpaper
  - MinimalWallpaper
```

**For space/astronomy:**
```yaml
subreddits:
  - spaceporn
  - Astronomy
  - astrophotography
```

## Automation Examples

### Linux/macOS (cron)

Change wallpaper every hour:
```bash
crontab -e
```
Add:
```
0 * * * * cd /path/to/wallpaper-randomizer && source venv/bin/activate && python -m wallpaper_randomizer set
```

Change wallpaper every 30 minutes:
```
*/30 * * * * cd /path/to/wallpaper-randomizer && source venv/bin/activate && python -m wallpaper_randomizer set
```

Change wallpaper at login:
```
@reboot cd /path/to/wallpaper-randomizer && source venv/bin/activate && python -m wallpaper_randomizer set
```

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily (or your preference)
4. Action: Start a program
5. Program/script: `C:\path\to\wallpaper-randomizer\venv\Scripts\python.exe`
6. Arguments: `-m wallpaper_randomizer set`
7. Start in: `C:\path\to\wallpaper-randomizer`

## Managing Cache

**View current cache size:**
```bash
python -m wallpaper_randomizer test-config
```

**Clear all cached images:**
```bash
python -m wallpaper_randomizer clear-cache
```

**Adjust maximum cache size in config.yaml:**
```yaml
max_cache_size_mb: 1000  # Allow 1GB of cached images
```

## Troubleshooting

### "No image posts found"
- Check if subreddit names are correct (no r/ prefix needed)
- Try different subreddits
- Check if Reddit is accessible

### "Failed to download or validate image"
- The image may not meet minimum resolution requirements
- The image URL may be invalid or expired
- Check your internet connection

### Wallpaper not changing
- Check if the desktop environment is supported
- Ensure you have necessary permissions
- Try running with verbose output to see error messages

### Resolution issues
- Adjust `min_resolution` in config.yaml to match your screen
- Some images may be removed if they don't meet requirements
