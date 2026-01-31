from typing import List, Dict

class Variable():
    value: float = 0.0
    name: str = ""
    displayname: str = ""
    tags: List[str] = None

    def __init__(self, name, value=0, displayname=None):
        self.name = name
        self.value = value
        self.tags = []
        if displayname:
            self.displayname = displayname

    def get(self, t):
        return self.value
    
    def set(self, x, t):
        self.value = x

class LinearVariable(Variable):
    t0: float = 0.0
    rate: float = 0.0
    min: float = 0.0
    max: float = 10000

    def __init__(self, name, value=0, displayname=None, min=0, max=10000, rate=0):
        super().__init__(name, value, displayname)

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
