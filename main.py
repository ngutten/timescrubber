from typing import Dict, List
import bisect
from copy import deepcopy

from variable import Variable, LinearVariable
from timeline import TimeState, Timeline, Event
from registry import Registry
from gamestate import GameState
from gamedefs import register_all_upgrades
from upgrades import get_upgrade_registry
from modifiers import get_modifier_registry


def create_initial_state() -> GameState:
    """Create the initial game state with starting resources."""
    initial = TimeState(0)

    # Resource variables (LinearVariable for time-based accumulation)
    # Basic resources - always visible
    initial.add_variable(LinearVariable("Stamina", value=5, min=0, max=10, rate=1,
                                         tags=["resource", "basic"], unlocked=True))
    initial.add_variable(LinearVariable("Wood", min=0, max=100,
                                         tags=["resource", "basic", "material"], unlocked=True))
    initial.add_variable(LinearVariable("Stone", min=0, max=100,
                                         tags=["resource", "basic", "material"], unlocked=True))
    initial.add_variable(LinearVariable("Insights", min=0, max=100,
                                         tags=["resource", "mental"], unlocked=True))

    # Advanced resources - unlocked through research
    initial.add_variable(LinearVariable("Ore", min=0, max=100,
                                         tags=["resource", "material", "advanced"], unlocked=False))
    initial.add_variable(LinearVariable("Metal", min=0, max=50,
                                         tags=["resource", "material", "advanced"], unlocked=False))

    # Meta-progression resource - persistent across resets
    initial.add_variable(Variable("Motes", value=0,
                                  tags=["resource", "meta", "persistent"], unlocked=True))

    # Building/item variables (discrete counts)
    initial.add_variable(Variable("Cot", tags=["building", "shelter"]))
    initial.add_variable(Variable("Table", tags=["building", "furniture"]))
    initial.add_variable(Variable("Study", tags=["building", "furniture"]))

    gamestate = GameState(initial)

    # Set initial max_time to allow timeline to work
    gamestate.timeline.max_time = 1000

    # Register all upgrade definitions
    register_all_upgrades()

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
    from gamedefs import (
        get_unlocked_activities, make_activity_task,
        REGULAR_UPGRADES, RESEARCH_UPGRADES, NEXUS_UPGRADES,
        get_research_tree_data
    )
    from upgrades import create_purchase_event, UpgradeType

    gamestate = create_initial_state()
    gamestate.timeline.recompute(0)

    print("Timescrubber - CLI Demo Mode")
    print("=" * 60)

    # Show basic state info
    print("\n--- Basic State ---")
    print(f"Stamina at t=0: {gamestate.timeline.state_at(0).registry.get_variable('Stamina').get(0)}")
    print(f"Stamina at t=5: {gamestate.timeline.state_at(5).registry.get_variable('Stamina').get(5)}")

    # Show unlocked activities
    print("\n--- Unlocked Activities ---")
    for activity in get_unlocked_activities():
        tags = activity.get("tags", [])
        print(f"  {activity['displayname']}: tags={tags}")

    # Show upgrade categories
    print("\n--- Regular Upgrades ---")
    for upgrade in REGULAR_UPGRADES:
        costs_str = ", ".join(f"{c.amount} {c.resource}" for c in upgrade.costs)
        print(f"  {upgrade.displayname}: {costs_str}")

    print("\n--- Research Upgrades ---")
    for upgrade in RESEARCH_UPGRADES:
        costs_str = ", ".join(f"{c.amount} {c.resource}" for c in upgrade.costs)
        pos = upgrade.render_position
        print(f"  {upgrade.displayname} at ({pos[0]}, {pos[1]}): {costs_str}")

    print("\n--- Nexus Upgrades ---")
    for upgrade in NEXUS_UPGRADES:
        costs_str = ", ".join(f"{c.amount} {c.resource}" for c in upgrade.costs)
        print(f"  {upgrade.displayname}: {costs_str}")

    # Demonstrate modifier system
    print("\n--- Modifier System Demo ---")
    upgrade_registry = get_upgrade_registry()
    modifier_registry = get_modifier_registry()

    # Give player some resources to test with
    ts = gamestate.timeline.state_at(0)
    ts.get_variable("Wood").set(50, 0)
    ts.get_variable("Stone").set(30, 0)
    ts.get_variable("Insights").set(20, 0)

    # Show base gathering rate
    print(f"Base gathering task rate: 10 (gather_wood)")

    # Purchase sharp_tools upgrade
    print("\nPurchasing 'Sharp Tools' upgrade...")
    if upgrade_registry.can_purchase("sharp_tools", ts, 0):
        upgrade_registry.purchase("sharp_tools", ts, 0)
        print("  Purchased!")

        # Show modifier effect
        from modifiers import apply_rate_modifier
        modified_rate = apply_rate_modifier(10, ["gathering"])
        print(f"  Modified gathering rate: {modified_rate} (+15%)")
    else:
        print("  Cannot purchase (check prerequisites or costs)")

    # Show research tree structure
    print("\n--- Research Tree Structure ---")
    research_data = get_research_tree_data()
    for node in research_data:
        prereqs = ", ".join(node["prerequisites"]) if node["prerequisites"] else "None"
        print(f"  {node['displayname']} @ {node['position']}")
        print(f"    Prerequisites: {prereqs}")
        print(f"    Visible: {node['visible']}")

    print("\n" + "=" * 60)
    print("Demo complete!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        main_cli()
    else:
        main()
