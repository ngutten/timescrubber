# Upgrade System for Timescrubber
#
# This module defines the upgrade system including:
# - Regular Upgrades: Permanent improvements purchased with resources
# - Research Upgrades: Tech tree unlocks purchased with Insights
# - Nexus Upgrades: Meta-progression purchased with Motes (persistent currency)
#
# Upgrades have:
# - Prerequisites (other upgrades, research topics, etc.)
# - Costs (resources to spend)
# - Effects (modifiers, unlocks, etc.)
# - Visibility rules (shown only when prereqs met)

from typing import Dict, List, Optional, Any, Tuple, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from copy import deepcopy

from modifiers import Modifier, get_modifier_registry


class UpgradeType(Enum):
    """The category of upgrade, determining which UI tab it appears in."""
    REGULAR = "regular"      # Standard upgrades in the Upgrades tab
    RESEARCH = "research"    # Research tree in the Research tab
    NEXUS = "nexus"          # Meta-progression in the Nexus tab


class PrerequisiteType(Enum):
    """Types of prerequisites an upgrade can have."""
    UPGRADE = "upgrade"      # Another upgrade must be purchased
    RESEARCH = "research"    # A research topic must be completed
    RESOURCE = "resource"    # A resource must have been obtained (lifetime)
    VARIABLE = "variable"    # A variable must have a certain value
    TASK = "task"            # A task must have been completed


@dataclass
class Prerequisite:
    """A prerequisite for an upgrade.

    Attributes:
        prereq_type: What kind of prerequisite this is
        target: The name of the required upgrade/research/resource/etc.
        value: For RESOURCE/VARIABLE types, the minimum value required
    """
    prereq_type: PrerequisiteType
    target: str
    value: float = 0.0


@dataclass
class UpgradeCost:
    """A cost to purchase an upgrade.

    Attributes:
        resource: Name of the resource to spend
        amount: Amount required
    """
    resource: str
    amount: float


@dataclass
class UpgradeEffect:
    """An effect granted by an upgrade.

    Attributes:
        effect_type: What kind of effect (modifier, unlock, etc.)
        params: Parameters for the effect (varies by type)

    Effect types:
        - "modifier": Adds a Modifier to the registry
            params: {"modifier_type": str, "value": float, "target_param": str, "target_tags": List[str]}
        - "unlock_task": Makes a task available
            params: {"task_name": str}
        - "unlock_resource": Makes a resource visible
            params: {"resource_name": str}
        - "unlock_upgrade": Makes an upgrade visible (beyond normal prereqs)
            params: {"upgrade_name": str}
        - "set_variable": Sets a variable to a value
            params: {"variable_name": str, "value": float}
        - "add_variable": Adds to a variable
            params: {"variable_name": str, "value": float}
        - "max_time_multiplier": Multiplies the max_time value
            params: {"multiplier": float}
        - "parallel_tasks": Changes the number of parallel tasks allowed
            params: {"value": int}
    """
    effect_type: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UpgradeDefinition:
    """Complete definition of an upgrade.

    Attributes:
        name: Internal unique identifier
        displayname: Human-readable name
        description: Description text
        upgrade_type: Which category (regular/research/nexus)
        prerequisites: List of prerequisites that must be met
        costs: List of resources to spend
        effects: List of effects when purchased
        render_position: For research tree, (x, y) position in the graph
        icon: Optional icon identifier
        purchased: Whether this upgrade has been bought
    """
    name: str
    displayname: str
    description: str
    upgrade_type: UpgradeType
    prerequisites: List[Prerequisite] = field(default_factory=list)
    costs: List[UpgradeCost] = field(default_factory=list)
    effects: List[UpgradeEffect] = field(default_factory=list)
    render_position: Tuple[float, float] = (0, 0)  # For research tree layout
    icon: str = ""
    tags: List[str] = field(default_factory=list)  # Tags for this upgrade itself


