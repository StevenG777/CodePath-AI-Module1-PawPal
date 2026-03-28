"""Tests for the Scheduler class: retrieval, sorting, filtering, conflicts,
schedule generation, slot-finding, mutation, and day advancement."""
import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# get_tasks_for_pet
# ---------------------------------------------------------------------------

def test_get_tasks_for_pet_returns_correct_tasks(scheduler_with_pets):
    tasks = scheduler_with_pets.get_tasks_for_pet("Bella")
    names = [t.task_name for t in tasks]
    assert "Morning Walk" in names
    assert "Feeding" in names


def test_get_tasks_for_pet_returns_empty_for_unknown_pet(scheduler_with_pets):
    assert scheduler_with_pets.get_tasks_for_pet("Ghost") == []


def test_get_tasks_for_pet_does_not_include_other_pets_tasks(scheduler_with_pets):
    bella_tasks = scheduler_with_pets.get_tasks_for_pet("Bella")
    names = [t.task_name for t in bella_tasks]
    assert "Evening Walk" not in names
    assert "Playtime" not in names


# ---------------------------------------------------------------------------
# get_tasks_by_priority
# ---------------------------------------------------------------------------

def test_get_tasks_by_priority_high(scheduler_with_pets):
    pairs = scheduler_with_pets.get_tasks_by_priority("high")
    assert all(t.priority == "high" for _, t in pairs)


def test_get_tasks_by_priority_low(scheduler_with_pets):
    pairs = scheduler_with_pets.get_tasks_by_priority("low")
    assert all(t.priority == "low" for _, t in pairs)
    names = [t.task_name for _, t in pairs]
    assert "Playtime" in names


def test_get_tasks_by_priority_returns_empty_when_none_match(scheduler_with_pets):
    pairs = scheduler_with_pets.get_tasks_by_priority("medium")
    assert pairs == []


# ---------------------------------------------------------------------------
# filter_by_status
# ---------------------------------------------------------------------------

def test_filter_by_status_incomplete_returns_all_initially(scheduler_with_pets):
    incomplete = scheduler_with_pets.filter_by_status(completed=False)
    assert len(incomplete) == 4  # all tasks start incomplete


def test_filter_by_status_completed_returns_empty_initially(scheduler_with_pets):
    assert scheduler_with_pets.filter_by_status(completed=True) == []


def test_filter_by_status_after_completing_one(scheduler_with_pets):
    bella = scheduler_with_pets.owner.get_pet("Bella")
    bella.get_task("Morning Walk").mark_complete()

    completed = scheduler_with_pets.filter_by_status(completed=True)
    assert len(completed) == 1
    assert completed[0][1].task_name == "Morning Walk"


# ---------------------------------------------------------------------------
# filter_by_frequency
# ---------------------------------------------------------------------------

def test_filter_by_frequency_daily(scheduler_with_pets):
    """All tasks default to daily — all 4 should be returned."""
    daily = scheduler_with_pets.filter_by_frequency("daily")
    assert len(daily) == 4


def test_filter_by_frequency_weekly_empty_by_default(scheduler_with_pets):
    assert scheduler_with_pets.filter_by_frequency("weekly") == []


def test_filter_by_frequency_after_adding_weekly_task(scheduler_with_pets):
    bella = scheduler_with_pets.owner.get_pet("Bella")
    bella.add_task(Task("Bath", duration=20, priority="medium", frequency="weekly"))
    weekly = scheduler_with_pets.filter_by_frequency("weekly")
    assert len(weekly) == 1
    assert weekly[0][1].task_name == "Bath"


# ---------------------------------------------------------------------------
# sort_by_time (existing cases kept here for completeness)
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Dinner",    duration=20, priority="high",   start_time=1080))
    pet.add_task(Task("Breakfast", duration=10, priority="high",   start_time=480))
    pet.add_task(Task("Lunch",     duration=15, priority="medium", start_time=720))
    owner.add_pet(pet)
    sched = Scheduler(owner, available_minutes=300)
    result = sched.sort_by_time(sched.get_all_tasks())
    names = [t.task_name for _, t in result]
    assert names == ["Breakfast", "Lunch", "Dinner"]


