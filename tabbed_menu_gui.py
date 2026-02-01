"""
Tabbed Menu GUI for Timescrubber

This module contains the code for the tabbed menu that selects between various screens:
- Activities
- Upgrades
- Nexus Upgrades
- Research
- World Map
- Site Development
- Events
- Achievements
- Configuration
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, TYPE_CHECKING

from gamestate import GameState
from gamedefs import SCREENS, SETTINGS, GAME_INFO, get_screen_by_key

if TYPE_CHECKING:
    from app_gui import TimescrubberApp


class TabbedMenu(ttk.Frame):
    """Main content area with tabbed navigation."""

    def __init__(self, parent, gamestate: GameState, app: "TimescrubberApp"):
        super().__init__(parent)
        self.gamestate = gamestate
        self.app = app
        self.screens: Dict[str, ttk.Frame] = {}

        self._create_widgets()

    def _create_widgets(self):
        """Create the tabbed interface."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        # Import screens with custom implementations
        from activities_gui import ActivitiesScreen
        from upgrades_gui import UpgradesScreen, NexusScreen
        from research_gui import ResearchScreen

        # Create tabs from SCREENS definitions
        for screen_def in SCREENS:
            key = screen_def["key"]
            tab_text = screen_def["tab_text"]
            title = screen_def["title"]
            description = screen_def["description"]

            if key == "activities":
                # Activities has custom implementation
                frame = ActivitiesScreen(self.notebook, self.gamestate, self.app)
                self.activities = frame
            elif key == "upgrades":
                # Upgrades screen
                frame = UpgradesScreen(self.notebook, self.gamestate, self.app)
                self.upgrades = frame
            elif key == "nexus":
                # Nexus meta-progression screen
                frame = NexusScreen(self.notebook, self.gamestate, self.app)
                self.nexus = frame
            elif key == "research":
                # Research tree screen
                frame = ResearchScreen(self.notebook, self.gamestate, self.app)
                self.research = frame
            elif key == "config":
                # Config has custom implementation
                frame = self._create_config_placeholder()
                self.config = frame
            else:
                # Use placeholder for other screens
                frame = self._create_placeholder(title, description)
                setattr(self, key, frame)

            self.notebook.add(frame, text=tab_text)
            self.screens[key] = frame

    def _create_placeholder(self, title: str, description: str) -> ttk.Frame:
        """Create a placeholder screen with a title and description."""
        frame = ttk.Frame(self.notebook, padding=20)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(1, weight=1)

        # Title
        title_label = ttk.Label(frame, text=title,
                                font=("TkDefaultFont", 16, "bold"))
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Description
        desc_frame = ttk.Frame(frame)
        desc_frame.grid(row=1, column=0, sticky="nsew")

        desc_label = ttk.Label(desc_frame, text=description,
                               wraplength=500, justify="left",
                               foreground="gray")
        desc_label.pack(anchor="nw")

        # Placeholder indicator
        placeholder = ttk.Label(desc_frame, text="\n[Screen not yet implemented]",
                                foreground="#999999", font=("TkDefaultFont", 10, "italic"))
        placeholder.pack(anchor="nw", pady=(20, 0))

        return frame

    def _create_config_placeholder(self) -> ttk.Frame:
        """Create a configuration placeholder with some functional options."""
        frame = ttk.Frame(self.notebook, padding=20)
        frame.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ttk.Label(frame, text="Settings",
                                font=("TkDefaultFont", 16, "bold"))
        title_label.grid(row=0, column=0, sticky="w", pady=(0, 20))

        # Game settings section
        game_frame = ttk.LabelFrame(frame, text="Game Settings", padding=10)
        game_frame.grid(row=1, column=0, sticky="ew", pady=(0, 10))

        # Auto-save toggle
        autosave_def = SETTINGS["autosave"]
        self.autosave_var = tk.BooleanVar(value=autosave_def["default"])
        autosave_check = ttk.Checkbutton(game_frame, text=autosave_def["label"],
                                         variable=self.autosave_var)
        autosave_check.grid(row=0, column=0, sticky="w")

        # Notifications toggle
        notif_def = SETTINGS["notifications"]
        self.notifications_var = tk.BooleanVar(value=notif_def["default"])
        notifications_check = ttk.Checkbutton(game_frame, text=notif_def["label"],
                                              variable=self.notifications_var)
        notifications_check.grid(row=1, column=0, sticky="w")

        # Display settings section
        display_frame = ttk.LabelFrame(frame, text="Display Settings", padding=10)
        display_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Theme selection
        theme_def = SETTINGS["theme"]
        ttk.Label(display_frame, text=f"{theme_def['label']}:").grid(row=0, column=0, sticky="w")
        self.theme_var = tk.StringVar(value=theme_def["default"])
        theme_combo = ttk.Combobox(display_frame, textvariable=self.theme_var,
                                   values=theme_def["options"],
                                   state="readonly", width=15)
        theme_combo.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Number format
        format_def = SETTINGS["number_format"]
        ttk.Label(display_frame, text=f"{format_def['label']}:").grid(row=1, column=0, sticky="w")
        self.number_format_var = tk.StringVar(value=format_def["default"])
        format_combo = ttk.Combobox(display_frame, textvariable=self.number_format_var,
                                    values=format_def["options"],
                                    state="readonly", width=15)
        format_combo.grid(row=1, column=1, sticky="w", padx=(10, 0))

        # About section
        about_frame = ttk.LabelFrame(frame, text="About", padding=10)
        about_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        about_text = (
            f"{GAME_INFO['name']} - {GAME_INFO['subtitle']}\n"
            f"Version: {GAME_INFO['version']}\n\n"
            f"{GAME_INFO['description']}"
        )
        ttk.Label(about_frame, text=about_text, wraplength=400,
                  justify="left").grid(row=0, column=0, sticky="w")

        # Placeholder indicator
        placeholder = ttk.Label(frame, text="[Most settings are placeholders]",
                                foreground="#999999", font=("TkDefaultFont", 10, "italic"))
        placeholder.grid(row=4, column=0, sticky="w", pady=(10, 0))

        return frame

    def update_display(self, current_time: float):
        """Update the currently visible screen."""
        # Get current tab
        current_tab = self.notebook.index(self.notebook.select())
        tab_name = self.notebook.tab(current_tab, "text")

        # Update the appropriate screen
        if tab_name == "Activities":
            self.activities.update_display(current_time)
        elif tab_name == "Upgrades":
            self.upgrades.update_display(current_time)
        elif tab_name == "Nexus":
            self.nexus.update_display(current_time)
        elif tab_name == "Research":
            self.research.update_display(current_time)

    def select_tab(self, tab_name: str):
        """Programmatically select a tab by name."""
        tab_names = {
            "activities": 0,
            "upgrades": 1,
            "nexus": 2,
            "research": 3,
            "map": 4,
            "site": 5,
            "events": 6,
            "achievements": 7,
            "config": 8,
        }
        if tab_name.lower() in tab_names:
            self.notebook.select(tab_names[tab_name.lower()])
