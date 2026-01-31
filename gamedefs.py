# Game Content Definitions for Timescrubber
#
# This module contains all game content definitions - activities, resources,
# screens, settings, etc. GUI code should import from here rather than
# defining content inline.

from typing import Dict, List, Any, Optional

# =============================================================================
# ACTIVITY DEFINITIONS
# =============================================================================

# Each activity has:
# - name: Internal name (used for uniqueness)
# - displayname: Display name shown to player
# - description: Full description text
# - rate: Progress rate (100/rate = time to complete)
# - consumed: List of (resource_name, rate) tuples for resources consumed over time
# - produced: List of (resource_name, rate) tuples for resources produced over time
# - on_complete_give: Dict of resource_name -> amount given on completion
# - requirements: Dict of resource_name -> minimum amount needed to start

ACTIVITIES: List[Dict[str, Any]] = [
    {
        "name": "rest",
        "displayname": "Rest",
        "description": (
            "Take a break and recover your stamina. "
            "Stamina is essential for performing most activities. "
            "Resting accelerates stamina recovery."
        ),
        "rate": 20,  # 5 time units to complete
        "consumed": [],
        "produced": [("Stamina", 1)],  # Extra +1 stamina/time while resting
        "on_complete_give": {},
        "requirements": {},
    },
    {
        "name": "gather_wood",
        "displayname": "Gather Wood",
        "description": (
            "Collect wood from nearby trees. "
            "Wood is a basic resource used in many crafting recipes."
        ),
        "rate": 10,  # 10 time units to complete
        "consumed": [("Stamina", 0.5)],  # Consumes 0.5 stamina per time
        "produced": [],
        "on_complete_give": {"Wood": 5},  # Get 5 wood on completion
        "requirements": {"Stamina": 2},
    },
    {
        "name": "gather_stone",
        "displayname": "Gather Stone",
        "description": (
            "Search for and collect stone. "
            "Stone is needed for tools and building structures."
        ),
        "rate": 8,  # 12.5 time units to complete
        "consumed": [("Stamina", 0.6)],
        "produced": [],
        "on_complete_give": {"Stone": 3},
        "requirements": {"Stamina": 3},
    },
    {
        "name": "craft_tools",
        "displayname": "Craft Basic Tools",
        "description": (
            "Create simple tools to improve efficiency. "
            "Tools make gathering and building faster."
        ),
        "rate": 5,  # 20 time units to complete
        "consumed": [("Stamina", 0.2)],
        "produced": [],
        "on_complete_give": {"Wood": -5, "Stone": -2},  # Consumes materials on completion
        "requirements": {"Wood": 5, "Stone": 2},
    },
    {
        "name": "build_shelter",
        "displayname": "Build Shelter",
        "description": (
            "Construct a basic shelter for protection. "
            "Shelters provide bonuses to resting and storage."
        ),
        "rate": 2,  # 50 time units to complete
        "consumed": [("Stamina", 0.3)],
        "produced": [],
        "on_complete_give": {"Wood": -20, "Stone": -10},
        "requirements": {"Wood": 20, "Stone": 10},
    },
    {
        "name": "explore",
        "displayname": "Explore Area",
        "description": (
            "Scout the surrounding area to discover new locations "
            "and resources."
        ),
        "rate": 5,  # 20 time units
        "consumed": [("Stamina", 0.4)],
        "produced": [],
        "on_complete_give": {"Insights": 2},
        "requirements": {"Stamina": 5},
    },
    {
        "name": "meditate",
        "displayname": "Meditate",
        "description": (
            "Quiet contemplation to gain insights. "
            "Insights are used for research and upgrades."
        ),
        "rate": 10,  # 10 time units
        "consumed": [("Stamina", 0.1)],
        "produced": [("Insights", 0.2)],  # Produces insights over time
        "on_complete_give": {},
        "requirements": {"Stamina": 1},
    },
    {
        "name": "study",
        "displayname": "Study",
        "description": (
            "Study your surroundings and acquired knowledge to unlock "
            "new abilities and understanding."
        ),
        "rate": 4,  # 25 time units
        "consumed": [("Insights", 0.2), ("Stamina", 0.1)],
        "produced": [],
        "on_complete_give": {},
        "requirements": {"Insights": 5},
    },
]


def get_activity_names() -> List[str]:
    """Return list of all activity display names."""
    return [a["displayname"] for a in ACTIVITIES]


def get_activity_by_displayname(displayname: str) -> Optional[Dict[str, Any]]:
    """Get full activity definition by display name."""
    for activity in ACTIVITIES:
        if activity["displayname"] == displayname:
            return activity
    return None


