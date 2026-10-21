# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

I organized the project into four classes with separate responsibilities:

* **Task:** Represents a care activity, including its scheduled time, duration, priority, and recurrence.
* **Pet:** Stores information about a pet and the tasks assigned to it.
* **Owner:** Keeps track of the owner's pets and daily available time. It also collects tasks from all pets.
* **Scheduler:** Uses the tasks collected by the Owner to create a schedule across all pets.

**b. Design changes**

I made a few changes as the project developed. I added `pet_name` to Task so each schedule entry could identify the correct pet. I also added time validation to convert entries like "9:00" to "09:00," which keeps text-based sorting accurate. Finally, I prevented duplicate pet names so looking up a pet by name would return the right one.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler considers the owner's daily time limit, task priority, scheduled time, and due date.

Priority and available time guide which tasks are selected. Higher-priority activities, such as feeding and medication, come before lower-priority activities like grooming. After choosing the tasks that fit within the time limit, the scheduler displays them in chronological order.

**b. Tradeoffs**

One limitation is that conflict detection only catches tasks with the same start time. It does not catch tasks whose durations overlap. For example, a 30-minute walk starting at 7:30 would not trigger a conflict with feeding at 7:45. This kept the first version simple, but it leaves some scheduling conflicts undetected.

Another limitation is that the time limit can cause a fixed appointment, such as a vet visit, to be skipped. A future version should let certain tasks remain required even when the daily time limit is reached.

---

## 3. AI Collaboration

**a. How I used AI**

I used Claude Code throughout the six project phases. It helped create the UML diagram, build the class structure, implement the scheduling logic, develop the command-line demo, write 19 pytest tests, and connect the Streamlit interface. It also helped draft the README.

Claude Code handled most of the coding, while my role was to guide the work and review the results. The project moved through one phase at a time, with a separate commit for each phase. Breaking the assignment into smaller steps made the work easier to follow and check.

**b. Judgment and verification**

Some parts needed revision after the first implementation. The "All tasks" table originally sorted only by time, which mixed tasks from different dates. That was corrected by sorting by date first and then by time. The conflict messages in the demo were also rewritten to make them easier to understand.

For verification, I ran `python main.py`, checked that all 19 tests passed with `python -m pytest`, and tried the Streamlit app. Looking back, I would spend more time checking unusual scheduling situations instead of relying mainly on the normal examples.

---

## 4. Testing and Verification

**a. What I tested**

The tests covered:

* Marking tasks complete and adding tasks to pets.
* Sorting tasks by time and priority.
* Filtering tasks by pet and completion status.
* Daily and weekly recurrence.
* Making sure one-time tasks do not repeat.
* Detecting conflicts without treating matching times on different dates as conflicts.
* Applying the owner's daily time limit.
* Handling pets without tasks, invalid times, and duplicate pet names.

These checks matter because a schedule can appear correct while still containing mistakes. For example, inconsistent time formatting could place a 9:00 task after a 10:00 task without causing an obvious error.

**b. Confidence**

I would rate my confidence at about 4 out of 5. The existing tests pass and cover the main implemented rules, but there are still situations the scheduler does not handle fully.

Next, I would test overlapping tasks with different start times, tasks that continue past midnight, and weekly tasks that are completed after their scheduled date.

---

## 5. Reflection

**a. What went well**

The recurring task feature was one of the strongest parts of the project. Completing a daily task creates its next occurrence automatically, which reduces the need to enter the same activity repeatedly. It helped make the scheduler useful for ongoing pet care.

**b. What I would improve**

I would improve conflict detection so it considers the full duration of each task. I would also add required tasks that cannot be skipped because of the daily time limit. Another improvement would be saving pets and tasks to a file so the information remains available after closing the app.

**c. Key takeaway**

I learned that being the lead architect involves defining the system's behavior and checking whether the implementation matches those decisions. AI can produce code quickly, but I still need to set priorities, question its choices, and review the results. Testing gives me evidence that the program follows the intended rules.
