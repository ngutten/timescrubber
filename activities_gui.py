"""
Activities Screen GUI for Timescrubber

This module displays the Activities screen where players can
start tasks and processes.
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING

from gamestate import GameState
from gamedefs import (
    get_activity_names,
    get_activity_description,
    get_activity_requirements,
    get_activity_by_displayname,
    format_requirements,
    format_consumed_produced,
    make_activity_task,
    get_unlocked_activities
)
from variable import LinearVariable

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

        self._displayed_activities = []

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

        activity_name = self.activities_list.get(selection[0])
        activity = get_activity_by_displayname(activity_name)
        if not activity:
            return

        self.details_header.configure(text=activity["displayname"])

        # Update details with description and resource effects
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)

        description = get_activity_description(activity_name)
        resource_effects = format_consumed_produced(activity)

        # Add duration estimate
        rate = activity.get("rate", 10)
        duration = 100 / rate if rate > 0 else float('inf')

        full_text = f"{description}\n\n"
        full_text += f"Duration: ~{duration:.1f} time units\n\n"
        full_text += f"{resource_effects}"

        self.details_text.insert("1.0", full_text)
        self.details_text.configure(state="disabled")

        # Update requirements
        reqs = get_activity_requirements(activity_name)
        self.requirements_label.configure(text=format_requirements(reqs))

    def _start_activity(self):
        """Start the selected activity as a Task on the timeline."""
        selection = self.activities_list.curselection()
        if not selection:
            return

        activity_name = self.activities_list.get(selection[0])

        # Check if requirements are met
        if not self._can_start_activity(activity_name):
            print(f"Cannot start {activity_name}: requirements not met")
            return

        # Create the task at the current time
        current_time = self.app.current_time
        ts = self.gamestate.timeline.state_at(current_time)
        task = make_activity_task(activity_name, current_time, ts)

        if task:
            # Add the task to the timeline
            self.gamestate.timeline.add_event(task)
            print(f"Started activity: {activity_name} at t={current_time}")
            # Display updates automatically on next update loop
        else:
            print(f"Failed to create task for: {activity_name}")

    def _can_start_activity(self, activity_name: str) -> bool:
        """Check if an activity can be started based on current resources."""
        activity = get_activity_by_displayname(activity_name)
        if not activity:
            return False

        requirements = activity.get("requirements", {})
        current_time = self.app.current_time
        ts = self.gamestate.timeline.state_at(current_time)

        # Check requirements
        for var_name, amount in requirements.items():
            var = ts.get_variable(var_name)
            if not var:
                return False
            if isinstance(var, LinearVariable):
                if var.get(current_time) < amount:
                    return False
            else:
                if var.get(current_time) < amount:
                    return False

        # Check that the task isn't already running (uniqueness)
        internal_name = activity.get("name", "")
        if ts.get_variable(internal_name + "_progress"):
            return False

        return True

    def update_display(self, current_time: float):
        """Update the activities display based on what's unlocked at current time."""
        ts = self.gamestate.timeline.state_at(current_time)
 
        # Get currently unlocked activities (time-aware)
        unlocked = get_unlocked_activities(ts)
        unlocked_names = [a["displayname"] for a in unlocked]
 
        # Only refresh list if the set of unlocked activities changed
        if unlocked_names != self._displayed_activities:
            # Remember current selection
            selection = self.activities_list.curselection()
            selected_name = None
            if selection:
                selected_name = self.activities_list.get(selection[0])
 
            # Rebuild the list
            self.activities_list.delete(0, tk.END)
            for name in unlocked_names:
                self.activities_list.insert(tk.END, name)
            self._displayed_activities = unlocked_names
 
            # Restore selection if the activity is still in the list
            if selected_name and selected_name in unlocked_names:
                idx = unlocked_names.index(selected_name)
                self.activities_list.selection_set(idx)
 
        # Update each activity's availability status (can start vs locked)
        for i in range(self.activities_list.size()):
            activity_name = self.activities_list.get(i)
            if self._can_start_activity(activity_name):
                self.activities_list.itemconfig(i, fg="black")
            else:
                self.activities_list.itemconfig(i, fg="gray")
