"""
Timeline Panel GUI for Timescrubber

This module displays the timeline visualization showing events
and allows the user to scrub through time.
"""

import tkinter as tk
from tkinter import ttk
from typing import List, Tuple, Optional, TYPE_CHECKING

from gamestate import GameState
from timeline import Event, Process, Task, ProcessEnd, TaskComplete, TaskInterrupt

if TYPE_CHECKING:
    from app_gui import TimescrubberApp


class TimelinePanel(ttk.Frame):
    """Bottom panel showing the timeline with events."""

    # Visual constants
    TIMELINE_HEIGHT = 100
    MARKER_HEIGHT = 40
    EVENT_HEIGHT = 20
    PADDING = 20
    BAR_HEIGHT = 8  # Height of each process/task bar
    BAR_SPACING = 10  # Vertical spacing between overlapping bars

    def __init__(self, parent, gamestate: GameState, app: "TimescrubberApp"):
        super().__init__(parent)
        self.gamestate = gamestate
        self.app = app

        # Timeline view settings
        self.view_start = 0.0      # Left edge of visible timeline
        self.view_duration = 100.0  # How much time is visible
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_time = 0.0

        # Event tracking for hover/click
        self.event_hitboxes = []  # List of (x1, y1, x2, y2, event) for click detection
        self.hovered_event = None
        self.popup_window = None

        self._create_widgets()
        self._bind_events()

    def _create_widgets(self):
        """Create timeline widgets."""
        self.grid_columnconfigure(0, weight=1)

        # Control bar
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        controls.grid_columnconfigure(3, weight=1)

        ttk.Label(controls, text="Timeline").grid(row=0, column=0, sticky="w")

        # Zoom controls
        ttk.Button(controls, text="-", width=3,
                   command=self._zoom_out).grid(row=0, column=1, padx=(10, 2))
        ttk.Button(controls, text="+", width=3,
                   command=self._zoom_in).grid(row=0, column=2, sticky="w")

        # Clear future events button
        ttk.Button(controls, text="Clear Future",
                   command=self._clear_future_events).grid(row=0, column=3, padx=(10, 0))

        # View range label
        self.range_label = ttk.Label(controls, text="View: 0 - 100")
        self.range_label.grid(row=0, column=4, sticky="e", padx=(10, 0))

        # Canvas for timeline
        self.canvas = tk.Canvas(
            self,
            height=self.TIMELINE_HEIGHT,
            bg="white",
            highlightthickness=1,
            highlightbackground="gray"
        )
        self.canvas.grid(row=1, column=0, sticky="ew")

    def _bind_events(self):
        """Bind mouse events for interaction."""
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<MouseWheel>", self._on_scroll)
        self.canvas.bind("<Button-4>", self._on_scroll)  # Linux scroll up
        self.canvas.bind("<Button-5>", self._on_scroll)  # Linux scroll down
        self.canvas.bind("<Configure>", self._on_resize)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-3>", self._on_right_click)  # Right-click

    def _time_to_x(self, t: float) -> float:
        """Convert time to canvas x coordinate."""
        width = self.canvas.winfo_width() - 2 * self.PADDING
        if self.view_duration <= 0:
            return self.PADDING
        return self.PADDING + (t - self.view_start) / self.view_duration * width

    def _x_to_time(self, x: float) -> float:
        """Convert canvas x coordinate to time."""
        width = self.canvas.winfo_width() - 2 * self.PADDING
        if width <= 0:
            return self.view_start
        return self.view_start + (x - self.PADDING) / width * self.view_duration

    def _zoom_in(self):
        """Zoom in on the timeline."""
        center = self.view_start + self.view_duration / 2
        self.view_duration = max(10, self.view_duration * 0.7)
        self.view_start = center - self.view_duration / 2
        self._clamp_view()

    def _zoom_out(self):
        """Zoom out on the timeline."""
        center = self.view_start + self.view_duration / 2
        self.view_duration = min(1000, self.view_duration * 1.4)
        self.view_start = center - self.view_duration / 2
        self._clamp_view()

    def _clamp_view(self):
        """Ensure view stays within valid bounds."""
        if self.view_start < 0:
            self.view_start = 0

    def _on_click(self, event):
        """Handle mouse click - set time or start drag."""
        self.dragging = True
        self.drag_start_x = event.x
        self.drag_start_time = self.view_start

        # Set current time to clicked position
        clicked_time = self._x_to_time(event.x)
        if clicked_time >= 0:
            self.app.set_time(clicked_time)

    def _on_drag(self, event):
        """Handle mouse drag - pan the view or scrub time."""
        if self.dragging:
            # Scrub time while dragging
            clicked_time = self._x_to_time(event.x)
            if clicked_time >= 0:
                self.app.set_time(clicked_time)

    def _on_release(self, event):
        """Handle mouse release."""
        self.dragging = False

    def _on_scroll(self, event):
        """Handle scroll wheel - zoom or pan."""
        # Get scroll direction
        if event.num == 4 or (hasattr(event, 'delta') and event.delta > 0):
            self._zoom_in()
        elif event.num == 5 or (hasattr(event, 'delta') and event.delta < 0):
            self._zoom_out()

    def _on_resize(self, event):
        """Handle canvas resize."""
        pass  # Will be redrawn on next update

    def update_display(self, current_time: float):
        """Update the timeline display."""
        # Auto-scroll if current time is near edge
        view_end = self.view_start + self.view_duration
        margin = self.view_duration * 0.1

        if current_time > view_end - margin:
            self.view_start = current_time - self.view_duration * 0.8
        elif current_time < self.view_start + margin and self.view_start > 0:
            self.view_start = max(0, current_time - self.view_duration * 0.2)

        self._draw(current_time)

    def _draw(self, current_time: float):
        """Draw the timeline."""
        self.canvas.delete("all")

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()

        if width < 10:
            return

        # Update range label
        view_end = self.view_start + self.view_duration
        self.range_label.configure(text=f"View: {self.view_start:.0f} - {view_end:.0f}")

        # Draw background
        self._draw_time_grid(height)

        # Draw events
        self._draw_events(height)

        # Draw state cache markers
        self._draw_state_markers(height)

        # Draw current time marker
        self._draw_current_time(current_time, height)

    def _draw_time_grid(self, height: int):
        """Draw the time axis with grid lines."""
        # Calculate tick interval based on zoom level
        tick_interval = self._calculate_tick_interval()

        # Find first tick
        first_tick = int(self.view_start / tick_interval) * tick_interval
        if first_tick < self.view_start:
            first_tick += tick_interval

        # Draw ticks
        t = first_tick
        while t < self.view_start + self.view_duration:
            x = self._time_to_x(t)

            # Grid line
            self.canvas.create_line(x, 0, x, height, fill="#e0e0e0", dash=(2, 2))

            # Tick label
            if t == int(t):
                label = str(int(t))
            else:
                label = f"{t:.1f}"
            self.canvas.create_text(x, height - 5, text=label,
                                    anchor="s", font=("TkDefaultFont", 8))

            t += tick_interval

        # Draw baseline
        baseline_y = height - 20
        self.canvas.create_line(self.PADDING, baseline_y,
                                self.canvas.winfo_width() - self.PADDING, baseline_y,
                                fill="black", width=2)

    def _calculate_tick_interval(self):
        """Calculate appropriate tick interval based on zoom level."""
        # Target approximately 10 ticks visible
        target_ticks = 10
        raw_interval = self.view_duration / target_ticks

        # Round to nice numbers
        if raw_interval < 1:
            return 1
        elif raw_interval < 2:
            return 2
        elif raw_interval < 5:
            return 5
        elif raw_interval < 10:
            return 10
        elif raw_interval < 20:
            return 20
        elif raw_interval < 50:
            return 50
        else:
            return 100

    def _draw_events(self, height: int):
        """Draw events on the timeline."""
        baseline_y = height - 20
        event_y = baseline_y - 35
        base_process_y = baseline_y - 20  # Base Y position for process bars

        events = self.gamestate.timeline.events

        # Clear hitboxes for new frame
        self.event_hitboxes = []

        # Collect all process/task spans to calculate overlaps
        spans = []
        for event in events:
            if isinstance(event, (Process, Task)) and not isinstance(event, (ProcessEnd, TaskComplete, TaskInterrupt)):
                end_time = None
                end_event = getattr(event, 'end_event', None)
                if end_event:
                    end_time = end_event.t
                spans.append((event.t, end_time or event.t, event))

        # Assign vertical offsets to avoid overlaps
        span_offsets = {}
        for start_t, end_t, event in sorted(spans, key=lambda x: x[0]):
            # Find the lowest offset that doesn't overlap with existing spans
            offset = 0
            while True:
                overlaps = False
                for other_start, other_end, other_event in spans:
                    if other_event.name == event.name:
                        continue
                    if other_event.name in span_offsets and span_offsets[other_event.name] == offset:
                        # Check if time ranges overlap
                        if not (end_t <= other_start or start_t >= other_end):
                            overlaps = True
                            break
                if not overlaps:
                    break
                offset += 1
            span_offsets[event.name] = offset

        # First pass: draw process/task spans (bars connecting start to end)
        drawn_spans = set()  # Track which processes we've drawn spans for
        for event in events:
            if isinstance(event, (Process, Task)) and not isinstance(event, (ProcessEnd, TaskComplete, TaskInterrupt)):
                if event.name in drawn_spans:
                    continue
                drawn_spans.add(event.name)

                # Find the end event for this process/task
                end_time = None
                end_event = getattr(event, 'end_event', None)
                if end_event:
                    end_time = end_event.t

                # Skip if completely out of view
                start_x = self._time_to_x(event.t)
                end_x = self._time_to_x(end_time) if end_time else start_x

                if end_x < self.PADDING - 50 or start_x > self.canvas.winfo_width() - self.PADDING + 50:
                    continue

                # Clamp to visible area
                draw_start_x = max(self.PADDING, start_x)
                draw_end_x = end_x
                if end_time:
                    draw_end_x = min(self.canvas.winfo_width() - self.PADDING, end_x)

                # Calculate Y position based on offset
                offset = span_offsets.get(event.name, 0)
                process_y = base_process_y - (offset * self.BAR_SPACING)

                # Determine colors based on type and hover state
                if isinstance(event, Task):
                    bar_color = "#A5D6A7"  # Light green for task span
                    outline_color = "#4CAF50"  # Green
                else:
                    bar_color = "#90CAF9"  # Light blue for process span
                    outline_color = "#2196F3"  # Blue

                # Highlight if hovered
                if self.hovered_event and self.hovered_event.name == event.name:
                    bar_color = "#FFEB3B"  # Yellow highlight
                    outline_color = "#FFC107"

                # Draw the span bar
                half_bar = self.BAR_HEIGHT // 2
                if end_time and draw_end_x > draw_start_x:
                    self.canvas.create_rectangle(
                        draw_start_x, process_y - half_bar,
                        draw_end_x, process_y + half_bar,
                        fill=bar_color, outline=outline_color, width=2
                    )
                    # Add hitbox for the bar
                    self.event_hitboxes.append((
                        draw_start_x, process_y - half_bar,
                        draw_end_x, process_y + half_bar,
                        event
                    ))

        # Second pass: draw event markers
        for event in events:
            # Skip if out of view
            view_end = self.view_start + self.view_duration
            if event.t < self.view_start - 5 or event.t > view_end + 5:
                continue

            x = self._time_to_x(event.t)

            # Adjust marker Y based on span offset if applicable
            marker_y = event_y
            if hasattr(event, 'name') and event.name in span_offsets:
                marker_y = event_y - (span_offsets[event.name] * self.BAR_SPACING)
            elif hasattr(event, 'task') and event.task.name in span_offsets:
                marker_y = event_y - (span_offsets[event.task.name] * self.BAR_SPACING)
            elif hasattr(event, 'process') and event.process.name in span_offsets:
                marker_y = event_y - (span_offsets[event.process.name] * self.BAR_SPACING)

            # Determine color and shape based on event type
            if isinstance(event, TaskComplete):
                # Green diamond for task completion
                self._draw_diamond(x, marker_y, "#4CAF50", "darkgreen")
                name = event.displayname or "Complete"
                self.event_hitboxes.append((x - 6, marker_y - 6, x + 6, marker_y + 6, event))
            elif isinstance(event, TaskInterrupt):
                # Red X for task interrupt
                self._draw_x_marker(x, marker_y, "#F44336")
                name = event.displayname or "Interrupt"
                self.event_hitboxes.append((x - 6, marker_y - 6, x + 6, marker_y + 6, event))
            elif isinstance(event, ProcessEnd):
                # Blue square for process end
                self.canvas.create_rectangle(
                    x - 5, marker_y - 5,
                    x + 5, marker_y + 5,
                    fill="#2196F3", outline="darkblue"
                )
                name = event.displayname or "End"
                self.event_hitboxes.append((x - 5, marker_y - 5, x + 5, marker_y + 5, event))
            elif isinstance(event, Task):
                # Green circle for task start
                self.canvas.create_oval(
                    x - 6, marker_y - 6,
                    x + 6, marker_y + 6,
                    fill="#4CAF50", outline="black"
                )
                name = event.displayname or event.name or "Task"
                self.event_hitboxes.append((x - 6, marker_y - 6, x + 6, marker_y + 6, event))
            elif isinstance(event, Process):
                # Blue circle for process start
                self.canvas.create_oval(
                    x - 6, marker_y - 6,
                    x + 6, marker_y + 6,
                    fill="#2196F3", outline="black"
                )
                name = event.displayname or event.name or "Process"
                self.event_hitboxes.append((x - 6, marker_y - 6, x + 6, marker_y + 6, event))
            else:
                # Orange circle for generic events
                self.canvas.create_oval(
                    x - 6, marker_y - 6,
                    x + 6, marker_y + 6,
                    fill="#FF9800", outline="black"
                )
                name = event.displayname or event.name or "Event"
                self.event_hitboxes.append((x - 6, marker_y - 6, x + 6, marker_y + 6, event))

            # Calculate baseline connector Y based on offset
            offset = 0
            if hasattr(event, 'name') and event.name in span_offsets:
                offset = span_offsets[event.name]
            elif hasattr(event, 'task') and event.task.name in span_offsets:
                offset = span_offsets[event.task.name]
            elif hasattr(event, 'process') and event.process.name in span_offsets:
                offset = span_offsets[event.process.name]
            connector_baseline = baseline_y - (offset * self.BAR_SPACING)

            # Draw connector to baseline
            self.canvas.create_line(x, marker_y + 6, x, connector_baseline,
                                    fill="gray", dash=(2, 2))

            # Draw event name (skip for end events to reduce clutter)
            if not isinstance(event, (ProcessEnd, TaskComplete, TaskInterrupt)):
                self.canvas.create_text(x, marker_y - 12, text=name,
                                        anchor="s", font=("TkDefaultFont", 8))

    def _draw_diamond(self, x: float, y: float, fill: str, outline: str):
        """Draw a diamond shape marker."""
        size = 6
        self.canvas.create_polygon(
            x, y - size,
            x + size, y,
            x, y + size,
            x - size, y,
            fill=fill, outline=outline
        )

    def _draw_x_marker(self, x: float, y: float, color: str):
        """Draw an X shape marker."""
        size = 5
        self.canvas.create_line(x - size, y - size, x + size, y + size,
                                fill=color, width=2)
        self.canvas.create_line(x - size, y + size, x + size, y - size,
                                fill=color, width=2)

    def _draw_state_markers(self, height: int):
        """Draw markers for cached states."""
        baseline_y = height - 20
        marker_y = baseline_y + 8

        states = self.gamestate.timeline.state_cache

        for state in states:
            # Skip if out of view
            if state.time < self.view_start - 5 or state.time > self.view_start + self.view_duration + 5:
                continue

            x = self._time_to_x(state.time)

            # Draw small triangle marker
            self.canvas.create_polygon(
                x, marker_y,
                x - 4, marker_y + 8,
                x + 4, marker_y + 8,
                fill="#9E9E9E", outline="black"
            )

    def _draw_current_time(self, current_time: float, height: int):
        """Draw the current time marker."""
        x = self._time_to_x(current_time)

        # Vertical line
        self.canvas.create_line(x, 0, x, height - 10,
                                fill="red", width=2)

        # Triangle at top
        self.canvas.create_polygon(
            x, 5,
            x - 8, 15,
            x + 8, 15,
            fill="red", outline="darkred"
        )

        # Time label
        self.canvas.create_text(x, 25, text=f"{current_time:.1f}",
                                anchor="n", fill="red",
                                font=("TkDefaultFont", 9, "bold"))

    def _on_motion(self, event):
        """Handle mouse motion for hover effects."""
        x, y = event.x, event.y
        hovered = None

        # Check if hovering over any event hitbox
        for x1, y1, x2, y2, ev in self.event_hitboxes:
            if x1 <= x <= x2 and y1 <= y <= y2:
                hovered = ev
                break

        if hovered != self.hovered_event:
            self.hovered_event = hovered
            self._update_popup(event)

    def _on_leave(self, event):
        """Handle mouse leaving the canvas."""
        self.hovered_event = None
        self._hide_popup()

    def _update_popup(self, event):
        """Show or update the popup window for hovered event."""
        self._hide_popup()

        if not self.hovered_event:
            return

        ev = self.hovered_event

        # Create popup window
        self.popup_window = tk.Toplevel(self.winfo_toplevel())
        self.popup_window.wm_overrideredirect(True)
        self.popup_window.wm_attributes("-topmost", True)

        # Position near mouse
        x = self.winfo_rootx() + event.x + 15
        y = self.winfo_rooty() + event.y + 15
        self.popup_window.wm_geometry(f"+{x}+{y}")

        # Create popup content
        frame = ttk.Frame(self.popup_window, padding=5)
        frame.pack()

        # Event info
        name = ev.displayname or ev.name or "Event"
        ttk.Label(frame, text=name, font=("TkDefaultFont", 10, "bold")).pack(anchor="w")
        ttk.Label(frame, text=f"Time: {ev.t:.2f}").pack(anchor="w")

        # Event type
        if isinstance(ev, TaskComplete):
            event_type = "Task Complete"
        elif isinstance(ev, TaskInterrupt):
            event_type = "Task Interrupted"
        elif isinstance(ev, ProcessEnd):
            event_type = "Process End"
        elif isinstance(ev, Task):
            event_type = "Task"
            # Show progress info if available
            end_event = getattr(ev, 'end_event', None)
            if end_event:
                duration = end_event.t - ev.t
                ttk.Label(frame, text=f"Duration: {duration:.1f}").pack(anchor="w")
        elif isinstance(ev, Process):
            event_type = "Process"
        else:
            event_type = "Event"

        ttk.Label(frame, text=f"Type: {event_type}", foreground="gray").pack(anchor="w")

        if ev.is_action:
            ttk.Label(frame, text="(Player-created)", foreground="blue").pack(anchor="w")
            ttk.Label(frame, text="Right-click to delete", foreground="gray",
                     font=("TkDefaultFont", 8, "italic")).pack(anchor="w")

    def _hide_popup(self):
        """Hide the popup window."""
        if self.popup_window:
            self.popup_window.destroy()
            self.popup_window = None

    def _on_right_click(self, event):
        """Handle right-click for context menu."""
        x, y = event.x, event.y
        clicked_event = None

        # Check if clicking on any event hitbox
        for x1, y1, x2, y2, ev in self.event_hitboxes:
            if x1 <= x <= x2 and y1 <= y <= y2:
                clicked_event = ev
                break

        if not clicked_event:
            return

        # Only allow deletion of player-created events (is_action=True)
        # And only for start events (Task, Process), not end events
        if clicked_event.is_action and isinstance(clicked_event, (Task, Process)) and not isinstance(clicked_event, (ProcessEnd, TaskComplete, TaskInterrupt)):
            # Create context menu
            menu = tk.Menu(self.canvas, tearoff=0)
            menu.add_command(
                label=f"Delete '{clicked_event.displayname or clicked_event.name}'",
                command=lambda: self._delete_event(clicked_event)
            )
            menu.tk_popup(event.x_root, event.y_root)

    def _delete_event(self, event):
        """Delete a player-created event from the timeline."""
        self._hide_popup()
        self.gamestate.timeline.remove_event(event)

    def _clear_future_events(self):
        """Clear all player-created future events from the current time."""
        current_time = self.app.current_time
        events_to_remove = []

        # Find all player-created events in the future
        for event in self.gamestate.timeline.events:
            if event.t > current_time and event.is_action:
                # Only remove start events (Task, Process), not system-generated end events
                if isinstance(event, (Task, Process)) and not isinstance(event, (ProcessEnd, TaskComplete, TaskInterrupt)):
                    events_to_remove.append(event)

        # Remove them (in reverse order to avoid index issues)
        for event in reversed(events_to_remove):
            self.gamestate.timeline.remove_event(event)