def test_sort_unscheduled_tasks_go_last():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Unscheduled", duration=10, priority="high"))
    pet.add_task(Task("Morning",     duration=10, priority="high", start_time=480))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    result = sched.sort_by_time(sched.get_all_tasks())
    assert result[0][1].task_name == "Morning"
    assert result[1][1].task_name == "Unscheduled"


def test_sort_unscheduled_tie_broken_by_priority():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("LowTask",  duration=10, priority="low"))
    pet.add_task(Task("HighTask", duration=10, priority="high"))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    result = sched.sort_by_time(sched.get_all_tasks())
    assert result[0][1].task_name == "HighTask"


def test_sort_empty_task_list():
    owner = Owner("Sam")
    owner.add_pet(Pet("Cleo", "Sam"))
    sched = Scheduler(owner)
    assert sched.sort_by_time([]) == []


def test_sort_two_tasks_same_start_time_priority_wins():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("LowAtNoon",  duration=10, priority="low",  start_time=720))
    pet.add_task(Task("HighAtNoon", duration=10, priority="high", start_time=720))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    result = sched.sort_by_time(sched.get_all_tasks())
    assert result[0][1].task_name == "HighAtNoon"


# ---------------------------------------------------------------------------
# sort_by_priority
# ---------------------------------------------------------------------------

def test_sort_by_priority_high_before_medium_before_low():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Low",    duration=10, priority="low"))
    pet.add_task(Task("High",   duration=10, priority="high"))
    pet.add_task(Task("Medium", duration=10, priority="medium"))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    result = sched.sort_by_priority(sched.get_all_tasks())
    priorities = [t.priority for _, t in result]
    assert priorities == ["high", "medium", "low"]


def test_sort_by_priority_timed_before_unscheduled_within_same_priority():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Unscheduled High", duration=10, priority="high"))
    pet.add_task(Task("Timed High",       duration=10, priority="high", start_time=480))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    result = sched.sort_by_priority(sched.get_all_tasks())
    assert result[0][1].task_name == "Timed High"


def test_sort_by_priority_shorter_duration_wins_tiebreak():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Long High",  duration=60, priority="high"))
    pet.add_task(Task("Short High", duration=10, priority="high"))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    result = sched.sort_by_priority(sched.get_all_tasks())
    assert result[0][1].task_name == "Short High"


# ---------------------------------------------------------------------------
# Conflict detection
# ---------------------------------------------------------------------------

def test_no_conflict_for_sequential_tasks():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=30, priority="high", start_time=480))
    pet.add_task(Task("B", duration=30, priority="high", start_time=510))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    assert sched.get_conflicts() == []


def test_conflict_detected_for_overlapping_tasks():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=60, priority="high", start_time=480))
    pet.add_task(Task("B", duration=30, priority="high", start_time=510))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    assert len(sched.get_conflicts()) == 1


def test_conflict_detected_same_start_time():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=30, priority="high",   start_time=600))
    pet.add_task(Task("B", duration=15, priority="medium", start_time=600))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    assert len(sched.get_conflicts()) == 1


