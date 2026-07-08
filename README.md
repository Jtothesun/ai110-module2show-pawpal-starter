# 🐾 PawPal+

**A smart pet care planner.** PawPal+ helps a busy pet owner stay consistent with
their pets' care by tracking tasks (walks, feeding, meds, grooming, enrichment),
organizing them across all of an owner's pets, and building a prioritized daily
plan. Recurring tasks re-create themselves automatically when completed.

Built with a clean, testable Python domain model (`pawpal_system.py`), a runnable
command-line demo (`main.py`), and an interactive Streamlit UI (`app.py`).

---

## Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Installation](#-installation)
- [Usage](#-usage)
- [Demo Walkthrough](#-demo-walkthrough)
- [Smarter Scheduling Reference](#-smarter-scheduling-reference)
- [Testing](#-testing)
- [Roadmap](#-roadmap)

---

## ✨ Features

Each feature below maps to real logic in `pawpal_system.py`.

- **Priority-based daily planning** — `Scheduler.build_daily_plan()` orders every
  pending task across all of an owner's pets using the key
  `(-priority, scheduled_time)`: most urgent first, and within the same urgency,
  earliest time of day first. `Priority` is an `IntEnum` (`LOW < MEDIUM < HIGH`),
  so tasks sort by urgency directly with no custom comparison code.

- **Sorting by time of day** — `Scheduler.sort_by_time()` returns all tasks in
  chronological order. It sorts on a `"HH:MM"` string key; because the format is
  zero-padded 24-hour, plain string comparison matches clock order, so no time
  arithmetic is needed.

- **Filtering by status and/or pet** — `Scheduler.filter_tasks(completed=…,
  pet_name=…)` narrows tasks by completion state, by pet (case-insensitive), or
  both at once (logical AND). Either argument may be omitted to skip that filter.

- **Daily & weekly recurrence** — completing a recurring task auto-creates its
  next occurrence. `Task.mark_complete()` calls `Task.next_occurrence()`, which
  advances the due date with `datetime.timedelta` (daily → +1 day, weekly →
  +7 days) and attaches a fresh pending copy to the same pet. One-off (`ONCE`)
  tasks simply close. A guard prevents a double-completion from spawning a
  duplicate.

- **Task lifecycle management** — `Task.mark_complete()`, `Task.reset()`
  (in-place reopen of a recurring task), and `Task.is_pending()` keep a task's
  state transitions in one place; `Scheduler.reset_daily_tasks()` reopens every
  recurring task for a fresh day.

- **Cross-pet aggregation** — `Owner.all_tasks()` flattens every task across
  every pet into one list, and `Owner.get_pet(name)` does a case-insensitive
  lookup. The `Scheduler` reads live from the `Owner`, so it never falls out of
  date.

- **Human-readable plan explanation** — `Scheduler.explain_plan()` produces a
  numbered, ordered plan naming the pet for each task, and `Scheduler.next_task()`
  returns the single most important pending task.

- **Type-safe domain enums** — `Priority` (`LOW/MEDIUM/HIGH`) and `Frequency`
  (`ONCE/DAILY/WEEKLY/MONTHLY`) replace loose strings with a typo-proof source of
  truth. Stable, auto-incrementing IDs are handed out via `itertools.count`.

---

## 🏗️ Architecture

Four classes, each with a single responsibility. Storing tasks is deliberately
separated from organizing them: the data classes hold state; the `Scheduler`
makes decisions.

| Class | Responsibility | Key members |
|-------|----------------|-------------|
| `Task` | One care activity + its own state transitions | `description`, `scheduled_time`, `frequency`, `priority`, `completed`, `due_date`; `mark_complete()`, `next_occurrence()`, `reset()`, `is_pending()` |
| `Pet` | Home for a pet's tasks | `name`, `species`, `breed`, `tasks`; `add_task()`, `remove_task()`, `pending_tasks()`, `completed_tasks()` |
| `Owner` | Manages pets and aggregates their tasks | `first_name`, `last_name`, `pets`; `add_pet()`, `get_pet()`, `all_tasks()` |
| `Scheduler` | The "brain" — retrieves, sorts, filters, prioritizes | `build_daily_plan()`, `sort_by_time()`, `filter_tasks()`, `next_task()`, `explain_plan()`, `reset_daily_tasks()` |

Relationships are one-to-many and bidirectional (`Owner → Pets → Tasks`, with
each child holding a back-reference), so the `Scheduler` can walk the object
graph in either direction. See `diagrams/pawPal.mmd` for the UML class diagram.

---

## 📦 Installation

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## 🚀 Usage

**Run the interactive Streamlit app:**

```bash
streamlit run app.py
```

Then open the local URL Streamlit prints (default http://localhost:8501).

**Run the command-line demo** (builds sample owners/pets/tasks and exercises the
sorting, filtering, and recurrence logic):

```bash
python main.py
```

---

## 🎬 Demo Walkthrough

### Main UI features and available actions

The Streamlit app (`app.py`) is organized top-to-bottom into five sections:

1. **Add a Pet** — enter a name, species, and breed. Duplicate names are rejected
   with a warning.
2. **Schedule a Task** — pick one of the owner's pets, then set a description,
   time of day, **frequency** (Once / Daily / Weekly / Monthly — defaults to
   Daily), and **priority** (Low / Medium / High).
3. **Current Tasks** — a live table of all tasks with **Pet, Task, Due, Time,
   Frequency, Priority, Done** columns. Three controls sit above it:
   - a **Pet** filter (All or a specific pet),
   - a **Status** filter (All / Pending / Completed),
   - a **Sort by time of day** toggle.
4. **Mark a Task Complete** — choose a pending task and complete it. If the task
   recurs, a banner confirms the next occurrence that was auto-created.
5. **Build Schedule** — generates the prioritized, explained daily plan.

### Example workflow

1. In **Add a Pet**, add `Mochi` (dog).
2. In **Schedule a Task**, schedule `Morning walk` for Mochi at `08:00`,
   frequency **Daily**, priority **High**.
3. The **Current Tasks** table immediately shows the new task, due today.
4. Go to **Mark a Task Complete**, select *Mochi: Morning walk (08:00, …)*, and
   click **Mark complete**.
5. A success message appears, plus an info banner:
   *"Recurring task re-created: 'Morning walk' now due 2026-07-08 (daily)."*
   The table now shows two rows — today's completed walk and tomorrow's pending
   walk.
6. Click **Generate schedule** to see the ordered, explained plan.

### Key Scheduler behaviors demonstrated

- **Sorting** — the *Current Tasks* time toggle uses `sort_by_time()`; *Build
  Schedule* uses `build_daily_plan()` (priority first, then time).
- **Filtering** — the Pet and Status dropdowns call `filter_tasks(pet_name=…,
  completed=…)`, including the combined AND case.
- **Daily recurrence** — completing a daily/weekly task spawns its next
  occurrence via `timedelta`; one-off tasks close without a follow-up.

### Sample CLI output (`python main.py`)

```text
All tasks, sorted by time of day:
  2026-07-07 06:45 - Meds Pandora (Pandora, pending)
  2026-07-07 08:00 - Feed Pandora (Pandora, done)
  2026-07-08 08:00 - Feed Pandora (Pandora, pending)
  2026-07-07 12:30 - Pet Jimmy (Jimmy, done)
  2026-07-08 12:30 - Pet Jimmy (Jimmy, pending)
  2026-07-07 17:15 - Walk Sapphy (Sapphy, pending)
  2026-07-07 21:00 - Groom Jimmy (Jimmy, pending)

Pending tasks only (completed=False):
  2026-07-07 17:15 - Walk Sapphy (Sapphy, pending)
  2026-07-07 06:45 - Meds Pandora (Pandora, pending)
  2026-07-08 08:00 - Feed Pandora (Pandora, pending)
  2026-07-07 21:00 - Groom Jimmy (Jimmy, pending)
  2026-07-08 12:30 - Pet Jimmy (Jimmy, pending)

Tasks for Pandora (pet_name='Pandora'):
  2026-07-07 08:00 - Feed Pandora (Pandora, done)
  2026-07-07 06:45 - Meds Pandora (Pandora, pending)
  2026-07-08 08:00 - Feed Pandora (Pandora, pending)

Pending tasks for Pandora (both filters, AND):
  2026-07-07 06:45 - Meds Pandora (Pandora, pending)
  2026-07-08 08:00 - Feed Pandora (Pandora, pending)

============================================================
Recurrence demo (complete a task -> next occurrence appears)
============================================================
Created:   Brush Sapphy due 2026-07-07 (daily)
Completed: Brush Sapphy due 2026-07-07 -> completed=True
Spawned:   Brush Sapphy due 2026-07-08   <- advanced by timedelta(days=1)

One-off:   Vet visit due 2026-07-07 (once)
Spawned:   None   <- ONCE tasks do not recur

Re-completing the already-done daily task returns: None
```

---

## 📐 Smarter Scheduling Reference

| Capability | Method(s) | Notes |
|------------|-----------|-------|
| Task sorting (priority) | `Scheduler.build_daily_plan()`, `_sort_key()` | Key `(-priority, scheduled_time)` — urgent first, then earliest |
| Task sorting (time) | `Scheduler.sort_by_time()` | Lambda `"HH:MM"` key; zero-padded 24h sorts chronologically |
| Filtering | `Scheduler.filter_tasks(completed=…, pet_name=…)` | Keyword-only, `None` = skip, both = AND |
| Recurring tasks | `Task.mark_complete()`, `Task.next_occurrence()` | Daily → +1 day, weekly → +7 days via `timedelta`; once/monthly do not recur |
| Reset for a new day | `Task.reset()`, `Scheduler.reset_daily_tasks()` | In-place reopen of recurring tasks |
| Conflict handling | — | **Planned, not yet implemented** (see Roadmap) |

---

## 🧪 Testing

```bash
# Run the test suite from the starter directory:
python -m pytest

# With coverage:
python -m pytest --cov
```

Current suite (`tests/test_pawpal.py`) covers task completion and task-to-pet
addition:

```text
..                                                                       [100%]
2 passed in 0.00s
```

---

## 🗺️ Roadmap

Ideas not yet implemented, in rough priority order:

- **Conflict warnings** — flag tasks whose time windows overlap (requires adding
  a `duration` to `Task`, then a greedy interval-overlap check).
- **Priority aging** — bump the effective priority of overdue tasks so they don't
  get starved by newer high-priority ones.
- **Owner constraints** — honor availability windows (work hours, free time) when
  building the plan.
- **Monthly recurrence** — needs calendar-aware date math
  (`dateutil.relativedelta`), since a month isn't a fixed `timedelta`.
- **Persistence** — save/load pets and tasks (e.g. JSON or a database) so state
  survives a browser refresh.
```
