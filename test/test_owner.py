"""Tests for the Owner class: pet management, info editing, and JSON persistence."""
import json
import pytest
from pawpal_system import Task, Pet, Owner


# ---------------------------------------------------------------------------
# Pet addition & retrieval
# ---------------------------------------------------------------------------

def test_owner_starts_with_no_pets(owner_alex):
    assert len(owner_alex.pets) == 0


def test_add_pet_increases_count(owner_alex, bella):
    owner_alex.add_pet(bella)
    assert len(owner_alex.pets) == 1


def test_get_pet_returns_correct_pet(owner_alex, bella):
    owner_alex.add_pet(bella)
    assert owner_alex.get_pet("Bella") is bella


def test_get_pet_returns_none_for_missing(owner_alex):
    assert owner_alex.get_pet("Ghost") is None


def test_add_multiple_pets(owner_alex):
    owner_alex.add_pet(Pet("Bella", "Alex"))
    owner_alex.add_pet(Pet("Max",   "Alex"))
    owner_alex.add_pet(Pet("Cleo",  "Alex"))
    assert len(owner_alex.pets) == 3


# ---------------------------------------------------------------------------
# Pet removal
# ---------------------------------------------------------------------------

def test_remove_pet_returns_true_when_found(owner_alex, bella):
    owner_alex.add_pet(bella)
    assert owner_alex.remove_pet("Bella") is True


def test_remove_pet_decreases_count(owner_alex, bella):
    owner_alex.add_pet(bella)
    owner_alex.remove_pet("Bella")
    assert len(owner_alex.pets) == 0


def test_remove_pet_returns_false_when_not_found(owner_alex):
    assert owner_alex.remove_pet("Ghost") is False


def test_remove_pet_only_removes_named_pet(owner_alex):
    owner_alex.add_pet(Pet("Bella", "Alex"))
    owner_alex.add_pet(Pet("Max",   "Alex"))
    owner_alex.remove_pet("Bella")
    assert owner_alex.get_pet("Bella") is None
    assert owner_alex.get_pet("Max") is not None


# ---------------------------------------------------------------------------
# edit_info
# ---------------------------------------------------------------------------

def test_edit_info_changes_owner_name(owner_alex):
    owner_alex.edit_info("Jordan")
    assert owner_alex.name == "Jordan"


# ---------------------------------------------------------------------------
# get_all_tasks
# ---------------------------------------------------------------------------

def test_get_all_tasks_returns_all_pet_task_pairs(owner_with_two_pets):
    pairs = owner_with_two_pets.get_all_tasks()
    assert len(pairs) == 4  # 2 Bella + 2 Max


def test_get_all_tasks_returns_correct_types(owner_with_two_pets):
    for pet, task in owner_with_two_pets.get_all_tasks():
        assert isinstance(pet, Pet)
        assert isinstance(task, Task)


def test_get_all_tasks_empty_owner(owner_alex):
    assert owner_alex.get_all_tasks() == []


def test_get_all_tasks_owner_with_pet_but_no_tasks(owner_alex, bella):
    owner_alex.add_pet(bella)
    assert owner_alex.get_all_tasks() == []


# ---------------------------------------------------------------------------
# Persistence: to_dict / save_to_json / load_from_json
# ---------------------------------------------------------------------------

def test_to_dict_contains_owner_name(owner_with_two_pets):
    d = owner_with_two_pets.to_dict()
    assert d["name"] == "Alex"


def test_to_dict_contains_pets(owner_with_two_pets):
    d = owner_with_two_pets.to_dict()
    pet_names = [p["name"] for p in d["pets"]]
    assert "Bella" in pet_names
    assert "Max" in pet_names


def test_to_dict_contains_tasks(owner_with_two_pets):
    d = owner_with_two_pets.to_dict()
    bella_data = next(p for p in d["pets"] if p["name"] == "Bella")
    task_names = [t["task_name"] for t in bella_data["tasks"]]
    assert "Morning Walk" in task_names
    assert "Feeding" in task_names


def test_save_and_load_roundtrip(owner_with_two_pets, tmp_path):
    path = str(tmp_path / "data.json")
    owner_with_two_pets.save_to_json(path)
    loaded = Owner.load_from_json(path)

    assert loaded.name == owner_with_two_pets.name
    assert len(loaded.pets) == len(owner_with_two_pets.pets)


def test_save_and_load_preserves_task_fields(owner_with_two_pets, tmp_path):
    path = str(tmp_path / "data.json")
    owner_with_two_pets.save_to_json(path)
    loaded = Owner.load_from_json(path)

    bella = loaded.get_pet("Bella")
    assert bella is not None
    walk = bella.get_task("Morning Walk")
    assert walk is not None
    assert walk.duration == 30
    assert walk.priority == "high"
    assert walk.start_time == 480


def test_load_from_json_raises_on_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        Owner.load_from_json(str(tmp_path / "missing.json"))


def test_save_to_json_produces_valid_json(owner_with_two_pets, tmp_path):
    path = str(tmp_path / "data.json")
    owner_with_two_pets.save_to_json(path)
    with open(path) as fh:
        data = json.load(fh)
    assert "name" in data
    assert "pets" in data


def test_save_and_load_preserves_completed_state(owner_alex, tmp_path):
    pet = Pet("Cleo", "Alex")
    task = Task("Walk", duration=30, priority="high")
    task.mark_complete()
    pet.add_task(task)
    owner_alex.add_pet(pet)

    path = str(tmp_path / "data.json")
    owner_alex.save_to_json(path)
    loaded = Owner.load_from_json(path)

    loaded_task = loaded.get_pet("Cleo").get_task("Walk") # type: ignore
    assert loaded_task.completed is True # type: ignore
