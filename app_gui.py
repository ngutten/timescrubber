"""
Main GUI Application for Timescrubber

This module creates the main application window and coordinates all GUI components.
Uses tkinter for the interface.
"""

import tkinter as tk
from tkinter import ttk
from typing import Optional

from gamestate import GameState
from timeline import TimeState, Timeline
from variable import Variable, LinearVariable


class TimescrubberApp:
    """Main application class that creates and manages the GUI."""

    def __init__(self, gamestate: GameState):
        self.gamestate = gamestate
        self.current_time = 0.0
        self.time_scale = 1.0  # How fast time passes (1.0 = real-time)
        self.paused = True

        # Create main window
        self.root = tk.Tk()
        self.root.title("Timescrubber")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)

        # Configure grid weights for resizing
        self.root.grid_columnconfigure(0, weight=0)  # Side panel - fixed width
        self.root.grid_columnconfigure(1, weight=1)  # Main content - expandable
        self.root.grid_rowconfigure(0, weight=1)     # Main area
        self.root.grid_rowconfigure(1, weight=0)     # Timeline - fixed height

        self._create_widgets()
        self._start_update_loop()

    def _create_widgets(self):
        """Create all GUI widgets."""
        # Import GUI components here to avoid circular imports
        from panel_gui import ResourcePanel
        from timeline_gui import TimelinePanel
        from tabbed_menu_gui import TabbedMenu

        # Left side panel (resources and active tasks)
        self.side_panel = ResourcePanel(self.root, self.gamestate, self)
        self.side_panel.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        # Main content area with tabbed menu
        self.main_content = TabbedMenu(self.root, self.gamestate, self)
        self.main_content.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)

        # Bottom timeline visualization
        self.timeline_panel = TimelinePanel(self.root, self.gamestate, self)
        self.timeline_panel.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)

    def _start_update_loop(self):
        """Start the periodic update loop."""
        self._update()

    def _update(self):
        """Update the game state and GUI periodically."""
        if not self.paused:
            # Advance time
            self.current_time += 0.1 * self.time_scale

            # Extend max_time if needed
            if self.current_time > self.gamestate.timeline.max_time - 10:
                self.gamestate.timeline.change_max_time(self.current_time + 100)

        # Update all panels
        self.side_panel.update_display(self.current_time)
        self.timeline_panel.update_display(self.current_time)
        self.main_content.update_display(self.current_time)

        # Schedule next update (100ms = 10 updates per second)
        self.root.after(100, self._update)

    def toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused

    def set_time(self, t: float):
        """Set the current time (for timeline scrubbing)."""
        self.current_time = max(0, t)

    def run(self):
        """Start the main event loop."""
        self.root.mainloop()


def create_app(gamestate: GameState) -> TimescrubberApp:
    """Factory function to create the application."""
    return TimescrubberApp(gamestate)
