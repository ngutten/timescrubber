"""
Research Screen GUI for Timescrubber

This module displays the Research screen with a visual tech tree
where players can unlock new technologies and abilities.
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

from gamestate import GameState
from gamedefs import RESEARCH_UPGRADES, get_research_tree_data
from upgrades import (
    UpgradeDefinition, UpgradeType, get_upgrade_registry, create_purchase_event
)
from variable import LinearVariable

if TYPE_CHECKING:
    from app_gui import TimescrubberApp


# Node sizing and spacing for the research tree
NODE_WIDTH = 140
NODE_HEIGHT = 60
GRID_SPACING_X = 180
GRID_SPACING_Y = 100
CANVAS_PADDING = 50


class ResearchScreen(ttk.Frame):
    """Research screen showing the research tech tree."""

    def __init__(self, parent, gamestate: GameState, app: "TimescrubberApp"):
        super().__init__(parent)
        self.gamestate = gamestate
        self.app = app
        self.selected_research: Optional[UpgradeDefinition] = None
        self.node_rects: Dict[str, int] = {}  # Maps upgrade name to canvas rect id
        self.node_positions: Dict[str, Tuple[int, int]] = {}  # Maps upgrade name to (x, y)

        self._create_widgets()

    def _create_widgets(self):
        """Create research screen widgets."""
        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left side - Research Tree Canvas
        tree_frame = ttk.LabelFrame(self, text="Research Tree", padding=5)
        tree_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        # Canvas with scrollbars
        canvas_frame = ttk.Frame(tree_frame)
        canvas_frame.grid(row=0, column=0, sticky="nsew")
        canvas_frame.grid_columnconfigure(0, weight=1)
        canvas_frame.grid_rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(canvas_frame, bg="#2b2b2b", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        # Scrollbars
        h_scroll = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        h_scroll.grid(row=1, column=0, sticky="ew")
        v_scroll = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        v_scroll.grid(row=0, column=1, sticky="ns")

        self.canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        # Right side - Details Panel
        details_frame = ttk.LabelFrame(self, text="Research Details", padding=10)
        details_frame.grid(row=0, column=1, sticky="nsew")
        details_frame.grid_columnconfigure(0, weight=1)

        # Details header
        self.details_header = ttk.Label(details_frame, text="Select a research topic",
                                        font=("TkDefaultFont", 11, "bold"))
        self.details_header.grid(row=0, column=0, sticky="w")

        # Status label
        self.status_label = ttk.Label(details_frame, text="",
                                      font=("TkDefaultFont", 9, "italic"))
        self.status_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Description
        desc_label = ttk.Label(details_frame, text="Description:",
                               font=("TkDefaultFont", 9, "bold"))
        desc_label.grid(row=2, column=0, sticky="w", pady=(10, 0))

        self.details_text = tk.Text(details_frame, height=6, width=35, wrap="word",
                                    state="disabled", bg="#f0f0f0")
        self.details_text.grid(row=3, column=0, sticky="ew", pady=(5, 0))

        # Cost section
        costs_frame = ttk.LabelFrame(details_frame, text="Cost", padding=5)
        costs_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        costs_frame.grid_columnconfigure(0, weight=1)

        self.costs_label = ttk.Label(costs_frame, text="None", foreground="gray")
        self.costs_label.grid(row=0, column=0, sticky="w")

        # Prerequisites section
        prereq_frame = ttk.LabelFrame(details_frame, text="Prerequisites", padding=5)
        prereq_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        prereq_frame.grid_columnconfigure(0, weight=1)

        self.prereq_label = ttk.Label(prereq_frame, text="None", foreground="gray")
        self.prereq_label.grid(row=0, column=0, sticky="w")

        # Effects section
        effects_frame = ttk.LabelFrame(details_frame, text="Unlocks", padding=5)
        effects_frame.grid(row=6, column=0, sticky="ew", pady=(10, 0))
        effects_frame.grid_columnconfigure(0, weight=1)

        self.effects_label = ttk.Label(effects_frame, text="None",
                                       foreground="gray", wraplength=200)
        self.effects_label.grid(row=0, column=0, sticky="w")

        # Research button
        self.research_btn = ttk.Button(details_frame, text="Research",
                                       command=self._purchase_research)
        self.research_btn.grid(row=7, column=0, sticky="ew", pady=(15, 0))

        # Bind canvas events
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # Initial draw
        self._draw_tree()

    def _get_node_screen_position(self, render_pos: Tuple[float, float]) -> Tuple[int, int]:
        """Convert grid position to screen coordinates."""
        x = CANVAS_PADDING + render_pos[0] * GRID_SPACING_X
        # Invert Y so positive goes down, center at middle
        y = 200 + render_pos[1] * GRID_SPACING_Y
        return int(x), int(y)

    def _draw_tree(self):
        """Draw the research tree on the canvas."""
        self.canvas.delete("all")
        self.node_rects.clear()
        self.node_positions.clear()

        registry = get_upgrade_registry()
        current_time = self.app.current_time
        ts = self.gamestate.timeline.state_at(current_time)

        # First pass: calculate positions and draw connections
        for upgrade in RESEARCH_UPGRADES:
            x, y = self._get_node_screen_position(upgrade.render_position)
            self.node_positions[upgrade.name] = (x + NODE_WIDTH // 2, y + NODE_HEIGHT // 2)

        # Draw prerequisite lines first (so they're behind nodes)
        for upgrade in RESEARCH_UPGRADES:
            if not registry.is_visible(upgrade.name, ts) and not ts.is_upgrade_purchased(upgrade.name):
                continue

            x, y = self._get_node_screen_position(upgrade.render_position)
            node_center = (x + NODE_WIDTH // 2, y + NODE_HEIGHT // 2)

            for prereq in upgrade.prerequisites:
                if prereq.target in self.node_positions:
                    prereq_center = self.node_positions[prereq.target]
                    # Draw line from prerequisite to this node
                    line_color = "#4a4a4a"
                    if ts.is_upgrade_purchased(prereq.target):
                        line_color = "#4CAF50"  # Green if prereq is purchased

                    self.canvas.create_line(
                        prereq_center[0], prereq_center[1],
                        node_center[0], node_center[1],
                        fill=line_color, width=2, arrow=tk.LAST
                    )

        # Second pass: draw nodes
        for upgrade in RESEARCH_UPGRADES:
            # Determine visibility (time-aware)
            is_visible = registry.is_visible(upgrade.name, ts)
            is_purchased = ts.is_upgrade_purchased(upgrade.name)

            if not is_visible and not is_purchased:
                # Show as locked placeholder if any prerequisite is visible/purchased
                any_prereq_visible = False
                for prereq in upgrade.prerequisites:
                    if registry.is_visible(prereq.target, ts) or ts.is_upgrade_purchased(prereq.target):
                        any_prereq_visible = True
                        break
                if not any_prereq_visible:
                    continue  # Don't show at all

            x, y = self._get_node_screen_position(upgrade.render_position)

            # Determine colors based on state
            if is_purchased:
                fill_color = "#4CAF50"  # Green
                text_color = "white"
                border_color = "#2E7D32"
            elif registry.can_purchase(upgrade.name, ts, current_time):
                fill_color = "#2196F3"  # Blue
                text_color = "white"
                border_color = "#1565C0"
            elif is_visible:
                fill_color = "#FF9800"  # Orange (visible but can't afford)
                text_color = "black"
                border_color = "#E65100"
            else:
                fill_color = "#424242"  # Gray (locked)
                text_color = "#888888"
                border_color = "#303030"

            # Draw node rectangle with rounded corners effect
            rect = self.canvas.create_rectangle(
                x, y, x + NODE_WIDTH, y + NODE_HEIGHT,
                fill=fill_color, outline=border_color, width=2
            )
            self.node_rects[upgrade.name] = rect

            # Draw text
            display_text = upgrade.displayname
            if len(display_text) > 18:
                display_text = display_text[:16] + "..."

            self.canvas.create_text(
                x + NODE_WIDTH // 2, y + NODE_HEIGHT // 2,
                text=display_text, fill=text_color,
                font=("TkDefaultFont", 9, "bold"),
                width=NODE_WIDTH - 10
            )

            # Draw status indicator
            if is_purchased:
                status_text = "Researched"
            elif registry.can_purchase(upgrade.name, ts, current_time):
                status_text = "Available"
            elif is_visible:
                cost = upgrade.costs[0] if upgrade.costs else None
                if cost:
                    status_text = f"{int(cost.amount)} Insights"
                else:
                    status_text = "Locked"
            else:
                status_text = "???"

            self.canvas.create_text(
                x + NODE_WIDTH // 2, y + NODE_HEIGHT - 8,
                text=status_text, fill=text_color,
                font=("TkDefaultFont", 7)
            )

        # Update scroll region
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_click(self, event):
        """Handle click on canvas to select research."""
        # Convert to canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)

        # Find which node was clicked
        for upgrade in RESEARCH_UPGRADES:
            x, y = self._get_node_screen_position(upgrade.render_position)
            if x <= canvas_x <= x + NODE_WIDTH and y <= canvas_y <= y + NODE_HEIGHT:
                self.selected_research = upgrade
                self._update_details()
                self._draw_tree()  # Redraw to show selection
                return

    def _on_canvas_configure(self, event):
        """Handle canvas resize."""
        # Could adjust layout here if needed
        pass

    def _update_details(self):
        """Update the details panel for the selected research."""
        if not self.selected_research:
            return

        upgrade = self.selected_research
        registry = get_upgrade_registry()
        current_time = self.app.current_time
        ts = self.gamestate.timeline.state_at(current_time)

        # Update header
        self.details_header.configure(text=upgrade.displayname)

        # Update status (time-aware)
        if ts.is_upgrade_purchased(upgrade.name):
            self.status_label.configure(text="Researched", foreground="green")
        elif registry.can_purchase(upgrade.name, ts, current_time):
            self.status_label.configure(text="Available", foreground="blue")
        elif registry.check_prerequisites(upgrade.name, ts):
            self.status_label.configure(text="Need More Insights", foreground="orange")
        else:
            self.status_label.configure(text="Prerequisites Required", foreground="red")

        # Update description
        self.details_text.configure(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", upgrade.description)
        self.details_text.configure(state="disabled")

        # Update costs
        if upgrade.costs:
            cost_parts = []
            for cost in upgrade.costs:
                var = ts.get_variable(cost.resource)
                current = var.get(current_time) if var else 0
                indicator = "ok" if current >= cost.amount else "need"
                cost_parts.append(f"{cost.amount:.0f} {cost.resource} [{indicator}]")
            self.costs_label.configure(text="\n".join(cost_parts))
        else:
            self.costs_label.configure(text="Free")

        # Update prerequisites
        if upgrade.prerequisites:
            prereq_parts = []
            for prereq in upgrade.prerequisites:
                met = registry._check_prereq(prereq, ts)
                status = "ok" if met else "x"
                # Try to get display name
                prereq_upgrade = None
                for u in RESEARCH_UPGRADES:
                    if u.name == prereq.target:
                        prereq_upgrade = u
                        break
                prereq_name = prereq_upgrade.displayname if prereq_upgrade else prereq.target
                prereq_parts.append(f"[{status}] {prereq_name}")
            self.prereq_label.configure(text="\n".join(prereq_parts))
        else:
            self.prereq_label.configure(text="None - Starting research")

        # Update effects (unlocks)
        effect_parts = []
        for effect in upgrade.effects:
            if effect.effect_type == "modifier":
                param = effect.params.get("target_param", "rate")
                value = effect.params.get("value", 0)
                tags = effect.params.get("target_tags", [])
                sign = "+" if value >= 0 else ""
                tag_str = f" ({', '.join(tags)})" if tags else ""
                effect_parts.append(f"{sign}{value*100:.0f}% {param}{tag_str}")
            elif effect.effect_type == "unlock_task":
                effect_parts.append(f"Activity: {effect.params.get('task_name', '?')}")
            elif effect.effect_type == "unlock_resource":
                effect_parts.append(f"Resource: {effect.params.get('resource_name', '?')}")

        if effect_parts:
            self.effects_label.configure(text="\n".join(effect_parts))
        else:
            self.effects_label.configure(text="Unlocks further research")

        # Update button state (time-aware)
        if ts.is_upgrade_purchased(upgrade.name):
            self.research_btn.configure(state="disabled", text="Researched")
        elif registry.can_purchase(upgrade.name, ts, current_time):
            self.research_btn.configure(state="normal", text="Research")
        else:
            self.research_btn.configure(state="disabled", text="Research")

    def _purchase_research(self):
        """Purchase the selected research."""
        if not self.selected_research:
            return

        registry = get_upgrade_registry()
        current_time = self.app.current_time
        ts = self.gamestate.timeline.state_at(current_time)

        if registry.can_purchase(self.selected_research.name, ts, current_time):
            # Create a purchase event and add it to the timeline
            # This ensures the research shows up on the timeline and persists correctly
            purchase_event = create_purchase_event(self.selected_research.name, current_time)
            if purchase_event:
                self.gamestate.timeline.add_event(purchase_event)
                print(f"Researched: {self.selected_research.displayname}")
                self._draw_tree()
                self._update_details()
            else:
                print(f"Failed to create research event: {self.selected_research.displayname}")
        else:
            print(f"Cannot research: {self.selected_research.displayname}")

    def update_display(self, current_time: float):
        """Update the research display."""
        self._draw_tree()
        if self.selected_research:
            self._update_details()
