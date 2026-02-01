# Modifier System for Timescrubber
#
# Modifiers are stacking effects that modify game values. Each modifier has a "type"
# string that determines how it combines with other modifiers:
# - Modifiers of the SAME type are ADDITIVE (e.g., two +20% speed bonuses = +40%)
# - Modifiers of DIFFERENT types are MULTIPLICATIVE (e.g., +20% from tools * +20% from research = +44%)
#
# This allows for interesting upgrade interactions where different sources of
# bonuses stack multiplicatively while similar bonuses stack additively.

from typing import Dict, List, Optional, Tuple, Set
from dataclasses import dataclass, field


@dataclass
class Modifier:
    """A single modifier that affects a game value.

    Attributes:
        source: The source of this modifier (e.g., upgrade name)
        modifier_type: The type of modifier (e.g., "tools", "research", "nexus")
                      Modifiers of the same type are additive, different types multiply
        value: The modifier value (e.g., 0.2 for +20%, -0.1 for -10%)
        target_param: The parameter being modified (e.g., "rate", "consumed", "produced")
        target_tags: Tags that must match for this modifier to apply (e.g., ["gathering"])
                    If empty, applies to all matching parameters
    """
    source: str
    modifier_type: str
    value: float
    target_param: str
    target_tags: List[str] = field(default_factory=list)

    def applies_to(self, param: str, tags: List[str]) -> bool:
        """Check if this modifier applies to a given parameter and tag set.

        Args:
            param: The parameter name to check
            tags: The tags of the target (Task, Process, etc.)

        Returns:
            True if this modifier applies to the target
        """
        # Must match parameter
        if self.target_param != param:
            return False

        # If no target tags specified, applies to all
        if not self.target_tags:
            return True

        # Must have at least one matching tag
        return any(tag in tags for tag in self.target_tags)


class ModifierStack:
    """A collection of modifiers that can be combined to get a final multiplier.

    The stack groups modifiers by type, sums within each type, then multiplies
    across types to get the final value.

    Example:
        - Tools upgrade: +20% gathering speed (type="tools")
        - Better tools upgrade: +15% gathering speed (type="tools")
        - Research bonus: +10% gathering speed (type="research")

        Result: (1 + 0.20 + 0.15) * (1 + 0.10) = 1.35 * 1.10 = 1.485 = +48.5%
    """

    def __init__(self):
        self._modifiers: List[Modifier] = []

    def add(self, modifier: Modifier):
        """Add a modifier to the stack."""
        self._modifiers.append(modifier)

    def remove_by_source(self, source: str):
        """Remove all modifiers from a specific source."""
        self._modifiers = [m for m in self._modifiers if m.source != source]

    def clear(self):
        """Remove all modifiers."""
        self._modifiers = []

    def get_modifiers(self) -> List[Modifier]:
        """Get all modifiers in the stack."""
        return self._modifiers.copy()

    def get_modifiers_for(self, param: str, tags: List[str]) -> List[Modifier]:
        """Get all modifiers that apply to a given parameter and tags."""
        return [m for m in self._modifiers if m.applies_to(param, tags)]

    def calculate_multiplier(self, param: str, tags: List[str]) -> float:
        """Calculate the final multiplier for a parameter with given tags.

        Groups applicable modifiers by type, sums within types (additive),
        then multiplies across types.

        Args:
            param: The parameter being modified
            tags: The tags to check against

        Returns:
            The final multiplier (1.0 = no change, 1.2 = +20%, 0.8 = -20%)
        """
        applicable = self.get_modifiers_for(param, tags)

        if not applicable:
            return 1.0

        # Group by modifier type
        by_type: Dict[str, float] = {}
        for mod in applicable:
            if mod.modifier_type not in by_type:
                by_type[mod.modifier_type] = 0.0
            by_type[mod.modifier_type] += mod.value

        # Multiply across types (each type contributes (1 + sum_of_values))
        result = 1.0
        for type_sum in by_type.values():
            result *= (1.0 + type_sum)

        return result

    def calculate_additive(self, param: str, tags: List[str]) -> float:
        """Calculate a purely additive sum of all matching modifiers.

        Unlike calculate_multiplier, this just sums all values without
        the type-based grouping. Useful for flat bonuses.

        Args:
            param: The parameter being modified
            tags: The tags to check against

        Returns:
            The sum of all modifier values
        """
        applicable = self.get_modifiers_for(param, tags)
        return sum(m.value for m in applicable)