def test_no_conflict_for_adjacent_tasks():
    """End of A == start of B is NOT an overlap."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=30, priority="high", start_time=480))
    pet.add_task(Task("B", duration=30, priority="high", start_time=510))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    assert sched.get_conflicts() == []


def test_completed_tasks_not_flagged_as_conflicts():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    t1 = Task("A", duration=60, priority="high", start_time=480)
    t2 = Task("B", duration=60, priority="high", start_time=480)
    t1.mark_complete()
    pet.add_task(t1)
    pet.add_task(t2)
    owner.add_pet(pet)
    sched = Scheduler(owner)
    assert sched.get_conflicts() == []


def test_unscheduled_tasks_not_flagged_as_conflicts():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=30, priority="high"))
    pet.add_task(Task("B", duration=30, priority="high"))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    assert sched.get_conflicts() == []


def test_no_conflict_when_no_tasks():
    owner = Owner("Sam")
    owner.add_pet(Pet("Cleo", "Sam"))
    sched = Scheduler(owner)
    assert sched.get_conflicts() == []


def test_warn_conflicts_returns_count():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=60, priority="high", start_time=480))
    pet.add_task(Task("B", duration=30, priority="high", start_time=500))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    assert sched.warn_conflicts() == 1


def test_conflicts_across_multiple_pets():
    """Tasks on different pets can still conflict."""
    owner = Owner("Sam")
    p1 = Pet("Bella", "Sam")
    p2 = Pet("Max",   "Sam")
    p1.add_task(Task("WalkA", duration=60, priority="high", start_time=480))
    p2.add_task(Task("WalkB", duration=30, priority="high", start_time=490))
    owner.add_pet(p1)
    owner.add_pet(p2)
    sched = Scheduler(owner)
    assert len(sched.get_conflicts()) == 1


# ---------------------------------------------------------------------------
# generate_schedule
# ---------------------------------------------------------------------------

def test_generate_schedule_respects_time_budget():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Long Task", duration=90, priority="high"))
    owner.add_pet(pet)
    sched = Scheduler(owner, available_minutes=60)
    assert sched.generate_schedule() == []


def test_generate_schedule_zero_budget_returns_empty():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Walk", duration=1, priority="high"))
    owner.add_pet(pet)
    sched = Scheduler(owner, available_minutes=0)
    assert sched.generate_schedule() == []


def test_generate_schedule_pet_with_no_tasks():
    owner = Owner("Sam")
    owner.add_pet(Pet("Cleo", "Sam"))
    sched = Scheduler(owner, available_minutes=120)
    assert sched.generate_schedule() == []


def test_generate_schedule_skips_completed_tasks(scheduler_with_pets):
    bella = scheduler_with_pets.owner.get_pet("Bella")
    bella.get_task("Morning Walk").mark_complete()
    names = [t.task_name for _, t in scheduler_with_pets.generate_schedule()]
    assert "Morning Walk" not in names


def test_generate_schedule_happy_path(scheduler_with_pets):
    schedule = scheduler_with_pets.generate_schedule()
    assert len(schedule) > 0
    total = sum(t.duration for _, t in schedule)
    assert total <= scheduler_with_pets.available_minutes


def test_generate_schedule_excludes_not_yet_due_task():
    """A daily task completed today must not appear in today's schedule."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    task = Task("Feeding", duration=10, priority="high", frequency="daily")
    task.mark_complete(as_of=date.today())
    pet.add_task(task)
    owner.add_pet(pet)
    sched = Scheduler(owner, available_minutes=120)
    assert all(t.task_name != "Feeding" for _, t in sched.generate_schedule())


