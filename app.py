import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler
from ai_planner import run_ai_planner

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

if "owner" not in st.session_state:
    st.session_state.owner = Owner("Alice")

owner = st.session_state.owner
scheduler = Scheduler(owner)

st.title("🐾 PawPal+")

st.write(f"Managing pets for {owner.name}")

if st.button("Reset app data"):
    st.session_state.owner = Owner("Alice")
    st.rerun()

owner = st.session_state.owner
scheduler = Scheduler(owner)

st.markdown(
    """
Welcome to PawPal+.

This app lets you add pets, assign tasks, and view a smarter schedule using
sorting, filtering, recurring task support, and conflict detection.
"""
)

st.divider()

st.subheader("Owner and Pet Setup")
owner_name = st.text_input("Owner name", value=owner.name)
pet_name = st.text_input("Pet name", value="Mochi")
species = st.selectbox("Species", ["Dog", "Cat", "Other"])

if owner_name:
    owner.name = owner_name

if st.button("Add pet"):
    if pet_name.strip():
        pet = Pet(pet_name, 0, species)
        owner.add_pet(pet)
        st.success(f"Pet '{pet_name}' has been added.")
        st.rerun()
    else:
        st.error("Please enter a pet name.")

selected_pet_name = None
if owner.pets:
    selected_pet_name = st.selectbox(
        "Choose a pet for the task",
        [pet.name for pet in owner.pets]
    )

st.divider()

st.subheader("Add Tasks")

col1, col2, col3 = st.columns(3)
with col1:
    task_title = st.text_input("Task title", value="Morning walk")
with col2:
    task_time = st.text_input("Task time (HH:MM)", value="09:00")
with col3:
    frequency = st.selectbox("Frequency", ["daily", "weekly", "bi-weekly", "once"], index=0)

if st.button("Add task"):
    if owner.pets and selected_pet_name:
        selected_pet = next((pet for pet in owner.pets if pet.name == selected_pet_name), None)

        if selected_pet:
            new_task = Task(task_title, task_time, frequency)
            selected_pet.add_task(new_task)
            st.success(f"Task '{task_title}' has been added for {selected_pet.name}.")
            st.rerun()
    else:
        st.error("You must first add a pet before adding tasks.")

st.subheader("AI Care Planner")

owner_goal = st.text_input("What is your goal for your pet?", placeholder="e.g. exercise, groom")

if st.button("Generate AI Care Plan"):

    if owner.pets and selected_pet_name:
        selected_pet = next((pet for pet in owner.pets if pet.name == selected_pet_name), None)

        if selected_pet:
            result = run_ai_planner(
                selected_pet,
                owner_goal,
                selected_pet.tasks
            )

            for task in result["approved_tasks"]:
                selected_pet.add_task(task)

            st.success("AI care plan generated and tasks added!")

            if result["warnings"]:
                for warning in result["warnings"]:
                    st.warning(warning)

            st.rerun()
    else:
        st.error("Please select a pet first.")

st.divider()

st.subheader("Task View")

filter_pet = st.selectbox(
    "Filter by pet",
    ["All pets"] + [pet.name for pet in owner.pets] if owner.pets else ["All pets"]
)

filter_status = st.selectbox(
    "Filter by status",
    ["All", "Pending", "Completed"]
)

if filter_pet == "All pets":
    tasks = scheduler.filter_tasks(
        completed=True if filter_status == "Completed" else False if filter_status == "Pending" else None
    )
else:
    tasks = scheduler.filter_tasks(
        pet_name=filter_pet,
        completed=True if filter_status == "Completed" else False if filter_status == "Pending" else None
    )

tasks = scheduler.sort_by_time(tasks)

task_rows = []
for pet in owner.get_pets():
    for task in pet.tasks:
        if task in tasks:
            task_rows.append(
                {
                    "Pet": pet.name,
                    "Task": task.description,
                    "Time": task.time,
                    "Frequency": task.frequency,
                    "Due Date": task.due_date,
                    "Completed": task.completed,
                }
            )

if task_rows:
    st.table(task_rows)
else:
    st.info("No tasks match the current filter.")

st.divider()

st.subheader("Complete a Task")

task_options = []
task_lookup = {}

for pet in owner.get_pets():
    for i, task in enumerate(pet.tasks):
        if not task.completed:
            label = f"{pet.name} - {task.description} at {task.time} ({task.frequency})"
            task_options.append(label)
            task_lookup[label] = (pet, task)

if task_options:
    selected_task_label = st.selectbox("Choose a task to complete", task_options)

    if st.button("Mark task complete"):
        pet, task = task_lookup[selected_task_label]
        new_task = scheduler.complete_task(pet, task)

        st.success(f"Marked '{task.description}' as complete.")

        if new_task:
            st.info(
                f"Recurring task created: '{new_task.description}' on {new_task.due_date} at {new_task.time}"
            )

        st.rerun()
else:
    st.info("No pending tasks available to complete.")

st.divider()

st.subheader(f"{owner.name}'s Schedule")

if st.button("Generate schedule"):
    tasks = scheduler.sort_by_time(owner.get_tasks())

    if tasks:
        schedule_rows = []

        for task in tasks:
            pet_name = next(
                (pet.name for pet in owner.get_pets() if task in pet.tasks),
                "Unknown"
            )

            schedule_rows.append(
                {
                    "Pet": pet_name,
                    "Time": task.time,
                    "Task": task.description,
                    "Frequency": task.frequency,
                    "Due Date": task.due_date,
                    "Completed": task.completed,
                }
            )

        st.table(schedule_rows)
    else:
        st.warning("No tasks available to schedule.")

st.divider()

st.subheader(f"{owner.name}'s Conflict Warnings")

conflicts = scheduler.find_conflicts()

if conflicts:
    for (due_date, time), conflict_tasks in conflicts.items():
        st.warning(f"{owner.name} has a conflict on {due_date} at {time}")
        for task in conflict_tasks:
            st.write(f"- {task.description} ({task.frequency})")
else:
    st.success("No task conflicts found.")