class UpgradeRegistry:
    """Manages all upgrade definitions and their purchase state.

    This is the central system for upgrades. It tracks:
    - All defined upgrades
    - Which upgrades have been purchased
    - Visibility based on prerequisites
    - Unlock effects for tasks, resources, and other upgrades
    """

    def __init__(self):
        self._upgrades: Dict[str, UpgradeDefinition] = {}
        self._purchased: Set[str] = set()
        self._unlocked_tasks: Set[str] = set()
        self._unlocked_resources: Set[str] = set()
        # Tracks task completion for prerequisites
        self._completed_tasks: Set[str] = set()
        # Nexus-specific values
        self._max_time_multiplier: float = 1.0
        self._max_parallel_tasks: int = 1

    def register(self, upgrade: UpgradeDefinition):
        """Register an upgrade definition."""
        self._upgrades[upgrade.name] = upgrade

    def register_all(self, upgrades: List[UpgradeDefinition]):
        """Register multiple upgrade definitions."""
        for upgrade in upgrades:
            self.register(upgrade)

    def get(self, name: str) -> Optional[UpgradeDefinition]:
        """Get an upgrade definition by name."""
        return self._upgrades.get(name)

    def get_all(self) -> List[UpgradeDefinition]:
        """Get all registered upgrades."""
        return list(self._upgrades.values())

    def get_by_type(self, upgrade_type: UpgradeType) -> List[UpgradeDefinition]:
        """Get all upgrades of a specific type."""
        return [u for u in self._upgrades.values() if u.upgrade_type == upgrade_type]

    def is_purchased(self, name: str) -> bool:
        """Check if an upgrade has been purchased."""
        return name in self._purchased

    def _check_prereq(self, prereq: Prerequisite, timestate=None) -> bool:
        """Check if a single prerequisite is met.

        Args:
            prereq: The prerequisite to check
            timestate: Optional TimeState for checking variable values
        """
        if prereq.prereq_type == PrerequisiteType.UPGRADE:
            return self.is_purchased(prereq.target)

        elif prereq.prereq_type == PrerequisiteType.RESEARCH:
            # Research is also tracked as purchased upgrades (of type RESEARCH)
            return self.is_purchased(prereq.target)

        elif prereq.prereq_type == PrerequisiteType.TASK:
            return prereq.target in self._completed_tasks

        elif prereq.prereq_type == PrerequisiteType.RESOURCE:
            # Check if resource has ever reached the required value
            # This would need integration with timeline tracking
            # For now, check if resource is unlocked
            return prereq.target in self._unlocked_resources

        elif prereq.prereq_type == PrerequisiteType.VARIABLE:
            if timestate:
                var = timestate.get_variable(prereq.target)
                if var:
                    return var.get(timestate.time) >= prereq.value
            return False

        return False

    def check_prerequisites(self, name: str, timestate=None) -> bool:
        """Check if all prerequisites for an upgrade are met.

        Args:
            name: The upgrade name
            timestate: Optional TimeState for variable checks
        """
        upgrade = self.get(name)
        if not upgrade:
            return False

        return all(self._check_prereq(p, timestate) for p in upgrade.prerequisites)

    def check_costs(self, name: str, timestate, t: float) -> bool:
        """Check if resources are available to purchase an upgrade.

        Args:
            name: The upgrade name
            timestate: The TimeState to check resources in
            t: The time to check at
        """
        upgrade = self.get(name)
        if not upgrade:
            return False

        for cost in upgrade.costs:
            var = timestate.get_variable(cost.resource)
            if not var:
                return False
            if var.get(t) < cost.amount:
                return False

        return True

    def can_purchase(self, name: str, timestate, t: float) -> bool:
        """Check if an upgrade can be purchased (prereqs met and costs affordable)."""
        return (
            not self.is_purchased(name) and
            self.check_prerequisites(name, timestate) and
            self.check_costs(name, timestate, t)
        )

    def is_visible(self, name: str, timestate=None) -> bool:
        """Check if an upgrade should be visible in the UI.

        Regular upgrades: visible when prereqs met (even if can't afford)
        Research upgrades: visible when prereqs met (one step out)
        Nexus upgrades: always visible if prereqs met
        """
        upgrade = self.get(name)
        if not upgrade:
            return False

        # Already purchased = visible
        if self.is_purchased(name):
            return True

        # Check prerequisites
        return self.check_prerequisites(name, timestate)

    def get_visible_upgrades(self, upgrade_type: UpgradeType, timestate=None) -> List[UpgradeDefinition]:
        """Get all visible upgrades of a type."""
        return [
            u for u in self.get_by_type(upgrade_type)
            if self.is_visible(u.name, timestate)
        ]

    def purchase(self, name: str, timestate, t: float) -> bool:
        """Attempt to purchase an upgrade.

        Args:
            name: The upgrade to purchase
            timestate: The TimeState to modify
            t: The time of purchase

        Returns:
            True if purchased successfully, False otherwise
        """
        if not self.can_purchase(name, timestate, t):
            return False

        upgrade = self.get(name)

        # Deduct costs
        for cost in upgrade.costs:
            var = timestate.get_variable(cost.resource)
            if var:
                from variable import LinearVariable
                current = var.get(t)
                var.set(current - cost.amount, t)

        # Mark as purchased
        self._purchased.add(name)

        # Apply effects
        self._apply_effects(upgrade, timestate, t)

        return True

    def _apply_effects(self, upgrade: UpgradeDefinition, timestate, t: float):
        """Apply all effects of a purchased upgrade."""
        modifier_registry = get_modifier_registry()

        for effect in upgrade.effects:
            if effect.effect_type == "modifier":
                # Add modifier to the global modifier registry
                modifier = Modifier(
                    source=upgrade.name,
                    modifier_type=effect.params.get("modifier_type", "default"),
                    value=effect.params.get("value", 0.0),
                    target_param=effect.params.get("target_param", "rate"),
                    target_tags=effect.params.get("target_tags", [])
                )
                modifier_registry.add_modifier(modifier)

            elif effect.effect_type == "unlock_task":
                self._unlocked_tasks.add(effect.params.get("task_name", ""))

            elif effect.effect_type == "unlock_resource":
                self._unlocked_resources.add(effect.params.get("resource_name", ""))

            elif effect.effect_type == "unlock_upgrade":
                # This just makes the upgrade visible; it still needs to be purchased
                pass  # Handled by prerequisite checks

            elif effect.effect_type == "set_variable":
                var_name = effect.params.get("variable_name", "")
                value = effect.params.get("value", 0)
                var = timestate.get_variable(var_name)
                if var:
                    var.set(value, t)

            elif effect.effect_type == "add_variable":
                var_name = effect.params.get("variable_name", "")
                value = effect.params.get("value", 0)
                var = timestate.get_variable(var_name)
                if var:
                    from variable import LinearVariable
                    current = var.get(t)
                    var.set(current + value, t)

            elif effect.effect_type == "max_time_multiplier":
                multiplier = effect.params.get("multiplier", 1.0)
                self._max_time_multiplier *= multiplier

            elif effect.effect_type == "parallel_tasks":
                value = effect.params.get("value", 1)
                self._max_parallel_tasks = max(self._max_parallel_tasks, value)

    def mark_task_completed(self, task_name: str):
        """Mark a task as completed (for prerequisite checking)."""
        self._completed_tasks.add(task_name)

    def is_task_unlocked(self, task_name: str) -> bool:
        """Check if a task is unlocked (visible to the player)."""
        # A task is unlocked if it was explicitly unlocked OR if it has no unlock requirement
        return task_name in self._unlocked_tasks

    def is_resource_unlocked(self, resource_name: str) -> bool:
        """Check if a resource is unlocked (visible to the player)."""
        return resource_name in self._unlocked_resources

    def get_max_time_multiplier(self) -> float:
        """Get the current max_time multiplier from nexus upgrades."""
        return self._max_time_multiplier

    def get_max_parallel_tasks(self) -> int:
        """Get the maximum number of parallel tasks allowed."""
        return self._max_parallel_tasks

    def get_research_tree_layout(self) -> List[Tuple[UpgradeDefinition, List[str]]]:
        """Get research upgrades with their prerequisite connections for rendering.

        Returns:
            List of (upgrade, [prereq_names]) tuples for drawing the tree
        """
        research = self.get_by_type(UpgradeType.RESEARCH)
        result = []
        for upgrade in research:
            prereq_names = [
                p.target for p in upgrade.prerequisites
                if p.prereq_type in (PrerequisiteType.UPGRADE, PrerequisiteType.RESEARCH)
            ]
            result.append((upgrade, prereq_names))
        return result

    def get_purchase_state(self) -> Dict[str, bool]:
        """Get a dictionary of all upgrade names to their purchase state."""
        return {name: self.is_purchased(name) for name in self._upgrades}

    def load_purchase_state(self, state: Dict[str, bool]):
        """Load purchase state from saved data."""
        self._purchased = {name for name, purchased in state.items() if purchased}

    def reset(self):
        """Reset all purchase state (for new game)."""
        self._purchased.clear()
        self._unlocked_tasks.clear()
        self._unlocked_resources.clear()
        self._completed_tasks.clear()
        self._max_time_multiplier = 1.0
        self._max_parallel_tasks = 1
        get_modifier_registry().clear()

    def reset_non_nexus(self):
        """Reset non-nexus upgrades (for timeline reset/prestige).

        Nexus upgrades persist, regular and research upgrades reset.
        """
        modifier_registry = get_modifier_registry()

        # Find all non-nexus purchases
        nexus_upgrades = {u.name for u in self.get_by_type(UpgradeType.NEXUS)}
        non_nexus = self._purchased - nexus_upgrades

        # Remove modifiers from non-nexus upgrades
        for name in non_nexus:
            modifier_registry.remove_modifiers_from(name)

        # Remove from purchased set
        self._purchased -= non_nexus

        # Reset task unlocks (but keep nexus-granted ones)
        # For simplicity, we rebuild unlocks from remaining purchases
        self._unlocked_tasks.clear()
        self._unlocked_resources.clear()
        self._completed_tasks.clear()

        for name in self._purchased:
            upgrade = self.get(name)
            if upgrade:
                for effect in upgrade.effects:
                    if effect.effect_type == "unlock_task":
                        self._unlocked_tasks.add(effect.params.get("task_name", ""))
                    elif effect.effect_type == "unlock_resource":
                        self._unlocked_resources.add(effect.params.get("resource_name", ""))