def test_generate_schedule_high_priority_included_before_low():
    """When budget is tight, high-priority tasks are scheduled before low-priority ones."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Low",  duration=60, priority="low"))
    pet.add_task(Task("High", duration=60, priority="high"))
    owner.add_pet(pet)
    sched = Scheduler(owner, available_minutes=60)  # fits only one
    schedule = sched.generate_schedule()
    assert len(schedule) == 1
    assert schedule[0][1].task_name == "High"


# ---------------------------------------------------------------------------
# find_next_available_slot
# ---------------------------------------------------------------------------

def test_find_slot_returns_start_after_when_no_tasks():
    owner = Owner("Sam")
    owner.add_pet(Pet("Cleo", "Sam"))
    sched = Scheduler(owner)
    assert sched.find_next_available_slot(30) == 360  # default start_after=360


def test_find_slot_skips_occupied_window():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Walk", duration=60, priority="high", start_time=360))  # 06:00–07:00
    owner.add_pet(pet)
    sched = Scheduler(owner)
    slot = sched.find_next_available_slot(30)
    assert slot == 420  # 07:00, right after the walk ends


def test_find_slot_returns_none_when_no_gap():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    # Fill the entire 06:00–22:00 window
    pet.add_task(Task("Block", duration=960, priority="high", start_time=360))
    owner.add_pet(pet)
    sched = Scheduler(owner)
    assert sched.find_next_available_slot(30) is None


def test_find_slot_respects_custom_start_after():
    owner = Owner("Sam")
    owner.add_pet(Pet("Cleo", "Sam"))
    sched = Scheduler(owner)
    assert sched.find_next_available_slot(30, start_after=600) == 600


def test_find_slot_returns_none_for_zero_duration():
    owner = Owner("Sam")
    owner.add_pet(Pet("Cleo", "Sam"))
    sched = Scheduler(owner)
    assert sched.find_next_available_slot(0) is None


def test_find_slot_ignores_completed_tasks():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    t = Task("Walk", duration=60, priority="high", start_time=360)
    t.mark_complete()
    pet.add_task(t)
    owner.add_pet(pet)
    sched = Scheduler(owner)
    # Completed task should not block the slot
    assert sched.find_next_available_slot(30) == 360


# ---------------------------------------------------------------------------
# remove_task (Scheduler public API)
# ---------------------------------------------------------------------------

def test_remove_task_via_scheduler(scheduler_with_pets):
    result = scheduler_with_pets.remove_task("Bella", "Morning Walk")
    assert result is True
    assert scheduler_with_pets.owner.get_pet("Bella").get_task("Morning Walk") is None


def test_remove_task_returns_false_for_unknown_pet(scheduler_with_pets):
    assert scheduler_with_pets.remove_task("Ghost", "Walk") is False


def test_remove_task_returns_false_for_unknown_task(scheduler_with_pets):
    assert scheduler_with_pets.remove_task("Bella", "Nonexistent") is False


# ---------------------------------------------------------------------------
# reset_all_tasks
# ---------------------------------------------------------------------------

def test_reset_all_tasks_clears_every_task(scheduler_with_pets):
    for pet in scheduler_with_pets.owner.pets:
        for task in pet.tasks:
            task.mark_complete()
    scheduler_with_pets.reset_all_tasks()
    for _, task in scheduler_with_pets.get_all_tasks():
        assert task.completed is False


def test_reset_all_tasks_clears_next_due_dates(scheduler_with_pets):
    for pet in scheduler_with_pets.owner.pets:
        for task in pet.tasks:
            task.mark_complete()
    scheduler_with_pets.reset_all_tasks()
    for _, task in scheduler_with_pets.get_all_tasks():
        assert task.next_due_date is None


# ---------------------------------------------------------------------------
# advance_day / rollover
# ---------------------------------------------------------------------------

def test_advance_day_resets_daily_task_next_day():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    task = Task("Feeding", duration=10, priority="high", frequency="daily")
    today = date(2026, 3, 27)
    task.mark_complete(as_of=today)
    pet.add_task(task)
    owner.add_pet(pet)
    sched = Scheduler(owner)
    reset = sched.advance_day(as_of=today + timedelta(days=1))
    assert task in reset
    assert task.completed is False


def test_advance_day_does_not_reset_task_not_yet_due():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    task = Task("Bath", duration=30, priority="medium", frequency="weekly")
    today = date(2026, 3, 27)
    task.mark_complete(as_of=today)
    pet.add_task(task)
    owner.add_pet(pet)
    sched = Scheduler(owner)
    reset = sched.advance_day(as_of=today + timedelta(days=1))
    assert task not in reset
    assert task.completed is True


def test_advance_day_resets_weekly_task_after_seven_days():
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    task = Task("Bath", duration=30, priority="medium", frequency="weekly")
    today = date(2026, 3, 27)
    task.mark_complete(as_of=today)
    pet.add_task(task)
    owner.add_pet(pet)
    sched = Scheduler(owner)
    reset = sched.advance_day(as_of=today + timedelta(days=7))
    assert task in reset


def test_advance_day_returns_empty_when_nothing_due():
    owner = Owner("Sam")
    owner.add_pet(Pet("Cleo", "Sam"))
    sched = Scheduler(owner)
    assert sched.advance_day() == []
