from datetime import date

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")
st.caption("Plan your pets' care day: feedings, walks, meds and appointments.")

# Streamlit reruns this script on every click, so the Owner lives in session_state.
if "owner" not in st.session_state:
    st.session_state.owner = Owner("Jordan", available_minutes=120)
owner: Owner = st.session_state.owner

st.subheader("Owner")
owner.name = st.text_input("Owner name", value=owner.name)

st.subheader("Add a pet")
with st.form("add_pet", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    pet_name = c1.text_input("Pet name", value="Mochi")
    species = c2.selectbox("Species", ["dog", "cat", "other"])
    age = c3.number_input("Age", min_value=0, max_value=40, value=2)
    if st.form_submit_button("Add pet"):
        try:
            owner.add_pet(Pet(pet_name.strip(), species, int(age)))
            st.success(f"Added {pet_name}.")
        except ValueError as e:
            st.error(str(e))

if not owner.pets:
    st.info("No pets yet. Add one above.")
    st.stop()

st.subheader("Schedule a task")
with st.form("add_task", clear_on_submit=True):
    c1, c2 = st.columns(2)
    pet_choice = c1.selectbox("Pet", [p.name for p in owner.pets])
    description = c2.text_input("Task", value="Morning walk")
    c3, c4, c5 = st.columns(3)
    when = c3.time_input("Time")
    duration = c4.number_input("Duration (min)", min_value=1, max_value=240, value=20)
    priority = c5.selectbox("Priority", ["high", "medium", "low"])
    if st.form_submit_button("Add task"):
        owner.get_pet(pet_choice).add_task(
            Task(description, when.strftime("%H:%M"), int(duration), priority, "once", date.today())
        )
        st.success(f"Scheduled {description} for {pet_choice}.")

st.subheader("Today's schedule")
scheduler = Scheduler(owner)
plan = scheduler.build_daily_plan(date.today())
if plan:
    st.table([{"Time": t.time, "Pet": t.pet_name, "Task": t.description, "Min": t.duration_minutes, "Priority": t.priority} for t in plan])
else:
    st.info("Nothing scheduled for today yet.")