# Global upgrade registry instance
_global_upgrade_registry: Optional[UpgradeRegistry] = None


def get_upgrade_registry() -> UpgradeRegistry:
    """Get the global upgrade registry, creating it if needed."""
    global _global_upgrade_registry
    if _global_upgrade_registry is None:
        _global_upgrade_registry = UpgradeRegistry()
    return _global_upgrade_registry


def reset_upgrade_registry():
    """Reset the global upgrade registry."""
    global _global_upgrade_registry
    _global_upgrade_registry = UpgradeRegistry()


# =============================================================================
# Upgrade Purchase Event
# =============================================================================

def create_purchase_event(upgrade_name: str, t: float):
    """Create an Event that purchases an upgrade at time t.

    This integrates the upgrade system with the timeline system.

    Args:
        upgrade_name: Name of the upgrade to purchase
        t: Time at which to purchase

    Returns:
        An Event instance that will purchase the upgrade when triggered
    """
    from timeline import Event, TimeState, Timeline

    upgrade = get_upgrade_registry().get(upgrade_name)
    if not upgrade:
        return None

    class UpgradePurchaseEvent(Event):
        """Event that purchases an upgrade."""

        def __init__(self, upgrade_def: UpgradeDefinition, time: float):
            super().__init__(
                name=f"purchase_{upgrade_def.name}",
                displayname=f"Purchase {upgrade_def.displayname}"
            )
            self.upgrade_def = upgrade_def
            self.t = time
            self.is_action = True  # Player-created event
            self.invalidate = False  # Persists across timeline changes

        def validate(self, timestate: TimeState, t: float) -> bool:
            """Check if upgrade can be purchased."""
            registry = get_upgrade_registry()
            return registry.can_purchase(self.upgrade_def.name, timestate, t)

        def on_start_vars(self, timestate: TimeState):
            """Purchase the upgrade and apply its effects."""
            registry = get_upgrade_registry()
            registry.purchase(self.upgrade_def.name, timestate, self.t)

    return UpgradePurchaseEvent(upgrade, t)


