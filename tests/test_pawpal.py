"""Basic tests for the PawPal+ domain model.

Run from the starter directory with:  python -m pytest
"""

from datetime import time

from pawpal_system import Task, Pet, Frequency, Priority


def test_mark_complete_changes_status():
    """Task Completion: mark_complete() flips a task from pending to done."""
    task = Task("Feed Pandora", time(8, 0), Frequency.DAILY, Priority.HIGH)

    # A brand-new task starts out not completed.
    assert task.completed is False

    task.mark_complete()

    # After marking complete, the status flag should be True.
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    """Task Addition: adding a task to a Pet grows that pet's task list."""
    pet = Pet("Pandora", "cat", "american shorthair")
    assert len(pet.tasks) == 0

    pet.add_task(Task("Morning walk", time(9, 0), Frequency.DAILY, Priority.MEDIUM))

    assert len(pet.tasks) == 1
