"""CLI demo: verify the PawPal+ logic layer in the terminal before using the Streamlit UI."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo(today: date) -> Owner:
    owner = Owner("Samson", available_minutes=60)
    luna = Pet("Luna", "dog", age=3)
    milo = Pet("Milo", "cat", age=5)
    owner.add_pet(luna)
    owner.add_pet(milo)

    # Added out of order on purpose, so sorting has work to do.
    milo.add_task(Task("Brush coat", "19:30", 15, "low", "weekly", today))
    luna.add_task(Task("Heartworm pill", "18:00", 5, "high", "weekly", today))
    luna.add_task(Task("Morning walk", "07:30", 30, "high", "daily", today))
    milo.add_task(Task("Breakfast", "08:00", 10, "high", "daily", today))
    luna.add_task(Task("Breakfast", "08:00", 10, "medium", "daily", today))  # same time as Milo: a conflict
    luna.add_task(Task("Vet check-up", "15:00", 45, "medium", "once", today))
    return owner


def section(title: str) -> None:
    print(f"\n== {title} ==")


if __name__ == "__main__":
    today = date.today()
    owner = build_demo(today)
    scheduler = Scheduler(owner)

    section("All tasks, sorted by time")
    print(scheduler.format_schedule(scheduler.sort_by_time(scheduler.get_tasks()), today))

    section("Conflict check")
    warnings = scheduler.detect_conflicts(scheduler.get_tasks())
    print("\n".join(f"  WARNING: {w}" for w in warnings) or "  No conflicts.")

    section(f"Today's plan (time budget {owner.available_minutes} min, highest priority first)")
    plan, reasons = scheduler.plan_with_reasons(today)
    print(scheduler.format_schedule(plan, today))
    for r in reasons:
        print("  - " + r)

    section("Filter: Luna's tasks only")
    for t in scheduler.sort_by_time(scheduler.filter_tasks(scheduler.get_tasks(), pet_name="Luna")):
        print(f"  {t.time}  {t.description}")

    section("Recurring: complete Luna's daily walk")
    walk = next(t for t in scheduler.get_tasks() if t.description == "Morning walk")
    nxt = scheduler.mark_task_complete(walk)
    print(f"  Done: {walk.description} on {walk.due_date}; next one auto-created for {nxt.due_date} at {nxt.time}")
    print(f"  Pending tasks now: {len(scheduler.filter_tasks(scheduler.get_tasks(), completed=False))}")
