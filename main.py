from datetime import date, timedelta
from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def print_section(title: str) -> None:
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)

def print_tasks(pairs):
    for pet, task in pairs:
        print(f"  [{pet.name}] {task}")

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(name="Alex")

bella = Pet(name="Bella", owner_name="Alex")
mochi = Pet(name="Mochi", owner_name="Alex")
owner.add_pet(bella)
owner.add_pet(mochi)

bella.add_task(Task(task_name="Morning Walk", duration=30, priority="high",   frequency="daily"))
bella.add_task(Task(task_name="Grooming",     duration=20, priority="medium", frequency="weekly"))
mochi.add_task(Task(task_name="Litter Box",   duration=10, priority="high",   frequency="daily"))
mochi.add_task(Task(task_name="Flea Treatment", duration=5, priority="low",   frequency="as-needed"))

scheduler = Scheduler(owner=owner, available_minutes=120)

# Use a fixed "today" so the demo is deterministic regardless of when it runs
TODAY    = date(2026, 3, 27)
TOMORROW = TODAY + timedelta(days=1)
IN_7     = TODAY + timedelta(days=7)

# ---------------------------------------------------------------------------
# Day 1 — mark all recurring tasks complete
# ---------------------------------------------------------------------------
print_section("DAY 1 — mark tasks complete")

for pet, task in scheduler.get_all_tasks():
    task.mark_complete(as_of=TODAY)
    print(f"  Completed: [{pet.name}] {task.task_name}  →  next due: {task.next_due_date or '(none)'}")

# ---------------------------------------------------------------------------
# Still Day 1 — schedule is empty (everything done, nothing ready yet)
# ---------------------------------------------------------------------------
print_section("DAY 1 — schedule after completing tasks")
schedule = scheduler.generate_schedule()
if not schedule:
    print("  (no pending tasks — all done for today)")
else:
    print_tasks(schedule)

# ---------------------------------------------------------------------------
# Advance to Day 2 — daily tasks become due again
# ---------------------------------------------------------------------------
print_section(f"ADVANCE TO DAY 2 ({TOMORROW})")

reset = scheduler.advance_day(as_of=TOMORROW)
print(f"  Tasks reset by advance_day: {[t.task_name for t in reset]}")
print()
print("  All tasks after rollover:")
print_tasks(scheduler.get_all_tasks())

# ---------------------------------------------------------------------------
# Day 2 schedule — daily tasks reappear; weekly is still snoozed
# ---------------------------------------------------------------------------
print_section("DAY 2 — schedule")
print_tasks(scheduler.generate_schedule())

# ---------------------------------------------------------------------------
# Advance to Day 8 — weekly task becomes due again
# ---------------------------------------------------------------------------
print_section(f"ADVANCE TO DAY 8 ({IN_7})")

reset = scheduler.advance_day(as_of=IN_7)
print(f"  Tasks reset by advance_day: {[t.task_name for t in reset]}")
print()
print("  All tasks after rollover:")
print_tasks(scheduler.get_all_tasks())

# ---------------------------------------------------------------------------
# Day 8 schedule — weekly task is back alongside daily tasks
# ---------------------------------------------------------------------------
print_section("DAY 8 — schedule (weekly task back)")
print_tasks(scheduler.generate_schedule())

# ---------------------------------------------------------------------------
# as-needed task — never auto-recurs; stays complete until manual reset
# ---------------------------------------------------------------------------
print_section("as-needed task lifecycle")
flea = mochi.get_task("Flea Treatment")
assert flea is not None

flea.mark_complete(as_of=TODAY)
print(f"  After mark_complete:  next_due_date = {flea.next_due_date!r}  (None — no auto recurrence)")

reset = scheduler.advance_day(as_of=IN_7)
print(f"  After advance_day+7:  still in reset list? {'Flea Treatment' in [t.task_name for t in reset]}")
print(f"  completed = {flea.completed}  (still True — requires manual reset)")

flea.reset()
print(f"  After flea.reset():   completed = {flea.completed}, next_due_date = {flea.next_due_date!r}")

# ===========================================================================
# ALGORITHMIC REVIEW & EDGE-CASE AUDIT
# Covers the failure modes AI logic commonly misses:
#   missing conditions · empty inputs · unexpected values · weird user behavior
# ===========================================================================

print_section("EDGE CASE 1 — duration = 0  (AI happy-path assumption)")
try:
    Task(task_name="Ghost Task", duration=0, priority="low")
    print("  BUG: zero-duration task was created silently")
