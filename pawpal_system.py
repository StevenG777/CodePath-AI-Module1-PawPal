from dataclasses import dataclass, field
from datetime import date, timedelta
from itertools import combinations
from typing import Literal, Optional

Priority = Literal["high", "medium", "low"]
Frequency = Literal["daily", "weekly", "as-needed"]

# Maps priority labels to sort order (lower number = higher priority)
PRIORITY_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


# Interval each frequency adds to today when a task is marked complete.
# as-needed has no automatic interval — it stays complete until manually reset.
_RECURRENCE_DELTA: dict[str, timedelta | None] = {
    "daily":     timedelta(days=1),
    "weekly":    timedelta(days=7),
    "as-needed": None,
}


def _mins_to_hhmm(minutes: int) -> str:
    """Convert an integer number of minutes-from-midnight to 'HH:MM' string."""
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"


# ---------------------------------------------------------------------------
# Task
# Represents a single care activity for a pet.
# Owned by Pet — Pet.tasks is the authoritative list.
# Deletion goes through Pet.remove_task() or Scheduler.remove_task().
# ---------------------------------------------------------------------------

@dataclass
class Task:
    task_name: str
    duration: int               # minutes
    priority: Priority
    frequency: Frequency = "daily"
    completed: bool = False
    start_time: Optional[int] = None           # minutes from midnight (0–1439); None = unscheduled
    last_completed_date: Optional[str] = None  # ISO "YYYY-MM-DD", set by mark_complete()
    next_due_date: Optional[str] = None        # ISO "YYYY-MM-DD"; None = due now

    def __post_init__(self) -> None:
        """Validate fields at construction so bad data never enters the system."""
        if self.duration <= 0:
            raise ValueError(
                f"Task '{self.task_name}': duration must be > 0, got {self.duration}"
            )
        if self.start_time is not None:
            if not (0 <= self.start_time <= 1439):
                raise ValueError(
                    f"Task '{self.task_name}': start_time must be 0–1439 "
                    f"(minutes from midnight), got {self.start_time}"
                )
            if self.start_time + self.duration > 1440:
                raise ValueError(
                    f"Task '{self.task_name}': window runs past midnight — "
                    f"{_mins_to_hhmm(self.start_time)} + {self.duration} min "
                    f"= {_mins_to_hhmm(self.start_time + self.duration)}"
                )

    # --- helpers ---

    @property
    def start_time_str(self) -> Optional[str]:
        """Human-readable HH:MM for start_time, or None if unset."""
        if self.start_time is None:
            return None
        h, m = divmod(self.start_time, 60)
        return f"{h:02d}:{m:02d}"

    @property
    def is_ready(self) -> bool:
        """
        True when this task's recurrence window has elapsed and it should
        appear in a new schedule.

        None means never completed (or manually reset) → always ready.
        AI suggestion adopted: collapse the two-branch if/return into a
        single boolean expression — same logic, one fewer branch.
        """
        return (
            self.next_due_date is None
            or date.today() >= date.fromisoformat(self.next_due_date)
        )

    @property
    def end_time(self) -> Optional[int]:
        """Minutes from midnight when this task finishes, or None if unscheduled."""
        if self.start_time is None:
            return None
        return self.start_time + self.duration

    # --- mutations ---

    def edit_task(
        self,
        task_name: Optional[str] = None,
        duration: Optional[int] = None,
        priority: Optional[Priority] = None,
        frequency: Optional[Frequency] = None,
        start_time: Optional[int] = None,
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
        if start_time is not None:
            self.start_time = start_time

    def mark_complete(self, as_of: Optional[date] = None) -> None:
        """
        Mark this task done and schedule its next occurrence using timedelta.

        - daily     → next_due_date = today + timedelta(days=1)
        - weekly    → next_due_date = today + timedelta(days=7)
        - as-needed → next_due_date stays None (no automatic recurrence)
        """
        today = as_of or date.today()
        self.completed = True
        self.last_completed_date = today.isoformat()
        delta = _RECURRENCE_DELTA[self.frequency]
        self.next_due_date = (today + delta).isoformat() if delta is not None else None

    def reset(self) -> None:
        """Clear completion state so this task appears in the next schedule."""
        self.completed = False
        self.next_due_date = None

    def __str__(self) -> str:
        status = "✓" if self.completed else "○"
        time_part = f" @ {self.start_time_str}" if self.start_time_str else ""
        due_part = f" | next: {self.next_due_date}" if self.next_due_date else ""
        return (
            f"[{status}] {self.task_name}{time_part} "
            f"({self.duration} min | {self.priority} priority | {self.frequency}{due_part})"
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

    def filter_by_status(self, completed: bool) -> list[tuple[Pet, Task]]:
        """Return all tasks that match the given completion status."""
        return [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if task.completed == completed
        ]

    def filter_by_frequency(self, frequency: Frequency) -> list[tuple[Pet, Task]]:
        """Return all tasks that match the given frequency."""
        return [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if task.frequency == frequency
        ]

    def sort_by_time(
        self, tasks: list[tuple[Pet, Task]]
    ) -> list[tuple[Pet, Task]]:
        """
        Sort (Pet, Task) pairs so that time-slotted tasks come first
        (ordered by start_time), followed by unscheduled tasks ordered by
        priority then duration.
        """
        return sorted(
            tasks,
            key=lambda pt: (
                pt[1].start_time if pt[1].start_time is not None else float("inf"),
                PRIORITY_ORDER[pt[1].priority],
                pt[1].duration,
            ),
        )

    def warn_conflicts(self) -> int:
        """
        Print a human-readable WARNING for every detected time conflict.
        Never raises — callers can always continue safely.

        Returns the number of conflicts found (0 = schedule is clean).

        Strategy (lightweight):
          For each conflicting pair, emit one line that names both tasks,
          their owners/pets, their time windows, and how many minutes they
          overlap.  That gives enough detail to fix the schedule without
          flooding the console.
        """
        conflicts = self.get_conflicts()
        if not conflicts:
            print("  ✓ No scheduling conflicts detected.")
            return 0

        print(f"  ⚠ WARNING: {len(conflicts)} conflict(s) found in today's schedule:")
        for (p1, t1), (p2, t2) in conflicts:
            assert t1.start_time is not None and t2.start_time is not None
            # Calculate overlap span (minutes)
            overlap_start = max(t1.start_time, t2.start_time)
            overlap_end   = min(t1.start_time + t1.duration, t2.start_time + t2.duration)
            overlap_mins  = overlap_end - overlap_start
            print(
                f"    • [{p1.name}] {t1.task_name} ({t1.start_time_str}–"
                f"{_mins_to_hhmm(t1.start_time + t1.duration)}, {t1.duration} min)"
                f"  overlaps  "
                f"[{p2.name}] {t2.task_name} ({t2.start_time_str}–"
                f"{_mins_to_hhmm(t2.start_time + t2.duration)}, {t2.duration} min)"
                f"  by {overlap_mins} min"
            )
        return len(conflicts)

    def get_conflicts(self) -> list[tuple[tuple[Pet, Task], tuple[Pet, Task]]]:
        """
        Detect pairs of incomplete tasks whose explicit time windows overlap.
        Only tasks with a start_time set are considered.

        Two tasks conflict when their intervals [start, start+duration) intersect:
            s1 < s2 + d2  AND  s2 < s1 + d1
        """
        # AI suggestion adopted: combinations(timed, 2) replaces the manual
        # range(len(...))/index pattern and directly expresses "all unique pairs"
        # without off-by-one risk.  The assert satisfies the type checker since
        # Optional[int] can't be narrowed across the list comprehension boundary.
        timed = [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if task.start_time is not None and not task.completed
        ]
        conflicts: list[tuple[tuple[Pet, Task], tuple[Pet, Task]]] = []
        for (p1, t1), (p2, t2) in combinations(timed, 2):
            assert t1.start_time is not None and t2.start_time is not None
            s1, e1 = t1.start_time, t1.start_time + t1.duration
            s2, e2 = t2.start_time, t2.start_time + t2.duration
            if s1 < e2 and s2 < e1:
                conflicts.append(((p1, t1), (p2, t2)))
        return conflicts

    # --- Core scheduling logic ---

    def generate_schedule(self) -> list[tuple[Pet, Task]]:
        """
        Build today's plan:
          1. Collect all incomplete tasks that are due today (respects recurrence).
          2. Sort by start_time → priority → duration.
          3. Greedily add tasks until available_minutes is exhausted.

        Recurrence rules (via _is_due):
          - daily     → always included
          - weekly    → skipped if completed within the last 7 days
          - as-needed → always included (lowest priority, never skipped by recurrence)
        """
        # Guard: no time budget means nothing can be scheduled.
        # AI would assume a positive budget — this catches the "weird user
        # behavior" case of available_minutes=0 before looping over all tasks.
        if self.available_minutes <= 0:
            return []

        pending = [
            (pet, task)
            for pet, task in self.get_all_tasks()
            if not task.completed and task.is_ready
        ]
        pending = self.sort_by_time(pending)

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

    def advance_day(self, as_of: Optional[date] = None) -> list[Task]:
        """
        Simulate a day rollover: reset every completed task whose next_due_date
        has arrived (i.e. as_of >= next_due_date).

        Pass `as_of` to simulate a future date in tests or demos; defaults to
        date.today().

        Returns the list of tasks that were reset so callers can report them.
        """
        today = as_of or date.today()
        reset_tasks: list[Task] = []
        for _, task in self.get_all_tasks():
            if (
                task.completed
                and task.next_due_date is not None
                and today >= date.fromisoformat(task.next_due_date)
            ):
                task.reset()
                reset_tasks.append(task)
        return reset_tasks

    def reset_all_tasks(self) -> None:
        """Force-reset every task regardless of recurrence (e.g. full day wipe)."""
        for pet in self.owner.pets:
            pet.reset_day()