# =============================================================================
# Helper functions for creating upgrade definitions
# =============================================================================

def make_upgrade(
    name: str,
    displayname: str,
    description: str,
    upgrade_type: UpgradeType = UpgradeType.REGULAR,
    prerequisites: Optional[List[Tuple[str, str, float]]] = None,
    costs: Optional[List[Tuple[str, float]]] = None,
    effects: Optional[List[Tuple[str, Dict[str, Any]]]] = None,
    render_position: Tuple[float, float] = (0, 0),
    icon: str = "",
    tags: Optional[List[str]] = None
) -> UpgradeDefinition:
    """Helper function to create an UpgradeDefinition with simpler syntax.

    Args:
        name: Internal unique identifier
        displayname: Human-readable name
        description: Description text
        upgrade_type: Category (REGULAR/RESEARCH/NEXUS)
        prerequisites: List of (type_str, target, value) tuples
            e.g., [("upgrade", "basic_tools", 0), ("research", "metallurgy", 0)]
        costs: List of (resource_name, amount) tuples
        effects: List of (effect_type, params_dict) tuples
        render_position: (x, y) for research tree layout
        icon: Optional icon identifier
        tags: Tags for this upgrade

    Returns:
        A fully constructed UpgradeDefinition
    """
    prereq_type_map = {
        "upgrade": PrerequisiteType.UPGRADE,
        "research": PrerequisiteType.RESEARCH,
        "resource": PrerequisiteType.RESOURCE,
        "variable": PrerequisiteType.VARIABLE,
        "task": PrerequisiteType.TASK,
    }

    prereqs = []
    if prerequisites:
        for type_str, target, value in prerequisites:
            prereq_type = prereq_type_map.get(type_str, PrerequisiteType.UPGRADE)
            prereqs.append(Prerequisite(prereq_type, target, value))

    cost_list = []
    if costs:
        for resource, amount in costs:
            cost_list.append(UpgradeCost(resource, amount))

    effect_list = []
    if effects:
        for effect_type, params in effects:
            effect_list.append(UpgradeEffect(effect_type, params))

    return UpgradeDefinition(
        name=name,
        displayname=displayname,
        description=description,
        upgrade_type=upgrade_type,
        prerequisites=prereqs,
        costs=cost_list,
        effects=effect_list,
        render_position=render_position,
        icon=icon,
        tags=tags or []
    )


