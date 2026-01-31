from copy import deepcopy
from typing import List, Dict, Optional, Tuple
import bisect

from variable import Variable, LinearVariable
from registry import Registry

class TimeState():
    registry: Registry = None
    processes: List[Optional["Process"]] = None  # These are things that modify rates while present, so we have to be careful to apply and undo their effects correctly
    time: float = 0.0 # Time of this state

    def __init__(self, t):
        self.time = t
        self.registry = Registry(t)
        self.processes = []

    def add_variable(self, var):
        self.registry.add_variable(var)

    def get_variable(self, name):
        return self.registry.get_variable(name)
    
    # Return a hard copy of the timestate, propagated forward to time t (for rehoming linearvariables)    
    def copy(self, t): 
        new_state = deepcopy(self)        
        new_state.time = t
        new_state.registry.time = t

        for key in self.registry.keys():
            if type(new_state.registry[key]) is LinearVariable:
                new_state.registry[key].rehome(t)

        return new_state
    
class Timeline():
    events: List[Optional["Event"]] = None
    state_cache: List[TimeState] = None
    initial: TimeState = None # Initial timestate
    max_time: float = 0.0 # This should go with game time, but we need it for recomputes. Change this with a method though

    def __init__(self, initial):
        self.initial = initial
        self.events = []
        self.clear_cache()

    def clear_cache(self):
        self.state_cache = [self.initial]

    # Remove everything from the cache after but not including t
    # Also remove and recompute all events after t which have invalidate=True
    def invalidate_after(self, t):
        self.state_cache = self.state_cache[:bisect.bisect_right(self.state_cache, t, key=lambda e: e.time)]
        i = bisect.bisect_right(self.events, t, key=lambda e: e.t)

        head_events = self.events[:i]

        for j in range(i, len(self.events)):
            if not self.events[j].invalidate: # Don't discard it out of hand...
                head_events.append(self.events[j])
        self.events = head_events

        # Now recompute from this time
        self.recompute(t)

    def next_event(self, t): # Returns (time, next event) or (max_time, None)
        idx = bisect.bisect_right(self.events, t, key=lambda e: e.t)

        if idx < len(self.events):
            ev = self.events[idx]
            return (ev.t, ev)
        else:
            return (self.max_time, None)
    
    # When the max time changes, we need to recalculate additional pieces of the timeline
    def change_max_time(self, new_max):
        if new_max > self.max_time:
            old_max = self.max_time
            self.max_time = new_max
            self.recompute(old_max)
        else:
            self.max_time = new_max
            self.invalidate_after(new_max)

    def recompute_bottlenecks(self, ts: TimeState):
        """Review all running processes and reschedule their end events if needed.

        This is called after each event triggers, as changes to variables might
        affect when running processes will deplete their resources.
        """
        t = ts.time

        for process in ts.processes[:]:  # Copy list as we might modify it
            # Skip if this process doesn't have an end event scheduled
            if not hasattr(process, 'end_event') or process.end_event is None:
                continue

            # Recalculate when resources will run out
            new_end_time = None

            # For Tasks, also consider progress completion
            if isinstance(process, Task):
                progress_var = ts.get_variable(process.name + "_progress")
                if progress_var:
                    completion_time = progress_var.when(100)
                    if completion_time is not None and completion_time > t:
                        new_end_time = completion_time

            # Check consumed resources for depletion
            for var_name, rate in process.consumed:
                var = ts.get_variable(var_name)
                if var and isinstance(var, LinearVariable):
                    zero_time = var.when(var.min)
                    if zero_time is not None and zero_time > t:
                        if new_end_time is None or zero_time < new_end_time:
                            new_end_time = zero_time
                            # For Tasks, mark this as interrupt, not completion
                            if isinstance(process, Task):
                                # This will be an interrupt since depletion comes first
                                pass

            # Update the end event if the time changed
            if new_end_time is not None:
                old_end_event = process.end_event
                if abs(old_end_event.t - new_end_time) > 0.001:  # Time changed significantly
                    # Create new appropriate end event (replaces the old one)
                    if isinstance(process, Task):
                        progress_var = ts.get_variable(process.name + "_progress")
                        completion_time = progress_var.when(100) if progress_var else None

                        if completion_time is not None and (completion_time <= new_end_time or new_end_time == completion_time):
                            process.end_event = TaskComplete(process, completion_time)
                        else:
                            process.end_event = TaskInterrupt(process, new_end_time)
                    else:
                        process.end_event = ProcessEnd(process, new_end_time)

                    process.end_event.invalidate = True
                    # Don't add to events list - check_bottlenecks finds it via process.end_event

    def check_bottlenecks(self, t0: float, t1: float) -> Tuple[float, Optional["Event"]]:
        """Check if there are any resource bottlenecks between t0 and t1.

        Returns (time, event) where the event is a ProcessEnd or TaskInterrupt
        that needs to fire, or (t1, None) if no bottleneck before t1.
        """
        ts = self.state_at(t0)
        earliest_time = t1
        earliest_event = None

        for process in ts.processes:
            if not hasattr(process, 'end_event') or process.end_event is None:
                continue

            end_time = process.end_event.t
            if t0 < end_time < earliest_time:
                earliest_time = end_time
                earliest_event = process.end_event

        return (earliest_time, earliest_event)

    def recompute(self, t0): # Recompute all events and states from t0 onwards
        cur_time = t0

        while cur_time < self.max_time:
            next_time, next_event = self.next_event(cur_time)

            # Check if there are any bottlenecks between now and then
            next_btime, next_bottleneck = self.check_bottlenecks(cur_time, next_time)
            if next_btime < next_time and next_bottleneck is not None:
                # Trigger the bottleneck event (process end, task complete, etc.)
                next_bottleneck.trigger(next_btime, self)
                cur_time = next_btime
                ts = self.state_at(cur_time)
                self.recompute_bottlenecks(ts)
            elif next_event is not None:
                # Do the event
                next_event.trigger(next_time, self)
                cur_time = next_time
                ts = self.state_at(cur_time)
                self.recompute_bottlenecks(ts)
            else:
                # No more events and no bottlenecks, done
                break

    def state_at(self, t): # Return the last TimeState from just before or equal to t from the state cache
        idx = bisect.bisect_right(self.state_cache, t, key=lambda e: e.time)-1
        return self.state_cache[idx]

    def add_timestate(self, timestate: TimeState):
        bisect.insort(self.state_cache, timestate, key=lambda e: e.time)

    # Note - this will call add_timestate to add a timestate to the cache
    def add_event(self, event):
        bisect.insort(self.events, event, key=lambda e: e.t)
        event.trigger(event.t, self)
        self.invalidate_after(event.t)

    # Remove an event from the timeline and invalidate/recompute
    def remove_event(self, event):
        if event in self.events:
            t = event.t
            self.events.remove(event)
            # Clear states at AND after the event time (unlike invalidate_after which keeps states at t)
            self.state_cache = self.state_cache[:bisect.bisect_left(self.state_cache, t, key=lambda e: e.time)]
            # Process remaining events - keep those without invalidate flag
            i = bisect.bisect_right(self.events, t, key=lambda e: e.t)
            head_events = self.events[:i]
            for j in range(i, len(self.events)):
                if not self.events[j].invalidate:
                    head_events.append(self.events[j])
            self.events = head_events
            self.recompute(t)

