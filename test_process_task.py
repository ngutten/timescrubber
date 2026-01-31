"""
Tests for Process and Task lifecycle in the timeline system.

These tests verify:
1. Process rate modification and end events
2. Bottleneck detection and handling
3. Task completion and cancellation
4. Event ordering and validation
5. Task chaining
"""

import unittest
from copy import deepcopy

from timeline import (
    Timeline, TimeState, Event, Process, Task,
    ProcessEnd, TaskComplete, TaskInterrupt
)
from variable import Variable, LinearVariable
from registry import Registry


class TestProcessBasic(unittest.TestCase):
    """Test basic Process functionality."""

    def setUp(self):
        """Create a fresh timeline for each test."""
        self.initial = TimeState(0)
        self.initial.add_variable(LinearVariable('Resource', value=100, min=0, max=1000, rate=0))
        self.initial.add_variable(LinearVariable('Product', value=0, min=0, max=1000, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

    def test_process_modifies_rates_on_start(self):
        """Process should modify variable rates when it starts."""
        # Create a process that consumes Resource and produces Product
        process = Process(
            name="converter",
            displayname="Resource Converter",
            consumed=[("Resource", 2.0)],  # Consume 2 per time
            produced=[("Product", 1.0)]    # Produce 1 per time
        )
        process.t = 10
        process.is_action = True

        self.timeline.add_event(process)

        # Check rates before process (t=5)
        ts_before = self.timeline.state_at(5)
        self.assertEqual(ts_before.get_variable('Resource').rate, 0)
        self.assertEqual(ts_before.get_variable('Product').rate, 0)

        # Check rates during process (t=15)
        ts_during = self.timeline.state_at(15)
        self.assertEqual(ts_during.get_variable('Resource').rate, -2.0)
        self.assertEqual(ts_during.get_variable('Product').rate, 1.0)

    def test_process_values_at_specific_times(self):
        """Verify resource values are correct at specific times."""
        process = Process(
            name="converter",
            consumed=[("Resource", 2.0)],
            produced=[("Product", 1.0)]
        )
        process.t = 10
        process.is_action = True

        self.timeline.add_event(process)

        # At t=10, process just started
        ts10 = self.timeline.state_at(10)
        self.assertEqual(ts10.get_variable('Resource').get(10), 100)
        self.assertEqual(ts10.get_variable('Product').get(10), 0)

        # At t=20, process has been running for 10 time units
        ts20 = self.timeline.state_at(20)
        self.assertEqual(ts20.get_variable('Resource').get(20), 80)  # 100 - 2*10
        self.assertEqual(ts20.get_variable('Product').get(20), 10)   # 0 + 1*10

    def test_process_end_reverts_rates(self):
        """ProcessEnd should revert rate changes."""
        process = Process(
            name="converter",
            consumed=[("Resource", 2.0)],
            produced=[("Product", 1.0)]
        )
        process.t = 10
        process.is_action = True

        self.timeline.add_event(process)

        # Process should have scheduled an end event at t=60 (100/2 + 10)
        self.assertIsNotNone(process.end_event)
        self.assertEqual(process.end_event.t, 60)  # Resource depletes at t=60

        # Check rates after process ends (t=65)
        ts_after = self.timeline.state_at(65)
        self.assertEqual(ts_after.get_variable('Resource').rate, 0)
        self.assertEqual(ts_after.get_variable('Product').rate, 0)

        # Values should be frozen after process ends
        self.assertEqual(ts_after.get_variable('Resource').get(65), 0)
        self.assertEqual(ts_after.get_variable('Product').get(65), 50)  # 1 * 50 time units


class TestProcessBottleneck(unittest.TestCase):
    """Test Process bottleneck detection and handling."""

    def setUp(self):
        """Create a timeline with limited resources."""
        self.initial = TimeState(0)
        # Limited resource that will deplete
        self.initial.add_variable(LinearVariable('Fuel', value=20, min=0, max=100, rate=0))
        self.initial.add_variable(LinearVariable('Energy', value=0, min=0, max=1000, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

    def test_process_stops_at_resource_depletion(self):
        """Process should automatically stop when consumed resource depletes."""
        process = Process(
            name="generator",
            consumed=[("Fuel", 2.0)],   # Consumes 2 fuel per time
            produced=[("Energy", 5.0)]  # Produces 5 energy per time
        )
        process.t = 0
        process.is_action = True

        self.timeline.add_event(process)

        # Fuel should deplete at t=10 (20/2 = 10)
        self.assertIsNotNone(process.end_event)
        self.assertEqual(process.end_event.t, 10)

        # At t=10, fuel should be 0 and process should have stopped
        ts10 = self.timeline.state_at(10)
        self.assertEqual(ts10.get_variable('Fuel').get(10), 0)
        self.assertEqual(ts10.get_variable('Energy').get(10), 50)  # 5 * 10
        self.assertEqual(len(ts10.processes), 0)

        # After t=10, values should be frozen
        ts15 = self.timeline.state_at(15)
        self.assertEqual(ts15.get_variable('Fuel').get(15), 0)
        self.assertEqual(ts15.get_variable('Energy').get(15), 50)  # Still 50

    def test_multiple_consumed_resources_earliest_depletion(self):
        """Process should stop at the earliest depletion among consumed resources."""
        self.initial.add_variable(LinearVariable('Water', value=15, min=0, max=100, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

        process = Process(
            name="reactor",
            consumed=[("Fuel", 2.0), ("Water", 3.0)],  # Water depletes first (15/3=5)
            produced=[("Energy", 10.0)]
        )
        process.t = 0
        process.is_action = True

        self.timeline.add_event(process)

        # Water should deplete at t=5 (15/3 = 5), before Fuel at t=10 (20/2 = 10)
        self.assertEqual(process.end_event.t, 5)

        ts5 = self.timeline.state_at(5)
        self.assertEqual(ts5.get_variable('Water').get(5), 0)
        self.assertEqual(ts5.get_variable('Fuel').get(5), 10)  # 20 - 2*5
        self.assertEqual(ts5.get_variable('Energy').get(5), 50)  # 10 * 5


class TestBottleneckAlteredByEvents(unittest.TestCase):
    """Test that bottleneck times are recalculated when events modify resources."""

    def setUp(self):
        """Create a timeline for bottleneck alteration tests."""
        self.initial = TimeState(0)
        self.initial.add_variable(LinearVariable('Fuel', value=20, min=0, max=100, rate=0))
        self.initial.add_variable(LinearVariable('Energy', value=0, min=0, max=1000, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

    def test_event_decreases_resource_bottleneck_sooner(self):
        """An event that decreases a resource should cause bottleneck sooner."""
        # Start process at t=0, would normally end at t=10 (20 fuel / 2 per time)
        process = Process(
            name="generator",
            consumed=[("Fuel", 2.0)],
            produced=[("Energy", 5.0)]
        )
        process.t = 0
        process.is_action = True
        self.timeline.add_event(process)

        # Add an event at t=5 that removes 6 fuel
        class RemoveFuelEvent(Event):
            def on_start_vars(self, timestate):
                fuel = timestate.get_variable('Fuel')
                current = fuel.get(timestate.time)
                fuel.set(current - 6, timestate.time)

        remove_event = RemoveFuelEvent("remove_fuel")
        remove_event.t = 5
        remove_event.invalidate = True
        self.timeline.add_event(remove_event)

        # After t=5: fuel = 20 - 2*5 - 6 = 4, rate = -2
        # Fuel depletes at t = 5 + 4/2 = 7
        # Process should be removed from state at t=7

        # At t=6, process should still be running
        ts6 = self.timeline.state_at(6)
        self.assertEqual(len(ts6.processes), 1)
        self.assertGreater(ts6.get_variable('Fuel').get(6), 0)

        # At t=7, fuel should be depleted and process should have stopped
        ts7 = self.timeline.state_at(7)
        self.assertEqual(ts7.get_variable('Fuel').get(7), 0)
        self.assertEqual(len(ts7.processes), 0)

        # At t=8, values should be frozen
        ts8 = self.timeline.state_at(8)
        self.assertEqual(ts8.get_variable('Fuel').get(8), 0)
        self.assertEqual(len(ts8.processes), 0)

    def test_event_increases_resource_bottleneck_later(self):
        """An event that increases a resource should cause bottleneck later."""
        # Start process at t=0, would normally end at t=10
        process = Process(
            name="generator",
            consumed=[("Fuel", 2.0)],
            produced=[("Energy", 5.0)]
        )
        process.t = 0
        process.is_action = True
        self.timeline.add_event(process)

        # Add an event at t=5 that adds 10 fuel
        class AddFuelEvent(Event):
            def on_start_vars(self, timestate):
                fuel = timestate.get_variable('Fuel')
                current = fuel.get(timestate.time)
                fuel.set(current + 10, timestate.time)

        add_event = AddFuelEvent("add_fuel")
        add_event.t = 5
        add_event.invalidate = True
        self.timeline.add_event(add_event)

        # After t=5: fuel = 20 - 2*5 + 10 = 20, rate = -2
        # Fuel depletes at t = 5 + 20/2 = 15
        # Process should still be running at t=10 (original end time)

        # At t=10, process should still be running (fuel refilled)
        ts10 = self.timeline.state_at(10)
        self.assertEqual(len(ts10.processes), 1)
        self.assertGreater(ts10.get_variable('Fuel').get(10), 0)

        # At t=15, fuel should be depleted and process should have stopped
        ts15 = self.timeline.state_at(15)
        self.assertEqual(ts15.get_variable('Fuel').get(15), 0)
        self.assertEqual(len(ts15.processes), 0)
        self.assertEqual(ts15.get_variable('Energy').get(15), 75)  # 5 * 15

        # At t=16, values should be frozen
        ts16 = self.timeline.state_at(16)
        self.assertEqual(ts16.get_variable('Fuel').get(16), 0)
        self.assertEqual(ts16.get_variable('Energy').get(16), 75)


class TestTaskCompletion(unittest.TestCase):
    """Test Task completion functionality."""

    def setUp(self):
        """Create a timeline for task tests."""
        self.initial = TimeState(0)
        self.initial.add_variable(LinearVariable('Stamina', value=100, min=0, max=100, rate=0))
        self.initial.add_variable(LinearVariable('Wood', value=0, min=0, max=1000, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

    def test_task_creates_progress_variable(self):
        """Task should create a progress variable when started."""
        task = Task(
            name="gather",
            rate=10,  # 10 time units to complete
            displayname="Gather Resources",
            consumed=[("Stamina", 1.0)],
            produced=[]
        )
        task.t = 0
        task.is_action = True

        self.timeline.add_event(task)

        # Progress variable should exist
        ts0 = self.timeline.state_at(0)
        progress = ts0.get_variable('gather_progress')
        self.assertIsNotNone(progress)
        self.assertEqual(progress.get(0), 0)
        self.assertEqual(progress.rate, 10)

        # Progress at t=5 should be 50
        ts5 = self.timeline.state_at(5)
        progress5 = ts5.get_variable('gather_progress')
        self.assertEqual(progress5.get(5), 50)

    def test_task_completes_at_100_progress(self):
        """Task should complete when progress reaches 100."""
        task = Task(
            name="gather",
            rate=10,  # Completes at t=10
            displayname="Gather Resources",
            consumed=[("Stamina", 1.0)],
            produced=[]
        )
        task.t = 0
        task.is_action = True

        self.timeline.add_event(task)

        # End event should be TaskComplete at t=10
        self.assertIsInstance(task.end_event, TaskComplete)
        self.assertEqual(task.end_event.t, 10)

        # After completion, progress variable should be removed
        ts_after = self.timeline.state_at(15)
        self.assertIsNone(ts_after.get_variable('gather_progress'))
        self.assertEqual(len(ts_after.processes), 0)

    def test_task_on_finish_vars_called(self):
        """Task's on_finish_vars should be called on completion."""
        class WoodGatherTask(Task):
            def on_finish_vars(self, timestate):
                wood = timestate.get_variable('Wood')
                current = wood.get(timestate.time)
                wood.set(current + 5, timestate.time)

        task = WoodGatherTask(
            name="gather_wood",
            rate=20,  # Completes at t=5
            displayname="Gather Wood",
            consumed=[],
            produced=[]
        )
        task.t = 0
        task.is_action = True

        self.timeline.add_event(task)

        # Before completion
        ts4 = self.timeline.state_at(4)
        self.assertEqual(ts4.get_variable('Wood').get(4), 0)

        # After completion
        ts6 = self.timeline.state_at(6)
        self.assertEqual(ts6.get_variable('Wood').get(6), 5)


class TestTaskInterruption(unittest.TestCase):
    """Test Task interruption when resources deplete."""

    def setUp(self):
        """Create a timeline with limited stamina."""
        self.initial = TimeState(0)
        self.initial.add_variable(LinearVariable('Stamina', value=5, min=0, max=100, rate=0))
        self.initial.add_variable(LinearVariable('Wood', value=0, min=0, max=1000, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

    def test_task_interrupted_on_resource_depletion(self):
        """Task should be interrupted when consumed resource depletes."""
        task = Task(
            name="gather",
            rate=5,  # Would complete at t=20
            displayname="Gather Resources",
            consumed=[("Stamina", 1.0)],  # Stamina depletes at t=5
            produced=[]
        )
        task.t = 0
        task.is_action = True

        self.timeline.add_event(task)

        # End event should be TaskInterrupt at t=5
        self.assertIsInstance(task.end_event, TaskInterrupt)
        self.assertEqual(task.end_event.t, 5)

        # Task should not complete - on_finish_vars not called
        ts_after = self.timeline.state_at(10)
        self.assertIsNone(ts_after.get_variable('gather_progress'))
        self.assertEqual(len(ts_after.processes), 0)

    def test_task_completion_before_depletion(self):
        """Task should complete normally if it finishes before resource depletes."""
        self.initial = TimeState(0)
        self.initial.add_variable(LinearVariable('Stamina', value=20, min=0, max=100, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

        task = Task(
            name="quick_gather",
            rate=20,  # Completes at t=5
            displayname="Quick Gather",
            consumed=[("Stamina", 2.0)],  # Would deplete at t=10
            produced=[]
        )
        task.t = 0
        task.is_action = True

        self.timeline.add_event(task)

        # Should be TaskComplete, not TaskInterrupt
        self.assertIsInstance(task.end_event, TaskComplete)
        self.assertEqual(task.end_event.t, 5)


class TestTaskCancellation(unittest.TestCase):
    """Test Task cancellation by player."""

    def setUp(self):
        """Create a timeline for cancellation tests."""
        self.initial = TimeState(0)
        self.initial.add_variable(LinearVariable('Stamina', value=100, min=0, max=100, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

    def test_task_can_be_cancelled(self):
        """Player should be able to cancel a running task by adding a cancel event."""
        task = Task(
            name="long_task",
            rate=5,  # Would complete at t=20
            displayname="Long Task",
            consumed=[("Stamina", 0.5)],
            produced=[]
        )
        task.t = 0
        task.is_action = True

        self.timeline.add_event(task)

        # Task should be running at t=5
        ts5 = self.timeline.state_at(5)
        self.assertEqual(len(ts5.processes), 1)
        self.assertIsNotNone(ts5.get_variable('long_task_progress'))

        # Cancel at t=10 by adding a TaskInterrupt event
        cancel_event = TaskInterrupt(task, 10, is_player_cancel=True)
        cancel_event.is_action = True  # Player action
        self.timeline.add_event(cancel_event)

        # Task should end at t=10
        ts_after = self.timeline.state_at(15)
        self.assertEqual(len(ts_after.processes), 0)
        self.assertIsNone(ts_after.get_variable('long_task_progress'))

        # Check that stamina stopped being consumed at t=10
        ts10 = self.timeline.state_at(10)
        stamina_at_10 = ts10.get_variable('Stamina').get(10)

        ts15 = self.timeline.state_at(15)
        stamina_at_15 = ts15.get_variable('Stamina').get(15)

        # Stamina should be same at t=10 and t=15 (no consumption after cancel)
        self.assertEqual(stamina_at_10, stamina_at_15)


class TestTaskChaining(unittest.TestCase):
    """Test Task chaining where one task queues another on completion."""

    def setUp(self):
        """Create a timeline for chaining tests."""
        self.initial = TimeState(0)
        self.initial.add_variable(LinearVariable('Stamina', value=100, min=0, max=100, rate=0))
        self.initial.add_variable(LinearVariable('Wood', value=0, min=0, max=1000, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

    def test_task_chains_another_task(self):
        """A task can queue another task when it completes."""
        second_task_started = []

        class SecondTask(Task):
            def validate(self, timestate, t):
                # Require 5 wood to start
                wood = timestate.get_variable('Wood')
                if not wood or wood.get(t) < 5:
                    return False
                return super().validate(timestate, t)

        class FirstTask(Task):
            def on_finish_vars(self, timestate):
                # Add 5 wood on completion
                wood = timestate.get_variable('Wood')
                current = wood.get(timestate.time)
                wood.set(current + 5, timestate.time)

            def on_finish_effects(self, timeline):
                # Queue second task
                second = SecondTask(
                    name="second_task",
                    rate=20,
                    displayname="Second Task",
                    consumed=[],
                    produced=[]
                )
                second.t = self.t + 10  # Small offset
                second.is_action = False  # System-queued
                second.invalidate = True
                second_task_started.append(second)
                timeline.add_event(second)

        first = FirstTask(
            name="first_task",
            rate=20,  # Completes at t=5
            displayname="First Task",
            consumed=[],
            produced=[]
        )
        first.t = 0
        first.is_action = True

        self.timeline.add_event(first)

        # First task should complete at t=5
        self.assertEqual(first.end_event.t, 5)

        # Second task should be queued
        self.assertEqual(len(second_task_started), 1)
        second = second_task_started[0]

        # Wood should be available for second task validation
        ts5 = self.timeline.state_at(5)
        self.assertEqual(ts5.get_variable('Wood').get(5), 5)

    def test_chained_task_resources_available(self):
        """Resources added by first task should be available for second task validation."""
        class SecondTask(Task):
            def validate(self, timestate, t):
                wood = timestate.get_variable('Wood')
                if not wood or wood.get(t) < 5:
                    return False
                return super().validate(timestate, t)

        class FirstTask(Task):
            def on_finish_vars(self, timestate):
                wood = timestate.get_variable('Wood')
                current = wood.get(timestate.time)
                wood.set(current + 5, timestate.time)

            def on_finish_effects(self, timeline):
                # Queue second task at exact same time
                second = SecondTask(
                    name="second_task",
                    rate=20,
                    displayname="Second Task",
                    consumed=[],
                    produced=[]
                )
                second.t = self.end_event.t  # Same time as first completes
                second.is_action = False
                second.invalidate = True
                timeline.add_event(second)

        first = FirstTask(
            name="first_task",
            rate=20,  # Completes at t=5
            displayname="First Task",
            consumed=[],
            produced=[]
        )
        first.t = 0
        first.is_action = True

        self.timeline.add_event(first)

        # Find the second task in events
        second_tasks = [e for e in self.timeline.events if e.name == "second_task"]
        self.assertEqual(len(second_tasks), 1)

        # Second task should have validated successfully (wood=5 at t=5)
        ts5 = self.timeline.state_at(5)
        # Check that second task is in the processes list
        process_names = [p.name for p in ts5.processes]
        self.assertIn("second_task", process_names)


class TestProcessUniqueness(unittest.TestCase):
    """Test that processes/tasks with the same name cannot run simultaneously."""

    def setUp(self):
        """Create a timeline for uniqueness tests."""
        self.initial = TimeState(0)
        self.initial.add_variable(LinearVariable('Resource', value=100, min=0, max=1000, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

    def test_duplicate_process_rejected(self):
        """Second process with same name should fail validation."""
        process1 = Process(
            name="converter",
            consumed=[("Resource", 1.0)],
            produced=[]
        )
        process1.t = 0
        process1.is_action = True

        process2 = Process(
            name="converter",  # Same name
            consumed=[("Resource", 1.0)],
            produced=[]
        )
        process2.t = 5
        process2.is_action = True

        self.timeline.add_event(process1)

        # Second process should fail validation
        ts5 = self.timeline.state_at(5)
        self.assertFalse(process2.validate(ts5, 5))

    def test_duplicate_task_rejected(self):
        """Second task with same name should fail validation."""
        task1 = Task(
            name="gather",
            rate=5,
            displayname="Gather",
            consumed=[],
            produced=[]
        )
        task1.t = 0
        task1.is_action = True

        task2 = Task(
            name="gather",  # Same name
            rate=10,
            displayname="Gather Again",
            consumed=[],
            produced=[]
        )
        task2.t = 5
        task2.is_action = True

        self.timeline.add_event(task1)

        # Task already has progress variable
        ts5 = self.timeline.state_at(5)
        self.assertFalse(task2.validate(ts5, 5))


class TestEventOrdering(unittest.TestCase):
    """Test correct ordering of events and states at simultaneous times."""

    def setUp(self):
        """Create a timeline for ordering tests."""
        self.initial = TimeState(0)
        self.initial.add_variable(LinearVariable('Value', value=0, min=0, max=1000, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

    def test_multiple_events_same_time(self):
        """Multiple events at the same time should all be processed."""
        class AddValueEvent(Event):
            def __init__(self, name, amount):
                super().__init__(name)
                self.amount = amount
                self.invalidate = True

            def on_start_vars(self, timestate):
                val = timestate.get_variable('Value')
                current = val.get(timestate.time)
                val.set(current + self.amount, timestate.time)

        # Add three events at t=5
        for i in range(3):
            event = AddValueEvent(f"add_{i}", 10)
            event.t = 5
            self.timeline.add_event(event)

        # All three should have executed
        ts_after = self.timeline.state_at(6)
        self.assertEqual(ts_after.get_variable('Value').get(6), 30)

    def test_state_cache_ordering(self):
        """State cache should maintain correct time ordering."""
        class SetValueEvent(Event):
            def __init__(self, name, value):
                super().__init__(name)
                self.value = value

            def on_start_vars(self, timestate):
                val = timestate.get_variable('Value')
                val.set(self.value, timestate.time)

        # Add events at different times
        for t in [10, 5, 15, 2]:
            event = SetValueEvent(f"set_at_{t}", t * 10)
            event.t = t
            self.timeline.add_event(event)

        # State cache should be sorted by time
        times = [s.time for s in self.timeline.state_cache]
        self.assertEqual(times, sorted(times))


class TestTaskInvalidation(unittest.TestCase):
    """Test Task invalidation when earlier events change."""

    def setUp(self):
        """Create a timeline for invalidation tests."""
        self.initial = TimeState(0)
        self.initial.add_variable(LinearVariable('Stamina', value=10, min=0, max=100, rate=0))
        self.timeline = Timeline(self.initial)
        self.timeline.max_time = 100

    def test_task_invalidated_by_earlier_event(self):
        """Task should be invalidated if an earlier event makes it invalid."""
        # Task that requires stamina > 5 to run
        class StaminaTask(Task):
            def validate(self, timestate, t):
                stamina = timestate.get_variable('Stamina')
                if not stamina or stamina.get(t) < 5:
                    return False
                return super().validate(timestate, t)

        task = StaminaTask(
            name="stamina_task",
            rate=20,
            displayname="Stamina Task",
            consumed=[],
            produced=[]
        )
        task.t = 10
        task.is_action = True
        task.invalidate = True

        self.timeline.add_event(task)

        # Task should be running at t=10
        ts10 = self.timeline.state_at(10)
        self.assertIn("stamina_task", [p.name for p in ts10.processes])

        # Add an event at t=5 that removes all stamina
        class DrainStaminaEvent(Event):
            def on_start_vars(self, timestate):
                stamina = timestate.get_variable('Stamina')
                stamina.set(0, timestate.time)

        drain = DrainStaminaEvent("drain_stamina")
        drain.t = 5
        drain.invalidate = True
        self.timeline.add_event(drain)

        # Task should no longer be in events (validation failed)
        task_events = [e for e in self.timeline.events if e.name == "stamina_task"]
        # The task might still be in events but should have failed to trigger
        ts10_after = self.timeline.state_at(10)
        self.assertNotIn("stamina_task", [p.name for p in ts10_after.processes])


if __name__ == '__main__':
    unittest.main()
