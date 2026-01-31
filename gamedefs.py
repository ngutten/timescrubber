# Game Content Definitions for Timescrubber
#
# This module contains all game content definitions - activities, resources,
# screens, settings, etc. GUI code should import from here rather than
# defining content inline.

from typing import Dict, List, Any

# =============================================================================
# ACTIVITY DEFINITIONS
# =============================================================================

# Each activity has:
# - name: Display name
# - description: Full description text
# - requirements: Dict of resource_name -> amount needed (empty dict if none)

ACTIVITIES: List[Dict[str, Any]] = [
    {
        "name": "Rest (Recover Stamina)",
        "description": (
            "Take a break and recover your stamina. "
            "Stamina is essential for performing most activities."
        ),
        "requirements": {},
    },
    {
        "name": "Gather Wood",
        "description": (
            "Collect wood from nearby trees. "
            "Wood is a basic resource used in many crafting recipes."
        ),
        "requirements": {"Stamina": 2},
    },
    {
        "name": "Gather Stone",
        "description": (
            "Search for and collect stone. "
            "Stone is needed for tools and building structures."
        ),
        "requirements": {"Stamina": 3},
    },
    {
        "name": "Craft Basic Tools",
        "description": (
            "Create simple tools to improve efficiency. "
            "Tools make gathering and building faster."
        ),
        "requirements": {"Wood": 5, "Stone": 2},
    },
    {
        "name": "Build Shelter",
        "description": (
            "Construct a basic shelter for protection. "
            "Shelters provide bonuses to resting and storage."
        ),
        "requirements": {"Wood": 20, "Stone": 10},
    },
    {
        "name": "Explore Area",
        "description": (
            "Scout the surrounding area to discover new locations "
            "and resources."
        ),
        "requirements": {"Stamina": 5},
    },
    {
        "name": "Meditate (Gain Insights)",
        "description": (
            "Quiet contemplation to gain insights. "
            "Insights are used for research and upgrades."
        ),
        "requirements": {"Stamina": 1},
    },
    {
        "name": "Study",
        "description": (
            "Study your surroundings and acquired knowledge to unlock "
            "new abilities and understanding."
        ),
        "requirements": {"Insights": 5},
    },
]


def get_activity_names() -> List[str]:
    """Return list of all activity names."""
    return [a["name"] for a in ACTIVITIES]


def get_activity_description(name: str) -> str:
    """Get description for an activity by name."""
    for activity in ACTIVITIES:
        if activity["name"] == name:
            return activity["description"]
    return "No description available."


def get_activity_requirements(name: str) -> Dict[str, int]:
    """Get requirements dict for an activity by name."""
    for activity in ACTIVITIES:
        if activity["name"] == name:
            return activity["requirements"]
    return {}


def format_requirements(requirements: Dict[str, int]) -> str:
    """Format requirements dict as display string."""
    if not requirements:
        return "None"
    return ", ".join(f"{res}: {amt}" for res, amt in requirements.items())


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
