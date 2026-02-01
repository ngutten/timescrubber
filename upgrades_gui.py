"""
Upgrades Screen GUI for Timescrubber

This module displays the Upgrades screen where players can purchase
regular upgrades that provide bonuses and unlocks.
"""

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, List, Optional

from gamestate import GameState
from gamedefs import REGULAR_UPGRADES
from upgrades import (
    UpgradeDefinition, UpgradeType, get_upgrade_registry
)
from variable import LinearVariable

if TYPE_CHECKING:
    from app_gui import TimescrubberApp


class UpgradesScreen(ttk.Frame):
    """Upgrades screen showing purchasable upgrades."""

    def __init__(self, parent, gamestate: GameState, app: "TimescrubberApp"):
        super().__init__(parent)
        self.gamestate = gamestate
        self.app = app
        self.selected_upgrade: Optional[UpgradeDefinition] = None

        self._create_widgets()

    def _create_widgets(self):
        """Create upgrades screen widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        header = ttk.Label(self, text="Upgrades",
                          font=("TkDefaultFont", 14, "bold"))
        header.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # Main content frame
        content = ttk.Frame(self)
        content.grid(row=1, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Available Upgrades section
        available_frame = ttk.LabelFrame(content, text="Available Upgrades", padding=10)
        available_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        available_frame.grid_columnconfigure(0, weight=1)
        available_frame.grid_rowconfigure(0, weight=1)

        # Upgrades list with scrollbar
        list_frame = ttk.Frame(available_frame)
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self.upgrades_list = tk.Listbox(list_frame, height=15, selectmode=tk.SINGLE)
        self.upgrades_list.grid(row=0, column=0, sticky="nsew")

        upgrades_scroll = ttk.Scrollbar(list_frame, orient="vertical",
                                        command=self.upgrades_list.yview)
        upgrades_scroll.grid(row=0, column=1, sticky="ns")
        self.upgrades_list.configure(yscrollcommand=upgrades_scroll.set)

        # Purchase button
        self.purchase_btn = ttk.Button(available_frame, text="Purchase Upgrade",
                                       command=self._purchase_upgrade)
        self.purchase_btn.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        # Upgrade Details section
        details_frame = ttk.LabelFrame(content, text="Upgrade Details", padding=10)
        details_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_rowconfigure(2, weight=1)

        # Details header
        self.details_header = ttk.Label(details_frame, text="Select an upgrade",
                                        font=("TkDefaultFont", 11, "bold"))
        self.details_header.grid(row=0, column=0, sticky="w")

        # Status label (purchased/available/locked)
        self.status_label = ttk.Label(details_frame, text="",
                                      font=("TkDefaultFont", 9, "italic"))
        self.status_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Details text
        self.details_text = tk.Text(details_frame, height=8, width=40, wrap="word",
                                    state="disabled", bg="#f0f0f0")
        self.details_text.grid(row=2, column=0, sticky="nsew", pady=(10, 0))

        # Costs section
        costs_frame = ttk.LabelFrame(details_frame, text="Cost", padding=5)
        costs_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        costs_frame.grid_columnconfigure(0, weight=1)

        self.costs_label = ttk.Label(costs_frame, text="None",
                                     foreground="gray")
        self.costs_label.grid(row=0, column=0, sticky="w")

        # Prerequisites section
        prereq_frame = ttk.LabelFrame(details_frame, text="Prerequisites", padding=5)
        prereq_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        prereq_frame.grid_columnconfigure(0, weight=1)

        self.prereq_label = ttk.Label(prereq_frame, text="None",
                                      foreground="gray")
        self.prereq_label.grid(row=0, column=0, sticky="w")

        # Effects section
        effects_frame = ttk.LabelFrame(details_frame, text="Effects", padding=5)
        effects_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        effects_frame.grid_columnconfigure(0, weight=1)

        self.effects_label = ttk.Label(effects_frame, text="None",
                                       foreground="gray", wraplength=250)
        self.effects_label.grid(row=0, column=0, sticky="w")

        # Bind selection event
        self.upgrades_list.bind("<<ListboxSelect>>", self._on_select)

        # Initial population
        self._populate_upgrades_list()

    def _populate_upgrades_list(self):
        """Populate the upgrades list with visible upgrades."""
        self.upgrades_list.delete(0, tk.END)

        registry = get_upgrade_registry()
        for upgrade in REGULAR_UPGRADES:
            # Show if visible (prerequisites met) or already purchased
            if registry.is_visible(upgrade.name) or registry.is_purchased(upgrade.name):
                prefix = "[OK] " if registry.is_purchased(upgrade.name) else ""
                self.upgrades_list.insert(tk.END, f"{prefix}{upgrade.displayname}")

    def _on_select(self, event):
        """Handle upgrade selection."""
        selection = self.upgrades_list.curselection()
        if not selection:
            return

        # Get the upgrade name (strip prefix if present)
        list_text = self.upgrades_list.get(selection[0])
        upgrade_name = list_text.replace("[OK] ", "")

        # Find the upgrade
        self.selected_upgrade = None
        for upgrade in REGULAR_UPGRADES:
            if upgrade.displayname == upgrade_name:
                self.selected_upgrade = upgrade
                break

        if not self.selected_upgrade:
            return

        self._update_details()

    def _update_details(self):
        """Update the details panel for the selected upgrade."""
        if not self.selected_upgrade:
            return

        upgrade = self.selected_upgrade
        registry = get_upgrade_registry()
        current_time = self.app.current_time
        ts = self.gamestate.timeline.state_at(current_time)

        # Update header
        self.details_header.configure(text=upgrade.displayname)

        # Update status
        if registry.is_purchased(upgrade.name):
            self.status_label.configure(text="Purchased", foreground="green")
        elif registry.can_purchase(upgrade.name, ts, current_time):
            self.status_label.configure(text="Available", foreground="blue")
        elif registry.check_prerequisites(upgrade.name, ts):
            self.status_label.configure(text="Insufficient Resources", foreground="orange")
        else:
            self.status_label.configure(text="Prerequisites Not Met", foreground="red")

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
                color_indicator = "+" if current >= cost.amount else "-"
                cost_parts.append(f"{cost.amount:.0f} {cost.resource} ({color_indicator})")
            self.costs_label.configure(text=", ".join(cost_parts))
        else:
            self.costs_label.configure(text="Free")

        # Update prerequisites
        if upgrade.prerequisites:
            prereq_parts = []
            for prereq in upgrade.prerequisites:
                met = registry._check_prereq(prereq, ts)
                status = "ok" if met else "x"
                prereq_parts.append(f"[{status}] {prereq.target}")
            self.prereq_label.configure(text="\n".join(prereq_parts))
        else:
            self.prereq_label.configure(text="None")

        # Update effects
        effect_parts = []
        for effect in upgrade.effects:
            if effect.effect_type == "modifier":
                param = effect.params.get("target_param", "rate")
                value = effect.params.get("value", 0)
                tags = effect.params.get("target_tags", [])
                sign = "+" if value >= 0 else ""
                tag_str = f" ({', '.join(tags)})" if tags else " (all)"
                effect_parts.append(f"{sign}{value*100:.0f}% {param}{tag_str}")
            elif effect.effect_type == "unlock_task":
                effect_parts.append(f"Unlocks: {effect.params.get('task_name', '?')}")
            elif effect.effect_type == "unlock_resource":
                effect_parts.append(f"Unlocks: {effect.params.get('resource_name', '?')}")

        if effect_parts:
            self.effects_label.configure(text="\n".join(effect_parts))
        else:
            self.effects_label.configure(text="No direct effects")

    def _purchase_upgrade(self):
        """Purchase the selected upgrade."""
        if not self.selected_upgrade:
            return

        registry = get_upgrade_registry()
        current_time = self.app.current_time
        ts = self.gamestate.timeline.state_at(current_time)

        if registry.can_purchase(self.selected_upgrade.name, ts, current_time):
            success = registry.purchase(self.selected_upgrade.name, ts, current_time)
            if success:
                print(f"Purchased upgrade: {self.selected_upgrade.displayname}")
                self._populate_upgrades_list()
                self._update_details()
            else:
                print(f"Failed to purchase: {self.selected_upgrade.displayname}")
        else:
            print(f"Cannot purchase: {self.selected_upgrade.displayname}")

    def update_display(self, current_time: float):
        """Update the upgrades display."""
        # Refresh list to show newly visible upgrades
        self._populate_upgrades_list()

        # Update item colors based on availability
        registry = get_upgrade_registry()
        ts = self.gamestate.timeline.state_at(current_time)

        for i in range(self.upgrades_list.size()):
            list_text = self.upgrades_list.get(i)
            upgrade_name = list_text.replace("[OK] ", "")

            # Find the upgrade
            upgrade = None
            for u in REGULAR_UPGRADES:
                if u.displayname == upgrade_name:
                    upgrade = u
                    break

            if upgrade:
                if registry.is_purchased(upgrade.name):
                    self.upgrades_list.itemconfig(i, fg="green")
                elif registry.can_purchase(upgrade.name, ts, current_time):
                    self.upgrades_list.itemconfig(i, fg="blue")
                elif registry.check_prerequisites(upgrade.name, ts):
                    self.upgrades_list.itemconfig(i, fg="orange")
                else:
                    self.upgrades_list.itemconfig(i, fg="gray")

        # Update details if something is selected
        if self.selected_upgrade:
            self._update_details()


class NexusScreen(ttk.Frame):
    """Nexus screen showing meta-progression upgrades purchased with Motes."""

    def __init__(self, parent, gamestate: GameState, app: "TimescrubberApp"):
        super().__init__(parent)
        self.gamestate = gamestate
        self.app = app
        self.selected_upgrade: Optional[UpgradeDefinition] = None

        # Import here to avoid circular imports
        from gamedefs import NEXUS_UPGRADES
        self.nexus_upgrades = NEXUS_UPGRADES

        self._create_widgets()

    def _create_widgets(self):
        """Create nexus screen widgets."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header with Motes display
        header_frame = ttk.Frame(self)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header_frame.grid_columnconfigure(1, weight=1)

        header = ttk.Label(header_frame, text="Nexus",
                          font=("TkDefaultFont", 14, "bold"))
        header.grid(row=0, column=0, sticky="w")

        self.motes_label = ttk.Label(header_frame, text="Motes: 0",
                                     font=("TkDefaultFont", 11),
                                     foreground="#9C27B0")
        self.motes_label.grid(row=0, column=1, sticky="e")

        # Description
        desc = ttk.Label(self, text="The Nexus contains meta-progression upgrades that persist across timeline resets. "
                                   "Purchase these with Motes earned from achievements.",
                        wraplength=600, foreground="gray")
        desc.grid(row=1, column=0, sticky="nw", pady=(0, 15))

        # Main content frame
        content = ttk.Frame(self)
        content.grid(row=2, column=0, sticky="nsew")
        content.grid_columnconfigure(0, weight=1)
        content.grid_columnconfigure(1, weight=1)
        content.grid_rowconfigure(0, weight=1)

        # Available Nexus Upgrades section
        available_frame = ttk.LabelFrame(content, text="Nexus Upgrades", padding=10)
        available_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        available_frame.grid_columnconfigure(0, weight=1)
        available_frame.grid_rowconfigure(0, weight=1)

        # Upgrades list with scrollbar
        list_frame = ttk.Frame(available_frame)
        list_frame.grid(row=0, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self.upgrades_list = tk.Listbox(list_frame, height=12, selectmode=tk.SINGLE)
        self.upgrades_list.grid(row=0, column=0, sticky="nsew")

        upgrades_scroll = ttk.Scrollbar(list_frame, orient="vertical",
                                        command=self.upgrades_list.yview)
        upgrades_scroll.grid(row=0, column=1, sticky="ns")
        self.upgrades_list.configure(yscrollcommand=upgrades_scroll.set)

        # Purchase button
        self.purchase_btn = ttk.Button(available_frame, text="Purchase Upgrade",
                                       command=self._purchase_upgrade)
        self.purchase_btn.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        # Upgrade Details section
        details_frame = ttk.LabelFrame(content, text="Upgrade Details", padding=10)
        details_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        details_frame.grid_columnconfigure(0, weight=1)
        details_frame.grid_rowconfigure(2, weight=1)

        # Details header
        self.details_header = ttk.Label(details_frame, text="Select an upgrade",
                                        font=("TkDefaultFont", 11, "bold"))
        self.details_header.grid(row=0, column=0, sticky="w")

        # Status label
        self.status_label = ttk.Label(details_frame, text="",
                                      font=("TkDefaultFont", 9, "italic"))
        self.status_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

        # Details text
        self.details_text = tk.Text(details_frame, height=6, width=40, wrap="word",
                                    state="disabled", bg="#f0f0f0")
        self.details_text.grid(row=2, column=0, sticky="nsew", pady=(10, 0))

        # Costs section
        costs_frame = ttk.LabelFrame(details_frame, text="Cost", padding=5)
        costs_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        costs_frame.grid_columnconfigure(0, weight=1)

        self.costs_label = ttk.Label(costs_frame, text="None",
                                     foreground="gray")
        self.costs_label.grid(row=0, column=0, sticky="w")

        # Prerequisites section
        prereq_frame = ttk.LabelFrame(details_frame, text="Prerequisites", padding=5)
        prereq_frame.grid(row=4, column=0, sticky="ew", pady=(10, 0))
        prereq_frame.grid_columnconfigure(0, weight=1)

        self.prereq_label = ttk.Label(prereq_frame, text="None",
                                      foreground="gray")
        self.prereq_label.grid(row=0, column=0, sticky="w")

        # Effects section
        effects_frame = ttk.LabelFrame(details_frame, text="Effects", padding=5)
        effects_frame.grid(row=5, column=0, sticky="ew", pady=(10, 0))
        effects_frame.grid_columnconfigure(0, weight=1)

        self.effects_label = ttk.Label(effects_frame, text="None",
                                       foreground="gray", wraplength=250)
        self.effects_label.grid(row=0, column=0, sticky="w")

        # Bind selection event
        self.upgrades_list.bind("<<ListboxSelect>>", self._on_select)

        # Initial population
        self._populate_upgrades_list()

    def _populate_upgrades_list(self):
        """Populate the upgrades list with visible nexus upgrades."""
        self.upgrades_list.delete(0, tk.END)

        registry = get_upgrade_registry()
        for upgrade in self.nexus_upgrades:
            # Show if visible (prerequisites met) or already purchased
            if registry.is_visible(upgrade.name) or registry.is_purchased(upgrade.name):
                prefix = "[OK] " if registry.is_purchased(upgrade.name) else ""
                self.upgrades_list.insert(tk.END, f"{prefix}{upgrade.displayname}")

    def _on_select(self, event):
        """Handle upgrade selection."""
        selection = self.upgrades_list.curselection()
        if not selection:
            return

        # Get the upgrade name (strip prefix if present)
        list_text = self.upgrades_list.get(selection[0])
        upgrade_name = list_text.replace("[OK] ", "")

        # Find the upgrade
        self.selected_upgrade = None
        for upgrade in self.nexus_upgrades:
            if upgrade.displayname == upgrade_name:
                self.selected_upgrade = upgrade
                break

        if not self.selected_upgrade:
            return

        self._update_details()

    def _update_details(self):
        """Update the details panel for the selected upgrade."""
        if not self.selected_upgrade:
            return

        upgrade = self.selected_upgrade
        registry = get_upgrade_registry()
        current_time = self.app.current_time
        ts = self.gamestate.timeline.state_at(current_time)

        # Update header
        self.details_header.configure(text=upgrade.displayname)

        # Update status
        if registry.is_purchased(upgrade.name):
            self.status_label.configure(text="Purchased", foreground="green")
        elif registry.can_purchase(upgrade.name, ts, current_time):
            self.status_label.configure(text="Available", foreground="#9C27B0")
        elif registry.check_prerequisites(upgrade.name, ts):
            self.status_label.configure(text="Insufficient Motes", foreground="orange")
        else:
            self.status_label.configure(text="Prerequisites Not Met", foreground="red")

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
                color_indicator = "+" if current >= cost.amount else "-"
                cost_parts.append(f"{cost.amount:.0f} {cost.resource} ({color_indicator})")
            self.costs_label.configure(text=", ".join(cost_parts))
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
                for u in self.nexus_upgrades:
                    if u.name == prereq.target:
                        prereq_upgrade = u
                        break
                prereq_name = prereq_upgrade.displayname if prereq_upgrade else prereq.target
                prereq_parts.append(f"[{status}] {prereq_name}")
            self.prereq_label.configure(text="\n".join(prereq_parts))
        else:
            self.prereq_label.configure(text="None")

        # Update effects
        effect_parts = []
        for effect in upgrade.effects:
            if effect.effect_type == "modifier":
                param = effect.params.get("target_param", "rate")
                value = effect.params.get("value", 0)
                tags = effect.params.get("target_tags", [])
                sign = "+" if value >= 0 else ""
                tag_str = f" ({', '.join(tags)})" if tags else " (all tasks)"
                effect_parts.append(f"{sign}{value*100:.0f}% {param}{tag_str}")
            elif effect.effect_type == "max_time_multiplier":
                mult = effect.params.get("multiplier", 1.0)
                effect_parts.append(f"Max time x{mult:.1f}")
            elif effect.effect_type == "parallel_tasks":
                value = effect.params.get("value", 1)
                effect_parts.append(f"Parallel tasks: {value}")

        if effect_parts:
            self.effects_label.configure(text="\n".join(effect_parts))
        else:
            self.effects_label.configure(text="No direct effects")

    def _purchase_upgrade(self):
        """Purchase the selected nexus upgrade."""
        if not self.selected_upgrade:
            return

        registry = get_upgrade_registry()
        current_time = self.app.current_time
        ts = self.gamestate.timeline.state_at(current_time)

        if registry.can_purchase(self.selected_upgrade.name, ts, current_time):
            success = registry.purchase(self.selected_upgrade.name, ts, current_time)
            if success:
                print(f"Purchased nexus upgrade: {self.selected_upgrade.displayname}")
                self._populate_upgrades_list()
                self._update_details()
            else:
                print(f"Failed to purchase: {self.selected_upgrade.displayname}")
        else:
            print(f"Cannot purchase: {self.selected_upgrade.displayname}")

    def update_display(self, current_time: float):
        """Update the nexus display."""
        # Update Motes display
        ts = self.gamestate.timeline.state_at(current_time)
        motes_var = ts.get_variable("Motes")
        motes = int(motes_var.get(current_time)) if motes_var else 0
        self.motes_label.configure(text=f"Motes: {motes}")

        # Refresh list to show newly visible upgrades
        self._populate_upgrades_list()

        # Update item colors based on availability
        registry = get_upgrade_registry()

        for i in range(self.upgrades_list.size()):
            list_text = self.upgrades_list.get(i)
            upgrade_name = list_text.replace("[OK] ", "")

            # Find the upgrade
            upgrade = None
            for u in self.nexus_upgrades:
                if u.displayname == upgrade_name:
                    upgrade = u
                    break

            if upgrade:
                if registry.is_purchased(upgrade.name):
                    self.upgrades_list.itemconfig(i, fg="green")
                elif registry.can_purchase(upgrade.name, ts, current_time):
                    self.upgrades_list.itemconfig(i, fg="#9C27B0")  # Purple
                elif registry.check_prerequisites(upgrade.name, ts):
                    self.upgrades_list.itemconfig(i, fg="orange")
                else:
                    self.upgrades_list.itemconfig(i, fg="gray")

        # Update details if something is selected
        if self.selected_upgrade:
            self._update_details()

