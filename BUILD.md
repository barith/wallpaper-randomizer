# Building Platform-Specific Applications

This document explains how to build standalone applications (Windows executable and macOS app) for the Wallpaper Randomizer GUI using GitHub Actions.

## Overview

The project uses GitHub Actions to automatically build platform-specific applications using PyInstaller:
- **Windows**: Creates a `.exe` file packaged in a ZIP
- **macOS**: Creates a `.app` bundle packaged in a DMG disk image

Both allow your friends to run the application without installing Python or any dependencies.

## Automated Build via GitHub Actions

Two separate workflows handle each platform:

### Windows Build (`.github/workflows/build-windows-exe.yml`)

1. Sets up a Windows environment with Python 3.11
2. Installs all required dependencies from `requirements.txt`
3. Runs PyInstaller with the spec file (`wallpaper_randomizer_gui.spec`)
4. Packages the executable with config template and README
5. Creates a downloadable ZIP file
6. Uploads it as a build artifact (and creates a GitHub Release for tags)

### macOS Build (`.github/workflows/build-macos-app.yml`)

1. Sets up a macOS environment with Python 3.11
2. Installs all required dependencies from `requirements.txt`
3. Runs PyInstaller with the spec file (`wallpaper_randomizer_gui_macos.spec`)
4. Creates a `.app` bundle
5. Packages into a DMG disk image with drag-to-Applications shortcut
6. Uploads it as a build artifact (and creates a GitHub Release for tags)

### Triggering a Build

Both workflows can be triggered the same way:

#### Method 1: Manual Trigger (Recommended for testing)

1. Go to your GitHub repository
2. Click on **Actions** tab
3. Select **Build Windows Executable** or **Build macOS Application** workflow
4. Click **Run workflow** button (on the right)
5. Optionally enter a version string
6. Click **Run workflow**

#### Method 2: Push to Main Branch

The workflow automatically runs when you push to the `main` branch:

```bash
git add .
git commit -m "Update code"
git push origin main
```

#### Method 3: Create a Release Tag (Recommended for distribution)

For official releases, create and push a version tag:

```bash
git tag v1.0.0
git push origin v1.0.0
```

This will:
- Build the executable
- Create a GitHub Release
- Attach the ZIP file to the release

## Downloading the Built Applications

### From Workflow Artifacts

1. Go to **Actions** tab in your repository
2. Click on the workflow run
3. Scroll down to **Artifacts** section
4. Download:
   - `WallpaperRandomizer-Windows-[version].zip` (Windows)
   - `WallpaperRandomizer-macOS-[version].dmg` (macOS)

Artifacts are kept for 30 days.

### From GitHub Releases

If you created a release tag:

1. Go to **Releases** section in your repository
2. Find your release version
3. Download the attached file(s)

## Distribution Packages

### Windows ZIP File

The distribution ZIP contains:

- `WallpaperRandomizer.exe` - The standalone executable
- `config.yaml.template` - Configuration template
- `README.md` - Project documentation
- `INSTRUCTIONS.txt` - Quick setup guide

### macOS DMG File

The DMG disk image contains:

- `WallpaperRandomizer.app` - The macOS application bundle
- `config.yaml.template` - Configuration template
- `README.md` - Project documentation
- `INSTRUCTIONS.txt` - Quick setup guide
- Drag-to-Applications shortcut

## Distribution to Your Friends

### For Windows Users

