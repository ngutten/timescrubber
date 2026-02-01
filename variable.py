from typing import List, Dict, Optional


class Variable():
    """A basic named variable with a value and optional tags.

    Attributes:
        name: Internal unique identifier
        displayname: Human-readable name for UI
        value: Current value
        tags: List of tags for categorization (e.g., ["resource", "basic"])
        unlocked: Whether this variable is visible to the player
    """
    value: float = 0.0
    name: str = ""
    displayname: str = ""
    tags: List[str] = None
    unlocked: bool = True  # Whether visible in UI (for unlock system)

    def __init__(self, name: str, value: float = 0, displayname: Optional[str] = None,
                 tags: Optional[List[str]] = None, unlocked: bool = True):
        self.name = name
        self.value = value
        self.tags = tags if tags is not None else []
        self.unlocked = unlocked
        if displayname:
            self.displayname = displayname
        else:
            self.displayname = name

    def get(self, t: float) -> float:
        return self.value

    def set(self, x: float, t: float):
        self.value = x

    def has_tag(self, tag: str) -> bool:
        """Check if this variable has a specific tag."""
        return tag in self.tags

    def has_any_tag(self, tags: List[str]) -> bool:
        """Check if this variable has any of the specified tags."""
        return any(tag in self.tags for tag in tags)

    def add_tag(self, tag: str):
        """Add a tag to this variable."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str):
        """Remove a tag from this variable."""
        if tag in self.tags:
            self.tags.remove(tag)

class LinearVariable(Variable):
    """A variable that changes linearly over time.

    The value at any time t is calculated as:
        clamp((t - t0) * rate + value, min, max)

    Attributes:
        t0: Reference time for the linear calculation
        rate: Change per time unit (can be negative)
        min: Minimum value (clamped)
        max: Maximum value (clamped)
    """
    t0: float = 0.0
    rate: float = 0.0
    min: float = 0.0
    max: float = 10000

    def __init__(self, name: str, value: float = 0, displayname: Optional[str] = None,
                 min: float = 0, max: float = 10000, rate: float = 0,
                 tags: Optional[List[str]] = None, unlocked: bool = True):
        super().__init__(name, value, displayname, tags, unlocked)

        self.min = min
        self.max = max
        self.rate = rate

    def get(self, t):
        x = (t-self.t0)*self.rate + self.value
        if x<self.min:
            return self.min
        if x>self.max:
            return self.max
        
        return x
    
    def set(self, x, t):
        self.value = x
        self.t0 = t

    def rehome(self, t):
        x = self.get(t)
        self.value = x
        self.t0 = t

    def when(self, target):
        """Calculate when this variable will reach the target value.

        Returns the time when target is reached, or None if:
        - Target is outside min/max bounds
        - Rate is zero (value never changes)
        - Rate direction means we're moving away from target
        """
        if target < self.min or target > self.max:
            return None

        if self.rate == 0:
            # Value is constant - only reaches target if already there
            return self.t0 if self.value == target else None

        # Calculate time to reach target
        t = (target - self.value) / self.rate + self.t0

        # Only return if the time is in the future (or present)
        if t >= self.t0:
            return t
        else:
            return None