def get_activity_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Get full activity definition by internal name."""
    for activity in ACTIVITIES:
        if activity["name"] == name:
            return activity
    return None


def get_activity_description(displayname: str) -> str:
    """Get description for an activity by display name."""
    activity = get_activity_by_displayname(displayname)
    if activity:
        return activity["description"]
    return "No description available."


def get_activity_requirements(displayname: str) -> Dict[str, int]:
    """Get requirements dict for an activity by display name."""
    activity = get_activity_by_displayname(displayname)
    if activity:
        return activity.get("requirements", {})
    return {}


def format_requirements(requirements: Dict[str, int]) -> str:
    """Format requirements dict as display string."""
    if not requirements:
        return "None"
    return ", ".join(f"{res}: {amt}" for res, amt in requirements.items())


def format_consumed_produced(activity: Dict[str, Any]) -> str:
    """Format consumed and produced resources as display string."""
    parts = []
    consumed = activity.get("consumed", [])
    produced = activity.get("produced", [])

    if consumed:
        consumed_str = ", ".join(f"-{rate} {name}/t" for name, rate in consumed)
        parts.append(f"Consumes: {consumed_str}")

    if produced:
        produced_str = ", ".join(f"+{rate} {name}/t" for name, rate in produced)
        parts.append(f"Produces: {produced_str}")

    on_complete = activity.get("on_complete_give", {})
    if on_complete:
        complete_parts = []
        for res, amt in on_complete.items():
            if amt > 0:
                complete_parts.append(f"+{amt} {res}")
            elif amt < 0:
                complete_parts.append(f"{amt} {res}")
        if complete_parts:
            parts.append(f"On complete: {', '.join(complete_parts)}")

    return "\n".join(parts) if parts else "No resource effects"


def make_activity_task(displayname: str, t: float):
    """Create a Task instance for an activity with completion rewards.

    Args:
        displayname: The display name of the activity
        t: The time at which to start the task

    Returns:
        A Task instance ready to be added to the timeline, or None if not found
    """
    from timeline import Task
    from variable import LinearVariable, Variable

    activity = get_activity_by_displayname(displayname)
    if not activity:
        return None

    # Create a custom Task class for this activity
    on_complete_give = activity.get("on_complete_give", {})

    class _ActivityTask(Task):
        """Task that applies on_complete_give resources when finished."""

        def on_finish_vars(self, timestate):
            """Apply completion rewards/costs."""
            for var_name, amount in on_complete_give.items():
                var = timestate.get_variable(var_name)
                if var:
                    if isinstance(var, LinearVariable):
                        current = var.get(timestate.time)
                        var.set(current + amount, timestate.time)
                    elif isinstance(var, Variable):
                        var.set(var.get(timestate.time) + amount, timestate.time)

    # Create the task instance
    task = _ActivityTask(
        name=activity["name"],
        rate=activity["rate"],
        displayname=activity["displayname"],
        consumed=activity.get("consumed", []),
        produced=activity.get("produced", [])
    )
    task.t = t
    task.is_action = True  # Player-created event

    return task


# =============================================================================
# SCREEN/TAB DEFINITIONS
# =============================================================================

# Each screen has:
# - key: Internal identifier
# - tab_text: Text shown on tab
# - title: Screen title
# - description: Description shown on placeholder screens

SCREENS: List[Dict[str, str]] = [
    {
        "key": "activities",
        "tab_text": "Activities",
        "title": "Activities",
        "description": "",  # Has custom implementation
    },
    {
        "key": "upgrades",
        "tab_text": "Upgrades",
        "title": "Upgrades",
        "description": (
            "Upgrade your abilities and tools to become more efficient.\n\n"
            "Upgrades are permanent improvements that persist across runs."
        ),
    },
    {
        "key": "nexus",
        "tab_text": "Nexus",
        "title": "Nexus Upgrades",
        "description": (
            "Meta-progression upgrades that affect all timelines.\n\n"
            "Nexus upgrades are earned through special achievements and milestones."
        ),
    },
    {
        "key": "research",
        "tab_text": "Research",
        "title": "Research",
        "description": (
            "Unlock new technologies and abilities through research.\n\n"
            "Research requires Insights and time to complete."
        ),
    },
    {
        "key": "map",
        "tab_text": "Map",
        "title": "World Map",
        "description": (
            "Explore the world and discover new locations.\n\n"
            "Each location offers unique resources and challenges."
        ),
    },
    {
        "key": "site",
        "tab_text": "Site",
        "title": "Site Development",
        "description": (
            "Develop your current location with buildings and improvements.\n\n"
            "Buildings provide bonuses and unlock new activities."
        ),
    },
    {
        "key": "events",
        "tab_text": "Events",
        "title": "Events Log",
        "description": (
            "View the history of events that have occurred on the timeline.\n\n"
            "Events can be reviewed and some can be modified or undone."
        ),
    },
    {
        "key": "achievements",
        "tab_text": "Achievements",
        "title": "Achievements",
        "description": (
            "Track your accomplishments and unlock rewards.\n\n"
            "Achievements provide bonuses and unlock new content."
        ),
    },
    {
        "key": "config",
        "tab_text": "Settings",
        "title": "Settings",
        "description": "",  # Has custom implementation
    },
]


def get_screen_by_key(key: str) -> Dict[str, str]:
    """Get screen definition by key."""
    for screen in SCREENS:
        if screen["key"] == key:
            return screen
    return {"key": key, "tab_text": key, "title": key, "description": ""}


# =============================================================================
# SETTINGS DEFINITIONS
# =============================================================================

SETTINGS: Dict[str, Any] = {
    "autosave": {
        "default": True,
        "label": "Auto-save enabled",
    },
    "notifications": {
        "default": True,
        "label": "Show notifications",
    },
    "theme": {
        "default": "Default",
        "options": ["Default", "Dark", "Light"],
        "label": "Theme",
    },
    "number_format": {
        "default": "Standard",
        "options": ["Standard", "Scientific", "Engineering"],
        "label": "Number format",
    },
}


# =============================================================================
# GAME INFO
# =============================================================================

GAME_INFO: Dict[str, str] = {
    "name": "Timescrubber",
    "subtitle": "A Non-Linear Time Idle Game",
    "version": "0.1.0 (Development)",
    "description": (
        "A timeline-based idle game where you can manipulate time "
        "and observe how changes cascade through history."
    ),
}
