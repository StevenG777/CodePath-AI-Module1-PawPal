"""Tests for the Task class: lifecycle, validation, properties, and recurrence."""
import pytest
from datetime import date, timedelta
from pawpal_system import Task, task_emoji


# ---------------------------------------------------------------------------
# Construction validation
# ---------------------------------------------------------------------------

def test_task_zero_duration_raises():
    with pytest.raises(ValueError, match="duration must be > 0"):
        Task(task_name="Bad", duration=0, priority="high")


def test_task_negative_duration_raises():
    with pytest.raises(ValueError, match="duration must be > 0"):
        Task(task_name="Bad", duration=-5, priority="high")


def test_task_start_time_too_large_raises():
    with pytest.raises(ValueError, match="start_time must be 0–1439"):
        Task(task_name="Bad", duration=10, priority="high", start_time=1440)


def test_task_start_time_negative_raises():
    with pytest.raises(ValueError, match="start_time must be 0–1439"):
        Task(task_name="Bad", duration=10, priority="high", start_time=-1)


def test_task_window_past_midnight_raises():
    """A task starting at 23:50 (1430) with 30-min duration overflows past midnight."""
    with pytest.raises(ValueError, match="runs past midnight"):
        Task(task_name="Late", duration=30, priority="high", start_time=1430)


def test_task_valid_boundary_start_time():
    """start_time=0 (midnight) is valid as long as it fits within the day."""
    task = Task(task_name="Midnight", duration=10, priority="low", start_time=0)
    assert task.start_time == 0


def test_task_valid_late_start_time():
    """start_time=1439 (23:59) with 1-min duration is exactly at the boundary."""
    task = Task(task_name="Last", duration=1, priority="low", start_time=1439)
    assert task.start_time == 1439


# ---------------------------------------------------------------------------
# Completion lifecycle
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


def test_mark_complete_records_last_completed_date():
    task = Task("Walk", duration=30, priority="high")
    today = date(2026, 3, 27)
    task.mark_complete(as_of=today)
    assert task.last_completed_date == today.isoformat()


def test_reset_clears_next_due_date():
    task = Task("Walk", duration=30, priority="high", frequency="daily")
    task.mark_complete(as_of=date(2026, 3, 27))
    task.reset()
    assert task.next_due_date is None
    assert task.completed is False


# ---------------------------------------------------------------------------
# Recurrence
# ---------------------------------------------------------------------------

def test_daily_task_next_due_is_tomorrow():
    task = Task("Feeding", duration=10, priority="high", frequency="daily")
    today = date(2026, 3, 27)
    task.mark_complete(as_of=today)
    assert task.next_due_date == (today + timedelta(days=1)).isoformat()


def test_weekly_task_next_due_is_seven_days():
    task = Task("Bath", duration=30, priority="medium", frequency="weekly")
    today = date(2026, 3, 27)
    task.mark_complete(as_of=today)
    assert task.next_due_date == (today + timedelta(days=7)).isoformat()


def test_as_needed_task_next_due_stays_none():
    task = Task("Vet Visit", duration=60, priority="high", frequency="as-needed")
    task.mark_complete()
    assert task.next_due_date is None


def test_daily_task_is_ready_next_day():
    task = Task("Feeding", duration=10, priority="high", frequency="daily")
    task.mark_complete(as_of=date.today() - timedelta(days=1))
    assert task.is_ready is True


def test_daily_task_not_ready_same_day():
    task = Task("Feeding", duration=10, priority="high", frequency="daily")
    task.mark_complete(as_of=date.today())
    assert task.is_ready is False


def test_uncompleted_task_is_always_ready():
    task = Task("Walk", duration=30, priority="high")
    assert task.is_ready is True


def test_weekly_task_not_ready_after_3_days():
    task = Task("Bath", duration=20, priority="medium", frequency="weekly")
    task.mark_complete(as_of=date.today() - timedelta(days=3))
    assert task.is_ready is False


def test_weekly_task_ready_after_7_days():
    task = Task("Bath", duration=20, priority="medium", frequency="weekly")
    task.mark_complete(as_of=date.today() - timedelta(days=7))
    assert task.is_ready is True


# ---------------------------------------------------------------------------
# Properties: start_time_str, end_time
# ---------------------------------------------------------------------------

def test_start_time_str_none_when_unscheduled(walk_task):
    assert walk_task.start_time_str is None


def test_start_time_str_formats_correctly():
    task = Task("Feeding", duration=10, priority="high", start_time=480)  # 08:00
    assert task.start_time_str == "08:00"


def test_start_time_str_midnight():
    task = Task("Early", duration=10, priority="low", start_time=0)
    assert task.start_time_str == "00:00"


def test_start_time_str_late_evening():
    task = Task("Late", duration=1, priority="low", start_time=1380)  # 23:00
    assert task.start_time_str == "23:00"


def test_end_time_none_when_unscheduled(walk_task):
    assert walk_task.end_time is None


def test_end_time_calculates_correctly():
    task = Task("Walk", duration=30, priority="high", start_time=480)
    assert task.end_time == 510


def test_end_time_equals_start_plus_duration():
    task = Task("Bath", duration=45, priority="medium", start_time=600)
    assert task.end_time == task.start_time + task.duration


# ---------------------------------------------------------------------------
# edit_task
# ---------------------------------------------------------------------------

def test_edit_task_name(walk_task):
    walk_task.edit_task(task_name="Evening Walk")
    assert walk_task.task_name == "Evening Walk"


def test_edit_task_duration(walk_task):
    walk_task.edit_task(duration=45)
    assert walk_task.duration == 45


def test_edit_task_priority(walk_task):
    walk_task.edit_task(priority="low")
    assert walk_task.priority == "low"


def test_edit_task_frequency(walk_task):
    walk_task.edit_task(frequency="weekly")
    assert walk_task.frequency == "weekly"


def test_edit_task_start_time(walk_task):
    walk_task.edit_task(start_time=720)
    assert walk_task.start_time == 720


def test_edit_task_multiple_fields(walk_task):
    walk_task.edit_task(task_name="Run", duration=20, priority="medium")
    assert walk_task.task_name == "Run"
    assert walk_task.duration == 20
    assert walk_task.priority == "medium"


def test_edit_task_none_args_leave_fields_unchanged(walk_task):
    """Passing None for a field leaves that field unchanged."""
    original_name = walk_task.task_name
    walk_task.edit_task(task_name=None, duration=60)
    assert walk_task.task_name == original_name
    assert walk_task.duration == 60


# ---------------------------------------------------------------------------
# task_emoji helper
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name,expected", [
    ("Morning Walk",    "🚶"),
    ("Feeding",         "🍽️"),
    ("Grooming",        "🪮"),
    ("Bath Time",       "🛁"),
    ("Vet Checkup",     "🏥"),
    ("Give Medicine",   "💊"),
    ("Nail Trim",       "✂️"),
    ("Dental Cleaning", "🦷"),
    ("Water Bowl",      "💧"),
    ("Playtime",        "🎾"),
    ("Training",        "🎓"),
    ("Litter Box",      "🗑️"),
    ("Ear Inspection",  "👂"),
    ("Unknown Task",    "🐾"),
])
def test_task_emoji_matches_keyword(name, expected):
    assert task_emoji(name) == expected


def test_task_emoji_case_insensitive():
    assert task_emoji("WALK") == "🚶"
    assert task_emoji("FEEDING") == "🍽️"