class Event():
    t: float = 0.0 # Time of this event
    invalidate: bool = False # Should we invalidate this event when recomputing the timeline?
    is_action: bool = False # Is this a player-created event (e.g. the player can delete it)
    name: str = ""
    displayname: str = ""

    def __init__(self, name, displayname = None):
        self.name = name

    def validate(self, timestate: TimeState, t: float): # Check if this event would be valid to fire at this time and timestate
        return True
    
    # Apply the effects of the event to the state and time.
    # Also clone and add a fresh timestate to represent changes from the event.
    # Returns True if the event was triggered, False if validation failed.
    def trigger(self, t: float, timeline: Timeline) -> bool:
        self.t = t
        timestate = timeline.state_at(t)
        if not self.validate(timestate, t):
            return False
        new_timestate = timestate.copy(t)
        self.on_start_vars(new_timestate)
        timeline.add_timestate(new_timestate)
        self.on_start_effects(timeline)
        return True

    def on_start_vars(self, timestate: TimeState): # Modify any variables when the event fires.
        pass

    def on_start_effects(self, timeline: Timeline): # Add any other events or consequences when the event fires. 
        pass

class Process(Event):
    """Ongoing event which converts one resource into another continuously while active.

    When started, modifies the rates of consumed and produced LinearVariables.
    Automatically creates a ProcessEnd event when consumed resources are depleted.
    """
    consumed: List[Tuple[str, float]] = None  # List of (variable_name, rate) pairs
    produced: List[Tuple[str, float]] = None  # List of (variable_name, rate) pairs
    throttle: float = 1.0  # What fraction of the maximum rate does this process operate at?
    end_event: Optional["ProcessEnd"] = None  # Reference to the end event

    def __init__(self, name, displayname=None, consumed=None, produced=None):
        super().__init__(name, displayname)
        self.consumed = consumed or []
        self.produced = produced or []
        self.end_event = None
        self.invalidate = True  # Processes can be invalidated if prerequisites change

    def validate(self, timestate: TimeState, t: float) -> bool:
        """Check if process can start - ensure uniqueness and resource availability."""
        # Check uniqueness - can't have two processes with same name running
        for proc in timestate.processes:
            if proc.name == self.name:
                return False

        # Check that we have enough of each consumed resource to start
        for var_name, rate in self.consumed:
            var = timestate.get_variable(var_name)
            if var is None:
                return False
            # Need at least some amount to start (value > 0 or min)
            if isinstance(var, LinearVariable):
                if var.get(t) <= var.min:
                    return False

        return True

    def on_start_vars(self, timestate: TimeState):
        """Modify variable rates when process starts."""
        # Decrease rates for consumed resources
        for var_name, rate in self.consumed:
            var = timestate.get_variable(var_name)
            if var and isinstance(var, LinearVariable):
                var.rate -= rate * self.throttle

        # Increase rates for produced resources
        for var_name, rate in self.produced:
            var = timestate.get_variable(var_name)
            if var and isinstance(var, LinearVariable):
                var.rate += rate * self.throttle

        # Add this process to the active processes list
        timestate.processes.append(self)

    def on_start_effects(self, timeline: Timeline):
        """Schedule the end event based on resource depletion."""
        self._schedule_end_event(timeline)

    def _schedule_end_event(self, timeline: Timeline):
        """Calculate when this process will end and schedule the end event."""
        ts = timeline.state_at(self.t)

        # Find the earliest time when any consumed resource hits zero
        end_time = None

        for var_name, rate in self.consumed:
            var = ts.get_variable(var_name)
            if var and isinstance(var, LinearVariable):
                # When will this variable hit its minimum?
                zero_time = var.when(var.min)
                if zero_time is not None and zero_time > self.t:
                    if end_time is None or zero_time < end_time:
                        end_time = zero_time

        # If there's an end time, create the end event
        # Don't add to timeline.events - check_bottlenecks will find it via process.end_event
        if end_time is not None:
            self.end_event = ProcessEnd(self, end_time)
            self.end_event.invalidate = True  # Will be recalculated on timeline changes

    def cancel(self, t: float, timeline: Timeline):
        """Cancel this process at time t (player-initiated stop)."""
        if self.end_event:
            # Move the end event to now
            timeline.events.remove(self.end_event)
        self.end_event = ProcessEnd(self, t, is_action=True)
        import bisect
        bisect.insort(timeline.events, self.end_event, key=lambda e: e.t)
        timeline.invalidate_after(t)


