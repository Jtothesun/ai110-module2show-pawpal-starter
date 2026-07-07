"""PawPal+ domain model.

This module defines the core objects for PawPal+, a smart pet care management
system. The classes here mirror the UML class diagram in ``diagrams/pawPal.mmd``.

Design notes (worth reading before you implement the method bodies):

* We use :mod:`dataclasses` so that each class reads like a clean data
  definition. ``@dataclass`` auto-generates ``__init__``, ``__repr__``, and
  ``__eq__`` from the annotated fields, which keeps the boilerplate out of your
  way and lets the *behavior* (the methods) stand out.
* Relationships are bidirectional in the diagram (an ``Owner`` knows its
  ``Pet`` objects, a ``Pet`` knows its ``Owner``, a ``Task`` knows its
  ``Pet``). Bidirectional links are convenient but they can drift out of sync,
  so the methods that create links (e.g. :meth:`Owner.add_pet`) are the right
  place to keep both sides consistent.
* Method bodies are intentionally left unimplemented. Each raises
  ``NotImplementedError`` and carries a docstring describing the contract you
  should fulfill. Replace the ``raise`` with your logic as you build the system.

Mutable defaults (``pets``, ``tasks``) MUST use ``field(default_factory=list)``.
Writing ``pets: list = []`` would share ONE list across every Owner instance —
a classic Python footgun that dataclasses explicitly guard against.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class TaskType(Enum):
    """The category of a pet care task.

    Using an ``Enum`` (instead of raw strings like ``"walk"``) gives you
    autocomplete, guards against typos, and makes it trivial to branch on the
    task category in your scheduling logic.
    """

    FEEDING = "feeding"
    WALK = "walk"
    MEDICATION = "medication"
    APPOINTMENT = "appointment"
    GROOMING = "grooming"
    TRAINING = "training"


@dataclass
class Task:
    """A single, schedulable pet care task (e.g. "8am walk", "give meds").

    Attributes:
        id: Stable unique identifier for the task.
        title: Human-readable label shown in the UI.
        type: The :class:`TaskType` category, used for grouping/prioritizing.
        due_date: When the task should happen.
        priority: Higher number == more urgent. Your scheduler sorts on this.
        completed: Whether the task has been carried out.
        pet: The :class:`Pet` this task belongs to (``None`` until assigned).
    """

    id: int
    title: str
    type: TaskType
    due_date: datetime
    priority: int = 0
    completed: bool = False
    pet: "Pet | None" = None

    def mark_complete(self) -> None:
        """Mark this task as done.

        Contract: set :attr:`completed` to ``True``. Consider recording a
        completion timestamp if you later want a history view.
        """
        raise NotImplementedError

    def reschedule(self, new_date: datetime) -> None:
        """Move this task to a new due date.

        Args:
            new_date: The new :class:`~datetime.datetime` for :attr:`due_date`.
        """
        raise NotImplementedError

    def is_overdue(self) -> bool:
        """Return ``True`` if the task is past due and still not completed.

        Hint: compare :attr:`due_date` against ``datetime.now()`` and be sure
        an already-completed task is never reported as overdue.
        """
        raise NotImplementedError


@dataclass
class Pet:
    """A pet cared for by an :class:`Owner`.

    The action methods (:meth:`eat`, :meth:`walk`, ...) represent things the
    pet *does*. A clean way to connect them to the scheduling model is to have
    each action locate and complete the matching outstanding :class:`Task`.

    Attributes:
        name: The pet's name.
        species: e.g. ``"dog"``, ``"cat"``.
        breed: e.g. ``"Shiba Inu"``.
        owner: The :class:`Owner` (``None`` until the pet is added to one).
        tasks: Care tasks assigned to this pet.
    """

    name: str
    species: str
    breed: str
    owner: "Owner | None" = None
    tasks: list[Task] = field(default_factory=list)

    def eat(self) -> None:
        """Record a feeding (e.g. complete the next FEEDING task)."""
        raise NotImplementedError

    def walk(self) -> None:
        """Record a walk (e.g. complete the next WALK task)."""
        raise NotImplementedError

    def take_meds(self) -> None:
        """Record that medication was administered."""
        raise NotImplementedError

    def train(self) -> None:
        """Record a training session."""
        raise NotImplementedError

    def groom(self) -> None:
        """Record a grooming session."""
        raise NotImplementedError


@dataclass
class Owner:
    """A pet owner who manages one or more :class:`Pet` objects and their tasks.

    Attributes:
        id: Stable unique identifier for the owner.
        first_name: Owner's first name.
        last_name: Owner's last name.
        pets: The pets this owner is responsible for.
    """

    id: int
    first_name: str
    last_name: str
    pets: list[Pet] = field(default_factory=list)

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner.

        Contract: append ``pet`` to :attr:`pets` AND set ``pet.owner`` to
        ``self`` so both sides of the relationship stay in sync. Consider
        guarding against adding the same pet twice.
        """
        raise NotImplementedError

    def schedule_task(self, task: Task) -> None:
        """Assign a care task to one of this owner's pets.

        Contract: attach ``task`` to the appropriate :class:`Pet` (append to
        ``pet.tasks`` and set ``task.pet``). This is the entry point the
        Streamlit UI will call, so validate that ``task.pet`` is a pet this
        owner actually owns.
        """
        raise NotImplementedError