class ModifierRegistry:
    """Global registry of all active modifiers in the game.

    This is the main interface for the modifier system. Other systems
    (upgrades, timeline) add modifiers here and query for final values.
    """

    def __init__(self):
        self._stack = ModifierStack()

    def add_modifier(self, modifier: Modifier):
        """Add a modifier to the registry."""
        self._stack.add(modifier)

    def remove_modifiers_from(self, source: str):
        """Remove all modifiers from a specific source (e.g., when upgrade is removed)."""
        self._stack.remove_by_source(source)

    def clear(self):
        """Clear all modifiers."""
        self._stack.clear()

    def get_multiplier(self, param: str, tags: Optional[List[str]] = None) -> float:
        """Get the final multiplier for a parameter.

        Args:
            param: The parameter name (e.g., "rate", "consumed", "produced")
            tags: Optional tags to filter by (e.g., ["gathering", "wood"])

        Returns:
            The combined multiplier from all applicable modifiers
        """
        return self._stack.calculate_multiplier(param, tags or [])

    def get_additive_bonus(self, param: str, tags: Optional[List[str]] = None) -> float:
        """Get the sum of all additive bonuses for a parameter.

        Args:
            param: The parameter name
            tags: Optional tags to filter by

        Returns:
            The sum of all applicable modifier values
        """
        return self._stack.calculate_additive(param, tags or [])

    def get_all_modifiers(self) -> List[Modifier]:
        """Get all active modifiers."""
        return self._stack.get_modifiers()

    def get_modifiers_for(self, param: str, tags: Optional[List[str]] = None) -> List[Modifier]:
        """Get all modifiers that apply to a parameter and tags."""
        return self._stack.get_modifiers_for(param, tags or [])


# Global modifier registry instance
# This is used throughout the game to track active modifiers
_global_registry: Optional[ModifierRegistry] = None


def get_modifier_registry() -> ModifierRegistry:
    """Get the global modifier registry, creating it if needed."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ModifierRegistry()
    return _global_registry


def reset_modifier_registry():
    """Reset the global modifier registry. Useful for testing or new games."""
    global _global_registry
    _global_registry = ModifierRegistry()


# Convenience functions for common operations

def apply_rate_modifier(base_rate: float, tags: List[str]) -> float:
    """Apply rate modifiers to a base rate value.

    Args:
        base_rate: The base rate before modifiers
        tags: Tags of the target (Task, Process, etc.)

    Returns:
        The modified rate
    """
    registry = get_modifier_registry()
    multiplier = registry.get_multiplier("rate", tags)
    return base_rate * multiplier


def apply_consumed_modifier(base_consumed: List[Tuple[str, float]], tags: List[str]) -> List[Tuple[str, float]]:
    """Apply consumption modifiers to resource consumption rates.

    Args:
        base_consumed: List of (resource_name, rate) tuples
        tags: Tags of the target

    Returns:
        Modified list of (resource_name, rate) tuples
    """
    registry = get_modifier_registry()
    multiplier = registry.get_multiplier("consumed", tags)
    return [(name, rate * multiplier) for name, rate in base_consumed]


def apply_produced_modifier(base_produced: List[Tuple[str, float]], tags: List[str]) -> List[Tuple[str, float]]:
    """Apply production modifiers to resource production rates.

    Args:
        base_produced: List of (resource_name, rate) tuples
        tags: Tags of the target

    Returns:
        Modified list of (resource_name, rate) tuples
    """
    registry = get_modifier_registry()
    multiplier = registry.get_multiplier("produced", tags)
    return [(name, rate * multiplier) for name, rate in base_produced]
