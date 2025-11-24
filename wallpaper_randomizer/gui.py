"""GUI for wallpaper randomizer."""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from pathlib import Path
from PIL import Image
import threading
import os
import logging
import sys

from .config import Config
from .reddit_fetcher import RedditFetcher
from .image_handler import ImageHandler
from .wallpaper_setter import WallpaperSetter
from .wallpaper_fetcher import fetch_wallpaper_with_retry


class TextboxHandler(logging.Handler):
    """Custom logging handler that writes to a CTkTextbox widget."""

    def __init__(self, textbox, root):
        """Initialize the handler.

        Args:
            textbox: CTkTextbox widget to write to
            root: CTk root window for thread-safe operations
        """
        super().__init__()
        self.textbox = textbox
        self.root = root

    def emit(self, record):
        """Emit a log record to the textbox.

        Args:
            record: LogRecord to emit
        """
        try:
            msg = self.format(record)
            # Use root.after for thread-safe GUI updates
            self.root.after(0, self._append_text, msg)
        except Exception:
            self.handleError(record)

    def _append_text(self, msg):
        """Append text to the textbox (must be called from main thread).

        Args:
            msg: Message to append
        """
        self.textbox.insert("end", msg + "\n")
        self.textbox.see("end")


class StreamRedirector:
    """Redirects stdout/stderr to a logging handler."""

    def __init__(self, logger, level):
        """Initialize the redirector.

        Args:
            logger: Logger instance to write to
            level: Logging level (e.g., logging.INFO)
        """
        self.logger = logger
        self.level = level
        self.buffer = ""

    def write(self, message):
        """Write message to logger.

        Args:
            message: Message to write
        """
        # Accumulate text until we hit a newline
        if message and message != "\n":
            self.buffer += message
            if "\n" in self.buffer:
                lines = self.buffer.split("\n")
                for line in lines[:-1]:
                    if line.strip():  # Only log non-empty lines
                        self.logger.log(self.level, line)
                self.buffer = lines[-1]
        elif message == "\n" and self.buffer:
            if self.buffer.strip():
                self.logger.log(self.level, self.buffer)
            self.buffer = ""

    def flush(self):
        """Flush any remaining buffer content."""
        if self.buffer and self.buffer.strip():
            self.logger.log(self.level, self.buffer)
            self.buffer = ""


