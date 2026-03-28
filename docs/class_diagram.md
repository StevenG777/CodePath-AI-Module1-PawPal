# PawPal+ Class Diagram

```mermaid
classDiagram
    class Owner {
        +String name
        +List~Pet~ pets
        +add_pet(pet: Pet) void
        +remove_pet(pet_name: String) bool
        +get_pet(pet_name: String) Pet
        +edit_info(name: String) void
        +get_all_tasks() List
    }

    class Pet {
        +String name
        +String owner_name
        +List~Task~ tasks
        +add_task(task: Task) void
        +remove_task(task_name: String) bool
        +get_task(task_name: String) Task
        +edit_info(name: String, owner_name: String) void
        +reset_day() void
    }

    class Task {
        +String task_name
        +int duration
        +String priority
        +String frequency
        +bool completed
        +int start_time
        +String last_completed_date
        +String next_due_date
        +edit_task(task_name: String, duration: int, priority: String, frequency: String, start_time: int) void
        +mark_complete() void
        +reset() void
    }

    class Scheduler {
        +Owner owner
        +int available_minutes
        +get_all_tasks() List
        +get_tasks_for_pet(pet_name: String) List~Task~
        +get_tasks_by_priority(priority: String) List
        +filter_by_status(completed: bool) List
        +filter_by_frequency(frequency: String) List
        +sort_by_time(tasks: List) List
        +generate_schedule() List
        +display_schedule() void
        +get_conflicts() List
        +warn_conflicts() int
        +remove_task(pet_name: String, task_name: String) bool
        +advance_day() List~Task~
        +reset_all_tasks() void
    }

    Owner "1" *-- "0..*" Pet : owns
    Pet "1" *-- "0..*" Task : has
    Scheduler "1" --> "1" Owner : uses
```

## Design Notes

- **Owner → Pet**: composition, one-to-many (Owner stores `Pet` objects, not name strings)
- **Pet → Task**: composition, one-to-many (Pet directly owns its tasks; Task has no back-reference to Pet)
- **Scheduler → Owner**: association, one-to-one (Scheduler holds a reference to Owner and reads all pets/tasks through it)
- `Task` is a pure value object — it holds no references to any other class
- `Owner.get_all_tasks()` is the key bridge method: it flattens all pets' tasks into `(Pet, Task)` pairs, which flow through most Scheduler methods so the pet context is never lost
- `priority` values: `"high"`, `"medium"`, `"low"`; `frequency` values: `"daily"`, `"weekly"`, `"as-needed"`
- `start_time` on Task is stored as integer minutes from midnight (0–1439); `None` means unscheduled
