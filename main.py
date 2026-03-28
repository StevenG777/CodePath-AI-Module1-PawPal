from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup: Owner ---
owner = Owner(name="Alex")

# --- Setup: Pets ---
bella = Pet(name="Bella", owner_name="Alex")
mochi = Pet(name="Mochi", owner_name="Alex")

owner.add_pet(bella)
owner.add_pet(mochi)

# --- Tasks for Bella (dog) ---
bella.add_task(Task(task_name="Morning Walk",    duration=30, priority="high",   frequency="daily"))
bella.add_task(Task(task_name="Feeding",         duration=10, priority="high",   frequency="daily"))
bella.add_task(Task(task_name="Grooming",        duration=20, priority="medium", frequency="weekly"))
# bella.add_task(Task(task_name="Nail Clipping",        duration=20, priority="medium", frequency="weekly"))

# --- Tasks for Mochi (cat) ---
mochi.add_task(Task(task_name="Litter Box Clean", duration=10, priority="high",   frequency="daily"))
mochi.add_task(Task(task_name="Playtime",         duration=15, priority="medium", frequency="daily"))
mochi.add_task(Task(task_name="Flea Treatment",   duration=5,  priority="low",    frequency="as-needed"))

# --- Mark some tasks complete to show [✓] vs [○] ---
morning_walk = bella.get_task("Morning Walk")
litter_box = mochi.get_task("Litter Box Clean")

if morning_walk:
    morning_walk.mark_complete()
if litter_box:
    litter_box.mark_complete()

# --- Scheduler: 90 minutes available today ---
scheduler = Scheduler(owner=owner, available_minutes=90)
scheduler.display_schedule()