from typing import Dict, List
import bisect
from copy import deepcopy

from variable import Variable, LinearVariable
from timeline import TimeState, Timeline, Event
from registry import Registry
from gamestate import GameState


def create_initial_state() -> GameState:
    """Create the initial game state with starting resources."""
    initial = TimeState(0)

    # Resource variables (LinearVariable for time-based accumulation)
    initial.add_variable(LinearVariable("Stamina", value=5, min=0, max=10, rate=1))
    initial.add_variable(LinearVariable("Wood", min=0, max=100))
    initial.add_variable(LinearVariable("Stone", min=0, max=100))
    initial.add_variable(LinearVariable("Insights", min=0, max=100))

    # Building/item variables (discrete counts)
    initial.add_variable(Variable("Cot"))
    initial.add_variable(Variable("Table"))
    initial.add_variable(Variable("Study"))

    gamestate = GameState(initial)

    # Set initial max_time to allow timeline to work
    gamestate.timeline.max_time = 1000

    return gamestate


def main():
    """Main entry point - launches the GUI."""
    gamestate = create_initial_state()

    # Import and launch GUI
    from app_gui import create_app

    app = create_app(gamestate)
    app.run()


def main_cli():
    """CLI demo mode for testing without GUI."""
    gamestate = create_initial_state()
    gamestate.timeline.recompute(0)

    print("Timescrubber - CLI Demo Mode")
    print("=" * 40)
    print(f"State cache: {gamestate.timeline.state_cache}")
    print(f"Stamina at t=0: {gamestate.timeline.state_at(0).registry.get_variable('Stamina').get(0)}")
    print(f"Stamina at t=2: {gamestate.timeline.state_at(2).registry.get_variable('Stamina').get(2)}")
    print(f"Stamina at t=10: {gamestate.timeline.state_at(10).registry.get_variable('Stamina').get(10)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        main_cli()
    else:
        main()
