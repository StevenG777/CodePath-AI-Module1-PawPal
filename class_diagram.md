# PawPal+ Class Diagram

```mermaid
classDiagram
    class Owner {
        +String name
        +List~String~ pet_names
        +add_info(name: String) void
        +edit_info(name: String) void
        +delete_info() void
        +add_pet(pet_name: String) void
    }

    class Pet {
        +String name
        +String owner_name
        +add_info(name: String, owner_name: String) void
        +edit_info(name: String) void
        +delete_info() void
    }

    class Task {
        +String task_name
        +String pet_name
        +int duration
        +String priority
        +add_task(task_name: String, pet_name: String) void
        +set_duration_priority(duration: int, priority: String) void
        +edit_task(task_name: String) void
        +delete_task() void
        +display_for_day(day: String) List~Task~
    }

    class Scheduler {
        +List~Task~ tasks
        +String pet_name
        +generate_schedule() List~Task~
        +display_schedule() void
    }

    Owner "1" --> "1..*" Pet : owns
    Pet "1" --> "0..*" Task : has
    Scheduler "1" --> "1..*" Task : schedules
    Scheduler "1" --> "1" Pet : plans for
```

## Design Notes

- **Owner → Pet**: one-to-many (an owner can have multiple pets)
- **Pet → Task**: one-to-many (each pet can have multiple care tasks)
- **Scheduler → Pet**: the scheduler is scoped to a single pet's tasks at a time
- `priority` on Task is typed as `String` — common values: `"high"`, `"medium"`, `"low"`
- **Scheduler** holds `List[Task]` directly rather than parallel lists (task_names, durations, priorities), keeping task data in one place and avoiding sync issues during edits
