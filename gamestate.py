from timeline import Timeline

class GameState():
    timeline: Timeline = None

    def __init__(self, initial):
        self.timeline = Timeline(initial)