from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task

DAY = date(2026, 10, 21)


@pytest.fixture
def setup():
    owner = Owner("Sam", available_minutes=60)
    luna, milo = Pet("Luna", "dog"), Pet("Milo", "cat")
    owner.add_pet(luna)
    owner.add_pet(milo)
    return owner, luna, milo, Scheduler(owner)


# --- core behaviour -------------------------------------------------------

def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Luna", "dog")
    assert pet.task_count() == 0
    pet.add_task(Task("Breakfast", "08:00", due_date=DAY))
    assert pet.task_count() == 1
    assert pet.tasks[0].pet_name == "Luna"


def test_scheduler_reads_tasks_from_all_pets(setup):
    owner, luna, milo, s = setup
    luna.add_task(Task("Walk", "07:00", due_date=DAY))
    milo.add_task(Task("Feed", "08:00", due_date=DAY))
    assert {t.description for t in s.get_tasks()} == {"Walk", "Feed"}


# --- sorting ----------------------------------------------------------------

def test_sort_by_time_is_chronological(setup):
    _, luna, _, s = setup
    for desc, time in [("Dinner", "18:00"), ("Walk", "07:30"), ("Pill", "12:15")]:
        luna.add_task(Task(desc, time, due_date=DAY))
    assert [t.time for t in s.sort_by_time(s.get_tasks())] == ["07:30", "12:15", "18:00"]


def test_single_digit_hour_is_normalised_so_sorting_stays_correct():
    # "9:00" would sort after "10:00" as text; the Task pads it to "09:00".
    assert Task("Walk", "9:00").time == "09:00"


def test_priority_then_time(setup):
    _, luna, _, s = setup
    luna.add_task(Task("Brush", "07:00", priority="low", due_date=DAY))
    luna.add_task(Task("Pill", "09:00", priority="high", due_date=DAY))
    luna.add_task(Task("Walk", "08:00", priority="high", due_date=DAY))
    assert [t.description for t in s.sort_by_priority_then_time(s.get_tasks())] == ["Walk", "Pill", "Brush"]


# --- filtering --------------------------------------------------------------

def test_filter_by_pet_and_status(setup):
    _, luna, milo, s = setup
    walk = Task("Walk", "07:00", due_date=DAY)
    luna.add_task(walk)
    milo.add_task(Task("Feed", "08:00", due_date=DAY))
    walk.mark_complete()
    assert [t.description for t in s.filter_tasks(s.get_tasks(), pet_name="luna")] == ["Walk"]
    assert [t.description for t in s.filter_tasks(s.get_tasks(), completed=False)] == ["Feed"]


# --- recurrence -------------------------------------------------------------

def test_completing_daily_task_creates_next_day_task(setup):
    _, luna, _, s = setup
    walk = Task("Walk", "07:30", frequency="daily", due_date=DAY)
    luna.add_task(walk)
    nxt = s.mark_task_complete(walk)
    assert walk.completed and nxt is not None
    assert nxt.due_date == DAY + timedelta(days=1)
    assert nxt.completed is False and nxt.time == "07:30"
    assert luna.task_count() == 2


def test_weekly_task_recurs_in_seven_days(setup):
    _, _, milo, s = setup
    brush = Task("Brush", "19:00", frequency="weekly", due_date=DAY)
    milo.add_task(brush)
    assert s.mark_task_complete(brush).due_date == DAY + timedelta(weeks=1)


def test_one_off_task_does_not_recur(setup):
    _, luna, _, s = setup
    vet = Task("Vet", "15:00", frequency="once", due_date=DAY)
    luna.add_task(vet)
    assert s.mark_task_complete(vet) is None
    assert luna.task_count() == 1


# --- conflicts --------------------------------------------------------------

def test_conflict_detected_for_same_time_across_pets(setup):
    _, luna, milo, s = setup
    luna.add_task(Task("Breakfast", "08:00", due_date=DAY))
    milo.add_task(Task("Breakfast", "08:00", due_date=DAY))
    warnings = s.detect_conflicts(s.get_tasks())
    assert len(warnings) == 1 and "08:00" in warnings[0]


def test_same_time_on_different_days_is_not_a_conflict(setup):
    _, luna, _, s = setup
    luna.add_task(Task("Walk", "08:00", due_date=DAY))
    luna.add_task(Task("Walk", "08:00", due_date=DAY + timedelta(days=1)))
    assert s.detect_conflicts(s.get_tasks()) == []


# --- planning with a time budget -----------------------------------------------

def test_plan_respects_time_budget_and_keeps_high_priority(setup):
    owner, luna, _, s = setup  # 60-minute budget
    luna.add_task(Task("Walk", "07:00", 40, "high", due_date=DAY))
    luna.add_task(Task("Grooming", "10:00", 30, "low", due_date=DAY))
    luna.add_task(Task("Pill", "18:00", 5, "high", due_date=DAY))
    plan, reasons = s.plan_with_reasons(DAY)
    assert [t.description for t in plan] == ["Walk", "Pill"]
    assert sum(t.duration_minutes for t in plan) <= owner.available_minutes
    assert any("Skipped" in r and "Grooming" in r for r in reasons)


def test_pet_with_no_tasks_gives_empty_plan(setup):
    _, _, _, s = setup
    assert s.build_daily_plan(DAY) == []
    assert s.detect_conflicts(s.get_tasks()) == []


# --- validation ---------------------------------------------------------------

@pytest.mark.parametrize("bad", ["25:00", "8", "ab:cd", "08:5"])
def test_invalid_time_rejected(bad):
    with pytest.raises(ValueError):
        Task("Walk", bad)


def test_duplicate_pet_name_rejected(setup):
    owner, *_ = setup
    with pytest.raises(ValueError):
        owner.add_pet(Pet("luna", "dog"))
