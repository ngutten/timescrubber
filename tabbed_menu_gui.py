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

        # Import and create screens
        from activities_gui import ActivitiesScreen

        # Activities tab (implemented)
        self.activities = ActivitiesScreen(self.notebook, self.gamestate, self.app)
        self.notebook.add(self.activities, text="Activities")
        self.screens["activities"] = self.activities

        # Upgrades tab (placeholder)
        self.upgrades = self._create_placeholder("Upgrades",
            "Upgrade your abilities and tools to become more efficient.\n\n"
            "Upgrades are permanent improvements that persist across runs.")
        self.notebook.add(self.upgrades, text="Upgrades")
        self.screens["upgrades"] = self.upgrades

        # Nexus Upgrades tab (placeholder)
        self.nexus = self._create_placeholder("Nexus Upgrades",
            "Meta-progression upgrades that affect all timelines.\n\n"
            "Nexus upgrades are earned through special achievements and milestones.")
        self.notebook.add(self.nexus, text="Nexus")
        self.screens["nexus"] = self.nexus

        # Research tab (placeholder)
        self.research = self._create_placeholder("Research",
            "Unlock new technologies and abilities through research.\n\n"
            "Research requires Insights and time to complete.")
        self.notebook.add(self.research, text="Research")
        self.screens["research"] = self.research

        # World Map tab (placeholder)
        self.world_map = self._create_placeholder("World Map",
            "Explore the world and discover new locations.\n\n"
            "Each location offers unique resources and challenges.")
        self.notebook.add(self.world_map, text="Map")
        self.screens["map"] = self.world_map

        # Site Development tab (placeholder)
        self.site = self._create_placeholder("Site Development",
            "Develop your current location with buildings and improvements.\n\n"
            "Buildings provide bonuses and unlock new activities.")
        self.notebook.add(self.site, text="Site")
        self.screens["site"] = self.site

        # Events tab (placeholder)
        self.events = self._create_placeholder("Events Log",
            "View the history of events that have occurred on the timeline.\n\n"
            "Events can be reviewed and some can be modified or undone.")
        self.notebook.add(self.events, text="Events")
        self.screens["events"] = self.events

        # Achievements tab (placeholder)
        self.achievements = self._create_placeholder("Achievements",
            "Track your accomplishments and unlock rewards.\n\n"
            "Achievements provide bonuses and unlock new content.")
        self.notebook.add(self.achievements, text="Achievements")
        self.screens["achievements"] = self.achievements

        # Configuration tab (placeholder)
        self.config = self._create_config_placeholder()
        self.notebook.add(self.config, text="Settings")
        self.screens["config"] = self.config

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
        self.autosave_var = tk.BooleanVar(value=True)
        autosave_check = ttk.Checkbutton(game_frame, text="Auto-save enabled",
                                         variable=self.autosave_var)
        autosave_check.grid(row=0, column=0, sticky="w")

        # Notifications toggle
        self.notifications_var = tk.BooleanVar(value=True)
        notifications_check = ttk.Checkbutton(game_frame, text="Show notifications",
                                              variable=self.notifications_var)
        notifications_check.grid(row=1, column=0, sticky="w")

        # Display settings section
        display_frame = ttk.LabelFrame(frame, text="Display Settings", padding=10)
        display_frame.grid(row=2, column=0, sticky="ew", pady=(0, 10))

        # Theme selection (placeholder)
        ttk.Label(display_frame, text="Theme:").grid(row=0, column=0, sticky="w")
        self.theme_var = tk.StringVar(value="Default")
        theme_combo = ttk.Combobox(display_frame, textvariable=self.theme_var,
                                   values=["Default", "Dark", "Light"],
                                   state="readonly", width=15)
        theme_combo.grid(row=0, column=1, sticky="w", padx=(10, 0))

        # Number format
        ttk.Label(display_frame, text="Number format:").grid(row=1, column=0, sticky="w")
        self.number_format_var = tk.StringVar(value="Standard")
        format_combo = ttk.Combobox(display_frame, textvariable=self.number_format_var,
                                    values=["Standard", "Scientific", "Engineering"],
                                    state="readonly", width=15)
        format_combo.grid(row=1, column=1, sticky="w", padx=(10, 0))

        # About section
        about_frame = ttk.LabelFrame(frame, text="About", padding=10)
        about_frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        about_text = (
            "Timescrubber - A Non-Linear Time Idle Game\n"
            "Version: 0.1.0 (Development)\n\n"
            "A timeline-based idle game where you can manipulate time "
            "and observe how changes cascade through history."
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
        # Other screens would update here when implemented

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
