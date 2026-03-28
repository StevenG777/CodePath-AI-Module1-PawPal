import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def walk_task():
    return Task(task_name="Walk", duration=30, priority="high")

@pytest.fixture
def bella():
    return Pet(name="Bella", owner_name="Alex")

@pytest.fixture
def scheduler_with_pets():
    """Owner with two pets and a mix of tasks for integration tests."""
    owner = Owner("Alex")
    bella = Pet(name="Bella", owner_name="Alex")
    max_ = Pet(name="Max", owner_name="Alex")

    bella.add_task(Task("Morning Walk",  duration=30, priority="high",   start_time=480))   # 08:00
    bella.add_task(Task("Feeding",       duration=10, priority="high",   start_time=540))   # 09:00
    bella.add_task(Task("Grooming",      duration=20, priority="medium", start_time=600))   # 10:00
    max_.add_task(Task("Evening Walk",   duration=30, priority="high",   start_time=1080))  # 18:00
    max_.add_task(Task("Playtime",       duration=15, priority="low"))                      # unscheduled

    owner.add_pet(bella)
    owner.add_pet(max_)
    return Scheduler(owner, available_minutes=120)


# ---------------------------------------------------------------------------
# Task Completion (existing)
# ---------------------------------------------------------------------------

def test_task_starts_incomplete(walk_task):
    assert walk_task.completed is False

def test_mark_complete_changes_status(walk_task):
    walk_task.mark_complete()
    assert walk_task.completed is True

def test_reset_after_complete(walk_task):
    walk_task.mark_complete()
    walk_task.reset()
    assert walk_task.completed is False

def test_get_task_returns_none_for_missing(bella):
    assert bella.get_task("Nonexistent") is None


# ---------------------------------------------------------------------------
# Pet Task Addition (existing)
# ---------------------------------------------------------------------------

def test_pet_starts_with_no_tasks(bella):
    assert len(bella.tasks) == 0

def test_add_task_increases_count(bella, walk_task):
    bella.add_task(walk_task)
    assert len(bella.tasks) == 1

def test_add_multiple_tasks_increases_count(bella):
    bella.add_task(Task(task_name="Feeding",  duration=10, priority="high"))
    bella.add_task(Task(task_name="Walk",     duration=30, priority="high"))
    bella.add_task(Task(task_name="Grooming", duration=20, priority="medium"))
    assert len(bella.tasks) == 3

def test_added_task_is_retrievable(bella, walk_task):
    bella.add_task(walk_task)
    assert bella.get_task("Walk") is walk_task


# ---------------------------------------------------------------------------
# Sorting Correctness
# Happy path: tasks with explicit start_times come first, ordered by time.
# Edge cases: unscheduled tasks go last; ties broken by priority then duration.
# ---------------------------------------------------------------------------

def test_sort_by_time_chronological_order():
    """Timed tasks appear in start_time order regardless of insertion order."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Dinner",    duration=20, priority="high",   start_time=1080))  # 18:00
    pet.add_task(Task("Breakfast", duration=10, priority="high",   start_time=480))   # 08:00
    pet.add_task(Task("Lunch",     duration=15, priority="medium", start_time=720))   # 12:00
    owner.add_pet(pet)

    sched = Scheduler(owner, available_minutes=300)
    result = sched.sort_by_time(sched.get_all_tasks())
    names = [t.task_name for _, t in result]
    assert names == ["Breakfast", "Lunch", "Dinner"]

def test_sort_unscheduled_tasks_go_last():
    """Tasks with no start_time sort after all timed tasks."""
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
    """Among unscheduled tasks, high priority comes before low priority."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("LowTask",  duration=10, priority="low"))
    pet.add_task(Task("HighTask", duration=10, priority="high"))
    owner.add_pet(pet)

    sched = Scheduler(owner)
    result = sched.sort_by_time(sched.get_all_tasks())
    assert result[0][1].task_name == "HighTask"

