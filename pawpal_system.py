"""PawPal+ domain model.

A smart pet care management system. This module defines the four core objects
and the logic that ties them together:

* :class:`Task`      - one activity (description, time, frequency, done?).
* :class:`Pet`       - a pet's details plus the list of tasks it needs.
* :class:`Owner`     - a person who manages several pets and their tasks.
* :class:`Scheduler` - the "brain" that retrieves, organizes, and prioritizes
  tasks across every pet an owner has.

Design notes worth reading:

* We lean on :mod:`dataclasses` so each class reads like a clean data
  definition; the interesting behavior lives in the methods, not in
  hand-written ``__init__`` boilerplate.
* Relationships are kept **bidirectional** and are always mutated through the
  helper methods (:meth:`Owner.add_pet`, :meth:`Pet.add_task`). That single
  choke point is what stops the two sides of a relationship from drifting out
  of sync.
* Mutable fields (``pets``, ``tasks``) use ``field(default_factory=list)`` so
  every instance gets its OWN list. ``pets: list = []`` would silently share
  one list across every Owner - a classic Python footgun.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from datetime import date, time, timedelta
from enum import Enum, IntEnum

# Module-level counters used to hand out unique, stable ids so callers never
# have to manage them by hand. ``itertools.count`` is a lazy infinite iterator;
# ``next(...)`` pulls the next integer each time a Task/Pet/Owner is created.
_task_ids = itertools.count(1)
_pet_ids = itertools.count(1)
_owner_ids = itertools.count(1)


class Priority(IntEnum):
    """How urgent a task is.

    Subclassing :class:`~enum.IntEnum` (rather than a plain ``Enum``) means the
    members compare and sort like integers, so ``Priority.HIGH > Priority.LOW``
    is ``True`` and we can sort tasks by priority directly.
    """

    LOW = 1
    MEDIUM = 2
    HIGH = 3


class Frequency(Enum):
    """How often a task repeats."""

    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"


# How far ahead the *next* occurrence of a recurring task lands. ``timedelta``
# represents an exact span of days, so DAILY and WEEKLY are precise. ONCE has no
# next occurrence (absent from the map). MONTHLY is intentionally omitted: a
# calendar month isn't a fixed number of days, so it can't be expressed as a
# reliable timedelta - it needs calendar-aware logic (e.g. dateutil.relativedelta)
# and is out of scope here.
_RECURRENCE_DELTAS: dict[Frequency, timedelta] = {
    Frequency.DAILY: timedelta(days=1),
    Frequency.WEEKLY: timedelta(weeks=1),
}


@dataclass
class Task:
    """A single pet care activity, e.g. "Morning walk at 08:00, daily".

    Attributes:
        description: Human-readable label shown in the UI.
        scheduled_time: The time of day the task should happen.
        frequency: How often the task recurs (see :class:`Frequency`).
        priority: How urgent the task is (see :class:`Priority`).
        completed: Whether the task has been carried out for the current cycle.
        due_date: The calendar day this occurrence is due. Combined with
            ``scheduled_time`` it pins down exactly when the task should happen.
            Defaults to today; recurring occurrences advance it via ``timedelta``.
        pet: Back-reference to the owning :class:`Pet`. Set automatically by
            :meth:`Pet.add_task`; leave it as ``None`` when constructing.
        id: Auto-assigned unique identifier.
    """

    description: str
    scheduled_time: time
    frequency: Frequency = Frequency.DAILY
    priority: Priority = Priority.MEDIUM
    completed: bool = False
    due_date: date = field(default_factory=date.today)
    # Back-reference to the owning Pet. Excluded from __eq__/__repr__ to avoid
    # infinite recursion: Task -> pet -> tasks -> Task -> ... (dataclasses
    # compare every field by default, and the relationship is bidirectional).
    pet: "Pet | None" = field(default=None, compare=False, repr=False)
    id: int = field(default_factory=lambda: next(_task_ids))

    def mark_complete(self) -> "Task | None":
        """Mark this task done and, if it recurs, spawn its next occurrence.

        For a DAILY or WEEKLY task, completing it automatically creates a fresh
        Task for the next cycle (tomorrow / next week) and attaches it to the
        same pet, so the owner's to-do list refills itself. ONCE (and the
        unsupported MONTHLY) tasks simply close.

        Guarded against double-completion: calling this on an already-completed
        task is a no-op and does NOT spawn a duplicate. Returns the newly
        created follow-up Task, or ``None`` when nothing was spawned.
        """
        if self.completed:
            return None
        self.completed = True

        following = self.next_occurrence()
        if following is not None and self.pet is not None:
            self.pet.add_task(following)
        return following

    def next_occurrence(self) -> "Task | None":
        """Return a fresh Task for this task's next cycle, or ``None``.

        Daily -> today + 1 day, weekly -> today + 7 days, computed with
        :class:`datetime.timedelta` for accurate date arithmetic (it rolls over
        month/year boundaries correctly). One-off and monthly tasks return
        ``None``. The returned Task is pending, carries the same description,
        time, frequency, and priority, and is NOT yet attached to a pet - that
        is the caller's job (see :meth:`mark_complete`).
        """
        delta = _RECURRENCE_DELTAS.get(self.frequency)
        if delta is None:
            return None
        return Task(
            description=self.description,
            scheduled_time=self.scheduled_time,
            frequency=self.frequency,
            priority=self.priority,
            due_date=date.today() + delta,
        )

    def reset(self) -> None:
        """Re-open a recurring task for its next cycle (no-op for one-offs).

        An in-place alternative to :meth:`mark_complete`'s spawn-a-new-instance
        behavior: instead of creating a follow-up Task, this just flips the same
        task back to pending. Used by :meth:`Scheduler.reset_daily_tasks` for a
        bulk "start a fresh day" reset. Prefer ``mark_complete`` for normal
        completion; use ``reset`` when you want to keep task identity/ids stable.
        """
        if self.frequency is not Frequency.ONCE:
            self.completed = False

    def is_pending(self) -> bool:
        """Return ``True`` if the task still needs to be done."""
        return not self.completed

    def __repr__(self) -> str:
        """Return a concise, unambiguous developer representation.

        Deliberately omits ``pet`` (the back-reference) so printing a Task -
        or a list of them - can't recurse through pet -> tasks -> task.
        """
        return (
            f"Task(id={self.id}, description={self.description!r}, "
            f"due={self.due_date.isoformat()} {self.scheduled_time.strftime('%H:%M')}, "
            f"priority={self.priority.name}, completed={self.completed})"
        )

    def __str__(self) -> str:
        """Return a compact one-line summary of the task."""
        status = "✓" if self.completed else "○"
        return (
            f"{status} {self.scheduled_time.strftime('%H:%M')} "
            f"{self.description} [{self.priority.name.lower()}, "
            f"{self.frequency.value}]"
        )


@dataclass
class Pet:
    """A pet and the care tasks it needs.

    Attributes:
        name: The pet's name.
        species: e.g. ``"dog"``, ``"cat"``.
        breed: e.g. ``"Shiba Inu"``.
        owner: Back-reference to the :class:`Owner`; set by
            :meth:`Owner.add_pet`.
        tasks: Every care task assigned to this pet.
        id: Auto-assigned unique identifier.
    """

    name: str
    species: str
    breed: str = "unknown"
    # Back-reference to the Owner. Excluded from __eq__/__repr__ for the same
    # reason as Task.pet above (breaks the Pet <-> Owner comparison cycle).
    owner: "Owner | None" = field(default=None, compare=False, repr=False)
    tasks: list[Task] = field(default_factory=list)
    id: int = field(default_factory=lambda: next(_pet_ids))

    def add_task(self, task: Task) -> Task:
        """Attach a task to this pet, linking it back via ``task.pet``."""
        task.pet = self
        self.tasks.append(task)
        return task

    def remove_task(self, task: Task) -> None:
        """Detach a task from this pet, if present."""
        if task in self.tasks:
            self.tasks.remove(task)
            task.pet = None

    def pending_tasks(self) -> list[Task]:
        """Return this pet's not-yet-completed tasks."""
        return [t for t in self.tasks if t.is_pending()]

    def completed_tasks(self) -> list[Task]:
        """Return this pet's completed tasks."""
        return [t for t in self.tasks if t.completed]

    def __repr__(self) -> str:
        """Return a concise developer representation.

        Summarizes ``tasks`` as a count (not the full list) and omits the
        ``owner`` back-reference, keeping the output short and recursion-free.
        """
        return (
            f"Pet(id={self.id}, name={self.name!r}, species={self.species!r}, "
            f"breed={self.breed!r}, tasks={len(self.tasks)})"
        )

    def __str__(self) -> str:
        """Return a readable label like ``Name (species, breed)``."""
        return f"{self.name} ({self.species}, {self.breed})"