class ProcessEnd(Event):
    """Event that stops a running Process and reverts its rate changes."""
    process: Process = None
    is_system_generated: bool = True  # True if auto-generated, False if player-cancelled

    def __init__(self, process: Process, t: float, is_action: bool = False):
        super().__init__(f"{process.name}_end", f"End {process.displayname or process.name}")
        self.process = process
        self.t = t
        self.is_action = is_action
        self.is_system_generated = not is_action
        self.invalidate = True  # Recalculate on timeline changes

    def validate(self, timestate: TimeState, t: float) -> bool:
        """End event is valid if the process is still running."""
        return any(p.name == self.process.name for p in timestate.processes)

    def on_start_vars(self, timestate: TimeState):
        """Revert the rate changes from the process."""
        # Restore rates for consumed resources
        for var_name, rate in self.process.consumed:
            var = timestate.get_variable(var_name)
            if var and isinstance(var, LinearVariable):
                var.rate += rate * self.process.throttle

        # Restore rates for produced resources
        for var_name, rate in self.process.produced:
            var = timestate.get_variable(var_name)
            if var and isinstance(var, LinearVariable):
                var.rate -= rate * self.process.throttle

        # Remove process from active processes (by name, since processes are deepcopied)
        timestate.processes = [p for p in timestate.processes if p.name != self.process.name]


