# Wallpaper Randomizer

A cross-platform CLI tool that sets random wallpapers from configurable subreddits.

**Testing status:** The core logic (configuration, Reddit fetching, image handling, retry, and wallpaper detection/routing) is covered by an automated pytest suite that runs on every push and pull request (see [Running Tests](#running-tests)). The GUI and the actual wallpaper application are not covered by automated tests.

## Features

- 🎨 Fetch wallpapers from multiple subreddits
- 🖼️ **GUI application** with live preview and configuration
- 📏 Filter by minimum resolution
- 🔄 Configurable post sorting (hot, top, new, etc.)
- 💾 Local image caching
- 🖥️ Cross-platform support (macOS, Windows, Linux)
- 🪟 Window manager support (i3wm, sway, hyprland, GNOME, KDE, XFCE, MATE, Cinnamon)
- 🚀 Automatic dependency management via wrapper script
- 📦 Isolated virtual environment handling

## Download (Pre-built Applications)

**For users who want ready-to-use applications without installing Python:**

### Windows

1. Go to the [Releases](../../releases) page
2. Download the latest `WallpaperRandomizer-Windows-*.zip` file
3. Extract the ZIP to a folder of your choice
4. Run `WallpaperRandomizer.exe`
5. The app will auto-create a config file at:
   - `%APPDATA%\WallpaperRandomizer\config.yaml`
   - To access: Press Win+R, type `%APPDATA%\WallpaperRandomizer`, press Enter
6. Edit the config file to add your Reddit API credentials
7. Restart the app

The executable includes everything you need - no Python installation required!

**See `INSTRUCTIONS-Windows.txt` (included in the ZIP) for detailed setup guide.**

### macOS

1. Go to the [Releases](../../releases) page
2. Download the latest `WallpaperRandomizer-macOS-*.dmg` file
3. Open the DMG and drag `WallpaperRandomizer.app` to Applications (or any folder)
4. **First run**: Right-click the app → "Open" → Click "Open" (bypasses Gatekeeper)
5. The app will auto-create a config file at:
   - `~/Library/Application Support/WallpaperRandomizer/config.yaml`
   - To access: Finder → Cmd+Shift+G → Enter path above
6. Edit the config file to add your Reddit API credentials
7. Restart the app

The app bundle includes everything you need - no Python installation required!

**Note**: The app is unsigned, so macOS will show a security warning on first launch. This is normal for free, open-source apps.

**See `INSTRUCTIONS-macOS.txt` (included in the DMG) for detailed setup guide.**

---

For developers who want to build from source or use the CLI, continue to the Quick Start section below.

See [BUILD.md](BUILD.md) for details on how these applications are built and distributed.

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

### GUI Application

**Launch the graphical interface:**
```bash
python run.py gui
```

The GUI provides an intuitive interface with:
- **Live Configuration Editor**: Edit all settings with instant auto-save
  - Add/remove subreddits dynamically
  - Adjust minimum resolution
  - Configure post filters (sort, time, limit)
  - Update Reddit API credentials
  - Manage cache settings
- **Wallpaper Preview**: See wallpapers before setting them
  - Image preview with aspect-ratio scaling
  - Display title, subreddit, and resolution
- **One-Click Operations**:
  - "Get Random Wallpaper" - Fetches and previews a new wallpaper
  - "Set as Wallpaper" - Applies the previewed wallpaper
- **Real-time Status**: See progress and results in the status log
- **Dark Theme**: Easy on the eyes for extended use
- **Background Processing**: Non-blocking operations keep the UI responsive

The GUI automatically saves all configuration changes to `config.yaml` as you edit.

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
├── requirements-dev.txt            # Dev/test dependencies (pytest, coverage)
├── pytest.ini                      # pytest configuration
├── config.yaml.template            # Configuration template
├── wallpaper_randomizer/           # Main package
│   ├── __init__.py
│   ├── __main__.py                 # CLI entry point
│   ├── config.py                   # Configuration handling
│   ├── reddit_fetcher.py           # Reddit API integration
│   ├── image_handler.py            # Image processing
│   ├── wallpaper_setter.py         # Platform-specific wallpaper setting
│   └── ...
├── tests/                          # Automated test suite
│   ├── conftest.py                 # Shared fixtures
│   ├── helpers.py                  # Shared test helpers
│   ├── test_config.py
│   ├── test_reddit_fetcher.py
│   ├── test_image_handler.py
│   ├── test_wallpaper_fetcher.py
│   ├── test_wallpaper_setter.py
│   └── test_integration_live.py    # Optional live Reddit API test
├── .venv/                          # Virtual environment (git-ignored)
└── README.md
```

### Running Tests

The project has an automated pytest suite covering the core logic: configuration validation and getters, Reddit post filtering/selection/caching, image validation and cache management, the retry loop, and wallpaper detection/routing. It runs on every push and pull request via GitHub Actions (`.github/workflows/tests.yml`).

To run the tests locally:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest
```

(On Windows, use `.venv\Scripts\python -m pytest`.) Run a single module's tests with, e.g., `.venv/bin/python -m pytest tests/test_config.py -v`.

**Optional live integration test:** `tests/test_integration_live.py` fetches from the real Reddit API and downloads a real image (it never applies a wallpaper). It is skipped automatically unless `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` are set in the environment. To enable it in CI, add both as secrets to the GitHub repository.

You can also validate your local configuration with:

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
