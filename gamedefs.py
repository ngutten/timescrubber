# Game Content Definitions for Timescrubber
#
# This module contains all game content definitions - activities, resources,
# screens, settings, upgrades, etc. GUI code should import from here rather than
# defining content inline.

from typing import Dict, List, Any, Optional

from upgrades import (
    UpgradeType, UpgradeDefinition, make_upgrade,
    make_rate_modifier_effect, make_consumed_modifier_effect,
    make_unlock_task_effect, make_unlock_resource_effect,
    get_upgrade_registry
)

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
# - tags: List of category tags for modifier targeting
# - unlocked: Whether visible by default (False = requires unlock)

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
        "tags": ["rest", "recovery"],
        "unlocked": True,
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
        "tags": ["gathering", "wood", "basic"],
        "unlocked": True,
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
        "tags": ["gathering", "stone", "basic"],
        "unlocked": True,
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
        "tags": ["crafting", "tools"],
        "unlocked": True,
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
        "tags": ["construction", "building", "shelter"],
        "unlocked": True,
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
        "tags": ["exploration", "discovery"],
        "unlocked": True,
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
        "tags": ["mental", "insights", "meditation"],
        "unlocked": True,
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
        "tags": ["mental", "research", "study"],
        "unlocked": True,
    },
    # Locked activities (require research/upgrades to unlock)
    {
        "name": "mine_ore",
        "displayname": "Mine Ore",
        "description": (
            "Extract raw ore from the ground. "
            "Ore can be smelted into metal for advanced crafting."
        ),
        "rate": 6,  # ~16.7 time units
        "consumed": [("Stamina", 0.8)],
        "produced": [],
        "on_complete_give": {"Ore": 2},
        "requirements": {"Stamina": 4},
        "tags": ["gathering", "mining", "ore"],
        "unlocked": False,  # Requires mining_basics research
    },
    {
        "name": "smelt_metal",
        "displayname": "Smelt Metal",
        "description": (
            "Smelt raw ore into usable metal ingots. "
            "Metal is required for advanced tools and equipment."
        ),
        "rate": 4,  # 25 time units
        "consumed": [("Stamina", 0.3)],
        "produced": [],
        "on_complete_give": {"Ore": -3, "Metal": 1},
        "requirements": {"Ore": 3},
        "tags": ["crafting", "smelting", "metal"],
        "unlocked": False,  # Requires metallurgy research
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


def is_activity_unlocked(name: str, timestate=None) -> bool:
    """Check if an activity is unlocked and available to the player.

    Args:
        name: The internal name of the activity
        timestate: Optional TimeState for time-aware unlock checking.
                   If provided, checks if activity was unlocked at or before this time.
                   If None, uses the global upgrade registry (not time-aware).

    Returns:
        True if the activity is visible/available
    """
    activity = get_activity_by_name(name)
    if not activity:
        return False

    # Check if unlocked by default
    if activity.get("unlocked", True):
        return True

    # Check if unlocked by upgrade system
    if timestate is not None:
        # Use time-aware check via timestate
        return timestate.is_task_unlocked(name)
    else:
        # Fall back to global registry (not time-aware)
        upgrade_registry = get_upgrade_registry()
        return upgrade_registry.is_task_unlocked(name)


def get_unlocked_activities(timestate=None) -> List[Dict[str, Any]]:
    """Get all activities that are currently unlocked.

    Args:
        timestate: Optional TimeState for time-aware unlock checking.
    """
    return [a for a in ACTIVITIES if is_activity_unlocked(a["name"], timestate)]


def make_activity_task(displayname: str, t: float, timestate=None):
    """Create a Task instance for an activity with completion rewards.

    Args:
        displayname: The display name of the activity
        t: The time at which to start the task
        timestate: Optional TimeState for time-aware unlock checking

    Returns:
        A Task instance ready to be added to the timeline, or None if not found
    """
    from timeline import Task
    from variable import LinearVariable, Variable

    activity = get_activity_by_displayname(displayname)
    if not activity:
        return None

    # Check if activity is unlocked (time-aware if timestate provided)
    if not is_activity_unlocked(activity["name"], timestate):
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

    # Create the task instance with tags
    task = _ActivityTask(
        name=activity["name"],
        rate=activity["rate"],
        displayname=activity["displayname"],
        consumed=activity.get("consumed", []),
        produced=activity.get("produced", []),
        tags=activity.get("tags", [])
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


# =============================================================================
# UPGRADE DEFINITIONS
# =============================================================================

# Regular Upgrades - purchased with resources, provide multipliers and unlocks
REGULAR_UPGRADES: List[UpgradeDefinition] = [
    make_upgrade(
        name="sharp_tools",
        displayname="Sharp Tools",
        description="Better-maintained tools make gathering faster. +15% gathering speed.",
        upgrade_type=UpgradeType.REGULAR,
        prerequisites=[],
        costs=[("Wood", 10), ("Stone", 5)],
        effects=[
            make_rate_modifier_effect("tools", 0.15, ["gathering"])
        ],
        tags=["tools", "gathering"]
    ),
    make_upgrade(
        name="sturdy_axe",
        displayname="Sturdy Axe",
        description="A well-crafted axe for wood gathering. +20% wood gathering speed.",
        upgrade_type=UpgradeType.REGULAR,
        prerequisites=[("upgrade", "sharp_tools", 0)],
        costs=[("Wood", 15), ("Stone", 10)],
        effects=[
            make_rate_modifier_effect("equipment", 0.20, ["wood"])
        ],
        tags=["tools", "wood"]
    ),
    make_upgrade(
        name="iron_pickaxe",
        displayname="Iron Pickaxe",
        description="A durable pickaxe for mining. +20% mining speed.",
        upgrade_type=UpgradeType.REGULAR,
        prerequisites=[("upgrade", "sharp_tools", 0), ("research", "mining_basics", 0)],
        costs=[("Metal", 5), ("Wood", 10)],
        effects=[
            make_rate_modifier_effect("equipment", 0.20, ["mining"])
        ],
        tags=["tools", "mining"]
    ),
    make_upgrade(
        name="efficient_gathering",
        displayname="Efficient Gathering",
        description="Learn to gather more efficiently. -10% stamina consumption for gathering.",
        upgrade_type=UpgradeType.REGULAR,
        prerequisites=[("upgrade", "sharp_tools", 0)],
        costs=[("Insights", 5)],
        effects=[
            make_consumed_modifier_effect("technique", -0.10, ["gathering"])
        ],
        tags=["efficiency", "gathering"]
    ),
    make_upgrade(
        name="construction_basics",
        displayname="Construction Basics",
        description="Fundamental building techniques. +10% construction speed.",
        upgrade_type=UpgradeType.REGULAR,
        prerequisites=[],
        costs=[("Wood", 20), ("Stone", 10)],
        effects=[
            make_rate_modifier_effect("technique", 0.10, ["construction"])
        ],
        tags=["construction"]
    ),
    make_upgrade(
        name="reinforced_structures",
        displayname="Reinforced Structures",
        description="Build stronger, faster. +15% construction speed, -10% resource consumption.",
        upgrade_type=UpgradeType.REGULAR,
        prerequisites=[("upgrade", "construction_basics", 0), ("research", "architecture", 0)],
        costs=[("Wood", 30), ("Stone", 20), ("Metal", 5)],
        effects=[
            make_rate_modifier_effect("materials", 0.15, ["construction"]),
            make_consumed_modifier_effect("materials", -0.10, ["construction"])
        ],
        tags=["construction", "efficiency"]
    ),
    make_upgrade(
        name="meditation_mat",
        displayname="Meditation Mat",
        description="A comfortable place for contemplation. +20% meditation speed.",
        upgrade_type=UpgradeType.REGULAR,
        prerequisites=[],
        costs=[("Wood", 5)],
        effects=[
            make_rate_modifier_effect("comfort", 0.20, ["meditation"])
        ],
        tags=["mental", "comfort"]
    ),
    make_upgrade(
        name="study_desk",
        displayname="Study Desk",
        description="A proper desk for focused study. +15% study and research speed.",
        upgrade_type=UpgradeType.REGULAR,
        prerequisites=[("upgrade", "meditation_mat", 0)],
        costs=[("Wood", 15), ("Stone", 5)],
        effects=[
            make_rate_modifier_effect("furniture", 0.15, ["study", "research"])
        ],
        tags=["mental", "furniture"]
    ),
]

# Research Upgrades - purchased with Insights, unlock new content
RESEARCH_UPGRADES: List[UpgradeDefinition] = [
    make_upgrade(
        name="basic_knowledge",
        displayname="Basic Knowledge",
        description="Fundamental understanding of the world. Unlocks further research.",
        upgrade_type=UpgradeType.RESEARCH,
        prerequisites=[],
        costs=[("Insights", 10)],
        effects=[],
        render_position=(0, 0),
        tags=["foundation"]
    ),
    make_upgrade(
        name="mining_basics",
        displayname="Mining Basics",
        description="Learn to extract ore from the earth. Unlocks mining activities and Ore resource.",
        upgrade_type=UpgradeType.RESEARCH,
        prerequisites=[("research", "basic_knowledge", 0)],
        costs=[("Insights", 15)],
        effects=[
            make_unlock_task_effect("mine_ore"),
            make_unlock_resource_effect("Ore")
        ],
        render_position=(1, -1),
        tags=["gathering", "mining"]
    ),
    make_upgrade(
        name="metallurgy",
        displayname="Metallurgy",
        description="The art of working with metals. Unlocks smelting and Metal resource.",
        upgrade_type=UpgradeType.RESEARCH,
        prerequisites=[("research", "mining_basics", 0)],
        costs=[("Insights", 25)],
        effects=[
            make_unlock_task_effect("smelt_metal"),
            make_unlock_resource_effect("Metal")
        ],
        render_position=(2, -1),
        tags=["crafting", "metal"]
    ),
    make_upgrade(
        name="architecture",
        displayname="Architecture",
        description="Advanced building techniques and structural understanding.",
        upgrade_type=UpgradeType.RESEARCH,
        prerequisites=[("research", "basic_knowledge", 0)],
        costs=[("Insights", 20)],
        effects=[],
        render_position=(1, 0),
        tags=["construction"]
    ),
    make_upgrade(
        name="advanced_construction",
        displayname="Advanced Construction",
        description="Complex building methods for larger structures. +25% construction speed.",
        upgrade_type=UpgradeType.RESEARCH,
        prerequisites=[("research", "architecture", 0)],
        costs=[("Insights", 35)],
        effects=[
            make_rate_modifier_effect("research", 0.25, ["construction"])
        ],
        render_position=(2, 0),
        tags=["construction"]
    ),
    make_upgrade(
        name="exploration_techniques",
        displayname="Exploration Techniques",
        description="Better methods for exploring the world. +30% exploration speed.",
        upgrade_type=UpgradeType.RESEARCH,
        prerequisites=[("research", "basic_knowledge", 0)],
        costs=[("Insights", 15)],
        effects=[
            make_rate_modifier_effect("research", 0.30, ["exploration"])
        ],
        render_position=(1, 1),
        tags=["exploration"]
    ),
    make_upgrade(
        name="deep_meditation",
        displayname="Deep Meditation",
        description="Advanced meditation practices. +50% insight generation during meditation.",
        upgrade_type=UpgradeType.RESEARCH,
        prerequisites=[("research", "exploration_techniques", 0)],
        costs=[("Insights", 30)],
        effects=[
            ("modifier", {
                "modifier_type": "research",
                "value": 0.50,
                "target_param": "produced",
                "target_tags": ["meditation"]
            })
        ],
        render_position=(2, 1),
        tags=["mental", "insights"]
    ),
    make_upgrade(
        name="time_mastery",
        displayname="Time Mastery",
        description="Fundamental understanding of temporal mechanics. Prerequisite for advanced timeline manipulation.",
        upgrade_type=UpgradeType.RESEARCH,
        prerequisites=[("research", "deep_meditation", 0)],
        costs=[("Insights", 50)],
        effects=[],
        render_position=(3, 1),
        tags=["temporal", "advanced"]
    ),
]

# Nexus Upgrades - purchased with Motes, provide meta-progression
NEXUS_UPGRADES: List[UpgradeDefinition] = [
    make_upgrade(
        name="temporal_extension_1",
        displayname="Temporal Extension I",
        description="Extend the maximum timeline by 50%. More time means more possibilities.",
        upgrade_type=UpgradeType.NEXUS,
        prerequisites=[],
        costs=[("Motes", 1)],
        effects=[
            ("max_time_multiplier", {"multiplier": 1.5})
        ],
        tags=["temporal", "extension"]
    ),
    make_upgrade(
        name="temporal_extension_2",
        displayname="Temporal Extension II",
        description="Further extend the maximum timeline by 50%.",
        upgrade_type=UpgradeType.NEXUS,
        prerequisites=[("upgrade", "temporal_extension_1", 0)],
        costs=[("Motes", 3)],
        effects=[
            ("max_time_multiplier", {"multiplier": 1.5})
        ],
        tags=["temporal", "extension"]
    ),
    make_upgrade(
        name="temporal_extension_3",
        displayname="Temporal Extension III",
        description="Greatly extend the maximum timeline by 100%.",
        upgrade_type=UpgradeType.NEXUS,
        prerequisites=[("upgrade", "temporal_extension_2", 0)],
        costs=[("Motes", 10)],
        effects=[
            ("max_time_multiplier", {"multiplier": 2.0})
        ],
        tags=["temporal", "extension"]
    ),
    make_upgrade(
        name="parallel_processing_1",
        displayname="Parallel Processing I",
        description="Unlock the ability to run 2 tasks simultaneously.",
        upgrade_type=UpgradeType.NEXUS,
        prerequisites=[],
        costs=[("Motes", 2)],
        effects=[
            ("parallel_tasks", {"value": 2})
        ],
        tags=["parallel", "tasks"]
    ),
    make_upgrade(
        name="parallel_processing_2",
        displayname="Parallel Processing II",
        description="Unlock the ability to run 3 tasks simultaneously.",
        upgrade_type=UpgradeType.NEXUS,
        prerequisites=[("upgrade", "parallel_processing_1", 0)],
        costs=[("Motes", 5)],
        effects=[
            ("parallel_tasks", {"value": 3})
        ],
        tags=["parallel", "tasks"]
    ),
    make_upgrade(
        name="parallel_processing_3",
        displayname="Parallel Processing III",
        description="Unlock the ability to run 4 tasks simultaneously.",
        upgrade_type=UpgradeType.NEXUS,
        prerequisites=[("upgrade", "parallel_processing_2", 0)],
        costs=[("Motes", 10)],
        effects=[
            ("parallel_tasks", {"value": 4})
        ],
        tags=["parallel", "tasks"]
    ),
    make_upgrade(
        name="efficiency_mastery",
        displayname="Efficiency Mastery",
        description="All tasks are 10% faster across all timelines.",
        upgrade_type=UpgradeType.NEXUS,
        prerequisites=[],
        costs=[("Motes", 5)],
        effects=[
            make_rate_modifier_effect("nexus", 0.10, [])  # Empty tags = applies to all
        ],
        tags=["efficiency", "global"]
    ),
    make_upgrade(
        name="resource_mastery",
        displayname="Resource Mastery",
        description="All resource consumption is reduced by 10% across all timelines.",
        upgrade_type=UpgradeType.NEXUS,
        prerequisites=[("upgrade", "efficiency_mastery", 0)],
        costs=[("Motes", 8)],
        effects=[
            make_consumed_modifier_effect("nexus", -0.10, [])  # Empty tags = applies to all
        ],
        tags=["efficiency", "global"]
    ),
]

# All upgrades combined
ALL_UPGRADES: List[UpgradeDefinition] = REGULAR_UPGRADES + RESEARCH_UPGRADES + NEXUS_UPGRADES


def register_all_upgrades():
    """Register all upgrade definitions with the global upgrade registry."""
    registry = get_upgrade_registry()
    registry.register_all(ALL_UPGRADES)


def get_upgrade_by_name(name: str) -> Optional[UpgradeDefinition]:
    """Get an upgrade definition by name."""
    for upgrade in ALL_UPGRADES:
        if upgrade.name == name:
            return upgrade
    return None


def get_upgrades_by_type(upgrade_type: UpgradeType) -> List[UpgradeDefinition]:
    """Get all upgrades of a specific type."""
    return [u for u in ALL_UPGRADES if u.upgrade_type == upgrade_type]


def get_research_tree_data() -> List[Dict[str, Any]]:
    """Get research upgrade data formatted for tree visualization.

    Returns:
        List of dicts with upgrade info and prerequisite connections
    """
    result = []
    for upgrade in RESEARCH_UPGRADES:
        prereq_names = []
        for prereq in upgrade.prerequisites:
            if prereq.prereq_type.value in ("upgrade", "research"):
                prereq_names.append(prereq.target)

        result.append({
            "name": upgrade.name,
            "displayname": upgrade.displayname,
            "description": upgrade.description,
            "position": upgrade.render_position,
            "prerequisites": prereq_names,
            "costs": [(c.resource, c.amount) for c in upgrade.costs],
            "purchased": get_upgrade_registry().is_purchased(upgrade.name),
            "visible": get_upgrade_registry().is_visible(upgrade.name),
        })
    return result