class Task(Process):
    """Process that runs until completion; creates a progress LinearVariable.

    Tasks have a fixed duration based on their progress rate. When progress
    reaches 100, the task completes and triggers on_finish_vars/on_finish_effects.
    """
    progress_var: LinearVariable = None
    rate: float = 0.0  # Progress rate (progress units per time unit, 100 = complete)

    def __init__(self, name, rate, displayname=None, consumed=None, produced=None):
        super().__init__(name, displayname, consumed, produced)
        self.rate = rate
        self.progress_var = None

    def validate(self, timestate: TimeState, t: float) -> bool:
        """Check if task can start - also check that task isn't already running."""
        # Check for existing progress variable (task already running)
        if timestate.get_variable(self.name + "_progress"):
            return False

        return super().validate(timestate, t)

    def on_start_vars(self, timestate: TimeState):
        """Create progress variable and apply process rate changes."""
        super().on_start_vars(timestate)

        # Create the progress variable
        self.progress_var = LinearVariable(
            self.name + "_progress",
            value=0,
            min=0,
            max=100,
            rate=self.rate
        )
        self.progress_var.t0 = timestate.time
        timestate.add_variable(self.progress_var)

    def on_start_effects(self, timeline: Timeline):
        """Schedule task completion or resource depletion end."""
        ts = timeline.state_at(self.t)

        # Calculate completion time from progress
        progress_var = ts.get_variable(self.name + "_progress")
        completion_time = progress_var.when(100) if progress_var else None

        # Calculate earliest resource depletion time
        depletion_time = None
        for var_name, rate in self.consumed:
            var = ts.get_variable(var_name)
            if var and isinstance(var, LinearVariable):
                zero_time = var.when(var.min)
                if zero_time is not None and zero_time > self.t:
                    if depletion_time is None or zero_time < depletion_time:
                        depletion_time = zero_time

        # Determine which comes first
        if completion_time is not None:
            if depletion_time is None or completion_time <= depletion_time:
                # Task completes before resources run out
                self.end_event = TaskComplete(self, completion_time)
            else:
                # Resources deplete before task completes (interrupt)
                self.end_event = TaskInterrupt(self, depletion_time)
        elif depletion_time is not None:
            # Resources deplete (shouldn't happen without completion, but handle it)
            self.end_event = TaskInterrupt(self, depletion_time)

        # Don't add to timeline.events - check_bottlenecks will find it via process.end_event
        if self.end_event:
            self.end_event.invalidate = True

    def on_finish_vars(self, timestate: TimeState):
        """Override in subclasses to apply effects when task completes."""
        pass

    def on_finish_effects(self, timeline: Timeline):
        """Override in subclasses to add follow-up events on completion."""
        pass


class TaskComplete(Event):
    """Event that fires when a Task reaches 100% progress."""
    task: Task = None

    def __init__(self, task: Task, t: float):
        super().__init__(f"{task.name}_complete", f"Complete {task.displayname or task.name}")
        self.task = task
        self.t = t
        self.is_action = False  # Completion cannot be deleted by player
        self.invalidate = True  # Recalculate on timeline changes

    def validate(self, timestate: TimeState, t: float) -> bool:
        """Completion is valid if the task is running and progress >= 100."""
        progress = timestate.get_variable(self.task.name + "_progress")
        if not progress:
            return False
        return progress.get(t) >= 100

    def on_start_vars(self, timestate: TimeState):
        """Revert process rates and apply task completion effects."""
        # Restore rates for consumed resources
        for var_name, rate in self.task.consumed:
            var = timestate.get_variable(var_name)
            if var and isinstance(var, LinearVariable):
                var.rate += rate * self.task.throttle

        # Restore rates for produced resources
        for var_name, rate in self.task.produced:
            var = timestate.get_variable(var_name)
            if var and isinstance(var, LinearVariable):
                var.rate -= rate * self.task.throttle

        # Remove process from active processes (by name, since processes are deepcopied)
        timestate.processes = [p for p in timestate.processes if p.name != self.task.name]

        # Remove progress variable (task is done)
        if self.task.name + "_progress" in timestate.registry:
            del timestate.registry[self.task.name + "_progress"]

        # Apply task-specific completion effects
        self.task.on_finish_vars(timestate)

    def on_start_effects(self, timeline: Timeline):
        """Apply task-specific follow-up effects."""
        self.task.on_finish_effects(timeline)


class TaskInterrupt(Event):
    """Event that fires when a Task is interrupted (resources depleted or cancelled)."""
    task: Task = None
    is_player_cancel: bool = False

    def __init__(self, task: Task, t: float, is_player_cancel: bool = False):
        super().__init__(
            f"{task.name}_interrupt",
            f"{'Cancel' if is_player_cancel else 'Interrupt'} {task.displayname or task.name}"
        )
        self.task = task
        self.t = t
        self.is_action = is_player_cancel
        self.is_player_cancel = is_player_cancel
        self.invalidate = True

    def validate(self, timestate: TimeState, t: float) -> bool:
        """Interrupt is valid if the task is running."""
        return any(p.name == self.task.name for p in timestate.processes)

    def on_start_vars(self, timestate: TimeState):
        """Revert process rates (task did not complete)."""
        # Restore rates for consumed resources
        for var_name, rate in self.task.consumed:
            var = timestate.get_variable(var_name)
            if var and isinstance(var, LinearVariable):
                var.rate += rate * self.task.throttle

        # Restore rates for produced resources
        for var_name, rate in self.task.produced:
            var = timestate.get_variable(var_name)
            if var and isinstance(var, LinearVariable):
                var.rate -= rate * self.task.throttle

        # Remove process from active processes (by name, since processes are deepcopied)
        timestate.processes = [p for p in timestate.processes if p.name != self.task.name]

        # Remove progress variable (task is incomplete but stopped)
        if self.task.name + "_progress" in timestate.registry:
            del timestate.registry[self.task.name + "_progress"]