@dataclass
class Owner:
    """A pet owner who manages one or more pets and their care tasks.

    The Owner is the top-level entry point the UI talks to. It knows about its
    pets; to reason about tasks *across* those pets, hand the owner to a
    :class:`Scheduler`.

    Attributes:
        first_name: Owner's first name.
        last_name: Owner's last name.
        pets: The pets this owner is responsible for.
        id: Auto-assigned unique identifier.
    """

    first_name: str
    last_name: str
    pets: list[Pet] = field(default_factory=list)
    id: int = field(default_factory=lambda: next(_owner_ids))

    @property
    def full_name(self) -> str:
        """Return the owner's first and last name combined."""
        return f"{self.first_name} {self.last_name}"

    def add_pet(self, pet: Pet) -> Pet:
        """Register a pet under this owner, linking it back via ``pet.owner``."""
        if pet not in self.pets:
            pet.owner = self
            self.pets.append(pet)
        return pet

    def get_pet(self, name: str) -> Pet | None:
        """Find a pet by name (case-insensitive); ``None`` if not found."""
        for pet in self.pets:
            if pet.name.lower() == name.lower():
                return pet
        return None

    def all_tasks(self) -> list[Task]:
        """Return every task across all of this owner's pets, flattened."""
        return [task for pet in self.pets for task in pet.tasks]

    def __repr__(self) -> str:
        """Return a concise developer representation (pets shown as a count)."""
        return (
            f"Owner(id={self.id}, name={self.full_name!r}, "
            f"pets={len(self.pets)})"
        )

    def __str__(self) -> str:
        """Return a summary naming the owner and pet count."""
        return f"{self.full_name} (owns {len(self.pets)} pet(s))"


