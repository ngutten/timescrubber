"""
Resource Panel GUI for Timescrubber

This module displays resource values and rates (upper part) and
active tasks/processes (lower part) in a side panel.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, Optional, TYPE_CHECKING

from variable import Variable, LinearVariable
from gamestate import GameState

if TYPE_CHECKING:
    from app_gui import TimescrubberApp


class ResourcePanel(ttk.Frame):
    """Side panel showing resources and active tasks."""

    def __init__(self, parent, gamestate: GameState, app: "TimescrubberApp"):
        super().__init__(parent, width=250)
        self.gamestate = gamestate
        self.app = app
        self.resource_labels: Dict[str, Dict[str, ttk.Label]] = {}
        self.task_labels: Dict[str, ttk.Label] = {}

        # Prevent the frame from shrinking
        self.grid_propagate(False)
        self.configure(width=250)

        self._create_widgets()

    def _create_widgets(self):
        """Create the panel widgets."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Resources section
        self.grid_rowconfigure(3, weight=1)  # Tasks section

        # Time display and controls
        time_frame = ttk.LabelFrame(self, text="Time", padding=5)
        time_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        time_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(time_frame, text="Current:").grid(row=0, column=0, sticky="w")
        self.time_label = ttk.Label(time_frame, text="0.00")
        self.time_label.grid(row=0, column=1, sticky="e")

        # Pause/Play button
        self.pause_btn = ttk.Button(time_frame, text="Play", command=self._toggle_pause)
        self.pause_btn.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(5, 0))

        # Speed control
        speed_frame = ttk.Frame(time_frame)
        speed_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        speed_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(speed_frame, text="Speed:").grid(row=0, column=0, sticky="w")
        self.speed_var = tk.DoubleVar(value=1.0)
        speed_scale = ttk.Scale(speed_frame, from_=0.1, to=10.0,
                                variable=self.speed_var, orient="horizontal",
                                command=self._on_speed_change)
        speed_scale.grid(row=0, column=1, sticky="ew", padx=(5, 0))
        self.speed_label = ttk.Label(speed_frame, text="1.0x")
        self.speed_label.grid(row=0, column=2, padx=(5, 0))

        # Resources section
        resources_frame = ttk.LabelFrame(self, text="Resources", padding=5)
        resources_frame.grid(row=1, column=0, sticky="nsew", pady=5)
        resources_frame.grid_columnconfigure(0, weight=1)

        # Create scrollable area for resources
        self.resources_canvas = tk.Canvas(resources_frame, highlightthickness=0)
        resources_scrollbar = ttk.Scrollbar(resources_frame, orient="vertical",
                                            command=self.resources_canvas.yview)
        self.resources_inner = ttk.Frame(self.resources_canvas)

        self.resources_canvas.configure(yscrollcommand=resources_scrollbar.set)

        resources_scrollbar.pack(side="right", fill="y")
        self.resources_canvas.pack(side="left", fill="both", expand=True)
        self.resources_window = self.resources_canvas.create_window(
            (0, 0), window=self.resources_inner, anchor="nw"
        )

        self.resources_inner.bind("<Configure>", self._on_resources_configure)
        self.resources_canvas.bind("<Configure>", self._on_canvas_configure)

        # Active Tasks section
        tasks_frame = ttk.LabelFrame(self, text="Active Tasks", padding=5)
        tasks_frame.grid(row=2, column=0, sticky="nsew", pady=5)
        tasks_frame.grid_columnconfigure(0, weight=1)
        tasks_frame.grid_rowconfigure(0, weight=1)

        # Create scrollable area for tasks
        self.tasks_canvas = tk.Canvas(tasks_frame, highlightthickness=0, height=150)
        tasks_scrollbar = ttk.Scrollbar(tasks_frame, orient="vertical",
                                        command=self.tasks_canvas.yview)
        self.tasks_inner = ttk.Frame(self.tasks_canvas)

        self.tasks_canvas.configure(yscrollcommand=tasks_scrollbar.set)

        tasks_scrollbar.pack(side="right", fill="y")
        self.tasks_canvas.pack(side="left", fill="both", expand=True)
        self.tasks_window = self.tasks_canvas.create_window(
            (0, 0), window=self.tasks_inner, anchor="nw"
        )

        self.tasks_inner.bind("<Configure>", self._on_tasks_configure)

        # Initialize resource display
        self._init_resources()

    def _on_resources_configure(self, event):
        """Update scroll region when resources frame changes."""
        self.resources_canvas.configure(scrollregion=self.resources_canvas.bbox("all"))

    def _on_tasks_configure(self, event):
        """Update scroll region when tasks frame changes."""
        self.tasks_canvas.configure(scrollregion=self.tasks_canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        """Resize inner frame when canvas is resized."""
        self.resources_canvas.itemconfig(self.resources_window, width=event.width)

    def _toggle_pause(self):
        """Toggle pause state."""
        self.app.toggle_pause()
        self.pause_btn.configure(text="Pause" if not self.app.paused else "Play")

    def _on_speed_change(self, value):
        """Handle speed slider change."""
        speed = float(value)
        self.app.time_scale = speed
        self.speed_label.configure(text=f"{speed:.1f}x")

    def _init_resources(self):
        """Initialize resource labels from initial state."""
        initial_state = self.gamestate.timeline.initial
        row = 0

        for name in initial_state.registry.keys():
            var = initial_state.registry.get_variable(name)

            # Create frame for this resource
            res_frame = ttk.Frame(self.resources_inner)
            res_frame.grid(row=row, column=0, sticky="ew", pady=2)
            res_frame.grid_columnconfigure(1, weight=1)

            # Resource name
            name_label = ttk.Label(res_frame, text=var.displayname or var.name,
                                   font=("TkDefaultFont", 9, "bold"))
            name_label.grid(row=0, column=0, sticky="w")

            # Value label
            value_label = ttk.Label(res_frame, text="0.00")
            value_label.grid(row=0, column=1, sticky="e")

            # Rate label (for LinearVariables)
            rate_label = None
            if isinstance(var, LinearVariable):
                rate_label = ttk.Label(res_frame, text="", foreground="gray")
                rate_label.grid(row=1, column=0, columnspan=2, sticky="e")

            # Progress bar for bounded resources
            progress = None
            if isinstance(var, LinearVariable) and var.max < 10000:
                progress = ttk.Progressbar(res_frame, length=200, mode="determinate")
                progress.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(2, 0))

            self.resource_labels[name] = {
                "value": value_label,
                "rate": rate_label,
                "progress": progress,
                "var": var
            }

            row += 1

    def update_display(self, current_time: float):
        """Update the display with current values."""
        # Update time display
        self.time_label.configure(text=f"{current_time:.2f}")

        # Get current state
        state = self.gamestate.timeline.state_at(current_time)

        # Update resource values
        for name, labels in self.resource_labels.items():
            try:
                var = state.registry.get_variable(name)
                value = var.get(current_time)

                # Format value display
                if abs(value) >= 1000:
                    value_str = f"{value:.0f}"
                elif abs(value) >= 100:
                    value_str = f"{value:.1f}"
                else:
                    value_str = f"{value:.2f}"

                labels["value"].configure(text=value_str)

                # Update rate display
                if labels["rate"] is not None and isinstance(var, LinearVariable):
                    rate = var.rate
                    if rate > 0:
                        rate_str = f"+{rate:.2f}/s"
                        labels["rate"].configure(text=rate_str, foreground="green")
                    elif rate < 0:
                        rate_str = f"{rate:.2f}/s"
                        labels["rate"].configure(text=rate_str, foreground="red")
                    else:
                        labels["rate"].configure(text="")

                # Update progress bar
                if labels["progress"] is not None and isinstance(var, LinearVariable):
                    if var.max > var.min:
                        percent = (value - var.min) / (var.max - var.min) * 100
                        labels["progress"]["value"] = percent

            except KeyError:
                pass  # Variable doesn't exist at this time

        # Update active tasks display
        self._update_tasks(state, current_time)

    def _update_tasks(self, state, current_time: float):
        """Update the active tasks display."""
        # Clear existing task labels
        for widget in self.tasks_inner.winfo_children():
            widget.destroy()
        self.task_labels.clear()

        # Find progress variables (tasks in progress)
        row = 0
        for name in state.registry.keys():
            if name.endswith("_progress"):
                var = state.registry.get_variable(name)
                if isinstance(var, LinearVariable):
                    task_name = name.replace("_progress", "")
                    progress = var.get(current_time)

                    # Task frame
                    task_frame = ttk.Frame(self.tasks_inner)
                    task_frame.grid(row=row, column=0, sticky="ew", pady=2)
                    task_frame.grid_columnconfigure(0, weight=1)

                    # Task name
                    ttk.Label(task_frame, text=task_name).grid(row=0, column=0, sticky="w")

                    # Progress percentage
                    ttk.Label(task_frame, text=f"{progress:.1f}%").grid(row=0, column=1, sticky="e")

                    # Progress bar
                    prog_bar = ttk.Progressbar(task_frame, length=200, mode="determinate")
                    prog_bar["value"] = min(progress, 100)
                    prog_bar.grid(row=1, column=0, columnspan=2, sticky="ew")

                    row += 1

        if row == 0:
            ttk.Label(self.tasks_inner, text="No active tasks",
                      foreground="gray").grid(row=0, column=0)