def test_sort_empty_task_list():
    """Sorting an empty list returns an empty list without error."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    owner.add_pet(pet)
    sched = Scheduler(owner)
    assert sched.sort_by_time([]) == []

def test_sort_two_tasks_same_start_time_priority_wins():
    """Two tasks at the same time: higher priority comes first."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("LowAtNoon",  duration=10, priority="low",  start_time=720))
    pet.add_task(Task("HighAtNoon", duration=10, priority="high", start_time=720))
    owner.add_pet(pet)

    sched = Scheduler(owner)
    result = sched.sort_by_time(sched.get_all_tasks())
    assert result[0][1].task_name == "HighAtNoon"


# ---------------------------------------------------------------------------
# Recurrence Logic
# Happy path: daily/weekly tasks get correct next_due_date after completion.
# Edge cases: as-needed stays None; reset clears next_due_date.
# ---------------------------------------------------------------------------

def test_daily_task_next_due_is_tomorrow():
    """Completing a daily task sets next_due_date to today + 1 day."""
    task = Task("Feeding", duration=10, priority="high", frequency="daily")
    today = date(2026, 3, 27)
    task.mark_complete(as_of=today)
    assert task.next_due_date == (today + timedelta(days=1)).isoformat()

def test_weekly_task_next_due_is_seven_days():
    """Completing a weekly task sets next_due_date to today + 7 days."""
    task = Task("Bath", duration=30, priority="medium", frequency="weekly")
    today = date(2026, 3, 27)
    task.mark_complete(as_of=today)
    assert task.next_due_date == (today + timedelta(days=7)).isoformat()

def test_as_needed_task_next_due_stays_none():
    """Completing an as-needed task does NOT set a next_due_date."""
    task = Task("Vet Visit", duration=60, priority="high", frequency="as-needed")
    task.mark_complete()
    assert task.next_due_date is None

def test_mark_complete_records_last_completed_date():
    """mark_complete stores the date it was called on."""
    task = Task("Walk", duration=30, priority="high")
    today = date(2026, 3, 27)
    task.mark_complete(as_of=today)
    assert task.last_completed_date == today.isoformat()

def test_reset_clears_next_due_date():
    """After reset, next_due_date is None so the task is immediately ready."""
    task = Task("Walk", duration=30, priority="high", frequency="daily")
    task.mark_complete(as_of=date(2026, 3, 27))
    task.reset()
    assert task.next_due_date is None
    assert task.completed is False

def test_daily_task_is_ready_next_day():
    """A daily task completed yesterday is ready today."""
    task = Task("Feeding", duration=10, priority="high", frequency="daily")
    yesterday = date.today() - timedelta(days=1)
    task.mark_complete(as_of=yesterday)
    # next_due_date == today → is_ready should be True
    assert task.is_ready is True

def test_daily_task_not_ready_same_day():
    """A daily task completed today is NOT ready until tomorrow."""
    task = Task("Feeding", duration=10, priority="high", frequency="daily")
    task.mark_complete(as_of=date.today())
    assert task.is_ready is False

def test_generate_schedule_excludes_not_yet_due_task():
    """A task completed today (daily) should not appear in today's schedule."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    task = Task("Feeding", duration=10, priority="high", frequency="daily")
    task.mark_complete(as_of=date.today())
    pet.add_task(task)
    owner.add_pet(pet)

    sched = Scheduler(owner, available_minutes=120)
    schedule = sched.generate_schedule()
    assert all(t.task_name != "Feeding" for _, t in schedule)


# ---------------------------------------------------------------------------
# Conflict Detection
# Happy path: non-overlapping tasks → no conflicts.
# Edge cases: exact same start time; adjacent (touching but not overlapping);
#             completed tasks ignored; unscheduled tasks ignored.
# ---------------------------------------------------------------------------

def test_no_conflict_for_sequential_tasks():
    """Tasks that end before the next one starts have no conflict."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=30, priority="high", start_time=480))  # 08:00–08:30
    pet.add_task(Task("B", duration=30, priority="high", start_time=510))  # 08:30–09:00
    owner.add_pet(pet)

    sched = Scheduler(owner)
    assert sched.get_conflicts() == []

