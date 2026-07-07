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
from datetime import time
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


@dataclass
class Task:
    """A single pet care activity, e.g. "Morning walk at 08:00, daily".

    Attributes:
        description: Human-readable label shown in the UI.
        scheduled_time: The time of day the task should happen.
        frequency: How often the task recurs (see :class:`Frequency`).
        priority: How urgent the task is (see :class:`Priority`).
        completed: Whether the task has been carried out for the current cycle.
        pet: Back-reference to the owning :class:`Pet`. Set automatically by
            :meth:`Pet.add_task`; leave it as ``None`` when constructing.
        id: Auto-assigned unique identifier.
    """

    description: str
    scheduled_time: time
    frequency: Frequency = Frequency.DAILY
    priority: Priority = Priority.MEDIUM
    completed: bool = False
    pet: "Pet | None" = None
    id: int = field(default_factory=lambda: next(_task_ids))

    def mark_complete(self) -> None:
        """Mark this task as done for the current cycle."""
        self.completed = True

    def reset(self) -> None:
        """Re-open the task for its next cycle.

        Recurring tasks (daily/weekly) should be reset at the start of each new
        period so they show up as pending again. A one-off task normally stays
        completed, so this is a no-op for :attr:`Frequency.ONCE`.
        """
        if self.frequency is not Frequency.ONCE:
            self.completed = False

    def is_pending(self) -> bool:
        """Return ``True`` if the task still needs to be done."""
        return not self.completed

    def __str__(self) -> str:
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
    owner: "Owner | None" = None
    tasks: list[Task] = field(default_factory=list)
    id: int = field(default_factory=lambda: next(_pet_ids))

    def add_task(self, task: Task) -> Task:
        """Attach a care task to this pet.

        Keeps both sides of the relationship consistent by setting
        ``task.pet`` to ``self``. Returns the task so callers can chain or keep
        a reference.
        """
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

    def __str__(self) -> str:
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
        return f"{self.first_name} {self.last_name}"

    def add_pet(self, pet: Pet) -> Pet:
        """Register a pet under this owner.

        Sets ``pet.owner`` to ``self`` so the relationship is consistent in
        both directions, and guards against adding the same pet twice.
        """
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

    def __str__(self) -> str:
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
        """Sort key: higher priority first, then earlier time first.

        Priority is negated because Python sorts ascending, and we want the
        HIGH (largest) priority at the front of the list.
        """
        return (-int(task.priority), task.scheduled_time)

    def build_daily_plan(self) -> list[Task]:
        """Return today's pending tasks ordered by priority, then time.

        This is the primary method the UI's "Generate schedule" button should
        call. It answers: *what should this owner do next, and in what order?*
        """
        return sorted(self.pending_tasks(), key=self._sort_key)

    def next_task(self) -> Task | None:
        """The single most important pending task, or ``None`` if all done."""
        plan = self.build_daily_plan()
        return plan[0] if plan else None

    def complete_task(self, task: Task) -> None:
        """Mark a task complete (delegates to the task itself)."""
        task.mark_complete()

    def reset_daily_tasks(self) -> None:
        """Re-open recurring tasks for a fresh day.

        Call this at the start of a new day so daily/weekly tasks reappear in
        the plan while one-off tasks stay done.
        """
        for task in self.all_tasks():
            task.reset()

    # --- explanation -------------------------------------------------------

    def explain_plan(self) -> str:
        """Return a human-readable, ordered plan with the pet for each task.

        Explaining *why* each task is placed where it is makes the scheduler's
        decisions transparent - useful both for the UI and for debugging.
        """
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
