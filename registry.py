class Registry():
    vars: dict = {}
    time: float = 0.0

    def __init__(self, t):
        self.time = t
    
    def add_variable(self, var):
        self.vars[var.name] = var

    def get_variable(self, name):
        return self.vars[name]