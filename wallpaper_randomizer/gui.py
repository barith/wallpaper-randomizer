"""GUI for wallpaper randomizer."""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from pathlib import Path
from PIL import Image, ImageTk
import threading
import os

from .config import Config
from .reddit_fetcher import RedditFetcher
from .image_handler import ImageHandler
from .wallpaper_setter import WallpaperSetter


class WallpaperGUI:
    """Main GUI application for wallpaper randomizer."""

    # Dark theme colors
    BG_DARK = "#2b2b2b"
    BG_PANEL = "#3c3c3c"
    BG_INPUT = "#4a4a4a"
    FG_TEXT = "#e0e0e0"
    FG_DIM = "#a0a0a0"
    ACCENT_BLUE = "#4a9eff"
    ACCENT_GREEN = "#4caf50"
    BORDER_COLOR = "#555555"

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize GUI.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.current_image_path = None
        self.current_wallpaper_info = None
        self.preview_photo = None

        # Initialize window
        self.root = tk.Tk()
        self.root.title("Wallpaper Randomizer")
        self.root.geometry("1200x700")
        self.root.configure(bg=self.BG_DARK)

        # Load config
        try:
            self.config = Config(config_path)
            self.config_data = self.config.data.copy()
        except FileNotFoundError:
            messagebox.showerror(
                "Config Not Found",
                f"Configuration file not found: {config_path}\n"
                "Please run 'python run.py init' first."
            )
            self.root.destroy()
            return
        except Exception as e:
            messagebox.showerror("Config Error", f"Failed to load config: {e}")
            self.root.destroy()
            return

        # Initialize components (will be created on demand)
        self.reddit_fetcher = None
        self.image_handler = None
        self.wallpaper_setter = None

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Setup the user interface."""
        # Create main container with padding
        main_container = tk.Frame(self.root, bg=self.BG_DARK)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Left panel - Configuration
        left_panel = tk.Frame(
            main_container, bg=self.BG_PANEL, relief=tk.RAISED, bd=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 5), pady=0)
        left_panel.config(width=400)

        # Right panel - Preview and controls
        right_panel = tk.Frame(
            main_container, bg=self.BG_PANEL, relief=tk.RAISED, bd=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH,
                         expand=True, padx=(5, 0), pady=0)

        # Setup panels
        self._setup_config_panel(left_panel)
        self._setup_preview_panel(right_panel)

    def _setup_config_panel(self, parent):
        """Setup configuration panel."""
        # Title
        title = tk.Label(
            parent,
            text="Configuration",
            font=("Arial", 14, "bold"),
            bg=self.BG_PANEL,
            fg=self.FG_TEXT
        )
        title.pack(pady=(10, 15), padx=10, anchor=tk.W)

        # Scrollable frame for config options
        canvas = tk.Canvas(parent, bg=self.BG_PANEL, highlightthickness=0)
        scrollbar = ttk.Scrollbar(
            parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.BG_PANEL)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Subreddits section
        self._create_section_label(scrollable_frame, "Subreddits")
        self.subreddit_entries = []
        self.subreddit_frame = tk.Frame(scrollable_frame, bg=self.BG_PANEL)
        self.subreddit_frame.pack(fill=tk.X, padx=10, pady=5)

        # Load subreddits with state
        subreddits = self.config.get_subreddits_with_state()
        for sub_data in subreddits:
            if isinstance(sub_data, dict):
                self._add_subreddit_entry(
                    sub_data['name'], sub_data.get('enabled', True))
            else:
                # Handle old format
                self._add_subreddit_entry(sub_data, True)

        add_btn = tk.Button(
            scrollable_frame,
            text="+ Add Subreddit",
            command=self._add_subreddit_entry,
            bg=self.ACCENT_BLUE,
            fg="white",
            relief=tk.FLAT,
            padx=10,
            pady=5
        )
        add_btn.pack(padx=10, pady=5, anchor=tk.W)

        # Resolution section
        self._create_section_label(scrollable_frame, "Minimum Resolution")
        res_frame = tk.Frame(scrollable_frame, bg=self.BG_PANEL)
        res_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(res_frame, text="Width:", bg=self.BG_PANEL, fg=self.FG_TEXT).grid(
            row=0, column=0, sticky=tk.W, pady=2)
        self.width_var = tk.StringVar(
            value=str(self.config_data['min_resolution']['width']))
        width_entry = self._create_entry(res_frame, self.width_var)
        width_entry.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.width_var.trace('w', lambda *args: self._save_config())

        tk.Label(res_frame, text="Height:", bg=self.BG_PANEL,
                 fg=self.FG_TEXT).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.height_var = tk.StringVar(
            value=str(self.config_data['min_resolution']['height']))
        height_entry = self._create_entry(res_frame, self.height_var)
        height_entry.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.height_var.trace('w', lambda *args: self._save_config())

        res_frame.columnconfigure(1, weight=1)

        # Post filter section
        self._create_section_label(scrollable_frame, "Post Filter")
        filter_frame = tk.Frame(scrollable_frame, bg=self.BG_PANEL)
        filter_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(filter_frame, text="Sort:", bg=self.BG_PANEL,
                 fg=self.FG_TEXT).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.sort_var = tk.StringVar(
            value=self.config_data['post_filter']['sort'])
        sort_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.sort_var,
            values=['hot', 'new', 'top', 'controversial', 'rising'],
            state='readonly',
            width=15
        )
        sort_combo.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.sort_var.trace('w', lambda *args: self._save_config())

        tk.Label(filter_frame, text="Time:", bg=self.BG_PANEL,
                 fg=self.FG_TEXT).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.time_var = tk.StringVar(
            value=self.config_data['post_filter'].get('time_filter', 'month'))
        time_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.time_var,
            values=['hour', 'day', 'week', 'month', 'year', 'all'],
            state='readonly',
            width=15
        )
        time_combo.grid(row=1, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.time_var.trace('w', lambda *args: self._save_config())

        tk.Label(filter_frame, text="Limit:", bg=self.BG_PANEL,
                 fg=self.FG_TEXT).grid(row=2, column=0, sticky=tk.W, pady=2)
        self.limit_var = tk.StringVar(
            value=str(self.config_data['post_filter'].get('limit', 100)))
        limit_entry = self._create_entry(filter_frame, self.limit_var)
        limit_entry.grid(row=2, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.limit_var.trace('w', lambda *args: self._save_config())

        filter_frame.columnconfigure(1, weight=1)

        # Reddit credentials section
        self._create_section_label(scrollable_frame, "Reddit API Credentials")
        cred_frame = tk.Frame(scrollable_frame, bg=self.BG_PANEL)
        cred_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(cred_frame, text="Client ID:", bg=self.BG_PANEL,
                 fg=self.FG_TEXT).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.client_id_var = tk.StringVar(
            value=self.config_data['reddit']['client_id'])
        client_id_entry = self._create_entry(
            cred_frame, self.client_id_var, show="*")
        client_id_entry.grid(
            row=0, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.client_id_var.trace('w', lambda *args: self._save_config())

        tk.Label(cred_frame, text="Client Secret:", bg=self.BG_PANEL,
                 fg=self.FG_TEXT).grid(row=1, column=0, sticky=tk.W, pady=2)
        self.client_secret_var = tk.StringVar(
            value=self.config_data['reddit']['client_secret'])
        client_secret_entry = self._create_entry(
            cred_frame, self.client_secret_var, show="*")
        client_secret_entry.grid(
            row=1, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.client_secret_var.trace('w', lambda *args: self._save_config())

        cred_frame.columnconfigure(1, weight=1)

        # Cache settings section
        self._create_section_label(scrollable_frame, "Cache Settings")
        cache_frame = tk.Frame(scrollable_frame, bg=self.BG_PANEL)
        cache_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(cache_frame, text="Max Cache (MB):", bg=self.BG_PANEL,
                 fg=self.FG_TEXT).grid(row=0, column=0, sticky=tk.W, pady=2)
        self.cache_var = tk.StringVar(
            value=str(self.config_data.get('max_cache_size_mb', 500)))
        cache_entry = self._create_entry(cache_frame, self.cache_var)
        cache_entry.grid(row=0, column=1, sticky=tk.EW, pady=2, padx=(5, 0))
        self.cache_var.trace('w', lambda *args: self._save_config())

        cache_frame.columnconfigure(1, weight=1)

        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _setup_preview_panel(self, parent):
        """Setup preview and control panel."""
        # Title
        title = tk.Label(
            parent,
            text="Preview & Control",
            font=("Arial", 14, "bold"),
            bg=self.BG_PANEL,
            fg=self.FG_TEXT
        )
        title.pack(pady=(10, 15), padx=10, anchor=tk.W)

        # Preview area
        preview_container = tk.Frame(
            parent, bg=self.BG_INPUT, relief=tk.SUNKEN, bd=2)
        preview_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.preview_label = tk.Label(
            preview_container,
            text="No wallpaper loaded\n\nClick 'Get Random Wallpaper' to start",
            bg=self.BG_INPUT,
            fg=self.FG_DIM,
            font=("Arial", 12)
        )
        self.preview_label.pack(fill=tk.BOTH, expand=True)

        # Info frame
        info_frame = tk.Frame(parent, bg=self.BG_PANEL)
        info_frame.pack(fill=tk.X, padx=10, pady=5)

        self.info_title = tk.Label(
            info_frame,
            text="Title: -",
            bg=self.BG_PANEL,
            fg=self.FG_TEXT,
            anchor=tk.W,
            font=("Arial", 10)
        )
        self.info_title.pack(fill=tk.X, pady=2)

        self.info_subreddit = tk.Label(
            info_frame,
            text="Subreddit: -",
            bg=self.BG_PANEL,
            fg=self.FG_TEXT,
            anchor=tk.W,
            font=("Arial", 10)
        )
        self.info_subreddit.pack(fill=tk.X, pady=2)

        self.info_resolution = tk.Label(
            info_frame,
            text="Resolution: -",
            bg=self.BG_PANEL,
            fg=self.FG_TEXT,
            anchor=tk.W,
            font=("Arial", 10)
        )
        self.info_resolution.pack(fill=tk.X, pady=2)

        # Control buttons
        button_frame = tk.Frame(parent, bg=self.BG_PANEL)
        button_frame.pack(fill=tk.X, padx=10, pady=10)

        self.get_btn = tk.Button(
            button_frame,
            text="Get Random Wallpaper",
            command=self._get_random_wallpaper,
            bg=self.ACCENT_BLUE,
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10
        )
        self.get_btn.pack(fill=tk.X, pady=5)

        self.set_btn = tk.Button(
            button_frame,
            text="Set as Wallpaper",
            command=self._set_wallpaper,
            bg=self.ACCENT_GREEN,
            fg="white",
            font=("Arial", 11, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=10,
            state=tk.DISABLED
        )
        self.set_btn.pack(fill=tk.X, pady=5)

        # Status area
        status_label = tk.Label(
            parent,
            text="Status",
            bg=self.BG_PANEL,
            fg=self.FG_TEXT,
            font=("Arial", 10, "bold"),
            anchor=tk.W
        )
        status_label.pack(fill=tk.X, padx=10, pady=(10, 5))

        self.status_text = scrolledtext.ScrolledText(
            parent,
            height=6,
            bg=self.BG_INPUT,
            fg=self.FG_TEXT,
            font=("Courier", 9),
            relief=tk.SUNKEN,
            bd=1,
            state=tk.DISABLED
        )
        self.status_text.pack(fill=tk.X, padx=10, pady=(0, 10))

    def _create_section_label(self, parent, text):
        """Create a section label."""
        label = tk.Label(
            parent,
            text=text,
            font=("Arial", 11, "bold"),
            bg=self.BG_PANEL,
            fg=self.FG_TEXT,
            anchor=tk.W
        )
        label.pack(fill=tk.X, padx=10, pady=(15, 5))

        # Separator line
        sep = tk.Frame(parent, height=1, bg=self.BORDER_COLOR)
        sep.pack(fill=tk.X, padx=10, pady=(0, 5))

    def _create_entry(self, parent, textvariable, **kwargs):
        """Create a styled entry widget."""
        entry = tk.Entry(
            parent,
            textvariable=textvariable,
            bg=self.BG_INPUT,
            fg=self.FG_TEXT,
            insertbackground=self.FG_TEXT,
            relief=tk.FLAT,
            **kwargs
        )
        return entry

    def _add_subreddit_entry(self, value="", enabled=True):
        """Add a subreddit entry field with toggle checkbox.

        Args:
            value: Subreddit name
            enabled: Whether the subreddit is enabled
        """
        frame = tk.Frame(self.subreddit_frame, bg=self.BG_PANEL)
        frame.pack(fill=tk.X, pady=2)

        # Checkbox for enabled/disabled state
        enabled_var = tk.BooleanVar(value=enabled)
        checkbox = tk.Checkbutton(
            frame,
            variable=enabled_var,
            bg=self.BG_PANEL,
            fg=self.FG_TEXT,
            activebackground=self.BG_PANEL,
            activeforeground=self.FG_TEXT,
            selectcolor=self.BG_INPUT,
            command=lambda: self._on_subreddit_toggle(entry, enabled_var)
        )
        checkbox.pack(side=tk.LEFT, padx=(0, 5))

        # Text entry for subreddit name
        var = tk.StringVar(value=value)
        entry = self._create_entry(frame, var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        var.trace('w', lambda *args: self._save_config())

        # Set initial color based on enabled state
        if not enabled:
            entry.config(fg=self.FG_DIM)

        # Remove button
        remove_btn = tk.Button(
            frame,
            text="×",
            command=lambda: self._remove_subreddit_entry(
                frame, var, enabled_var),
            bg=self.BG_INPUT,
            fg=self.FG_TEXT,
            relief=tk.FLAT,
            width=3
        )
        remove_btn.pack(side=tk.RIGHT, padx=(5, 0))

        self.subreddit_entries.append((frame, var, enabled_var, entry))

    def _on_subreddit_toggle(self, entry, enabled_var):
        """Handle subreddit checkbox toggle.

        Args:
            entry: The text entry widget
            enabled_var: The BooleanVar for the checkbox
        """
        # Update text color based on enabled state
        if enabled_var.get():
            entry.config(fg=self.FG_TEXT)
        else:
            entry.config(fg=self.FG_DIM)

        # Save config with new state
        self._save_config()

    def _remove_subreddit_entry(self, frame, var, enabled_var):
        """Remove a subreddit entry.

        Args:
            frame: The frame containing the entry
            var: The StringVar for the entry
            enabled_var: The BooleanVar for the checkbox
        """
        self.subreddit_entries = [
            (f, v, e, entry) for f, v, e, entry in self.subreddit_entries
            if v != var
        ]
        frame.destroy()
        self._save_config()

    def _save_config(self):
        """Save current configuration to file."""
        try:
            # Update config data with subreddits in new format (name + enabled state)
            subreddits = []
            for _, var, enabled_var, _ in self.subreddit_entries:
                name = var.get().strip()
                if name:  # Only add non-empty subreddit names
                    subreddits.append({
                        'name': name,
                        'enabled': enabled_var.get()
                    })

            if not subreddits:
                return  # Don't save invalid config

            self.config_data['subreddits'] = subreddits
            self.config_data['min_resolution']['width'] = int(
                self.width_var.get() or 1920)
            self.config_data['min_resolution']['height'] = int(
                self.height_var.get() or 1080)
            self.config_data['post_filter']['sort'] = self.sort_var.get()
            self.config_data['post_filter']['time_filter'] = self.time_var.get()
            self.config_data['post_filter']['limit'] = int(
                self.limit_var.get() or 100)
            self.config_data['reddit']['client_id'] = self.client_id_var.get()
            self.config_data['reddit']['client_secret'] = self.client_secret_var.get(
            )
            self.config_data['max_cache_size_mb'] = int(
                self.cache_var.get() or 500)

            # Write to file
            import yaml
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config_data, f, default_flow_style=False)

            # Reload config object
            self.config = Config(self.config_path)

            # Reset components to use new config
            self.reddit_fetcher = None
            self.image_handler = None

        except (ValueError, Exception) as e:
            # Silently ignore invalid intermediate states during typing
            pass

    def _log_status(self, message):
        """Log a message to the status area."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.status_text.config(state=tk.DISABLED)

    def _clear_status(self):
        """Clear the status area."""
        self.status_text.config(state=tk.NORMAL)
        self.status_text.delete(1.0, tk.END)
        self.status_text.config(state=tk.DISABLED)

    def _get_random_wallpaper(self):
        """Fetch a random wallpaper in background thread."""
        # Disable button during fetch
        self.get_btn.config(state=tk.DISABLED, text="Fetching...")
        self.set_btn.config(state=tk.DISABLED)
        self._clear_status()

        # Run in thread to avoid blocking UI
        thread = threading.Thread(target=self._fetch_wallpaper_thread)
        thread.daemon = True
        thread.start()

    def _fetch_wallpaper_thread(self):
        """Background thread to fetch wallpaper."""
        try:
            # Initialize components if needed
            if self.reddit_fetcher is None:
                self.root.after(0, lambda: self._log_status(
                    "Initializing Reddit API..."))
                self.reddit_fetcher = RedditFetcher(
                    self.config.get_reddit_credentials())

            if self.image_handler is None:
                self.image_handler = ImageHandler(
                    self.config.get_cache_dir(),
                    self.config.get_min_resolution()
                )

            # Fetch wallpaper
            self.root.after(0, lambda: self._log_status(
                "Fetching posts from Reddit..."))
            post_filter = self.config.get_post_filter()

            wallpaper_info = self.reddit_fetcher.get_random_wallpaper_url(
                self.config.get_subreddits(),
                sort=post_filter['sort'],
                time_filter=post_filter.get('time_filter', 'month'),
                limit=post_filter.get('limit', 100),
                filter_nsfw=self.config.get_filter_nsfw()
            )

            if not wallpaper_info:
                self.root.after(0, lambda: self._log_status(
                    "❌ No suitable wallpapers found"))
                self.root.after(0, lambda: self.get_btn.config(
                    state=tk.NORMAL, text="Get Random Wallpaper"))
                return

            self.root.after(0, lambda: self._log_status(
                f"Found: {wallpaper_info['title'][:50]}..."))
            self.root.after(0, lambda: self._log_status(
                f"From: r/{wallpaper_info['subreddit']}"))

            # Download image
            self.root.after(0, lambda: self._log_status(
                "Downloading image..."))
            image_path = self.image_handler.download_image(
                wallpaper_info['url'],
                wallpaper_info['title']
            )

            if not image_path:
                self.root.after(0, lambda: self._log_status(
                    "❌ Failed to download or validate image"))
                self.root.after(0, lambda: self.get_btn.config(
                    state=tk.NORMAL, text="Get Random Wallpaper"))
                return

            # Success - update UI
            self.current_image_path = image_path
            self.current_wallpaper_info = wallpaper_info

            self.root.after(0, lambda: self._log_status(
                f"✓ Downloaded: {image_path.name}"))
            self.root.after(0, lambda: self._display_preview())
            self.root.after(0, lambda: self.get_btn.config(
                state=tk.NORMAL, text="Get Random Wallpaper"))
            self.root.after(0, lambda: self.set_btn.config(state=tk.NORMAL))

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.root.after(0, lambda: self._log_status(error_msg))
            self.root.after(0, lambda: self.get_btn.config(
                state=tk.NORMAL, text="Get Random Wallpaper"))

    def _display_preview(self):
        """Display the current image in preview area."""
        if not self.current_image_path or not self.current_image_path.exists():
            return

        try:
            # Load and resize image to fit preview
            img = Image.open(self.current_image_path)

            # Get preview area size
            preview_width = self.preview_label.winfo_width()
            preview_height = self.preview_label.winfo_height()

            # Use reasonable defaults if window not yet rendered
            if preview_width <= 1:
                preview_width = 700
            if preview_height <= 1:
                preview_height = 400

            # Calculate scaling to fit preview area while maintaining aspect ratio
            img_ratio = img.width / img.height
            preview_ratio = preview_width / preview_height

            if img_ratio > preview_ratio:
                # Image is wider than preview
                new_width = preview_width
                new_height = int(preview_width / img_ratio)
            else:
                # Image is taller than preview
                new_height = preview_height
                new_width = int(preview_height * img_ratio)

            # Resize image
            img_resized = img.resize(
                (new_width, new_height), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            self.preview_photo = ImageTk.PhotoImage(img_resized)

            # Update label
            self.preview_label.config(image=self.preview_photo, text="")

            # Update info labels
            self.info_title.config(
                text=f"Title: {self.current_wallpaper_info['title'][:60]}")
            self.info_subreddit.config(
                text=f"Subreddit: r/{self.current_wallpaper_info['subreddit']}")
            self.info_resolution.config(
                text=f"Resolution: {img.width}x{img.height}")

        except Exception as e:
            self._log_status(f"❌ Error displaying preview: {e}")

    def _set_wallpaper(self):
        """Set the current image as wallpaper."""
        if not self.current_image_path:
            messagebox.showwarning(
                "No Image", "Please fetch a wallpaper first")
            return

        self.set_btn.config(state=tk.DISABLED, text="Setting...")
        self._log_status("Setting wallpaper...")

        # Run in thread
        thread = threading.Thread(target=self._set_wallpaper_thread)
        thread.daemon = True
        thread.start()

    def _set_wallpaper_thread(self):
        """Background thread to set wallpaper."""
        try:
            if self.wallpaper_setter is None:
                self.wallpaper_setter = WallpaperSetter()

            success = self.wallpaper_setter.set_wallpaper(
                self.current_image_path)

            if success:
                self.root.after(0, lambda: self._log_status(
                    "✓ Wallpaper set successfully!"))

                # Clean up cache if needed
                max_cache_mb = self.config.get_max_cache_size_mb()
                current_cache_mb = self.image_handler.get_cache_size_mb()

                if current_cache_mb > max_cache_mb:
                    self.root.after(0, lambda: self._log_status(
                        f"Cache size: {current_cache_mb:.1f}MB / {max_cache_mb}MB"))
                    deleted = self.image_handler.cleanup_old_cache(
                        max_cache_mb)
                    self.root.after(0, lambda: self._log_status(
                        f"Cleaned up {deleted} old images"))
            else:
                self.root.after(0, lambda: self._log_status(
                    "❌ Failed to set wallpaper"))

            self.root.after(0, lambda: self.set_btn.config(
                state=tk.NORMAL, text="Set as Wallpaper"))

        except Exception as e:
            error_msg = f"❌ Error setting wallpaper: {str(e)}"
            self.root.after(0, lambda: self._log_status(error_msg))
            self.root.after(0, lambda: self.set_btn.config(
                state=tk.NORMAL, text="Set as Wallpaper"))

    def run(self):
        """Run the GUI application."""
        self.root.mainloop()


def launch_gui(config_path: str = "config.yaml"):
    """Launch the GUI application.

    Args:
        config_path: Path to configuration file
    """
    app = WallpaperGUI(config_path)
    app.run()
