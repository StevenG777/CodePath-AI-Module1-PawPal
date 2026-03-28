# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

The scheduler goes beyond a simple priority list with four new capabilities:

**Sorting by time**
Tasks with an explicit `start_time` (stored as minutes from midnight) are sorted chronologically before unscheduled tasks. Unscheduled tasks fall back to priority → duration order. The sort key is a 3-tuple lambda so all criteria are resolved in one pass.

**Filtering**
`Scheduler` exposes three filter methods that return `(Pet, Task)` pairs without mutating any state:
- `filter_by_status(completed)` — pending vs. done tasks
- `filter_by_frequency(frequency)` — `daily` / `weekly` / `as-needed`
- `get_tasks_for_pet(name)` — all tasks for one pet

The Streamlit UI uses these to drive the filter controls above the task table.

**Recurring task automation**
`Task.mark_complete()` uses `timedelta` to set a `next_due_date`:
- `daily` → today + 1 day
- `weekly` → today + 7 days
- `as-needed` → no automatic recurrence (stays complete until manually reset)

`Scheduler.advance_day(as_of)` rolls the calendar forward: it resets every completed task whose `next_due_date` has arrived and returns the list of reset tasks. Passing `as_of` lets tests and demos simulate any date without patching the system clock.

**Conflict detection**
`Scheduler.get_conflicts()` uses `itertools.combinations` to check every unique pair of timed tasks for window overlap (`s1 < e2 and s2 < e1`). `warn_conflicts()` turns those pairs into human-readable warnings that include the exact overlap in minutes — it never raises, so callers can always continue safely.

**Input validation**
`Task.__post_init__` rejects bad data at construction time:
- `duration ≤ 0` → `ValueError`
- `start_time` outside 0–1439 → `ValueError`
- window runs past midnight (`start_time + duration > 1440`) → `ValueError`

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