except ValueError as e:
    print(f"  ✓ Caught at construction: {e}")

print_section("EDGE CASE 2 — negative duration  (unexpected value)")
try:
    Task(task_name="Time Warp", duration=-5, priority="high")
    print("  BUG: negative-duration task was created silently")
except ValueError as e:
    print(f"  ✓ Caught at construction: {e}")

print_section("EDGE CASE 3 — start_time past midnight  (missing condition)")
# Without the guard, start_time=1430 + 30 min = 1460 → displays '24:20'
try:
    Task(task_name="Night Owl Walk", duration=30, priority="medium", start_time=1430)
    print("  BUG: task window past midnight accepted silently")
except ValueError as e:
    print(f"  ✓ Caught at construction: {e}")

print_section("EDGE CASE 4 — available_minutes = 0  (weird user behavior)")
owner3 = Owner(name="Sam")
pip = Pet(name="Pip", owner_name="Sam")
owner3.add_pet(pip)
pip.add_task(Task(task_name="Feeding", duration=10, priority="high"))
sched3 = Scheduler(owner=owner3, available_minutes=0)
result = sched3.generate_schedule()
print(f"  generate_schedule() returned: {result!r}")
print(f"  ✓ Empty list — early-return guard prevented pointless loop")

print_section("EDGE CASE 5 — no pets / no tasks  (empty inputs)")
empty_owner = Owner(name="Nobody")
sched4 = Scheduler(owner=empty_owner, available_minutes=60)
print(f"  get_all_tasks()    → {sched4.get_all_tasks()!r}")
print(f"  generate_schedule()→ {sched4.generate_schedule()!r}")
print(f"  warn_conflicts()   → ", end="")
sched4.warn_conflicts()

print_section("EDGE CASE 6 — duplicate task names  (overly simple rule)")
rex2 = Pet(name="Rex", owner_name="Sam")
owner3.add_pet(rex2)
rex2.add_task(Task(task_name="Walk", duration=20, priority="high"))
rex2.add_task(Task(task_name="Walk", duration=30, priority="low"))   # same name!
found = rex2.get_task("Walk")
print(f"  Two tasks named 'Walk' added. get_task('Walk') returns the FIRST match:")
print(f"  → duration={found.duration}, priority={found.priority}")
print(f"  ⚠ Note: get_task is name-based — duplicates silently shadow each other.")
print(f"    Callers should check for duplicates before calling add_task.")

# ---------------------------------------------------------------------------
# Conflict detection — clean schedule first, then introduce overlaps
# ---------------------------------------------------------------------------
print_section("CONFLICT DETECTION — clean schedule")

owner2 = Owner(name="Jordan")
rex  = Pet(name="Rex",  owner_name="Jordan")
luna = Pet(name="Luna", owner_name="Jordan")
owner2.add_pet(rex)
owner2.add_pet(luna)

# Tasks intentionally spaced so there is NO overlap
rex.add_task(Task(task_name="Morning Run",  duration=30, priority="high",   frequency="daily", start_time=420))  # 07:00–07:30
rex.add_task(Task(task_name="Feeding",      duration=10, priority="high",   frequency="daily", start_time=480))  # 08:00–08:10
luna.add_task(Task(task_name="Brushing",    duration=15, priority="medium", frequency="daily", start_time=510))  # 08:30–08:45

sched2 = Scheduler(owner=owner2, available_minutes=120)
sched2.warn_conflicts()

# ---------------------------------------------------------------------------
print_section("CONFLICT DETECTION — overlapping tasks")

# Now add two tasks whose windows genuinely overlap:
#   Vet Call  08:05–08:35  overlaps  Feeding  08:00–08:10  (5 min overlap)
#   Play Time 08:20–08:50  overlaps  Vet Call 08:05–08:35  (15 min overlap)
rex.add_task(Task(task_name="Vet Call",   duration=30, priority="high",   frequency="as-needed", start_time=485))  # 08:05–08:35
luna.add_task(Task(task_name="Play Time", duration=30, priority="medium", frequency="daily",     start_time=500))  # 08:20–08:50

print("  Tasks with start times:")
for pet in owner2.pets:
    for t in pet.tasks:
        if t.start_time is not None:
            end = t.start_time + t.duration
            h1, m1 = divmod(t.start_time, 60)
            h2, m2 = divmod(end, 60)
            print(f"    [{pet.name}] {t.task_name:15}  {h1:02d}:{m1:02d} – {h2:02d}:{m2:02d}")
print()
sched2.warn_conflicts()