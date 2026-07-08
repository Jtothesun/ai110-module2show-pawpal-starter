from datetime import time

import streamlit as st

from pawpal_system import Owner, Pet, Task, Priority, Frequency, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

st.title("🐾 PawPal+")

st.markdown(
    """
Welcome to the PawPal+ starter app.

This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
but **it does not implement the project logic**. Your job is to design the system and build it.

Use this app as your interactive demo once your backend classes/functions exist.
"""
)

with st.expander("Scenario", expanded=True):
    st.markdown(
        """
**PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
for their pet(s) based on constraints like time, priority, and preferences.

You will design and implement the scheduling logic and connect it to this Streamlit UI.
"""
    )

with st.expander("What you need to build", expanded=True):
    st.markdown(
        """
At minimum, your system should:
- Represent pet care tasks (what needs to happen, how long it takes, priority)
- Represent the pet and the owner (basic info and preferences)
- Build a plan/schedule for a day that chooses and orders tasks based on constraints
- Explain the plan (why each task was chosen and when it happens)
"""
    )

st.divider()

# --- Persistent state -------------------------------------------------------
# Streamlit reruns this script top-to-bottom on every interaction, so we keep
# the Owner in session_state and build it only once. Every rerun then reuses
# the SAME object, preserving the pets and tasks we've added.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", "Lee")

owner = st.session_state.owner

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
        pet = st.selectbox("Pet", owner.pets, format_func=lambda p: p.name)
        description = st.text_input("Task", value="Morning walk")
        scheduled_time = st.time_input("Time of day", value=time(8, 0))
        col1, col2 = st.columns(2)
        with col1:
            frequency = st.selectbox(
                "Frequency", list(Frequency), format_func=lambda f: f.value.title()
            )
        with col2:
            priority = st.selectbox(
                "Priority", list(Priority), index=1, format_func=lambda p: p.name.title()
            )
        if st.form_submit_button("Schedule task"):
            pet.add_task(Task(description, scheduled_time, frequency, priority))
            st.success(f"Scheduled '{description}' for {pet.name} at {scheduled_time:%H:%M}.")

# --- Current pets & tasks ---------------------------------------------------
st.markdown("### Current pets & tasks")
if not owner.pets:
    st.caption("No pets yet.")
else:
    for pet in owner.pets:
        st.markdown(f"**{pet}**")
        if pet.tasks:
            st.table(
                [
                    {
                        "Task": t.description,
                        "Time": t.scheduled_time.strftime("%H:%M"),
                        "Frequency": t.frequency.value,
                        "Priority": t.priority.name,
                        "Done": "✓" if t.completed else "",
                    }
                    for t in pet.tasks
                ]
            )
        else:
            st.caption("No tasks yet.")

# --- Mark a Task Complete ---------------------------------------------------
st.subheader("Mark a Task Complete")
pending = [t for t in owner.all_tasks() if t.is_pending()]
if not pending:
    st.caption("Nothing pending — every task is done. 🎉")
else:
    with st.form("complete_task_form"):
        task = st.selectbox(
            "Pending task",
            pending,
            format_func=lambda t: f"{t.pet.name}: {t.description} ({t.scheduled_time:%H:%M})",
        )
        if st.form_submit_button("Mark complete"):
            task.mark_complete()
            st.success(f"Marked '{task.description}' complete for {task.pet.name}.")

st.divider()

# --- Build Schedule ---------------------------------------------------------
st.subheader("Build Schedule")
st.caption("Orders every pending task across all pets by priority, then time of day.")

if st.button("Generate schedule"):
    plan = Scheduler(owner).explain_plan()
    st.text(plan)
