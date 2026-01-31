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
        i = bisect.bisect_right(self.events, t, key=lambda e: e.time)

        head_events = self.events[:i]

        for j in range(i, len(self.events)):
            if not self.events[j].invalidate: # Don't discard it out of hand...
                head_events.append(self.events[j])
        self.events = head_events

        # Now recompute from this time
        self.recompute(t)

    def next_event(self, t): # Returns (time, next event) or (max_time, None)
        idx = bisect.bisect_right(self.events, t, key=lambda e: e.time)

        if idx < len(self.events):
            ev = self.events[idx]
            return (ev.time, ev)
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

    # Examine all of the Processes in this state, and adjust their rates according to bottlenecks
    def recompute_bottlenecks(self, ts):
        pass

    # Check if there are any resource bottlenecks between t0 and t1
    # Returns (time, bottleneck) or (t1, None) if no bottleneck
    def check_bottlenecks(self, t0, t1):
        # Stub: no bottleneck system implemented yet
        return (t1, None)

    def recompute(self, t0): # Recompute all events and states from t0 onwards
        cur_time = t0

        while cur_time < self.max_time:
            next_time, next_event = self.next_event(cur_time)

            # Check if there are any bottlenecks between now and then
            next_btime, next_bottleneck = self.check_bottlenecks(cur_time, next_time)
            if next_btime < next_time:
                # Do the bottleneck first
                cur_time = next_btime
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
        bisect.insort(self.events, event, key=lambda e: e.time)
        event.trigger(event.time, self)
        self.invalidate_after(event.time)

    # Remove an event from the timeline and invalidate/recompute
    def remove_event(self, event):
        if event in self.events:
            t = event.time
            self.events.remove(event)
            # Clear states at AND after the event time (unlike invalidate_after which keeps states at t)
            self.state_cache = self.state_cache[:bisect.bisect_left(self.state_cache, t, key=lambda e: e.time)]
            # Process remaining events - keep those without invalidate flag
            i = bisect.bisect_right(self.events, t, key=lambda e: e.time)
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

class Process(Event): # Ongoing event which converts one resource into another continuously while it exists
    consumed: List[Tuple[LinearVariable, float]] = None
    produced: List[Tuple[LinearVariable, float]] = None
    throttle: float = 1.0 # What fraction of the maximum rate does this process operate at?

    def __init__(self, name, displayname = None):
        # We should make sure this process is unique
        super().__init__(name, displayname)
        self.consumed = []
        self.produced = []    

class Task(Process): # Event which runs until completion; registers a LinearVariable on trigger, removes it on completion
    progress: LinearVariable = None
    rate: float = 0.0

    def __init__(self, name, rate, displayname = None):
        super().__init__(name, displayname)
        self.rate = rate

    def trigger(self, t: float, timeline: Timeline):
        # Make sure this task is unique
        ts = timeline.state_at(t)
        if ts.get_variable(self.name+"_progress"): # Task already exists
            return
        
        super().trigger(t, timeline)

        ts = timeline.state_at(t)
        ts.add_variable(LinearVariable(self.name+"_progress", 0, min=0, max=100, rate=self.rate))

    def on_finish_vars(self, timestate: TimeState):
        pass

    def on_finish_effects(self, timeline: Timeline):
        pass