class WallpaperGUI:
    """Main GUI application for wallpaper randomizer."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize GUI.

        Args:
            config_path: Path to configuration file
        """
        self.config_path = config_path
        self.current_image_path = None
        self.current_wallpaper_info = None
        self.preview_photo = None

        # Set CustomTkinter appearance
        # Modes: "System" (default), "Dark", "Light"
        ctk.set_appearance_mode("dark")
        # Themes: "blue" (default), "green", "dark-blue"
        ctk.set_default_color_theme("blue")

        # Initialize window
        self.root = ctk.CTk()
        self.root.title("Wallpaper Randomizer")
        self.root.geometry("1200x700")

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
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel - Configuration
        left_panel = ctk.CTkFrame(main_container, width=400, corner_radius=10)
        left_panel.pack(side="left", fill="both", padx=(0, 5), pady=0)
        left_panel.pack_propagate(False)  # Maintain fixed width

        # Right panel - Preview and controls
        right_panel = ctk.CTkFrame(main_container, corner_radius=10)
        right_panel.pack(side="right", fill="both",
                         expand=True, padx=(5, 0), pady=0)

        # Setup panels
        self._setup_config_panel(left_panel)
        self._setup_preview_panel(right_panel)

    def _setup_config_panel(self, parent):
        """Setup configuration panel."""
        # Title
        title = ctk.CTkLabel(
            parent,
            text="Configuration",
            font=("Arial", 16, "bold")
        )
        title.pack(pady=(15, 20), padx=15, anchor="w")

        # Scrollable frame for config options
        scrollable_frame = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent"
        )
        scrollable_frame.pack(fill="both", expand=True, padx=(10, 5))

        # Subreddits section
        self._create_section_label(scrollable_frame, "Subreddits")
        self.subreddit_entries = []
        self.subreddit_frame = ctk.CTkFrame(
            scrollable_frame, fg_color="transparent")
        self.subreddit_frame.pack(fill="x", padx=15, pady=(0, 5))

        # Load subreddits with state
        subreddits = self.config.get_subreddits_with_state()
        for sub_data in subreddits:
            if isinstance(sub_data, dict):
                self._add_subreddit_entry(
                    sub_data['name'], sub_data.get('enabled', True))
            else:
                # Handle old format
                self._add_subreddit_entry(sub_data, True)

        add_btn = ctk.CTkButton(
            scrollable_frame,
            text="+ Add Subreddit",
            command=self._add_subreddit_entry,
            width=140,
            height=32
        )
        add_btn.pack(padx=15, pady=(5, 10), anchor="w")

        # Resolution section
        self._create_section_label(scrollable_frame, "Minimum Resolution")
        res_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        res_frame.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkLabel(res_frame, text="Width:", anchor="w").grid(
            row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        self.width_var = tk.StringVar(
            value=str(self.config_data['min_resolution']['width']))
        width_entry = self._create_entry(res_frame, self.width_var)
        width_entry.grid(row=0, column=1, sticky="ew", pady=5)
        self.width_var.trace('w', lambda *args: self._save_config())

        ctk.CTkLabel(res_frame, text="Height:", anchor="w").grid(
            row=1, column=0, sticky="w", pady=5, padx=(0, 10))
        self.height_var = tk.StringVar(
            value=str(self.config_data['min_resolution']['height']))
        height_entry = self._create_entry(res_frame, self.height_var)
        height_entry.grid(row=1, column=1, sticky="ew", pady=5)
        self.height_var.trace('w', lambda *args: self._save_config())

        res_frame.columnconfigure(1, weight=1)

        # Post filter section
        self._create_section_label(scrollable_frame, "Post Filter")
        filter_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        filter_frame.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkLabel(filter_frame, text="Sort:", anchor="w").grid(
            row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        self.sort_var = tk.StringVar(
            value=self.config_data['post_filter']['sort'])
        sort_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.sort_var,
            values=['hot', 'new', 'top', 'controversial', 'rising'],
            state='readonly',
            command=lambda _: self._save_config()
        )
        sort_combo.grid(row=0, column=1, sticky="ew", pady=5)

        ctk.CTkLabel(filter_frame, text="Time:", anchor="w").grid(
            row=1, column=0, sticky="w", pady=5, padx=(0, 10))
        self.time_var = tk.StringVar(
            value=self.config_data['post_filter'].get('time_filter', 'month'))
        time_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.time_var,
            values=['hour', 'day', 'week', 'month', 'year', 'all'],
            state='readonly',
            command=lambda _: self._save_config()
        )
        time_combo.grid(row=1, column=1, sticky="ew", pady=5)

        ctk.CTkLabel(filter_frame, text="Limit:", anchor="w").grid(
            row=2, column=0, sticky="w", pady=5, padx=(0, 10))
        self.limit_var = tk.StringVar(
            value=str(self.config_data['post_filter'].get('limit', 100)))
        limit_entry = self._create_entry(filter_frame, self.limit_var)
        limit_entry.grid(row=2, column=1, sticky="ew", pady=5)
        self.limit_var.trace('w', lambda *args: self._save_config())

        ctk.CTkLabel(filter_frame, text="Selection Mode:", anchor="w").grid(
            row=3, column=0, sticky="w", pady=5, padx=(0, 10))
        self.selection_mode_var = tk.StringVar(
            value=self.config_data['post_filter'].get('selection_mode', 'random'))
        selection_mode_combo = ctk.CTkComboBox(
            filter_frame,
            variable=self.selection_mode_var,
            values=['random', 'first'],
            state='readonly',
            command=lambda _: self._save_config()
        )
        selection_mode_combo.grid(row=3, column=1, sticky="ew", pady=5)

        ctk.CTkLabel(filter_frame, text="Retry Count:", anchor="w").grid(
            row=4, column=0, sticky="w", pady=5, padx=(0, 10))
        self.retry_count_var = tk.StringVar(
            value=str(self.config_data['post_filter'].get('retry_count', 5)))
        retry_count_entry = self._create_entry(
            filter_frame, self.retry_count_var)
        retry_count_entry.grid(row=4, column=1, sticky="ew", pady=5)
        self.retry_count_var.trace('w', lambda *args: self._save_config())

        filter_frame.columnconfigure(1, weight=1)

        # Reddit credentials section
        self._create_section_label(scrollable_frame, "Reddit API Credentials")
        cred_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        cred_frame.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkLabel(cred_frame, text="Client ID:", anchor="w").grid(
            row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        self.client_id_var = tk.StringVar(
            value=self.config_data['reddit']['client_id'])
        client_id_entry = self._create_entry(
            cred_frame, self.client_id_var, show="*")
        client_id_entry.grid(row=0, column=1, sticky="ew", pady=5)
        self.client_id_var.trace('w', lambda *args: self._save_config())

        ctk.CTkLabel(cred_frame, text="Client Secret:", anchor="w").grid(
            row=1, column=0, sticky="w", pady=5, padx=(0, 10))
        self.client_secret_var = tk.StringVar(
            value=self.config_data['reddit']['client_secret'])
        client_secret_entry = self._create_entry(
            cred_frame, self.client_secret_var, show="*")
        client_secret_entry.grid(row=1, column=1, sticky="ew", pady=5)
        self.client_secret_var.trace('w', lambda *args: self._save_config())

        cred_frame.columnconfigure(1, weight=1)

        # Cache settings section
        self._create_section_label(scrollable_frame, "Cache Settings")
        cache_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        cache_frame.pack(fill="x", padx=15, pady=(0, 5))

        ctk.CTkLabel(cache_frame, text="Max Cache (MB):", anchor="w").grid(
            row=0, column=0, sticky="w", pady=5, padx=(0, 10))
        self.cache_var = tk.StringVar(
            value=str(self.config_data.get('max_cache_size_mb', 500)))
        cache_entry = self._create_entry(cache_frame, self.cache_var)
        cache_entry.grid(row=0, column=1, sticky="ew", pady=5)
        self.cache_var.trace('w', lambda *args: self._save_config())

        cache_frame.columnconfigure(1, weight=1)

    def _setup_preview_panel(self, parent):
        """Setup preview and control panel."""
        # Title
        title = ctk.CTkLabel(
            parent,
            text="Preview & Control",
            font=("Arial", 16, "bold")
        )
        title.pack(pady=(15, 20), padx=15, anchor="w")

        # Preview area
        preview_container = ctk.CTkFrame(parent, corner_radius=8)
        preview_container.pack(fill="both", expand=True, padx=15, pady=(0, 10))

        self.preview_label = ctk.CTkLabel(
            preview_container,
            text="No wallpaper loaded\n\nClick 'Get Random Wallpaper' to start",
            font=("Arial", 12)
        )
        self.preview_label.pack(fill="both", expand=True, padx=10, pady=10)

        # Info frame
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.info_title = ctk.CTkLabel(
            info_frame,
            text="Title: -",
            anchor="w",
            font=("Arial", 10)
        )
        self.info_title.pack(fill="x", pady=2)

        self.info_subreddit = ctk.CTkLabel(
            info_frame,
            text="Subreddit: -",
            anchor="w",
            font=("Arial", 10)
        )
        self.info_subreddit.pack(fill="x", pady=2)

        self.info_resolution = ctk.CTkLabel(
            info_frame,
            text="Resolution: -",
            anchor="w",
            font=("Arial", 10)
        )
        self.info_resolution.pack(fill="x", pady=2)

        # Control buttons
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(0, 10))

        self.get_btn = ctk.CTkButton(
            button_frame,
            text="Get Random Wallpaper",
            command=self._get_random_wallpaper,
            font=("Arial", 12, "bold"),
            height=40
        )
        self.get_btn.pack(fill="x", pady=(0, 8))

        self.set_btn = ctk.CTkButton(
            button_frame,
            text="Set as Wallpaper",
            command=self._set_wallpaper,
            font=("Arial", 12, "bold"),
            height=40,
            state="disabled",
            fg_color="#4caf50",
            hover_color="#45a047"
        )
        self.set_btn.pack(fill="x", pady=(0, 8))

        # Status area
        status_label = ctk.CTkLabel(
            parent,
            text="Status",
            font=("Arial", 11, "bold"),
            anchor="w"
        )
        status_label.pack(fill="x", padx=15, pady=(10, 8))

        self.status_text = ctk.CTkTextbox(
            parent,
            height=120,
            font=("Courier", 9),
            wrap="word"
        )
        self.status_text.pack(fill="x", padx=15, pady=(0, 15))

        # Set up logging to capture all output in the status window
        self._setup_logging()

    def _create_section_label(self, parent, text):
        """Create a section label."""
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=("Arial", 13, "bold"),
            anchor="w"
        )
        label.pack(fill="x", padx=15, pady=(15, 10))

    def _create_entry(self, parent, textvariable, **kwargs):
        """Create a styled entry widget."""
        entry = ctk.CTkEntry(
            parent,
            textvariable=textvariable,
            **kwargs
        )
        return entry

    def _add_subreddit_entry(self, value="", enabled=True):
        """Add a subreddit entry field with toggle checkbox.

        Args:
            value: Subreddit name
            enabled: Whether the subreddit is enabled
        """
        frame = ctk.CTkFrame(self.subreddit_frame, fg_color="transparent")
        frame.pack(fill="x", pady=3)

        # Checkbox for enabled/disabled state
        enabled_var = tk.BooleanVar(value=enabled)
        checkbox = ctk.CTkCheckBox(
            frame,
            text="",
            variable=enabled_var,
            width=24,
            command=lambda: self._on_subreddit_toggle(entry, enabled_var)
        )
        checkbox.pack(side="left", padx=(0, 8))

        # Text entry for subreddit name
        var = tk.StringVar(value=value)
        entry = self._create_entry(frame, var)
        entry.pack(side="left", fill="x", expand=True)
        var.trace('w', lambda *args: self._save_config())

        # Set initial opacity based on enabled state
        if not enabled:
            entry.configure(text_color=("gray60", "gray50"))

        # Remove button
        remove_btn = ctk.CTkButton(
            frame,
            text="×",
            command=lambda: self._remove_subreddit_entry(
                frame, var, enabled_var),
            width=28,
            height=28,
            fg_color="transparent",
            hover_color=("gray75", "gray25")
        )
        remove_btn.pack(side="right", padx=(8, 0))

        self.subreddit_entries.append((frame, var, enabled_var, entry))

    def _on_subreddit_toggle(self, entry, enabled_var):
        """Handle subreddit checkbox toggle.

        Args:
            entry: The text entry widget
            enabled_var: The BooleanVar for the checkbox
        """
        # Update text color/opacity based on enabled state
        if enabled_var.get():
            entry.configure(text_color=("gray10", "gray90"))
        else:
            entry.configure(text_color=("gray60", "gray50"))

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
            self.config_data['post_filter']['selection_mode'] = self.selection_mode_var.get(
            )
            self.config_data['post_filter']['retry_count'] = int(
                self.retry_count_var.get() or 5)
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
        self.status_text.insert("end", message + "\n")
        self.status_text.see("end")

    def _clear_status(self):
        """Clear the status area."""
        self.status_text.delete("0.0", "end")

    def _setup_logging(self):
        """Set up logging to redirect console output to the status window."""
        # Create a logger for GUI output
        self.logger = logging.getLogger('wallpaper_randomizer_gui')
        self.logger.setLevel(logging.INFO)

        # Remove any existing handlers to avoid duplicates
        self.logger.handlers.clear()

        # Create and add the textbox handler
        textbox_handler = TextboxHandler(self.status_text, self.root)
        textbox_handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(textbox_handler)

        # Also configure the root logger to catch all logging calls
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        # Add our handler to root logger as well
        root_logger.addHandler(textbox_handler)

        # Redirect stdout and stderr to logger
        sys.stdout = StreamRedirector(self.logger, logging.INFO)
        sys.stderr = StreamRedirector(self.logger, logging.ERROR)

    def _get_random_wallpaper(self):
        """Fetch a random wallpaper in background thread."""
        # Disable button during fetch
        self.get_btn.configure(state="disabled", text="Fetching...")
        self.set_btn.configure(state="disabled")
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

            # Create a thread-safe status callback
            def status_callback(message):
                self.root.after(0, lambda msg=message: self._log_status(msg))

            # Fetch wallpaper with retry logic using shared function
            result = fetch_wallpaper_with_retry(
                config=self.config,
                reddit_fetcher=self.reddit_fetcher,
                image_handler=self.image_handler,
                status_callback=status_callback
            )

            if not result:
                self.root.after(0, lambda: self.get_btn.configure(
                    state="normal", text="Get Random Wallpaper"))
                return

            # Success - update UI
            image_path, wallpaper_info = result
            self.current_image_path = image_path
            self.current_wallpaper_info = wallpaper_info

            self.root.after(0, lambda: self._log_status(
                f"✓ Downloaded: {image_path.name}"))
            self.root.after(0, lambda: self._display_preview())
            self.root.after(0, lambda: self.get_btn.configure(
                state="normal", text="Get Random Wallpaper"))
            self.root.after(0, lambda: self.set_btn.configure(state="normal"))

        except Exception as e:
            error_msg = f"❌ Error: {str(e)}"
            self.root.after(0, lambda: self._log_status(error_msg))
            self.root.after(0, lambda: self.get_btn.configure(
                state="normal", text="Get Random Wallpaper"))

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

            # Convert to CTkImage for HighDPI support
            self.preview_photo = ctk.CTkImage(
                light_image=img_resized,
                dark_image=img_resized,
                size=(new_width, new_height)
            )

            # Update label
            self.preview_label.configure(image=self.preview_photo, text="")

            # Update info labels
            if self.current_wallpaper_info:
                self.info_title.configure(
                    text=f"Title: {self.current_wallpaper_info['title'][:60]}")
                self.info_subreddit.configure(
                    text=f"Subreddit: r/{self.current_wallpaper_info['subreddit']}")
            else:
                self.info_title.configure(
                    text=f"File: {self.current_image_path.name}")
                self.info_subreddit.configure(text="Subreddit: -")

            self.info_resolution.configure(
                text=f"Resolution: {img.width}x{img.height}")

        except Exception as e:
            self._log_status(f"❌ Error displaying preview: {e}")

    def _set_wallpaper(self):
        """Set the current image as wallpaper."""
        if not self.current_image_path:
            messagebox.showwarning(
                "No Image", "Please fetch a wallpaper first")
            return

        self.set_btn.configure(state="disabled", text="Setting...")
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

            self.root.after(0, lambda: self.set_btn.configure(
                state="normal", text="Set as Wallpaper"))

        except Exception as e:
            error_msg = f"❌ Error setting wallpaper: {str(e)}"
            self.root.after(0, lambda: self._log_status(error_msg))
            self.root.after(0, lambda: self.set_btn.configure(
                state="normal", text="Set as Wallpaper"))

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
