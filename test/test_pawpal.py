import pytest
from pawpal_system import Task, Pet


# --- Fixtures ---

@pytest.fixture
def walk_task():
    return Task(task_name="Walk", duration=30, priority="high")

@pytest.fixture
def bella():
    return Pet(name="Bella", owner_name="Alex")


# --- Task Completion ---

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


# --- Pet Task Addition ---

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
