"""Shared pytest fixtures used across all test modules."""
import pytest
from pawpal_system import Task, Pet, Owner, Scheduler


# ---------------------------------------------------------------------------
# Task fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def walk_task():
    return Task(task_name="Walk", duration=30, priority="high")


@pytest.fixture
def daily_walk():
    return Task(task_name="Walk", duration=30, priority="high", frequency="daily")


@pytest.fixture
def weekly_bath():
    return Task(task_name="Bath", duration=20, priority="medium", frequency="weekly")


# ---------------------------------------------------------------------------
# Pet fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def bella():
    return Pet(name="Bella", owner_name="Alex")


@pytest.fixture
def bella_with_tasks():
    pet = Pet(name="Bella", owner_name="Alex")
    pet.add_task(Task("Morning Walk", duration=30, priority="high", start_time=480))
    pet.add_task(Task("Feeding",      duration=10, priority="high", start_time=540))
    pet.add_task(Task("Grooming",     duration=20, priority="medium"))
    return pet


# ---------------------------------------------------------------------------
# Owner fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def owner_alex():
    return Owner("Alex")


@pytest.fixture
def owner_with_two_pets():
    owner = Owner("Alex")
    bella = Pet(name="Bella", owner_name="Alex")
    max_  = Pet(name="Max",   owner_name="Alex")
    bella.add_task(Task("Morning Walk", duration=30, priority="high",   start_time=480))
    bella.add_task(Task("Feeding",      duration=10, priority="high",   start_time=540))
    max_.add_task(Task("Evening Walk",  duration=30, priority="high",   start_time=1080))
    max_.add_task(Task("Playtime",      duration=15, priority="low"))
    owner.add_pet(bella)
    owner.add_pet(max_)
    return owner


# ---------------------------------------------------------------------------
# Scheduler fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def scheduler_with_pets(owner_with_two_pets):
    return Scheduler(owner_with_two_pets, available_minutes=120)
