"""Tests for the Pet class: task management, info editing, and day reset."""
import pytest
from pawpal_system import Task, Pet


# ---------------------------------------------------------------------------
# Task addition & retrieval
# ---------------------------------------------------------------------------

def test_pet_starts_with_no_tasks(bella):
    assert len(bella.tasks) == 0


def test_add_task_increases_count(bella, walk_task):
    bella.add_task(walk_task)
    assert len(bella.tasks) == 1


def test_add_multiple_tasks(bella):
    bella.add_task(Task("Feeding",  duration=10, priority="high"))
    bella.add_task(Task("Walk",     duration=30, priority="high"))
    bella.add_task(Task("Grooming", duration=20, priority="medium"))
    assert len(bella.tasks) == 3


def test_added_task_is_retrievable(bella, walk_task):
    bella.add_task(walk_task)
    assert bella.get_task("Walk") is walk_task


def test_get_task_returns_none_for_missing(bella):
    assert bella.get_task("Nonexistent") is None


# ---------------------------------------------------------------------------
# Task removal
# ---------------------------------------------------------------------------

def test_remove_task_returns_true_when_found(bella, walk_task):
    bella.add_task(walk_task)
    result = bella.remove_task("Walk")
    assert result is True


def test_remove_task_decreases_count(bella, walk_task):
    bella.add_task(walk_task)
    bella.remove_task("Walk")
    assert len(bella.tasks) == 0


def test_remove_task_returns_false_when_not_found(bella):
    assert bella.remove_task("Nonexistent") is False


def test_remove_task_only_removes_named_task(bella):
    bella.add_task(Task("Walk",    duration=30, priority="high"))
    bella.add_task(Task("Feeding", duration=10, priority="high"))
    bella.remove_task("Walk")
    assert bella.get_task("Walk") is None
    assert bella.get_task("Feeding") is not None


def test_remove_task_from_middle_of_list(bella):
    bella.add_task(Task("A", duration=10, priority="high"))
    bella.add_task(Task("B", duration=10, priority="high"))
    bella.add_task(Task("C", duration=10, priority="high"))
    bella.remove_task("B")
    names = [t.task_name for t in bella.tasks]
    assert names == ["A", "C"]


# ---------------------------------------------------------------------------
# edit_info
# ---------------------------------------------------------------------------

def test_edit_info_changes_name(bella):
    bella.edit_info(name="Luna")
    assert bella.name == "Luna"


def test_edit_info_changes_owner_name(bella):
    bella.edit_info(owner_name="Jordan")
    assert bella.owner_name == "Jordan"


def test_edit_info_none_leaves_field_unchanged(bella):
    original_name = bella.name
    bella.edit_info(owner_name="Jordan")
    assert bella.name == original_name


def test_edit_info_both_fields(bella):
    bella.edit_info(name="Luna", owner_name="Jordan")
    assert bella.name == "Luna"
    assert bella.owner_name == "Jordan"


# ---------------------------------------------------------------------------
# reset_day
# ---------------------------------------------------------------------------

def test_reset_day_clears_all_completed_tasks(bella_with_tasks):
    for task in bella_with_tasks.tasks:
        task.mark_complete()
    bella_with_tasks.reset_day()
    assert all(not t.completed for t in bella_with_tasks.tasks)


def test_reset_day_clears_next_due_dates(bella_with_tasks):
    for task in bella_with_tasks.tasks:
        task.mark_complete()
    bella_with_tasks.reset_day()
    assert all(t.next_due_date is None for t in bella_with_tasks.tasks)


def test_reset_day_on_pet_with_no_tasks(bella):
    """reset_day on an empty task list should not raise."""
    bella.reset_day()
    assert bella.tasks == []
