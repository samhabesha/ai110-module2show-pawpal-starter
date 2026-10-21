"""CLI demo: build an owner with two pets and print today's schedule."""

from datetime import date

from pawpal_system import Owner, Pet, Scheduler, Task


def build_demo() -> Owner:
    owner = Owner("Samson", available_minutes=90)
    luna = Pet("Luna", "dog", age=3)
    milo = Pet("Milo", "cat", age=5)
    owner.add_pet(luna)
    owner.add_pet(milo)

    today = date.today()
    luna.add_task(Task("Morning walk", "07:30", 30, "high", "daily", today))
    milo.add_task(Task("Breakfast", "08:00", 10, "high", "daily", today))
    luna.add_task(Task("Heartworm pill", "18:00", 5, "high", "weekly", today))
    milo.add_task(Task("Brush coat", "19:30", 15, "low", "weekly", today))
    return owner


if __name__ == "__main__":
    owner = build_demo()
    scheduler = Scheduler(owner)
    today = date.today()
    print(scheduler.format_schedule(scheduler.build_daily_plan(today), today))
