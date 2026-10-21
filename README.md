# 🐾 PawPal+ (Module 2 Project)

PawPal+ is a Streamlit app that helps a busy pet owner plan a day of pet care: walks, feedings, meds, grooming and appointments. It works across several pets, fits the day into the owner's available time (highest priority first), warns about double-booked times, and re-creates daily or weekly tasks automatically when they are done.

The logic lives in `pawpal_system.py` and was verified CLI-first with `main.py` and `pytest` before it was connected to the UI in `app.py`.

## Setup and run

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

python main.py                   # CLI demo
streamlit run app.py             # web app
python -m pytest                 # tests
```

## How it's built

| Class | Responsibility |
|---|---|
| `Task` (dataclass) | One care activity: description, `HH:MM` time, duration, priority, frequency (once/daily/weekly), due date, completed flag, owning pet. Validates its time and priority, and builds its own `next_occurrence()`. |
| `Pet` (dataclass) | A pet and its task list. `add_task()` stamps the pet's name on each task. |
| `Owner` | The person, their daily time budget (`available_minutes`) and their pets. `get_all_tasks()` returns every pet's tasks in one list. |
| `Scheduler` | The "brain". It reads tasks **only through `Owner.get_all_tasks()`**, so it plans across all pets, then sorts, filters, detects conflicts, handles recurrence and builds the daily plan. |

UML: [`diagrams/uml.mmd`](diagrams/uml.mmd) (final; also saved as `diagrams/uml_final.mmd`). The Phase 1 draft is in [`diagrams/uml_draft.mmd`](diagrams/uml_draft.mmd). Paste either into the [Mermaid Live Editor](https://mermaid.live/) to view it.

## Features

- **Multi-pet owner profile** with a daily time budget.
- **Sorting by time.** Times are normalised to zero-padded `HH:MM`, so `"9:00"` can't sort after `"10:00"`.
- **Priority planning.** High-priority tasks are picked first until the time budget runs out, then the plan is shown in clock order.
- **"Why this plan?"** Every kept or skipped task gets a one-line reason.
- **Conflict warnings.** Two tasks at the same date and time trigger a warning, not a crash.
- **Daily and weekly recurrence.** Completing a recurring task adds the next one (+1 day or +7 days, using `timedelta`).
- **Filtering** by pet and by status (pending, done or any).
- **Input validation.** Bad times (`25:00`, `8`), unknown priorities and duplicate pet names are rejected with clear errors.

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_time()`, `Scheduler.sort_by_priority_then_time()` | `sorted()` with a lambda key on the `HH:MM` string; priority ranks high → medium → low, with ties broken by time |
| Filtering | `Scheduler.filter_tasks(tasks, pet_name, completed)`, `Scheduler.tasks_for(day)` | Filters by pet name (case-insensitive) and/or completion status; `None` means "any" |
| Conflict handling | `Scheduler.detect_conflicts(tasks)` | Groups tasks by (date, time) and returns warning strings for any slot with 2+ tasks, across all pets |
| Recurring tasks | `Task.next_occurrence()`, `Scheduler.mark_task_complete(task)` | Daily → +1 day, weekly → +7 days; the new task is added to the same pet. One-off tasks don't repeat |
| Time budget + explanations | `Scheduler.plan_with_reasons(day)`, `Scheduler.build_daily_plan(day)` | Greedy by priority within `Owner.available_minutes`; returns the plan and a reason for each task |

## 🖥️ Sample Output

Output of `python main.py`:

```

== All tasks, sorted by time ==
Today's Schedule for Samson (Wed Oct 21)
----------------------------------------------------
  [ ] 07:30  Luna    Morning walk          30 min  (high)
  [ ] 08:00  Luna    Breakfast             10 min  (medium)
  [ ] 08:00  Milo    Breakfast             10 min  (high)
  [ ] 15:00  Luna    Vet check-up          45 min  (medium)
  [ ] 18:00  Luna    Heartworm pill         5 min  (high)
  [ ] 19:30  Milo    Brush coat            15 min  (low)

== Conflict check ==
  WARNING: Conflict at 08:00 on Oct 21: Luna: Breakfast, Milo: Breakfast

== Today's plan (time budget 60 min, highest priority first) ==
Today's Schedule for Samson (Wed Oct 21)
----------------------------------------------------
  [ ] 07:30  Luna    Morning walk          30 min  (high)
  [ ] 08:00  Milo    Breakfast             10 min  (high)
  [ ] 08:00  Luna    Breakfast             10 min  (medium)
  [ ] 18:00  Luna    Heartworm pill         5 min  (high)
  - Kept Luna's Morning walk (high priority, 30 min).
  - Kept Milo's Breakfast (high priority, 10 min).
  - Kept Luna's Heartworm pill (high priority, 5 min).
  - Kept Luna's Breakfast (medium priority, 10 min).
  - Skipped Luna's Vet check-up: needs 45 min, only 5 min left today.
  - Skipped Milo's Brush coat: needs 15 min, only 5 min left today.

== Filter: Luna's tasks only ==
  07:30  Morning walk
  08:00  Breakfast
  15:00  Vet check-up
  18:00  Heartworm pill

== Recurring: complete Luna's daily walk ==
  Done: Morning walk on 2026-10-21; next one auto-created for 2026-10-22 at 07:30
  Pending tasks now: 6
```

## 🧪 Testing PawPal+

```bash
python -m pytest
```

`tests/test_pawpal.py` has 19 tests covering:
- **Core:** completing a task, adding tasks to a pet, and the Scheduler reading tasks from *all* pets.
- **Sorting:** chronological order, single-digit hours normalised, and priority-then-time order.
- **Filtering:** by pet and by completion status.
- **Recurrence:** daily (+1 day), weekly (+7 days), and one-off tasks that don't recur.
- **Conflicts:** the same time across pets is flagged; the same time on different days is not.
- **Planning:** the time budget is respected, high priority is kept, and skipped tasks are explained.
- **Edge cases:** a pet with no tasks, invalid times, and duplicate pet names.

```
plugins: anyio-4.15.1
collected 19 items

tests\test_pawpal.py ...................                                 [100%]

============================= 19 passed in 0.05s ==============================
```

**Confidence level: ★★★★☆ (4/5).** Every scheduling rule has a passing test, including edge cases. One star is held back because conflicts only check *exact* start times, not overlapping durations (see the tradeoffs in `reflection.md`).

## 📸 Demo Walkthrough

1. Run `streamlit run app.py`. In the **sidebar**, enter the owner's name and set **Time available today** (e.g. 60 min).
2. Add pets in the sidebar, e.g. **Luna (dog)** and **Milo (cat)**. The sidebar lists your pets.
3. Under **Schedule a task**, pick a pet and enter the task, time, minutes, priority and whether it repeats (once/daily/weekly), then click **Add task**. A success message confirms it.
4. Add two tasks at the same time for different pets. A yellow **⚠️ Conflict at 08:00…** warning appears above the plan.
5. **Today's plan** shows the tasks that fit your time budget, in clock order, with a summary like "4 task(s) planned, 55 of 60 min used". Open **Why this plan?** to see why each task was kept or skipped.
6. Under **Mark tasks done**, click a task. A daily or weekly task immediately gets its next occurrence (shown in a toast), and the completed one leaves today's list.
7. Use **All tasks** to filter by pet and by status (Pending / Done / Any).

The CLI demo (`python main.py`) shows the same behaviour in the terminal. See **Sample Output** above.
