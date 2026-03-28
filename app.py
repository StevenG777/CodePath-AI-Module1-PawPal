import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session state — initialize once per browser session
# ---------------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None           # set after owner form is submitted

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None       # created when schedule is generated

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.title("🐾 PawPal+")
st.caption("A daily pet care planner — add your pets, assign tasks, and generate a schedule.")
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
                    st.success(f"Added **{new_pet.name}**!")
            else:
                st.error("Please enter a pet name.")

    # Show current pets
    owner = st.session_state.owner
    if owner.pets:
        st.write(f"**{owner.name}'s pets:**")
        for pet in owner.pets:
            st.write(f"- {pet.name} ({len(pet.tasks)} task(s))")
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
                    st.success(f"Added **{new_task.task_name}** to {pet.name}.")
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

    # Show tasks grouped by pet, respecting filters
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
            st.write(f"**{pet.name}'s tasks:**")
            rows = [
                {
                    "Task": t.task_name,
                    "Start": t.start_time_str or "—",
                    "Duration (min)": t.duration,
                    "Priority": t.priority,
                    "Frequency": t.frequency,
                    "Done": "✓" if t.completed else "○",
                }
                for t in tasks_to_show
            ]
            st.table(rows)

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
            st.markdown("**Already completed:**")
            for pet, task in done:
                st.write(f"  ✓ [{pet.name}] {task.task_name} ({task.duration} min)")

        # Conflict detection — check tasks with explicit start times
        conflicts = scheduler.get_conflicts()
        if conflicts:
            st.error(f"⚠️ {len(conflicts)} time conflict(s) detected:")
            for (p1, t1), (p2, t2) in conflicts:
                st.write(
                    f"  • **[{p1.name}] {t1.task_name}** ({t1.start_time_str}, {t1.duration} min) "
                    f"overlaps **[{p2.name}] {t2.task_name}** ({t2.start_time_str}, {t2.duration} min)"
                )

        if plan:
            st.markdown("**Up next:**")
            time_used = sum(t.duration for _, t in plan)
            for pet, task in plan:
                time_label = f" @ {task.start_time_str}" if task.start_time_str else ""
                freq_note = " *(weekly)*" if task.frequency == "weekly" else (
                    " *(as-needed)*" if task.frequency == "as-needed" else ""
                )
                st.write(
                    f"  ○ [{pet.name}] {task.task_name}{time_label}"
                    f" — {task.duration} min | {task.priority} priority{freq_note}"
                )
            st.info(f"Total scheduled: {time_used} / {scheduler.available_minutes} min")

            # Count tasks skipped due to time (not those skipped by recurrence)
            skipped = len(all_tasks) - len(done) - len(plan)
            if skipped:
                st.warning(f"{skipped} task(s) skipped — not enough time remaining.")
        else:
            st.warning("No tasks fit within the available time, or all tasks are already complete.")
