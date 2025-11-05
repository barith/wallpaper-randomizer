#!/usr/bin/env python3
"""
Cross-platform wrapper script for wallpaper-randomizer.
Handles virtual environment creation, dependency management, and execution.
Can be called from anywhere on the system.
"""

import sys
import subprocess
import os
from pathlib import Path
import shutil


class Colors:
    """ANSI color codes for terminal output."""
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

    @staticmethod
    def supports_color():
        """Check if terminal supports colors."""
        return (
            hasattr(sys.stdout, 'isatty') and sys.stdout.isatty() and
            os.environ.get('TERM') != 'dumb'
        )


def log_info(message):
    """Print info message."""
    if Colors.supports_color():
        print(f"{Colors.GREEN}[INFO]{Colors.NC} {message}")
    else:
        print(f"[INFO] {message}")


def log_warn(message):
    """Print warning message."""
    if Colors.supports_color():
        print(f"{Colors.YELLOW}[WARN]{Colors.NC} {message}")
    else:
        print(f"[WARN] {message}")


def log_error(message):
    """Print error message."""
    if Colors.supports_color():
        print(f"{Colors.RED}[ERROR]{Colors.NC} {message}", file=sys.stderr)
    else:
        print(f"[ERROR] {message}", file=sys.stderr)


def get_repo_root():
    """Get the absolute path to the repository root (where this script is located)."""
    return Path(__file__).parent.resolve()


def get_venv_path(repo_root):
    """Get the path to the virtual environment directory."""
    return repo_root / ".venv"


def get_python_executable(venv_path):
    """Get the path to the Python executable in the virtual environment."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "python.exe"
    else:
        return venv_path / "bin" / "python"


def get_pip_executable(venv_path):
    """Get the path to the pip executable in the virtual environment."""
    if sys.platform == "win32":
        return venv_path / "Scripts" / "pip.exe"
    else:
        return venv_path / "bin" / "pip"


def check_python_version():
    """Check if Python version is 3.7 or higher."""
    version_info = sys.version_info
    if version_info < (3, 7):
        log_error(
            f"Python 3.7+ is required (found Python {version_info.major}.{version_info.minor})")
        sys.exit(1)
    return f"{version_info.major}.{version_info.minor}.{version_info.micro}"


def venv_exists(venv_path):
    """Check if virtual environment exists and is valid."""
    if not venv_path.exists():
        return False

    python_exe = get_python_executable(venv_path)
    if not python_exe.exists():
        return False

    return True


def create_venv(repo_root, venv_path):
    """Create a new virtual environment."""
    log_info(f"Creating virtual environment at {venv_path}")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)],
            check=True,
            capture_output=True,
            text=True
        )
        log_info("Virtual environment created successfully")
        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to create virtual environment: {e}")
        if e.stderr:
            log_error(e.stderr)
        return False


def check_requirements_installed(venv_path, requirements_file):
    """Check if all requirements are installed in the virtual environment."""
    if not requirements_file.exists():
        log_warn(f"requirements.txt not found at {requirements_file}")
        return False

    pip_exe = get_pip_executable(venv_path)

    # Read requirements file
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.split('#')[0].strip()
            for line in f
            if line.strip() and not line.strip().startswith('#')
        ]

    # Check each package
    for requirement in requirements:
        # Extract package name (before version specifiers)
        package_name = requirement.split('==')[0].split('>=')[0].split('<=')[
            0].split('!=')[0].split('~=')[0].strip()

        try:
            subprocess.run(
                [str(pip_exe), "show", package_name],
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError:
            return False

    return True


def install_requirements(venv_path, requirements_file):
    """Install requirements in the virtual environment."""
    pip_exe = get_pip_executable(venv_path)

    log_info("Installing/updating dependencies from requirements.txt")

    # Upgrade pip first
    try:
        subprocess.run(
            [str(pip_exe), "install", "--upgrade", "pip"],
            check=True,
            capture_output=True,
            text=True
        )
    except subprocess.CalledProcessError as e:
        log_warn("Failed to upgrade pip (continuing anyway)")

    # Install requirements
    try:
        subprocess.run(
            [str(pip_exe), "install", "-r", str(requirements_file)],
            check=True
        )
        log_info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to install requirements: {e}")
        return False


def update_requirements(venv_path, requirements_file):
    """Update all requirements to latest versions."""
    pip_exe = get_pip_executable(venv_path)

    log_info("Updating all dependencies")

    # Upgrade pip
    try:
        subprocess.run(
            [str(pip_exe), "install", "--upgrade", "pip"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to upgrade pip: {e}")
        return False

    # Upgrade all requirements
    try:
        subprocess.run(
            [str(pip_exe), "install", "--upgrade",
             "-r", str(requirements_file)],
            check=True
        )
        log_info("Dependencies updated successfully")
        return True
    except subprocess.CalledProcessError as e:
        log_error(f"Failed to update requirements: {e}")
        return False


def recreate_venv(repo_root, venv_path, requirements_file):
    """Recreate the virtual environment from scratch."""
    log_warn("Recreating virtual environment")

    # Remove old venv
    if venv_path.exists():
        shutil.rmtree(venv_path)

    # Create new venv
    if not create_venv(repo_root, venv_path):
        return False

    # Install requirements
    return install_requirements(venv_path, requirements_file)


def run_wallpaper_randomizer(venv_path, args):
    """Execute wallpaper_randomizer module with given arguments."""
    python_exe = get_python_executable(venv_path)

    log_info("Executing wallpaper_randomizer")

    # Run the module
    result = subprocess.run(
        [str(python_exe), "-m", "wallpaper_randomizer"] + args,
        cwd=get_repo_root()
    )

    return result.returncode


def show_help():
    """Show help message."""
    help_text = """
