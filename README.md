# Wallpaper Randomizer

A cross-platform CLI tool that sets random wallpapers from configurable subreddits.

## Features

- 🎨 Fetch wallpapers from multiple subreddits
- 📏 Filter by minimum resolution
- 🔄 Configurable post sorting (hot, top, new, etc.)
- 💾 Local image caching
- 🖥️ Cross-platform support (macOS, Windows, Linux with GNOME/KDE)

## Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd wallpaper-randomizer
```

2. Create and activate a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up Reddit API credentials:
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Select "script" as the app type
   - Fill in the form (name, redirect uri can be http://localhost:8080)
   - Copy the client_id (under the app name) and client_secret

4. Initialize configuration:
```bash
python -m wallpaper_randomizer init
```

This will create a `config.yaml` file. Edit it to add your Reddit credentials and preferences.

## Usage

**Note:** Make sure to activate the virtual environment before running commands:
```bash
source venv/bin/activate  # On Linux/macOS
# or
venv\Scripts\activate  # On Windows
```

Set a random wallpaper:
```bash
python -m wallpaper_randomizer set
```

Clear cached images:
```bash
python -m wallpaper_randomizer clear-cache
```

Validate configuration:
```bash
python -m wallpaper_randomizer test-config
```

## Configuration

Edit `config.yaml` to customize:

```yaml
subreddits:
  - wallpaper
  - wallpapers
  - EarthPorn

min_resolution:
  width: 1920
  height: 1080

post_filter:
  sort: "top"           # Options: hot, new, top, controversial, rising
  time_filter: "month"  # Options: hour, day, week, month, year, all
  limit: 100            # Number of posts to fetch

reddit:
  client_id: "your_client_id"
  client_secret: "your_client_secret"
  user_agent: "wallpaper-randomizer/1.0"

cache_dir: "~/.wallpaper-randomizer/cache"
max_cache_size_mb: 500
```

## Scheduling

### Linux/macOS (cron)
Add to crontab to change wallpaper every hour:
```bash
0 * * * * cd /path/to/wallpaper-randomizer && python -m wallpaper_randomizer set
```

### Windows (Task Scheduler)
Create a task that runs:
```
python -m wallpaper_randomizer set
```

## License

MIT
