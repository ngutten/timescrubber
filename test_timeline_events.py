"""
Test for timeline event functionality.

This test verifies:
1. Events can add resources at specific times
2. Events can consume resources to produce other resources
3. Validation prevents events from triggering when resources are insufficient
4. Removing an event properly invalidates dependent events
"""

from variable import Variable, LinearVariable
from timeline import TimeState, Timeline, Event
from gamestate import GameState


class GiveWoodEvent(Event):
    """Event that gives Wood at a specific time."""
    amount: float = 0.0

    def __init__(self, time: float, amount: float):
        super().__init__("give_wood")
        self.time = time
        self.amount = amount

    def on_start_vars(self, timestate: TimeState):
        wood = timestate.get_variable("Wood")
        current = wood.get(self.time)
        wood.set(current + self.amount, self.time)


class ConvertWoodToStoneEvent(Event):
    """Event that consumes Wood to produce Stone."""
    wood_cost: float = 0.0
    stone_produced: float = 0.0

    def __init__(self, time: float, wood_cost: float, stone_produced: float):
        super().__init__("convert_wood_to_stone")
        self.time = time
        self.wood_cost = wood_cost
        self.stone_produced = stone_produced
        self.invalidate = True  # This event should be re-validated on recompute

    def validate(self, timestate: TimeState, t: float) -> bool:
        """Check if there's enough Wood to perform the conversion."""
        wood = timestate.get_variable("Wood")
        current_wood = wood.get(t)
        return current_wood >= self.wood_cost

    def on_start_vars(self, timestate: TimeState):
        # Consume Wood
        wood = timestate.get_variable("Wood")
        current_wood = wood.get(self.time)
        wood.set(current_wood - self.wood_cost, self.time)

        # Produce Stone
        stone = timestate.get_variable("Stone")
        current_stone = stone.get(self.time)
        stone.set(current_stone + self.stone_produced, self.time)


def create_test_state() -> GameState:
    """Create a test game state with Wood and Stone variables."""
    initial = TimeState(0)

    # Resource variables (start with 0)
    initial.add_variable(LinearVariable("Wood", value=0, min=0, max=100))
    initial.add_variable(LinearVariable("Stone", value=0, min=0, max=100))

    gamestate = GameState(initial)
    gamestate.timeline.max_time = 100

    return gamestate


def test_timeline_events():
    """Test adding and removing events on the timeline."""
    print("=" * 60)
    print("Timeline Events Test")
    print("=" * 60)

    # Create the game state
    gamestate = create_test_state()
    timeline = gamestate.timeline

    # Create event at t=5 that gives 5 Wood
    give_wood_event = GiveWoodEvent(time=5, amount=5)
    print("\n1. Adding event at t=5: Give 5 Wood")
    timeline.add_event(give_wood_event)

    # Check Wood at t=6 (after the event)
    wood_at_6 = timeline.state_at(6).get_variable("Wood").get(6)
    print(f"   Wood at t=6: {wood_at_6}")

    # Create event at t=7 that consumes 3 Wood to produce 5 Stone
    convert_event = ConvertWoodToStoneEvent(time=7, wood_cost=3, stone_produced=5)
    print("\n2. Adding event at t=7: Consume 3 Wood -> Produce 5 Stone")
    timeline.add_event(convert_event)

    # Check resources at t=9
    state_at_9 = timeline.state_at(9)
    wood_at_9 = state_at_9.get_variable("Wood").get(9)
    stone_at_9 = state_at_9.get_variable("Stone").get(9)
    print(f"\n3. Resources at t=9:")
    print(f"   Wood: {wood_at_9}")
    print(f"   Stone: {stone_at_9}")

    # Remove the event at t=5
    print("\n4. Removing event at t=5 (Give 5 Wood)")
    timeline.remove_event(give_wood_event)

    # Check that the t=7 event was invalidated (should not have produced Stone)
    print("\n5. After removing the t=5 event:")
    print(f"   Events remaining: {[e.name for e in timeline.events]}")

    # Check resources at t=9 again
    state_at_9_after = timeline.state_at(9)
    wood_at_9_after = state_at_9_after.get_variable("Wood").get(9)
    stone_at_9_after = state_at_9_after.get_variable("Stone").get(9)
    print(f"\n6. Resources at t=9 (after removing t=5 event):")
    print(f"   Wood: {wood_at_9_after}")
    print(f"   Stone: {stone_at_9_after}")

    # Verify the expected behavior
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)

    success = True

    # Check initial state worked correctly
    if stone_at_9 == 5:
        print("✓ Stone at t=9 (with t=5 event): 5 (correct)")
    else:
        print(f"✗ Stone at t=9 (with t=5 event): {stone_at_9} (expected 5)")
        success = False

    # Check that removing t=5 event invalidated the t=7 event
    if stone_at_9_after == 0:
        print("✓ Stone at t=9 (without t=5 event): 0 (correct - event was invalidated)")
    else:
        print(f"✗ Stone at t=9 (without t=5 event): {stone_at_9_after} (expected 0)")
        success = False

    # Check that the convert event was removed from the list (since invalidate=True)
    if convert_event not in timeline.events:
        print("✓ Convert event was removed from timeline (invalidate=True)")
    else:
        print("✗ Convert event still in timeline (expected removal)")
        success = False

    print("\n" + "=" * 60)
    if success:
        print("All tests passed!")
    else:
        print("Some tests failed.")
    print("=" * 60)

    return success


if __name__ == "__main__":
    test_timeline_events()
