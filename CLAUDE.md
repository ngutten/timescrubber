# CLAUDE.md - Timescrubber Codebase Guide

## Project Overview

**Timescrubber** is a non-linear time idle game written in Python. The core innovation is a timeline-based state management system where game state can be calculated at any point in time, with automatic recomputation when the timeline is modified.

- **Language:** Python 3.11+
- **Dependencies:** Standard library only (no external packages)
- **License:** CC0 1.0 Universal (Public Domain)
- **Status:** Early development/prototype

## Quick Start

```bash
# Run the game (currently outputs demo state)
python3 main.py
```

## Directory Structure

```
timescrubber/
├── main.py              # Entry point and demo initialization
├── gamestate.py         # High-level game state wrapper
├── timeline.py          # Core timeline engine (main logic)
├── variable.py          # Variable and LinearVariable classes
├── registry.py          # Variable storage container
├── gamedefs.py          # Game content definitions (placeholder)
└── *_gui.py             # GUI components (11 files, all stubs)
```

## Architecture

### Core Components

#### Timeline System (`timeline.py`)
The heart of the game engine. Key classes:

- **`TimeState`** - Snapshot of game state at a specific time
  - Contains a `Registry` of variables
  - `copy(t)` - Creates a deep copy propagated to time t
  - `add_variable(var)` / `get_variable(name)` - Variable management

- **`Timeline`** - Main game timeline manager
  - `state_cache` - List of TimeState objects, sorted by time
  - `events` - List of scheduled events, sorted by time
  - `state_at(t)` - Returns state at time t (O(log n) via bisect)
  - `add_event(event)` - Adds and triggers event, invalidates later states
  - `invalidate_after(t)` - Clears cache after time t, recomputes
  - `recompute(t0)` - Recalculates all events from t0 to max_time

- **`Event`** - Base class for game events
  - `validate(timestate, t)` - Check if event can fire
  - `trigger(t, timeline)` - Execute the event
  - `on_start_vars(timestate)` - Modify variables
  - `on_start_effects(timeline)` - Add follow-up events

- **`Process(Event)`** - Continuous resource conversion
  - `consumed` / `produced` - Resource conversion rates
  - `throttle` - Efficiency fraction

- **`Task(Process)`** - Time-limited completion events
  - Creates a `{taskname}_progress` LinearVariable on trigger
  - `on_finish_vars()` / `on_finish_effects()` - Completion handlers

#### Variable System (`variable.py`)

- **`Variable`** - Basic named value with tags
  - `get(t)` / `set(x, t)` - Access value (time parameter ignored)

- **`LinearVariable(Variable)`** - Time-dependent value with rate
  - `get(t)` returns: `clamp((t-t0)*rate + value, min, max)`
  - `rehome(t)` - Recalculates value at time t, updates reference point
  - `when(target)` - Solves for time when variable reaches target

#### Registry (`registry.py`)
Dictionary-like container mapping variable names to Variable objects.

#### GameState (`gamestate.py`)
Simple wrapper that creates a Timeline from an initial TimeState.

### Data Flow

```
1. Create TimeState with Variables → 2. Wrap in Timeline via GameState
                                           ↓
3. Add Events to timeline → 4. Events trigger and modify state
                                           ↓
5. Query state_at(t) for any time ← 6. Cache invalidation on changes
```

## Key Concepts

### Timeline Determinism
The timeline is fully deterministic - state at any point can be calculated independently from the initial state and events.

### Cache Invalidation
When an event is added or the timeline is modified, `invalidate_after(t)` clears cached states after time t and recomputes affected events.

### LinearVariables
Resources like Stamina, Wood, Stone use LinearVariables that accumulate at a rate over time, clamped to min/max bounds.

### Bisect Optimization
All lookups in sorted state/event lists use `bisect` for O(log n) performance.

## Code Conventions

### Naming
- **Classes:** PascalCase (`TimeState`, `LinearVariable`)
- **Methods/Functions:** snake_case (`state_at`, `add_variable`)
- **Variables:** snake_case (`cur_time`, `state_cache`)

### Type Hints
All code uses type hints from the `typing` module:
```python
from typing import List, Dict, Optional, Tuple
```

### Inheritance Pattern
```
Event → Process → Task
```

### Import Structure
```python
# Standard library
from copy import deepcopy
from typing import List, Dict, Optional, Tuple
import bisect

# Local modules
from variable import Variable, LinearVariable
from registry import Registry
from timeline import TimeState, Timeline, Event
```

## Current Implementation Status

### Implemented
- Time-based state calculation system
- Event scheduling and triggering
- Timeline caching with automatic invalidation
- Linear variables with rates and bounds
- Event hierarchy (Event → Process → Task)
- Registry pattern for variables

### Not Yet Implemented
- GUI (no framework chosen yet)
- Game content (`gamedefs.py` is placeholder)
- Bottleneck/throttling system (methods stubbed)
- Task completion mechanics (partially wired)
- Save/load persistence
- Player input and game loop
- Testing framework

## GUI Files (All Stubs)

| File | Intended Purpose |
|------|-----------------|
| `panel_gui.py` | Side panel for resources and active tasks |
| `tabbed_menu_gui.py` | Main menu tab navigation |
| `timeline_gui.py` | Timeline visualization |
| `map_gui.py` | World map with exploration/development |
| `activities_gui.py` | Activities screen |
| `upgrades_gui.py` | Upgrades and nexus upgrades |
| `research_gui.py` | Research graph visualization |
| `site_gui.py` | Site development and building |
| `events_gui.py` | Events log and reports |
| `achievements_gui.py` | Achievements display |
| `configuration_gui.py` | Settings screen |

## Known Issues / Missing Pieces

1. **`check_bottlenecks()`** - Called in `recompute()` but only stubbed (returns nothing)
2. **`recompute_bottlenecks()`** - Stubbed as `pass`

## Development Guidelines

### When Adding Events
1. Subclass `Event`, `Process`, or `Task`
2. Override `validate()` to define when the event can fire
3. Override `on_start_vars()` to modify variables
4. Override `on_start_effects()` to add follow-up events

### When Adding Variables
1. Use `Variable` for discrete/boolean state
2. Use `LinearVariable` for resources that accumulate over time
3. Register via `timestate.add_variable()`

### When Modifying Timeline
1. Add events via `timeline.add_event()` - handles cache invalidation
2. Never modify state_cache directly
3. Query state via `timeline.state_at(t)`

## Testing

No testing framework is currently set up. Manual testing via `main.py`:

```bash
python3 main.py
# Outputs: state_cache contents and Stamina value at t=2
```

## Future Development Priorities

1. Choose and implement GUI framework
2. Implement bottleneck system
3. Populate `gamedefs.py` with game content
4. Add save/load persistence
5. Create test suite
