#!/usr/bin/env python3
"""Test script for time-aware research prerequisites."""

from variable import Variable, LinearVariable
from timeline import TimeState, Timeline, Event
from gamestate import GameState
from gamedefs import (
    register_all_upgrades, get_unlocked_activities, is_activity_unlocked
)
from upgrades import get_upgrade_registry, reset_upgrade_registry, create_purchase_event


def create_test_state() -> GameState:
    """Create a test game state with resources."""
    initial = TimeState(0)

    # Basic resources
    initial.add_variable(LinearVariable("Stamina", value=5, min=0, max=10, rate=1,
                                         tags=["resource", "basic"], unlocked=True))
    initial.add_variable(LinearVariable("Wood", min=0, max=100,
                                         tags=["resource", "basic", "material"], unlocked=True))
    initial.add_variable(LinearVariable("Stone", min=0, max=100,
                                         tags=["resource", "basic", "material"], unlocked=True))
    initial.add_variable(LinearVariable("Insights", value=100, min=0, max=200,
                                         tags=["resource", "mental"], unlocked=True))

    # Advanced resources
    initial.add_variable(LinearVariable("Ore", min=0, max=100,
                                         tags=["resource", "material", "advanced"], unlocked=False))
    initial.add_variable(LinearVariable("Metal", min=0, max=50,
                                         tags=["resource", "material", "advanced"], unlocked=False))

    gamestate = GameState(initial)
    gamestate.timeline.max_time = 1000

    return gamestate


def test_research_prerequisites():
    """Test that research prerequisites are respected with timeline scrubbing."""
    print("=" * 60)
    print("Test: Research Prerequisites and Timeline Scrubbing")
    print("=" * 60)

    # Reset the upgrade registry to start fresh
    reset_upgrade_registry()
    register_all_upgrades()

    gamestate = create_test_state()
    timeline = gamestate.timeline

    # Get initial state
    ts_t0 = timeline.state_at(0)

    # Test 1: Mine Ore should NOT be unlocked at t=0 (requires mining_basics research)
    print("\n--- Test 1: Initial State at t=0 ---")
    print(f"is_activity_unlocked('mine_ore', ts_t0): {is_activity_unlocked('mine_ore', ts_t0)}")
    print(f"Unlocked activities at t=0:")
    for a in get_unlocked_activities(ts_t0):
        print(f"  - {a['displayname']}")

    # Verify mine_ore is NOT in the list
    unlocked_names = [a['name'] for a in get_unlocked_activities(ts_t0)]
    assert 'mine_ore' not in unlocked_names, "ERROR: mine_ore should NOT be unlocked at t=0"
    print("PASS: mine_ore is correctly NOT available at t=0")

    # Test 2: Purchase basic_knowledge at t=30, mining_basics at t=60
    print("\n--- Test 2: Purchase Research at t=30 and t=60 ---")

    # First, we need to purchase basic_knowledge (prereq for mining_basics)
    basic_knowledge_event = create_purchase_event("basic_knowledge", 30)
    if basic_knowledge_event:
        timeline.add_event(basic_knowledge_event)
        print("Purchased basic_knowledge at t=30")

    # Now purchase mining_basics at t=60
    mining_basics_event = create_purchase_event("mining_basics", 60)
    if mining_basics_event:
        timeline.add_event(mining_basics_event)
        print("Purchased mining_basics at t=60")

    # Test 3: Check state at t=50 (before mining_basics was purchased)
    print("\n--- Test 3: State at t=50 (before mining_basics purchase) ---")
    ts_t50 = timeline.state_at(50)
    print(f"is_activity_unlocked('mine_ore', ts_t50): {is_activity_unlocked('mine_ore', ts_t50)}")
    print(f"basic_knowledge purchased at t=50: {ts_t50.is_upgrade_purchased('basic_knowledge')}")
    print(f"mining_basics purchased at t=50: {ts_t50.is_upgrade_purchased('mining_basics')}")

    unlocked_at_50 = [a['name'] for a in get_unlocked_activities(ts_t50)]
    assert 'mine_ore' not in unlocked_at_50, "ERROR: mine_ore should NOT be unlocked at t=50"
    print("PASS: mine_ore is correctly NOT available at t=50")

    # Test 4: Check state at t=70 (after mining_basics was purchased)
    print("\n--- Test 4: State at t=70 (after mining_basics purchase) ---")
    ts_t70 = timeline.state_at(70)
    print(f"is_activity_unlocked('mine_ore', ts_t70): {is_activity_unlocked('mine_ore', ts_t70)}")
    print(f"basic_knowledge purchased at t=70: {ts_t70.is_upgrade_purchased('basic_knowledge')}")
    print(f"mining_basics purchased at t=70: {ts_t70.is_upgrade_purchased('mining_basics')}")

    unlocked_at_70 = [a['name'] for a in get_unlocked_activities(ts_t70)]
    assert 'mine_ore' in unlocked_at_70, "ERROR: mine_ore SHOULD be unlocked at t=70"
    print("PASS: mine_ore is correctly available at t=70")

    # Test 5: Verify timeline events show the research purchases
    print("\n--- Test 5: Timeline Events ---")
    print("Events on timeline:")
    for event in timeline.events:
        print(f"  t={event.t}: {event.displayname} (is_action={event.is_action})")

    # Test 6: Scrub back to t=25 (before basic_knowledge)
    print("\n--- Test 6: Scrub back to t=25 ---")
    ts_t25 = timeline.state_at(25)
    print(f"basic_knowledge purchased at t=25: {ts_t25.is_upgrade_purchased('basic_knowledge')}")
    print(f"mining_basics purchased at t=25: {ts_t25.is_upgrade_purchased('mining_basics')}")
    assert not ts_t25.is_upgrade_purchased('basic_knowledge'), \
        "ERROR: basic_knowledge should NOT be purchased at t=25"
    assert not ts_t25.is_upgrade_purchased('mining_basics'), \
        "ERROR: mining_basics should NOT be purchased at t=25"
    print("PASS: No research is purchased at t=25")

    # Test 7: Verify prerequisite checking for mining_basics at different times
    print("\n--- Test 7: Prerequisite checking at different times ---")
    registry = get_upgrade_registry()

    # At t=25: basic_knowledge not purchased, so mining_basics prereqs NOT met
    print(f"Can purchase mining_basics at t=25: {registry.can_purchase('mining_basics', ts_t25, 25)}")

    # At t=50: basic_knowledge purchased, so mining_basics prereqs ARE met
    print(f"Can purchase mining_basics at t=50: {registry.can_purchase('mining_basics', ts_t50, 50)}")

    # At t=70: mining_basics already purchased, so cannot purchase again
    print(f"Can purchase mining_basics at t=70: {registry.can_purchase('mining_basics', ts_t70, 70)}")

    print("\n" + "=" * 60)
    print("All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    test_research_prerequisites()
