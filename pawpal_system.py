from dataclasses import dataclass, field
from typing import Literal, Optional

Priority = Literal["high", "medium", "low"]
Frequency = Literal["daily", "weekly", "as-needed"]

# Maps priority labels to sort order (lower number = higher priority)
PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


# ---------------------------------------------------------------------------
# Task
# Represents a single care activity for a pet.
# Owned by Pet — Pet.tasks is the authoritative list.
# Deletion goes through Pet.remove_task() or Scheduler.remove_task().
# ---------------------------------------------------------------------------

@dataclass
class Task:
    task_name: str
    duration: int       # minutes
    priority: Priority
    frequency: Frequency = "daily"
    completed: bool = False

    def edit_task(
        self,
        task_name: Optional[str] = None,
        duration: Optional[int] = None,
        priority: Optional[Priority] = None,
        frequency: Optional[Frequency] = None,
    ) -> None:
        """Update any combination of task fields in place."""
        if task_name is not None:
            self.task_name = task_name
        if duration is not None:
            self.duration = duration
        if priority is not None:
            self.priority = priority
        if frequency is not None:
            self.frequency = frequency

    def mark_complete(self) -> None:
        """Mark this task as done for the day."""
        self.completed = True

    def reset(self) -> None:
        """Reset completion status (e.g. start of a new day)."""
        self.completed = False

    def __str__(self) -> str:
        status = "✓" if self.completed else "○"
        return (
            f"[{status}] {self.task_name} "
            f"({self.duration} min | {self.priority} priority | {self.frequency})"
        )


# ---------------------------------------------------------------------------
# Pet
# Stores pet details and owns the list of Tasks for that pet.
# Fix applied: tasks: list[Task] added (was missing from original skeleton).
# Fix applied: remove_task() lives here so Task doesn't need a back-reference.
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    name: str
    owner_name: str
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a new task to this pet."""
        self.tasks.append(task)

    def remove_task(self, task_name: str) -> bool:
        """Remove a task by name. Returns True if found and removed."""
        for i, task in enumerate(self.tasks):
            if task.task_name == task_name:
                self.tasks.pop(i)
                return True
        return False

    def get_task(self, task_name: str) -> Optional[Task]:
        """Look up a task by name, or return None."""
        for task in self.tasks:
            if task.task_name == task_name:
                return task
        return None

    def edit_info(self, name: Optional[str] = None, owner_name: Optional[str] = None) -> None:
        """Update pet name or owner name in place."""
        if name is not None:
            self.name = name
        if owner_name is not None:
            self.owner_name = owner_name

    def reset_day(self) -> None:
        """Reset all tasks to incomplete (call at the start of each day)."""
        for task in self.tasks:
            task.reset()

    def __str__(self) -> str:
        return f"{self.name} (owner: {self.owner_name}, {len(self.tasks)} task(s))"


# ---------------------------------------------------------------------------
# Owner
# Manages a collection of Pet objects.
# Fix applied: pets: list[Pet] replaces pet_names: list[str].
# Fix applied: get_all_tasks() is the bridge Scheduler calls — it returns
#              (Pet, Task) pairs so the scheduler knows which pet each task
#              belongs to without Task needing its own pet reference.
# ---------------------------------------------------------------------------

class Owner:
    def __init__(self, name: str):
        self.name: str = name
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def remove_pet(self, pet_name: str) -> bool:
        """Remove a pet by name. Returns True if found and removed."""
        for i, pet in enumerate(self.pets):
            if pet.name == pet_name:
                self.pets.pop(i)
                return True
        return False

    def get_pet(self, pet_name: str) -> Optional[Pet]:
        """Look up a pet by name, or return None."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet
        return None

    def edit_info(self, name: str) -> None:
        """Update the owner's name."""
        self.name = name

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """
        Return every task across every pet as (Pet, Task) pairs.
        This is the bridge Scheduler uses to retrieve all task data —
        it keeps Scheduler decoupled from Pet's internal structure.
        """
        return [
            (pet, task)
            for pet in self.pets
            for task in pet.tasks
        ]

    def __str__(self) -> str:
        return f"{self.name} ({len(self.pets)} pet(s))"


# ---------------------------------------------------------------------------
# Scheduler
# The "brain" — retrieves tasks from Owner, sorts by priority, and fits
# them into the owner's available daily time window.
#
# Fix applied: Scheduler(owner) instead of Scheduler(pet) — it now works
#              across ALL of the owner's pets, not just one.
# Fix applied: available_minutes added as a constraint for generate_schedule().
# Fix applied: display_for_day() moved here from Task (Task has no list context).
# Fix applied: remove_task() lives here as the public API for deletion.
# ---------------------------------------------------------------------------

class Scheduler:
    def __init__(self, owner: Owner, available_minutes: int = 120):
        self.owner: Owner = owner
        self.available_minutes: int = available_minutes  # daily time budget

    # --- Retrieval ---

    def get_all_tasks(self) -> list[tuple[Pet, Task]]:
        """Pull all (Pet, Task) pairs from the owner's pets."""
        return self.owner.get_all_tasks()

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks for a specific pet."""
        pet = self.owner.get_pet(pet_name)
        return pet.tasks if pet else []

    def get_tasks_by_priority(self, priority: Priority) -> list[tuple[Pet, Task]]:
        """Filter all tasks to a specific priority level."""
        return [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if task.priority == priority
        ]

    # --- Core scheduling logic ---

    def generate_schedule(self) -> list[tuple[Pet, Task]]:
        """
        Build today's plan:
          1. Collect all incomplete tasks across all pets.
          2. Sort by priority (high → medium → low).
          3. Greedily add tasks until available_minutes is exhausted.
        Returns a list of (Pet, Task) pairs in scheduled order.
        """
        pending = [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if not task.completed
        ]
        pending.sort(key=lambda pt: PRIORITY_ORDER[pt[1].priority])

        schedule: list[tuple[Pet, Task]] = []
        time_remaining = self.available_minutes

        for pet, task in pending:
            if task.duration <= time_remaining:
                schedule.append((pet, task))
                time_remaining -= task.duration

        return schedule

    def display_schedule(self) -> None:
        """Print today's generated schedule to the console."""
        all_tasks = self.get_all_tasks()
        done = [(pet, task) for pet, task in all_tasks if task.completed]
        schedule = self.generate_schedule()

        print(f"\n=== Today's Schedule for {self.owner.name} ===")
        print(f"Time budget: {self.available_minutes} min\n")

        if done:
            print("Already completed:")
            for pet, task in done:
                print(f"  [{pet.name}] {task}")
            print()

        print("Up next:")
        if not schedule:
            print("  No tasks fit within the available time.")
        else:
            time_used = 0
            for pet, task in schedule:
                print(f"  [{pet.name}] {task}")
                time_used += task.duration

            skipped = len(all_tasks) - len(done) - len(schedule)
            print(f"\nTotal: {time_used} / {self.available_minutes} min used")
            if skipped:
                print(f"Skipped: {skipped} task(s) — not enough time remaining")

    # --- Mutation via Scheduler (public API for deletion) ---

    def remove_task(self, pet_name: str, task_name: str) -> bool:
        """
        Delete a task by name from a specific pet.
        Returns True if the task was found and removed.
        """
        pet = self.owner.get_pet(pet_name)
        if pet is None:
            return False
        return pet.remove_task(task_name)

    def reset_all_tasks(self) -> None:
        """Reset completion status on every task (call at day rollover)."""
        for pet in self.owner.pets:
            pet.reset_day()
