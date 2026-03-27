from dataclasses import dataclass, field
from typing import Literal

# Priority values: "high", "medium", "low"
Priority = Literal["high", "medium", "low"]


@dataclass
class Task:
    task_name: str
    pet_name: str
    duration: int  # minutes
    priority: Priority

    def set_duration_priority(self, duration: int, priority: Priority) -> None:
        pass

    def edit_task(self, task_name: str) -> None:
        pass

    def delete_task(self) -> None:
        pass

    def display_for_day(self, day: str) -> list["Task"]:
        pass


@dataclass
class Pet:
    name: str
    owner_name: str

    def edit_info(self, name: str) -> None:
        pass

    def delete_info(self) -> None:
        pass


class Owner:
    def __init__(self, name: str):
        self.name: str = name
        self.pet_names: list[str] = []

    def add_info(self, name: str) -> None:
        pass

    def edit_info(self, name: str) -> None:
        pass

    def delete_info(self) -> None:
        pass

    def add_pet(self, pet_name: str) -> None:
        pass


class Scheduler:
    def __init__(self, pet: Pet):
        self.pet: Pet = pet
        self.tasks: list[Task] = []

    def generate_schedule(self) -> list[Task]:
        pass

    def display_schedule(self) -> None:
        pass
