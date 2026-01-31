class Registry():
    vars: dict = None
    time: float = 0.0

    def __init__(self, t):
        self.time = t
        self.vars = {}
    
    def add_variable(self, var):
        self.vars[var.name] = var

    def get_variable(self, name):
        return self.vars.get(name, None)

    def keys(self):
        return self.vars.keys()

    def __getitem__(self, name):
        return self.vars[name]

    def __contains__(self, name):
        return name in self.vars

    def __delitem__(self, name):
        if name in self.vars:
            del self.vars[name]