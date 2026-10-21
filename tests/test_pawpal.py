from datetime import date

from pawpal_system import Pet, Task


def test_mark_complete_changes_status():
    task = Task("Morning walk", "07:30")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    pet = Pet("Luna", "dog")
    assert pet.task_count() == 0
    pet.add_task(Task("Breakfast", "08:00", due_date=date(2026, 10, 21)))
    assert pet.task_count() == 1
    assert pet.tasks[0].pet_name == "Luna"