class Scheduler:
    """The 'brain' of PawPal+.

    Given an :class:`Owner`, the Scheduler retrieves and organizes tasks across
    all of that owner's pets. It deliberately holds no task state of its own -
    tasks live on their pets - so it always reflects the current world and can
    be created on demand.

    Prioritization rule used throughout: **most urgent first, and within the
    same urgency, earliest time of day first.** That ordering is what
    :meth:`build_daily_plan` produces.
    """

    def __init__(self, owner: Owner) -> None:
        """Create a scheduler that reads tasks live from ``owner``."""
        self.owner = owner

    # --- retrieval ---------------------------------------------------------

    def all_tasks(self) -> list[Task]:
        """Every task across every pet."""
        return self.owner.all_tasks()

    def pending_tasks(self) -> list[Task]:
        """Only the tasks that still need doing."""
        return [t for t in self.all_tasks() if t.is_pending()]

    def tasks_of_type(self, frequency: Frequency) -> list[Task]:
        """All tasks matching a given recurrence frequency."""
        return [t for t in self.all_tasks() if t.frequency is frequency]

    # --- organization / prioritization ------------------------------------

    @staticmethod
    def _sort_key(task: Task) -> tuple[int, time]:
        """Sort key ordering by highest priority first, then earliest time."""
        return (-int(task.priority), task.scheduled_time)

    def build_daily_plan(self) -> list[Task]:
        """Return pending tasks ordered by priority, then time of day."""
        return sorted(self.pending_tasks(), key=self._sort_key)

    def sort_by_time(self) -> list[Task]:
        """Return all tasks ordered chronologically by time of day.

        Uses ``sorted()`` with a lambda key that renders each task's time as an
        ``"HH:MM"`` string. Because the format is zero-padded 24-hour, plain
        string comparison ("08:00" < "14:00") matches chronological order, so
        no time arithmetic is needed. ``sorted()`` returns a NEW list and leaves
        the underlying task lists untouched.
        """
        return sorted(
            self.all_tasks(),
            key=lambda task: task.scheduled_time.strftime("%H:%M"),
        )

    def filter_tasks(
        self,
        *,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """Return tasks narrowed by completion status and/or pet name.

        Both filters are keyword-only and optional; leave one as ``None`` to
        skip it. When both are supplied a task must satisfy BOTH conditions
        (logical AND). Pet-name matching is case-insensitive.

        Examples:
            scheduler.filter_tasks(completed=False)          # everything pending
            scheduler.filter_tasks(pet_name="Pandora")       # one pet's tasks
            scheduler.filter_tasks(completed=True, pet_name="Jimmy")
        """
        tasks = self.all_tasks()
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        if pet_name is not None:
            tasks = [
                t for t in tasks
                if t.pet is not None and t.pet.name.lower() == pet_name.lower()
            ]
        return tasks

    def next_task(self) -> Task | None:
        """The single most important pending task, or ``None`` if all done."""
        plan = self.build_daily_plan()
        return plan[0] if plan else None

    def complete_task(self, task: Task) -> None:
        """Mark a task complete (delegates to the task itself)."""
        task.mark_complete()

    def reset_daily_tasks(self) -> None:
        """Re-open every recurring task for a fresh day."""
        for task in self.all_tasks():
            task.reset()

    # --- explanation -------------------------------------------------------

    def explain_plan(self) -> str:
        """Return a readable, ordered plan naming the pet for each task."""
        plan = self.build_daily_plan()
        if not plan:
            return "All tasks are complete. 🎉"

        lines = [f"Care plan for {self.owner.full_name}:"]
        for i, task in enumerate(plan, start=1):
            pet_name = task.pet.name if task.pet else "unassigned"
            lines.append(
                f"{i}. [{task.priority.name}] {task.scheduled_time.strftime('%H:%M')} "
                f"- {task.description} (for {pet_name})"
            )
        return "\n".join(lines)


if __name__ == "__main__":
    # Tiny smoke test / usage demo. Run: python3 pawpal_system.py
    jordan = Owner("Jordan", "Lee")
    mochi = jordan.add_pet(Pet("Mochi", "dog", "Shiba Inu"))
    luna = jordan.add_pet(Pet("Luna", "cat", "Tabby"))

    mochi.add_task(Task("Morning walk", time(8, 0), Frequency.DAILY, Priority.HIGH))
    mochi.add_task(Task("Breakfast", time(7, 30), Frequency.DAILY, Priority.HIGH))
    luna.add_task(Task("Give meds", time(9, 0), Frequency.DAILY, Priority.MEDIUM))
    luna.add_task(Task("Vet appointment", time(14, 0), Frequency.ONCE, Priority.HIGH))

    scheduler = Scheduler(jordan)
    print(scheduler.explain_plan())
    print("\nNext up:", scheduler.next_task())
