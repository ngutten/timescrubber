"""
Activities Screen GUI for Timescrubber

This module displays the Activities screen where players can
start tasks and processes.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Dict, TYPE_CHECKING

from gamestate import GameState

if TYPE_CHECKING:
    from app_gui import TimescrubberApp


class ActivitiesScreen(ttk.Frame):
    """Activities screen showing available tasks and activities."""

    def __init__(self, parent, gamestate: GameState, app: "TimescrubberApp"):
        super().__init__(parent)
        self.gamestate = gamestate
        self.app = app

        self._create_widgets()

    def _create_widgets(self):
        """Create activities screen widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ttk.Label(self, text="Activities",
                          font=("TkDefaultFont", 14, "bold"))
        header.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Main content frame
        content = ttk.Frame(self)
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)

        # Available Activities section
        available_frame = ttk.LabelFrame(content, text="Available Activities", padding=10)
        available_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        available_frame.grid_columnconfigure(0, weight=1)

        # Placeholder activities list
        self.activities_list = tk.Listbox(available_frame, height=15)
        self.activities_list.grid(row=0, column=0, sticky="nsew")

        activities_scroll = ttk.Scrollbar(available_frame, orient="vertical",
                                          command=self.activities_list.yview)
        activities_scroll.grid(row=0, column=1, sticky="ns")
        self.activities_list.configure(yscrollcommand=activities_scroll.set)

        # Add some placeholder activities
        placeholder_activities = [
            "Rest (Recover Stamina)",
            "Gather Wood",
            "Gather Stone",
            "Craft Basic Tools",
            "Build Shelter",
            "Explore Area",
            "Meditate (Gain Insights)",
            "Study",
        ]
        for activity in placeholder_activities:
            self.activities_list.insert(tk.END, activity)

        # Start button
        start_btn = ttk.Button(available_frame, text="Start Activity",
                               command=self._start_activity)
        start_btn.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))

        # Activity Details section
        details_frame = ttk.LabelFrame(content, text="Activity Details", padding=10)
        details_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_rowconfigure(1, weight=1)

        # Details header
        self.details_header = ttk.Label(details_frame, text="Select an activity",
                                        font=("TkDefaultFont", 11, "bold"))
        self.details_header.grid(row=0, column=0, sticky="w")

        # Details text
        self.details_text = tk.Text(details_frame, height=10, width=40, wrap="word",
                                    state="disabled", bg="#f0f0f0")
        self.details_text.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        # Requirements section
        req_frame = ttk.LabelFrame(details_frame, text="Requirements", padding=5)
        req_frame.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.requirements_label = ttk.Label(req_frame, text="None",
                                            foreground="gray")
        self.requirements_label.grid(row=0, column=0, sticky="w")

        # Bind selection event
        self.activities_list.bind("<<ListboxSelect>>", self._on_select)

    def _on_select(self, event):
        """Handle activity selection."""
        selection = self.activities_list.curselection()
        if not selection:
            return

        activity = self.activities_list.get(selection[0])
        self.details_header.configure(text=activity)

        # Update details (placeholder text)
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", self._get_activity_description(activity))
        self.details_text.configure(state="disabled")

        # Update requirements
        self.requirements_label.configure(
            text=self._get_activity_requirements(activity)
        )

    def _get_activity_description(self, activity: str) -> str:
        """Get placeholder description for an activity."""
        descriptions = {
            "Rest (Recover Stamina)": "Take a break and recover your stamina. "
                "Stamina is essential for performing most activities.",
            "Gather Wood": "Collect wood from nearby trees. "
                "Wood is a basic resource used in many crafting recipes.",
            "Gather Stone": "Search for and collect stone. "
                "Stone is needed for tools and building structures.",
            "Craft Basic Tools": "Create simple tools to improve efficiency. "
                "Tools make gathering and building faster.",
            "Build Shelter": "Construct a basic shelter for protection. "
                "Shelters provide bonuses to resting and storage.",
            "Explore Area": "Scout the surrounding area to discover new locations "
                "and resources.",
            "Meditate (Gain Insights)": "Quiet contemplation to gain insights. "
                "Insights are used for research and upgrades.",
            "Study": "Study your surroundings and acquired knowledge to unlock "
                "new abilities and understanding.",
        }
        return descriptions.get(activity, "No description available.")

    def _get_activity_requirements(self, activity: str) -> str:
        """Get placeholder requirements for an activity."""
        requirements = {
            "Rest (Recover Stamina)": "None",
            "Gather Wood": "Stamina: 2",
            "Gather Stone": "Stamina: 3",
            "Craft Basic Tools": "Wood: 5, Stone: 2",
            "Build Shelter": "Wood: 20, Stone: 10",
            "Explore Area": "Stamina: 5",
            "Meditate (Gain Insights)": "Stamina: 1",
            "Study": "Insights: 5",
        }
        return requirements.get(activity, "Unknown")

    def _start_activity(self):
        """Start the selected activity (placeholder)."""
        selection = self.activities_list.curselection()
        if not selection:
            return

        activity = self.activities_list.get(selection[0])
        # In a full implementation, this would create and add an event
        print(f"Starting activity: {activity}")

    def update_display(self, current_time: float):
        """Update the activities display."""
        # In a full implementation, this would update availability
        # based on current resources and state
        pass
