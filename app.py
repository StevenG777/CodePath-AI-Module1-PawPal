import os
import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, PRIORITY_LABEL, task_emoji

# Visual style per priority level used in schedule cards
_PRIORITY_COLOR = {"high": "🔴", "medium": "🟡", "low": "🟢"}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")

_DATA_FILE = "data/data.json"

# ---------------------------------------------------------------------------
# Session state — initialize once per browser session.
# On first load, attempt to restore a previous session from data.json.
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    if os.path.exists(_DATA_FILE):
        try:
            st.session_state.owner = Owner.load_from_json(_DATA_FILE)
        except Exception:
            st.session_state.owner = None   # corrupted file — start fresh
    else:
        st.session_state.owner = None

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None       # created when schedule is generated

# ---------------------------------------------------------------------------
# Sidebar — daily summary (updates on every rerun)
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📊 Daily Summary")
    _sb_owner = st.session_state.owner
    if _sb_owner is None:
        st.info("Set up an owner to see your summary here.")
    else:
        st.markdown(f"**Owner:** {_sb_owner.name}")

        _all_pairs = _sb_owner.get_all_tasks()
        _total     = len(_all_pairs)
        _done      = sum(1 for _, t in _all_pairs if t.completed)
        _pending   = _total - _done

        st.metric("Pets", len(_sb_owner.pets))
        c1, c2 = st.columns(2)
        c1.metric("✅ Done",    _done)
        c2.metric("⭕ Pending", _pending)

        if _total > 0:
            st.progress(_done / _total, text=f"{_done} / {_total} tasks complete")

        if _sb_owner.pets:
            st.markdown("---")
            st.markdown("**By pet:**")
            for _pet in _sb_owner.pets:
                _pt = len(_pet.tasks)
                _pd = sum(1 for t in _pet.tasks if t.completed)
                label = f"🐾 **{_pet.name}**  ({_pd}/{_pt})"
                if _pt > 0:
                    st.markdown(label)
                    st.progress(_pd / _pt)
                else:
                    st.markdown(f"🐾 **{_pet.name}** — no tasks yet")

        _sb_sched = st.session_state.scheduler
        if _sb_sched is not None:
            _plan      = _sb_sched.generate_schedule()
            _used      = sum(t.duration for _, t in _plan)
            _budget    = _sb_sched.available_minutes
            _high_n    = sum(1 for _, t in _plan if t.priority == "high")
            st.markdown("---")
            st.markdown("**Today's schedule:**")
            st.metric("Budget", f"{_budget} min")
            st.metric("Used",   f"{_used} min")
            if _high_n:
                st.success(f"🔴 {_high_n} high-priority task(s) scheduled")
            conflicts = _sb_sched.get_conflicts()
            if conflicts:
                st.warning(f"⚠️ {len(conflicts)} time conflict(s)")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🐾 PawPal+")
st.caption("A daily pet care planner — add your pets, assign tasks, and generate a schedule.")

if st.session_state.owner is not None and os.path.exists(_DATA_FILE):
    st.info(
        f"Session restored from **{_DATA_FILE}** — "
        f"welcome back, **{st.session_state.owner.name}**! "
        f"({len(st.session_state.owner.pets)} pet(s) loaded)"
    )

st.divider()

# ---------------------------------------------------------------------------
# Section 1: Owner setup
# ---------------------------------------------------------------------------
st.subheader("1. Owner Info")

with st.form("owner_form"):
    owner_name_input = st.text_input("Your name", placeholder="e.g. Alex")
    submitted = st.form_submit_button("Save Owner")
    if submitted:
        if owner_name_input.strip():
            # If an owner already exists just update the name, keep their pets
            if st.session_state.owner is None:
                st.session_state.owner = Owner(owner_name_input.strip())
            else:
                st.session_state.owner.edit_info(owner_name_input.strip())
            st.session_state.owner.save_to_json(_DATA_FILE)
            st.success(f"Owner set to **{st.session_state.owner.name}**")
        else:
            st.error("Please enter a name.")

if st.session_state.owner:
    st.write(f"Current owner: **{st.session_state.owner.name}**")

st.divider()

# ---------------------------------------------------------------------------
# Section 2: Add a Pet
# How it works:
#   User fills the form → Owner.add_pet(Pet(...)) stores the Pet object on
#   the Owner → next rerun reads owner.pets to display the updated list.
# ---------------------------------------------------------------------------
st.subheader("2. Add a Pet")

