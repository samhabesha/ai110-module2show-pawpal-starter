"""PawPal+ logic layer: owners, pets, care tasks and the scheduler that plans a day."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, timedelta


PRIORITY_RANK = {"high": 0, "medium": 1, "low": 2}


@dataclass
class Task:
    """One care activity for one pet, e.g. a walk at 08:00."""

    description: str
    time: str  # "HH:MM", 24-hour
    duration_minutes: int = 15
    priority: str = "medium"  # low | medium | high
    frequency: str = "once"  # once | daily | weekly
    due_date: date = field(default_factory=date.today)
    completed: bool = False
    pet_name: str = ""

    def __post_init__(self) -> None:
        """Validate fields so bad input fails early instead of breaking sorting later."""
        hh, _, mm = self.time.partition(":")
        if not (hh.isdigit() and mm.isdigit() and len(mm) == 2 and 0 <= int(hh) < 24 and 0 <= int(mm) < 60):
            raise ValueError(f"time must be HH:MM, got {self.time!r}")
        self.time = f"{int(hh):02d}:{mm}"  # "8:05" -> "08:05" so string order == clock order
        if self.priority not in PRIORITY_RANK:
            raise ValueError(f"priority must be low, medium or high, got {self.priority!r}")
        if self.duration_minutes <= 0:
            raise ValueError("duration_minutes must be positive")

    def mark_complete(self) -> None:
        """Mark this task as done."""
        self.completed = True

    def next_occurrence(self) -> Task | None:
        """The next copy of a daily/weekly task (due 1 or 7 days later), or None for one-off tasks."""
        step = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}.get(self.frequency)
        if step is None:
            return None
        return replace(self, due_date=self.due_date + step, completed=False)


@dataclass
class Pet:
    """A pet and the list of care tasks it needs."""

    name: str
    species: str
    age: int = 0
    tasks: list[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Attach a task to this pet and stamp the pet's name on it."""
        task.pet_name = self.name
        self.tasks.append(task)

    def task_count(self) -> int:
        """Return how many tasks this pet has."""
        return len(self.tasks)


class Owner:
    """A pet owner with a daily time budget and one or more pets."""

    def __init__(self, name: str, available_minutes: int = 120):
        self.name = name
        self.available_minutes = available_minutes
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet; pet names must be unique for this owner."""
        if self.get_pet(pet.name):
            raise ValueError(f"{self.name} already has a pet named {pet.name}")
        self.pets.append(pet)

    def get_pet(self, name: str) -> Pet | None:
        """Find a pet by name (case-insensitive), or None."""
        return next((p for p in self.pets if p.name.lower() == name.lower()), None)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]


class Scheduler:
    """The 'brain': reads all tasks through the Owner and organizes them."""

    def __init__(self, owner: Owner):
        self.owner = owner

    def get_tasks(self) -> list[Task]:
        """All tasks for all pets, read through Owner.get_all_tasks()."""
        return self.owner.get_all_tasks()

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks in chronological order (zero-padded HH:MM sorts correctly as text)."""
        return sorted(tasks, key=lambda t: t.time)

    def sort_by_priority_then_time(self, tasks: list[Task]) -> list[Task]:
        """High priority first; ties broken by time of day."""
        return sorted(tasks, key=lambda t: (PRIORITY_RANK[t.priority], t.time))

    def filter_tasks(self, tasks: list[Task], pet_name: str | None = None, completed: bool | None = None) -> list[Task]:
        """Keep tasks matching a pet name and/or completion status (None means 'any')."""
        return [
            t for t in tasks
            if (pet_name is None or t.pet_name.lower() == pet_name.lower())
            and (completed is None or t.completed == completed)
        ]

    def tasks_for(self, day: date) -> list[Task]:
        """Unfinished tasks due on the given day, across all pets."""
        return [t for t in self.get_tasks() if t.due_date == day and not t.completed]

    def detect_conflicts(self, tasks: list[Task]) -> list[str]:
        """Warning messages for tasks booked at the exact same date and time (never raises)."""
        slots: dict[tuple[date, str], list[Task]] = defaultdict(list)
        for t in tasks:
            slots[(t.due_date, t.time)].append(t)
        return [
            f"Conflict at {time} on {day:%b %d}: " + ", ".join(f"{t.pet_name}: {t.description}" for t in clash)
            for (day, time), clash in sorted(slots.items())
            if len(clash) > 1
        ]

    def mark_task_complete(self, task: Task) -> Task | None:
        """Complete a task; if it recurs, add the next occurrence to the same pet and return it."""
        task.mark_complete()
        nxt = task.next_occurrence()
        pet = self.owner.get_pet(task.pet_name)
        if nxt and pet:
            pet.add_task(nxt)
        return nxt

    def build_daily_plan(self, day: date) -> list[Task]:
        """The day's plan: pick tasks by priority until the owner's time budget runs out, then order by time."""
        plan, _ = self.plan_with_reasons(day)
        return plan

    def plan_with_reasons(self, day: date) -> tuple[list[Task], list[str]]:
        """Like build_daily_plan, but also explains why each task was kept or skipped."""
        budget = self.owner.available_minutes
        chosen, reasons = [], []
        for t in self.sort_by_priority_then_time(self.tasks_for(day)):
            if t.duration_minutes <= budget:
                chosen.append(t)
                budget -= t.duration_minutes
                reasons.append(f"Kept {t.pet_name}'s {t.description} ({t.priority} priority, {t.duration_minutes} min).")
            else:
                reasons.append(f"Skipped {t.pet_name}'s {t.description}: needs {t.duration_minutes} min, only {budget} min left today.")
        return self.sort_by_time(chosen), reasons

    def format_schedule(self, tasks: list[Task], day: date) -> str:
        """Readable text version of a schedule for the terminal."""
        lines = [f"Today's Schedule for {self.owner.name} ({day:%a %b %d})", "-" * 52]
        if not tasks:
            lines.append("  Nothing scheduled.")
        for t in tasks:
            mark = "x" if t.completed else " "
            lines.append(f"  [{mark}] {t.time}  {t.pet_name:<7} {t.description:<20} {t.duration_minutes:>3} min  ({t.priority})")
        return "\n".join(lines)
