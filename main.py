from typing import Dict, List
import bisect
from copy import deepcopy

from variable import Variable, LinearVariable
from timeline import TimeState, Timeline, Event
from registry import Registry
from gamestate import GameState

def main():
    initial = TimeState(0)
    
    initial.add_variable(LinearVariable("Stamina", min=0, max=10, rate=1))
    initial.add_variable(LinearVariable("Wood", min=0, max=10))
    initial.add_variable(LinearVariable("Stone", min=0, max=10))
    initial.add_variable(LinearVariable("Insights", min=0, max=100))
    
    initial.add_variable(Variable("Cot"))
    initial.add_variable(Variable("Table"))
    initial.add_variable(Variable("Study"))

    gamestate = GameState(initial)
    gamestate.timeline.recompute(0)
    
    print(gamestate.timeline.state_cache)    
    print(gamestate.timeline.state_at(2).registry.get_variable("Stamina").get(2))

if __name__ == "__main__":
    main()