if st.session_state.owner is None:
    st.info("Save an owner above before adding pets.")
else:
    with st.form("pet_form"):
        pet_name_input = st.text_input("Pet name", placeholder="e.g. Bella")
        add_pet_btn = st.form_submit_button("Add Pet")
        if add_pet_btn:
            if pet_name_input.strip():
                owner = st.session_state.owner
                # Avoid duplicate pet names
                if owner.get_pet(pet_name_input.strip()) is not None:
                    st.warning(f"A pet named **{pet_name_input.strip()}** already exists.")
                else:
                    new_pet = Pet(
                        name=pet_name_input.strip(),
                        owner_name=owner.name
                    )
                    owner.add_pet(new_pet)      # ← Owner.add_pet() wires Pet into the system
                    owner.save_to_json(_DATA_FILE)
                    st.success(f"Added **{new_pet.name}**!")
            else:
                st.error("Please enter a pet name.")

    # Show current pets with per-pet completion progress
    owner = st.session_state.owner
    if owner.pets:
        st.markdown(f"**{owner.name}'s pets:**")
        cols = st.columns(max(len(owner.pets), 1))
        for col, pet in zip(cols, owner.pets):
            total = len(pet.tasks)
            done  = sum(1 for t in pet.tasks if t.completed)
            with col:
                st.markdown(f"🐾 **{pet.name}**")
                if total > 0:
                    st.progress(done / total, text=f"{done}/{total} tasks done")
                else:
                    st.caption("No tasks yet")
    else:
        st.info("No pets yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Section 3: Add a Task to a Pet
# How it works:
#   User picks a pet from the dropdown → fills task details → submits →
#   Pet.add_task(Task(...)) attaches the Task to that Pet object in session
#   state → the task list below re-renders on the next rerun.
# ---------------------------------------------------------------------------
st.subheader("3. Add a Task")

owner = st.session_state.owner
if owner is None or not owner.pets:
    st.info("Add an owner and at least one pet before adding tasks.")
else:
    pet_names = [pet.name for pet in owner.pets]

    with st.form("task_form"):
        selected_pet_name = st.selectbox("Assign task to", pet_names)
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            task_name_input = st.text_input("Task name", placeholder="e.g. Morning walk")
        with col2:
            duration_input = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority_input = st.selectbox("Priority", ["high", "medium", "low"])
        with col4:
            frequency_input = st.selectbox("Frequency", ["daily", "weekly", "as-needed"])
        with col5:
            time_input = st.time_input(
                "Start time (optional)",
                value=None,
                help="Leave blank for unscheduled; set to pin this task to a specific time.",
            )

        add_task_btn = st.form_submit_button("Add Task")
        if add_task_btn:
            if task_name_input.strip():
                pet = owner.get_pet(selected_pet_name)
                if pet is not None:
                    start_minutes: int | None = None
                    if time_input is not None:
                        start_minutes = time_input.hour * 60 + time_input.minute
                    new_task = Task(
                        task_name=task_name_input.strip(),
                        duration=int(duration_input),
                        priority=priority_input,    # type: ignore[arg-type]
                        frequency=frequency_input,  # type: ignore[arg-type]
                        start_time=start_minutes,
                    )
                    pet.add_task(new_task)
                    owner.save_to_json(_DATA_FILE)
                    st.success(
                        f"Added {task_emoji(new_task.task_name)} **{new_task.task_name}**"
                        f" to {pet.name}."
                    )
            else:
                st.error("Please enter a task name.")

    # --- Filter controls ---
    st.markdown("**Filter tasks**")
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        filter_pet = st.selectbox("By pet", ["All"] + [p.name for p in owner.pets], key="filter_pet")
    with fcol2:
        filter_status = st.selectbox("By status", ["All", "Pending", "Completed"], key="filter_status")
    with fcol3:
        filter_freq = st.selectbox("By frequency", ["All", "daily", "weekly", "as-needed"], key="filter_freq")

    active_scheduler = st.session_state.scheduler
    if active_scheduler is not None:
        sort_mode = st.radio(
            "Sort tasks by",
            ["Priority → Time  (schedule order)", "Time → Priority  (calendar order)"],
            horizontal=True,
            key="sort_mode",
        )
    else:
        sort_mode = None

    for pet in owner.pets:
        if filter_pet != "All" and pet.name != filter_pet:
            continue
        tasks_to_show = pet.tasks
        if filter_status == "Pending":
            tasks_to_show = [t for t in tasks_to_show if not t.completed]
        elif filter_status == "Completed":
            tasks_to_show = [t for t in tasks_to_show if t.completed]
        if filter_freq != "All":
            tasks_to_show = [t for t in tasks_to_show if t.frequency == filter_freq]
        if tasks_to_show:
            if active_scheduler is not None:
                if sort_mode and sort_mode.startswith("Priority"):
                    pairs = active_scheduler.sort_by_priority([(pet, t) for t in tasks_to_show])
                    sort_label = "priority → time → duration"
                else:
                    pairs = active_scheduler.sort_by_time([(pet, t) for t in tasks_to_show])
                    sort_label = "start time → priority → duration"
                tasks_to_show = [t for _, t in pairs]
                st.write(f"**{pet.name}'s tasks** *(sorted: {sort_label})*:")
            else:
                st.write(f"**{pet.name}'s tasks:**")
            rows = [
                {
                    "Task": f"{task_emoji(t.task_name)} {t.task_name}",
                    "Priority": PRIORITY_LABEL[t.priority],
                    "Start": t.start_time_str or "—",
                    "Duration": t.duration,
                    "Frequency": t.frequency,
                    "Status": "✅" if t.completed else "⭕",
                }
                for t in tasks_to_show
            ]
            st.dataframe(
                rows,
                column_config={
                    "Duration": st.column_config.NumberColumn(
                        "Duration (min)", format="%d min"
                    ),
                    "Status": st.column_config.TextColumn("Status", width="small"),
                },
                hide_index=True,
                width=True,
            )

st.divider()

# ---------------------------------------------------------------------------
# Section 4: Generate Schedule
# How it works:
#   Scheduler(owner, available_minutes) is created → generate_schedule()
#   sorts all incomplete tasks by priority and fits them into the time budget
#   → results rendered in the UI.
# ---------------------------------------------------------------------------
st.subheader("4. Generate Today's Schedule")

owner = st.session_state.owner
if owner is None or not owner.pets or not any(p.tasks for p in owner.pets):
    st.info("Add at least one task before generating a schedule.")
else:
    available = st.number_input(
        "How many minutes do you have today?",
        min_value=5, max_value=480, value=90, step=5
    )

    if st.button("Generate Schedule"):
        scheduler = Scheduler(owner=owner, available_minutes=int(available))
        st.session_state.scheduler = scheduler

    if st.session_state.scheduler:
        scheduler = st.session_state.scheduler
        all_tasks = scheduler.get_all_tasks()
        done = [(pet, task) for pet, task in all_tasks if task.completed]
        plan = scheduler.generate_schedule()

        st.markdown(f"### Today's Schedule for {owner.name}")
        st.caption(f"Time budget: {scheduler.available_minutes} min")

        if done:
            st.markdown("**Already completed today:**")
            for pet, task in done:
                st.success(
                    f"✅ **[{pet.name}] {task_emoji(task.task_name)} {task.task_name}**"
                    f" — {task.duration} min | {PRIORITY_LABEL[task.priority]}"
                )

        # Conflict detection — check tasks with explicit start times
        conflicts = scheduler.get_conflicts()
        if conflicts:
            st.error(
                f"⚠️ {len(conflicts)} time conflict(s) detected — "
                "adjust a start time or duration to fix before running your day."
            )
            for (p1, t1), (p2, t2) in conflicts:
                assert t1.start_time is not None and t2.start_time is not None
                overlap_start = max(t1.start_time, t2.start_time)
                overlap_end   = min(t1.start_time + t1.duration, t2.start_time + t2.duration)
                overlap_mins  = overlap_end - overlap_start
                st.warning(
                    f"**[{p1.name}] {t1.task_name}** ({t1.start_time_str}, {t1.duration} min) "
                    f"overlaps **[{p2.name}] {t2.task_name}** ({t2.start_time_str}, {t2.duration} min) "
                    f"— **{overlap_mins} min overlap.** "
                    f"Try shifting *{t2.task_name}* to start after "
                    f"{t1.start_time_str} + {t1.duration} min."
                )

        if plan:
            time_used = sum(t.duration for _, t in plan)
            pct = time_used / scheduler.available_minutes

            col_a, col_b, col_c = st.columns(3)
            col_a.metric("Scheduled tasks", len(plan))
            col_b.metric("Time used (min)", time_used)
            col_c.metric("Time remaining (min)", scheduler.available_minutes - time_used)
            st.progress(min(pct, 1.0), text=f"{time_used} / {scheduler.available_minutes} min used")

            st.markdown("**Up next** *(grouped by priority — highest first):*")

            # Render schedule grouped by priority level so the most important
            # tasks are always visually at the top.
            for priority in ("high", "medium", "low"):
                group = [(pet, task) for pet, task in plan if task.priority == priority]
                if not group:
                    continue
                badge = PRIORITY_LABEL[priority]
                icon  = _PRIORITY_COLOR[priority]
                st.markdown(f"**{badge} priority**")
                for pet, task in group:
                    time_label = f" @ {task.start_time_str}" if task.start_time_str else " (unscheduled)"
                    freq_note  = f" · {task.frequency}" if task.frequency != "daily" else ""
                    card_text  = (
                        f"{icon} **[{pet.name}] {task_emoji(task.task_name)} {task.task_name}**"
                        f"{time_label} — {task.duration} min{freq_note}"
                    )
                    if priority == "high":
                        st.error(card_text)
                    elif priority == "medium":
                        st.warning(card_text)
                    else:
                        st.info(card_text)

            # Tasks that were ready but didn't fit in the time budget
            # (excludes tasks skipped due to recurrence — not the same as "all non-done")
            skipped_pairs = [
                (pet, task) for pet, task in all_tasks
                if not task.completed and task.is_ready
                and (pet, task) not in plan
            ]
            if skipped_pairs:
                cut_priorities = sorted(
                    {task.priority for _, task in skipped_pairs},
                    key=lambda p: ("high", "medium", "low").index(p),
                )
                cut_labels = ", ".join(PRIORITY_LABEL[p] for p in cut_priorities)
                st.warning(
                    f"{len(skipped_pairs)} task(s) didn't fit in your time budget "
                    f"({cut_labels} skipped). "
                    "Consider increasing available minutes or raising the priority "
                    "of the tasks you most need to keep."
                )
        else:
            st.warning("No tasks fit within the available time, or all tasks are already complete.")

        # --- Find Next Available Slot ---
        st.divider()
        with st.expander("🔍 Find a free time slot"):
            st.caption(
                "Scans today's timed tasks and returns the earliest gap that fits "
                "a new task. Works best when some tasks have a pinned start time."
            )
            slot_col1, slot_col2, slot_col3 = st.columns(3)
            with slot_col1:
                slot_duration = st.number_input(
                    "Task duration (min)",
                    min_value=1, max_value=240, value=30,
                    key="slot_duration",
                )
            with slot_col2:
                slot_start = st.time_input(
                    "Search from (default 06:00)",
                    value=None,
                    key="slot_start",
                )
            with slot_col3:
                slot_end = st.time_input(
                    "Search until (default 22:00)",
                    value=None,
                    key="slot_end",
                )
            if st.button("Find slot", key="find_slot_btn"):
                start_after = (
                    slot_start.hour * 60 + slot_start.minute
                    if slot_start is not None else 360
                )
                end_by = (
                    slot_end.hour * 60 + slot_end.minute
                    if slot_end is not None else 1320
                )
                result = scheduler.find_next_available_slot(
                    duration=int(slot_duration),
                    start_after=start_after,
                    end_by=end_by,
                )
                if result is not None:
                    sh, sm = divmod(result, 60)
                    eh, em = divmod(result + int(slot_duration), 60)
                    start_str = f"{sh:02d}:{sm:02d}"
                    end_str   = f"{eh:02d}:{em:02d}"
                    st.success(
                        f"✅ First available {int(slot_duration)}-minute slot: "
                        f"**{start_str} – {end_str}**"
                    )
                else:
                    sa_h, sa_m = divmod(start_after, 60)
                    eb_h, eb_m = divmod(end_by, 60)
                    st.warning(
                        f"No {int(slot_duration)}-minute gap found between "
                        f"{sa_h:02d}:{sa_m:02d} and {eb_h:02d}:{eb_m:02d}. "
                        "Try a shorter duration or a wider search window."
                    )