def test_conflict_detected_for_overlapping_tasks():
    """Tasks whose windows overlap are flagged as a conflict."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=60, priority="high", start_time=480))  # 08:00–09:00
    pet.add_task(Task("B", duration=30, priority="high", start_time=510))  # 08:30–09:00 → overlaps A
    owner.add_pet(pet)

    sched = Scheduler(owner)
    assert len(sched.get_conflicts()) == 1

def test_conflict_detected_same_start_time():
    """Two tasks starting at the exact same minute conflict."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=30, priority="high",   start_time=600))
    pet.add_task(Task("B", duration=15, priority="medium", start_time=600))
    owner.add_pet(pet)

    sched = Scheduler(owner)
    assert len(sched.get_conflicts()) == 1

def test_no_conflict_for_adjacent_tasks():
    """A task ending at minute 510 and another starting at 510 do NOT conflict."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=30, priority="high", start_time=480))  # ends 510
    pet.add_task(Task("B", duration=30, priority="high", start_time=510))  # starts 510
    owner.add_pet(pet)

    sched = Scheduler(owner)
    assert sched.get_conflicts() == []

def test_completed_tasks_not_flagged_as_conflicts():
    """Completed tasks are excluded from conflict detection."""
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
    """Tasks without start_time are never involved in conflicts."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=30, priority="high"))
    pet.add_task(Task("B", duration=30, priority="high"))
    owner.add_pet(pet)

    sched = Scheduler(owner)
    assert sched.get_conflicts() == []

def test_no_conflict_when_no_tasks():
    """A pet with zero tasks produces no conflicts."""
    owner = Owner("Sam")
    owner.add_pet(Pet("Cleo", "Sam"))
    sched = Scheduler(owner)
    assert sched.get_conflicts() == []

def test_warn_conflicts_returns_count():
    """warn_conflicts returns the number of conflicts found."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("A", duration=60, priority="high", start_time=480))
    pet.add_task(Task("B", duration=30, priority="high", start_time=500))
    owner.add_pet(pet)

    sched = Scheduler(owner)
    count = sched.warn_conflicts()
    assert count == 1


# ---------------------------------------------------------------------------
# Schedule Generation — edge cases
# ---------------------------------------------------------------------------

def test_generate_schedule_respects_time_budget():
    """Tasks exceeding available_minutes are not included."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Long Task", duration=90, priority="high"))
    owner.add_pet(pet)

    sched = Scheduler(owner, available_minutes=60)
    assert sched.generate_schedule() == []

def test_generate_schedule_zero_budget_returns_empty():
    """available_minutes=0 always yields an empty schedule."""
    owner = Owner("Sam")
    pet = Pet("Cleo", "Sam")
    pet.add_task(Task("Walk", duration=1, priority="high"))
    owner.add_pet(pet)

    sched = Scheduler(owner, available_minutes=0)
    assert sched.generate_schedule() == []

def test_generate_schedule_pet_with_no_tasks():
    """A pet with no tasks produces an empty schedule without error."""
    owner = Owner("Sam")
    owner.add_pet(Pet("Cleo", "Sam"))
    sched = Scheduler(owner, available_minutes=120)
    assert sched.generate_schedule() == []

def test_generate_schedule_skips_completed_tasks(scheduler_with_pets):
    """Completed tasks do not appear in the generated schedule."""
    bella = scheduler_with_pets.owner.get_pet("Bella")
    bella.get_task("Morning Walk").mark_complete()

    names = [t.task_name for _, t in scheduler_with_pets.generate_schedule()]
    assert "Morning Walk" not in names

def test_generate_schedule_happy_path(scheduler_with_pets):
    """All pending tasks that fit within the budget appear in the schedule."""
    schedule = scheduler_with_pets.generate_schedule()
    assert len(schedule) > 0
    total_duration = sum(t.duration for _, t in schedule)
    assert total_duration <= scheduler_with_pets.available_minutes


# ---------------------------------------------------------------------------
# advance_day / rollover
# ---------------------------------------------------------------------------

def test_advance_day_resets_daily_task_next_day():
    """After advancing to the next day, a completed daily task is reset."""
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
    """advance_day does not reset a task whose next_due_date is in the future."""
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