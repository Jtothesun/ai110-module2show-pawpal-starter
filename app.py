from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Task, Priority, Frequency, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    "A smart pet care planner. Add your pets, schedule care tasks, and let "
    "PawPal+ organize, sort, and prioritize them. Completing a **daily** or "
    "**weekly** task automatically re-creates it for the next occurrence."
)

st.divider()

# --- Persistent state -------------------------------------------------------
# Streamlit reruns this script top-to-bottom on every interaction, so we keep
# the Owner in session_state and build it only once. Every rerun then reuses
# the SAME object, preserving the pets and tasks we've added.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jason", "Morales")

owner = st.session_state.owner
scheduler = Scheduler(owner)

# --- Add a Pet --------------------------------------------------------------
st.subheader("Add a Pet")
with st.form("add_pet_form"):
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])
    breed = st.text_input("Breed", value="unknown")
    if st.form_submit_button("Add pet"):
        if owner.get_pet(pet_name):
            st.warning(f"{pet_name} is already registered.")
        else:
            owner.add_pet(Pet(pet_name, species, breed))
            st.success(f"Added {pet_name} the {species}.")

# --- Schedule a Task --------------------------------------------------------
st.subheader("Schedule a Task")
if not owner.pets:
    st.info("Add a pet first — tasks are assigned to a specific pet.")
else:
    with st.form("add_task_form"):
        # IMPORTANT: select by pet NAME (a stable primitive), not by passing the
        # Pet objects as options. Streamlit round-trips widget values through its
        # own state store and may hand back a *copy* of an option object, so
        # mutating that copy (pet.add_task(...)) would not touch the real pet in
        # owner.pets. We look the real object up via owner.get_pet(name) below.
        selected_pet_name = st.selectbox("Pet", [p.name for p in owner.pets])
        description = st.text_input("Task", value="Morning walk")
        scheduled_time = st.time_input("Time of day", value=time(8, 0))
        col1, col2 = st.columns(2)
        with col1:
            frequency = st.selectbox(
                "Frequency",
                list(Frequency),
                index=list(Frequency).index(Frequency.DAILY),
                format_func=lambda f: f.value.title(),
            )
        with col2:
            priority = st.selectbox(
                "Priority", list(Priority), index=1, format_func=lambda p: p.name.title()
            )
        if st.form_submit_button("Schedule task"):
            pet = owner.get_pet(selected_pet_name)  # the REAL, persisted object
            pet.add_task(Task(description, scheduled_time, frequency, priority))
            st.success(
                f"Scheduled '{description}' for {pet.name} at {scheduled_time:%H:%M}."
            )

# --- Current tasks (with filters + sort) ------------------------------------
st.subheader("Current Tasks")
if not owner.all_tasks():
    st.caption("No tasks yet — schedule one above.")
else:
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        pet_filter = st.selectbox("Pet", ["All"] + [p.name for p in owner.pets])
    with fcol2:
        status_filter = st.selectbox("Status", ["All", "Pending", "Completed"])
    with fcol3:
        sort_by_time = st.checkbox("Sort by time of day", value=True)

    # Map the UI choices onto filter_tasks()'s keyword args. "All" -> None
    # (skip that filter); Pending/Completed -> completed=False/True.
    completed = {"All": None, "Pending": False, "Completed": True}[status_filter]
    pet_name = None if pet_filter == "All" else pet_filter

    tasks = scheduler.filter_tasks(completed=completed, pet_name=pet_name)
    if sort_by_time:
        tasks = sorted(tasks, key=lambda t: t.scheduled_time.strftime("%H:%M"))

    if not tasks:
        st.caption("No tasks match these filters.")
    else:
        st.table(
            [
                {
                    "Pet": t.pet.name if t.pet else "—",
                    "Task": t.description,
                    "Due": t.due_date.strftime("%Y-%m-%d"),
                    "Time": t.scheduled_time.strftime("%H:%M"),
                    "Frequency": t.frequency.value,
                    "Priority": t.priority.name,
                    "Done": "✓" if t.completed else "",
                }
                for t in tasks
            ]
        )

# --- Mark a Task Complete ---------------------------------------------------
st.subheader("Mark a Task Complete")
pending = [t for t in owner.all_tasks() if t.is_pending()]
if not pending:
    st.caption("Nothing pending — every task is done. 🎉")
else:
    # Same lesson as the pet selector: choose by task id (a stable primitive),
    # then look the real Task up again before mutating it. A label dict keeps the
    # dropdown readable while the selectbox value stays a plain int.
    labels = {
        t.id: f"{t.pet.name}: {t.description} ({t.scheduled_time:%H:%M}, due {t.due_date})"
        for t in pending
    }
    with st.form("complete_task_form"):
        task_id = st.selectbox(
            "Pending task", list(labels), format_func=lambda i: labels[i]
        )
        if st.form_submit_button("Mark complete"):
            task = next(t for t in owner.all_tasks() if t.id == task_id)
            follow_up = task.mark_complete()
            st.success(f"Marked '{task.description}' complete for {task.pet.name}.")
            if follow_up is not None:
                st.info(
                    f"Recurring task re-created: '{follow_up.description}' "
                    f"now due {follow_up.due_date} ({follow_up.frequency.value})."
                )

st.divider()

# --- Build Schedule ---------------------------------------------------------
st.subheader("Build Schedule")
st.caption("Orders every pending task across all pets by priority, then time of day.")

if st.button("Generate schedule"):
    st.text(scheduler.explain_plan())