1. **Download** the ZIP file
2. **Extract** all files to a folder (e.g., `C:\WallpaperRandomizer\`)
3. **Run** `WallpaperRandomizer.exe`
   - The app will auto-create a config file at `%APPDATA%\WallpaperRandomizer\config.yaml`
4. **Locate config file**:
   - Press Win+R, type `%APPDATA%\WallpaperRandomizer`, press Enter
5. **Edit** `config.yaml`:
   - Get Reddit API credentials (see below)
   - Add desired subreddits
   - Configure preferences
6. **Restart** the app

See `INSTRUCTIONS-Windows.txt` (included in ZIP) for detailed instructions.

### For macOS Users

1. **Download** the DMG file
2. **Open** the DMG (double-click)
3. **Drag** `WallpaperRandomizer.app` to the Applications folder (or any location)
4. **First Run**: Right-click the app → "Open" → Click "Open" in the dialog
   - This bypasses Gatekeeper (only needed once for unsigned apps)
   - The app will auto-create a config file at `~/Library/Application Support/WallpaperRandomizer/config.yaml`
5. **Locate config file**:
   - Press Cmd+Shift+G in Finder
   - Enter: `~/Library/Application Support/WallpaperRandomizer`
   - Press Enter
6. **Edit** `config.yaml`:
   - Get Reddit API credentials (see below)
   - Add desired subreddits
   - Configure preferences
7. **Restart** the app

See `INSTRUCTIONS-macOS.txt` (included in DMG) for detailed instructions.

### Getting Reddit API Credentials

Your friend will need to create a Reddit app to get API credentials:

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in:
   - **name**: Any name (e.g., "My Wallpaper App")
   - **type**: Select "script"
   - **description**: Optional
   - **about url**: Optional
   - **redirect uri**: `http://localhost:8080`
4. Click "Create app"
5. Copy the credentials:
   - **client_id**: String under "personal use script"
   - **client_secret**: The "secret" field
6. Paste these into `config.yaml`

## Building Locally (Advanced)

If you need to build locally instead of using GitHub Actions:

### On Windows

```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build executable
pyinstaller wallpaper_randomizer_gui.spec

# Find executable in dist/WallpaperRandomizer.exe
```

### On macOS

```bash
# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build .app bundle
pyinstaller wallpaper_randomizer_gui_macos.spec

# Find app in dist/WallpaperRandomizer.app

# Optional: Create DMG
brew install create-dmg
# Follow DMG creation steps from the workflow
```

### On Linux (Cross-compilation)

```bash
# Cross-compiling for Windows or macOS from Linux is complex
# GitHub Actions is strongly recommended instead
```

## Troubleshooting

### Build Fails in GitHub Actions

1. **Check the workflow logs**: Go to Actions → Click the failed run → View logs
2. **Common issues**:
   - Missing dependencies: Update `requirements.txt`
   - Import errors: Add missing packages to `hidden_imports` in the spec file
   - PyInstaller errors: Check PyInstaller compatibility with dependency versions

### Executable Doesn't Run on Windows

1. **Missing DLLs**: Some Windows systems may need Visual C++ Redistributables
2. **Antivirus blocking**: Windows Defender or antivirus may flag the .exe
   - This is common with PyInstaller executables
   - Add an exception or have your friend verify the file is safe
3. **Config file missing**: Ensure `config.yaml` exists and is properly configured

### Config File Issues

If the executable can't find `config.yaml.template`:

1. Make sure it's in the same directory as the `.exe`
2. Check the spec file includes it in the `datas` list

## Customization

### Adding an Icon

1. Create or download a `.ico` file
2. Place it in the project root (e.g., `icon.ico`)
3. Edit `wallpaper_randomizer_gui.spec`:
   ```python
   icon='icon.ico',  # Update this line
   ```

### Modifying Build Settings

Edit `wallpaper_randomizer_gui.spec` to:

- Change executable name
- Add/remove bundled files
- Adjust PyInstaller options
- Include additional hidden imports

### Changing Python Version

Edit `.github/workflows/build-windows-exe.yml`:

```yaml
python-version: '3.11'  # Change to desired version
```

## File Structure

```
wallpaper-randomizer/
├── .github/
│   └── workflows/
│       └── build-windows-exe.yml    # GitHub Actions workflow
├── wallpaper_randomizer/            # Source code
│   └── gui.py                       # GUI entry point
├── wallpaper_randomizer_gui.spec    # PyInstaller spec file
├── config.yaml.template             # Config template (bundled)
├── requirements.txt                 # Python dependencies
└── BUILD.md                         # This file
```

## Version Management

### Semantic Versioning

Use version tags like:

- `v1.0.0` - Major release
- `v1.1.0` - Minor update
- `v1.1.1` - Patch/bugfix

### Creating a New Version

```bash
# Update version somewhere in code if needed
git add .
git commit -m "Release version 1.0.0"
git tag v1.0.0
git push origin main
git push origin v1.0.0
```

The GitHub Actions workflow will automatically create a release with the executable.

## Advanced Topics

### Code Signing (Optional)

To avoid Windows warnings about "unknown publisher":

1. Get a code signing certificate
2. Add signing step to GitHub Actions workflow
3. Sign the `.exe` file after building

This requires purchasing a certificate (~$100-300/year).

### Creating an Installer

For a more professional distribution:

1. Use NSIS or Inno Setup to create an installer
2. Add installer creation to the workflow
3. Distribute `.msi` or `.exe` installer instead of ZIP

## Support

If you encounter issues:

1. Check the [GitHub Issues](https://github.com/yourusername/wallpaper-randomizer/issues)
2. Review workflow logs in the Actions tab
3. Ensure all dependencies are up to date

## License

See the main [README.md](README.md) for license information.