def make_rate_modifier_effect(
    modifier_type: str,
    value: float,
    target_tags: Optional[List[str]] = None
) -> Tuple[str, Dict[str, Any]]:
    """Helper to create a rate modifier effect.

    Args:
        modifier_type: Type string for stacking (e.g., "tools", "research")
        value: Modifier value (0.2 = +20%)
        target_tags: Tags to target (empty = all tasks)
    """
    return ("modifier", {
        "modifier_type": modifier_type,
        "value": value,
        "target_param": "rate",
        "target_tags": target_tags or []
    })


def make_consumed_modifier_effect(
    modifier_type: str,
    value: float,
    target_tags: Optional[List[str]] = None
) -> Tuple[str, Dict[str, Any]]:
    """Helper to create a consumption modifier effect.

    Args:
        modifier_type: Type string for stacking
        value: Modifier value (negative = less consumption)
        target_tags: Tags to target
    """
    return ("modifier", {
        "modifier_type": modifier_type,
        "value": value,
        "target_param": "consumed",
        "target_tags": target_tags or []
    })


def make_unlock_task_effect(task_name: str) -> Tuple[str, Dict[str, Any]]:
    """Helper to create a task unlock effect."""
    return ("unlock_task", {"task_name": task_name})


def make_unlock_resource_effect(resource_name: str) -> Tuple[str, Dict[str, Any]]:
    """Helper to create a resource unlock effect."""
    return ("unlock_resource", {"resource_name": resource_name})
