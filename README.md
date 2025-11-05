# Wallpaper Randomizer

A cross-platform CLI tool that sets random wallpapers from configurable subreddits.

WARNING: This is vibe coded and not properly tested and reviewed.

## Features

- 🎨 Fetch wallpapers from multiple subreddits
- 📏 Filter by minimum resolution
- 🔄 Configurable post sorting (hot, top, new, etc.)
- 💾 Local image caching
- 🖥️ Cross-platform support (macOS, Windows, Linux)
- 🪟 Window manager support (i3wm, sway, hyprland, GNOME, KDE, XFCE, MATE, Cinnamon)
- 🚀 Automatic dependency management via wrapper script
- 📦 Isolated virtual environment handling

## Quick Start

1. **Clone the repository:**
```bash
git clone <repository-url>
cd wallpaper-randomizer
```

2. **Set up Reddit API credentials:**
   - Go to https://www.reddit.com/prefs/apps
   - Click "Create App" or "Create Another App"
   - Select "script" as the app type
   - Fill in the form (name, redirect uri can be http://localhost:8080)
   - Copy the client_id (under the app name) and client_secret

3. **Initialize configuration:**
```bash
python run.py init
```

This will create a `config.yaml` file. Edit it to add your Reddit credentials and preferences.

4. **Set a random wallpaper:**
```bash
python run.py set
```

That's it! The wrapper script automatically:
- Creates a virtual environment (`.venv/`) on first run
- Installs all required dependencies
- Executes the wallpaper randomizer

## Usage

The `run.py` wrapper script handles all virtual environment management automatically. You don't need to manually activate anything.

### Basic Commands

**Set a random wallpaper:**
```bash
python run.py set
```

**Set wallpaper with specific fill mode:**
```bash
python run.py set --fill-mode zoom
python run.py set --fill-mode fill
python run.py set --fill-mode center
```

**Clear cached images:**
```bash
python run.py clear-cache
```

**Test configuration:**
```bash
python run.py test-config
```

**View help:**
```bash
python run.py --help
```

### Wrapper Management Commands

**Update all dependencies to latest versions:**
```bash
python run.py --update
```

**Recreate virtual environment from scratch:**
```bash
python run.py --recreate-venv
```

### Running from Anywhere

Since the wrapper script uses absolute paths, you can call it from any directory:

```bash
# From anywhere on your system
python /path/to/wallpaper-randomizer/run.py set
```

For even easier access, you can create a shell alias:

**Linux/macOS (add to `~/.bashrc` or `~/.zshrc`):**
```bash
alias wallpaper='python /path/to/wallpaper-randomizer/run.py'
```

**Windows (PowerShell profile):**
```powershell
function wallpaper { python C:\path\to\wallpaper-randomizer\run.py $args }
```

Then use it simply as:
```bash
wallpaper set
wallpaper clear-cache
```

## Understanding Virtual Environments

### What is a Virtual Environment?

A virtual environment is an isolated Python environment that keeps project dependencies separate from your system Python installation. This prevents conflicts between different projects that might need different versions of the same package.

### How This Project Uses Virtual Environments

The `run.py` wrapper script automatically manages a virtual environment for you:

1. **Location**: `.venv/` directory in the repository root
2. **Automatic Creation**: Created on first run if it doesn't exist
3. **Dependency Installation**: All packages from `requirements.txt` are installed automatically
4. **No Manual Activation Needed**: The wrapper handles activation internally

### Virtual Environment Files

```
wallpaper-randomizer/
├── .venv/                    # Virtual environment (auto-created, git-ignored)
│   ├── bin/                  # Linux/macOS executables
│   ├── Scripts/              # Windows executables
│   ├── lib/                  # Installed packages
│   └── ...
├── run.py                    # Wrapper script
├── requirements.txt          # Python dependencies
└── ...
```

### Manual Virtual Environment Access (Optional)

While the wrapper handles everything automatically, you can manually access the virtual environment if needed:

**Activate manually (Linux/macOS):**
```bash
source .venv/bin/activate
python -m wallpaper_randomizer set
deactivate  # when done
```

**Activate manually (Windows):**
```cmd
.venv\Scripts\activate
python -m wallpaper_randomizer set
deactivate
```

However, using `run.py` is recommended as it's simpler and works identically on all platforms.

## Configuration

Edit `config.yaml` to customize behavior:

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

See `config.yaml.template` for a complete example with all available options.

## Window Manager Support

### Supported Environments

The wallpaper randomizer automatically detects and supports the following:

**Desktop Environments:**
- GNOME (uses `gsettings`)
- KDE Plasma (uses `plasma-apply-wallpaperimage` or `qdbus`)
- XFCE (uses `xfconf-query`)
- MATE (uses `gsettings`)
- Cinnamon (uses `gsettings`)

**Window Managers:**
- **i3wm** (X11) - Requires one of: `feh`, `nitrogen`, or `xwallpaper`
- **sway** (Wayland) - Requires: `swaybg` (recommended) or `swayimg`
- **hyprland** (Wayland) - Requires: `hyprpaper` (recommended) or `swaybg`

### Installing Wallpaper Tools

**For i3wm users:**
```bash
# Arch Linux
sudo pacman -S feh

# Ubuntu/Debian
sudo apt install feh

# Fedora
sudo dnf install feh
```

**For sway users:**
```bash
# Arch Linux
sudo pacman -S swaybg

# Ubuntu/Debian
sudo apt install swaybg

# Fedora
sudo dnf install swaybg
```

**For hyprland users:**
```bash
# Arch Linux
sudo pacman -S hyprpaper

# Or use swaybg as fallback
sudo pacman -S swaybg
```

### Optional Configuration Override

By default, the tool tries available wallpaper tools automatically. If you want to force a specific tool, add this to your `config.yaml`:

```yaml
# Optional: Override wallpaper tool
wallpaper_tool:
  tool: "feh"  # For i3: feh, nitrogen, xwallpaper
              # For sway: swaybg, swayimg
              # For hyprland: hyprpaper, swaybg
```

This is useful if you have multiple tools installed and prefer one over the others.

## Scheduling Automatic Wallpaper Changes

### Linux/macOS (cron)

Add to crontab to change wallpaper every hour:

```bash
# Edit crontab
crontab -e

# Add this line (adjust path to your repository)
0 * * * * python /path/to/wallpaper-randomizer/run.py set
```

**Examples:**
- Every hour: `0 * * * *`
- Every 30 minutes: `*/30 * * * *`
- Every day at 9 AM: `0 9 * * *`
- Every Monday at 8 AM: `0 8 * * 1`

### Windows (Task Scheduler)

1. Open Task Scheduler
2. Create a new task
3. Set trigger (e.g., daily at login, or every hour)
4. Set action:
   - Program: `python`
   - Arguments: `C:\path\to\wallpaper-randomizer\run.py set`
   - Start in: `C:\path\to\wallpaper-randomizer`

### macOS (launchd)

Create `~/Library/LaunchAgents/com.wallpaper-randomizer.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.wallpaper-randomizer</string>
    <key>ProgramArguments</key>
    <array>
        <string>python3</string>
        <string>/path/to/wallpaper-randomizer/run.py</string>
        <string>set</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Load it:
```bash
launchctl load ~/Library/LaunchAgents/com.wallpaper-randomizer.plist
```

## Troubleshooting

### Dependencies Won't Install

Try recreating the virtual environment:
```bash
python run.py --recreate-venv
```

### Script Not Finding Python

Ensure Python 3.7+ is installed and in your PATH:
```bash
python --version  # or python3 --version
```

### Permission Denied (Linux/macOS)

Make the wrapper executable:
```bash
chmod +x run.py
./run.py set  # Then you can use ./run.py instead of python run.py
```

### Virtual Environment is Corrupted

Delete `.venv/` and let the wrapper recreate it:
```bash
rm -rf .venv
python run.py set  # Will recreate venv automatically
```

## Development

### Project Structure

```
wallpaper-randomizer/
├── run.py                          # Wrapper script (entry point)
├── requirements.txt                # Python dependencies
├── config.yaml.template            # Configuration template
├── wallpaper_randomizer/           # Main package
│   ├── __init__.py
│   ├── __main__.py                 # CLI entry point
│   ├── config.py                   # Configuration handling
│   ├── reddit_fetcher.py           # Reddit API integration
│   ├── image_handler.py            # Image processing
│   └── wallpaper_setter.py         # Platform-specific wallpaper setting
├── .venv/                          # Virtual environment (git-ignored)
└── README.md
```

### Running Tests

```bash
python run.py test-config
```

### Adding New Dependencies

1. Add package to `requirements.txt`
2. Run `python run.py --update` to install new dependencies

## License

MIT

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