Wallpaper Randomizer Wrapper Script

This script automatically manages the virtual environment and dependencies
for wallpaper-randomizer, then executes the requested command.

USAGE:
    python run.py [OPTIONS] <command> [args...]

WRAPPER OPTIONS:
    --update            Update all dependencies to latest versions
    --recreate-venv     Recreate the virtual environment from scratch
    --help, -h          Show this help message

WALLPAPER RANDOMIZER COMMANDS:
    set                 Set a random wallpaper
    init                Initialize configuration file
    clear-cache         Clear cached images
    test-config         Test configuration

EXAMPLES:
    python run.py set                    # Set a random wallpaper
    python run.py init                   # Initialize config
    python run.py --update               # Update dependencies
    python run.py --recreate-venv        # Recreate virtual environment
    python run.py set --fill-mode zoom   # Set wallpaper with zoom fill mode

VIRTUAL ENVIRONMENT:
    The script automatically creates and manages a virtual environment in
    .venv/ directory within the repository. You don't need to manually
    activate it - the wrapper handles everything automatically.

For more information, see README.md
"""
    print(help_text)


def main():
    """Main entry point."""
    # Check Python version
    python_version = check_python_version()

    # Get paths
    repo_root = get_repo_root()
    venv_path = get_venv_path(repo_root)
    requirements_file = repo_root / "requirements.txt"

    # Parse wrapper-specific arguments
    args = sys.argv[1:]

    if not args or "--help" in args or "-h" in args:
        show_help()
        return 0

    # Handle --update flag
    if "--update" in args:
        if not venv_exists(venv_path):
            log_error(
                "Virtual environment doesn't exist. Create it first by running a command.")
            return 1

        success = update_requirements(venv_path, requirements_file)
        return 0 if success else 1

    # Handle --recreate-venv flag
    if "--recreate-venv" in args:
        success = recreate_venv(repo_root, venv_path, requirements_file)
        return 0 if success else 1

    # Create venv if it doesn't exist
    need_install = False
    if not venv_exists(venv_path):
        if not create_venv(repo_root, venv_path):
            return 1
        need_install = True

    # Check and install requirements if needed
    if need_install or not check_requirements_installed(venv_path, requirements_file):
        if not install_requirements(venv_path, requirements_file):
            return 1

    # Run wallpaper_randomizer with all arguments
    return run_wallpaper_randomizer(venv_path, args)


if __name__ == "__main__":
    sys.exit(main())
