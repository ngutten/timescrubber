from typing import List, Dict

class Variable():
    value: float = 0.0
    name: str = ""
    displayname: str = ""
    tags: List[str] = []

    def __init__(self, name, value=0, displayname=None):
        self.name = name
        self.value = value
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
        if target<self.min:
            return None
        if target>self.max:
            return None
        
        if self.rate>0:
            return (target-self.value)/self.rate + self.t0
        else:
            return None
