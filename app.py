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
scheduler = Scheduler(owner)
today = date.today()

with st.sidebar:
    st.header("Owner")
    owner.name = st.text_input("Owner name", value=owner.name)
    owner.available_minutes = st.slider("Time available today (min)", 15, 480, owner.available_minutes, step=15)

    st.header("Add a pet")
    with st.form("add_pet", clear_on_submit=True):
        pet_name = st.text_input("Pet name", value="Mochi")
        species = st.selectbox("Species", ["dog", "cat", "other"])
        age = st.number_input("Age", min_value=0, max_value=40, value=2)
        if st.form_submit_button("Add pet"):
            try:
                owner.add_pet(Pet(pet_name.strip(), species, int(age)))
                st.success(f"Added {pet_name}.")
            except ValueError as e:
                st.error(str(e))
    if owner.pets:
        st.caption("Pets: " + ", ".join(f"{p.name} ({p.species})" for p in owner.pets))

if not owner.pets:
    st.info("Start by adding a pet in the sidebar.")
    st.stop()

st.subheader("Schedule a task")
with st.form("add_task", clear_on_submit=True):
    c1, c2 = st.columns(2)
    pet_choice = c1.selectbox("Pet", [p.name for p in owner.pets])
    description = c2.text_input("Task", value="Morning walk")
    c3, c4, c5, c6 = st.columns(4)
    when = c3.time_input("Time")
    duration = c4.number_input("Minutes", min_value=1, max_value=240, value=20)
    priority = c5.selectbox("Priority", ["high", "medium", "low"])
    frequency = c6.selectbox("Repeats", ["once", "daily", "weekly"])
    if st.form_submit_button("Add task"):
        owner.get_pet(pet_choice).add_task(
            Task(description.strip(), when.strftime("%H:%M"), int(duration), priority, frequency, today)
        )
        st.success(f"Scheduled {description} for {pet_choice} at {when:%H:%M}.")

# Conflict warnings come first: a double-booked slot is the thing an owner must fix.
for warning in scheduler.detect_conflicts(scheduler.tasks_for(today)):
    st.warning("⚠️ " + warning + ". Move one of these so you're not in two places at once.")

st.subheader(f"Today's plan · {owner.available_minutes} min available")
plan, reasons = scheduler.plan_with_reasons(today)
if plan:
    used = sum(t.duration_minutes for t in plan)
    st.success(f"{len(plan)} task(s) planned, {used} of {owner.available_minutes} min used.")
    st.table([{"Time": t.time, "Pet": t.pet_name, "Task": t.description, "Min": t.duration_minutes,
               "Priority": t.priority, "Repeats": t.frequency} for t in plan])
    with st.expander("Why this plan?"):
        for r in reasons:
            st.write("• " + r)
    skipped = [r for r in reasons if r.startswith("Skipped")]
    if skipped:
        st.info(f"{len(skipped)} task(s) didn't fit today's time budget. Raise your available time or lower their priority.")
else:
    st.info("Nothing scheduled for today yet.")

st.subheader("Mark tasks done")
pending = scheduler.sort_by_time(scheduler.tasks_for(today))
for i, t in enumerate(pending):
    if st.button(f"✅ {t.time} · {t.pet_name}: {t.description}", key=f"done-{i}-{t.pet_name}-{t.time}-{t.description}"):
        nxt = scheduler.mark_task_complete(t)
        if nxt:
            st.toast(f"Next {t.description} for {t.pet_name} added for {nxt.due_date:%a %b %d}.")
        st.rerun()

st.subheader("All tasks")
pet_filter = st.selectbox("Show", ["All pets"] + [p.name for p in owner.pets])
status = st.radio("Status", ["Pending", "Done", "Any"], horizontal=True)
shown = scheduler.filter_tasks(
    scheduler.get_tasks(),
    pet_name=None if pet_filter == "All pets" else pet_filter,
    completed={"Pending": False, "Done": True, "Any": None}[status],
)
st.table([{"Date": f"{t.due_date:%b %d}", "Time": t.time, "Pet": t.pet_name, "Task": t.description,
           "Done": "✓" if t.completed else ""} for t in sorted(shown, key=lambda t: (t.due_date, t.time))]
         or [{"Info": "No tasks match."}])
