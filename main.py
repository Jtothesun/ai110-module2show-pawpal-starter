from datetime import time

from pawpal_system import Priority, Frequency, Task, Pet, Owner, Scheduler

# Build owners, then attach pets via add_pet() so each pet's `owner` back-link
# is wired to the real Owner object (pet.owner is jason, not the string "Jason").
jason = Owner("Jason", "Morales")
jason.add_pet(Pet("Sapphy", "cat", "american shorthair"))
jason.add_pet(Pet("Pandora", "cat", "american shorthair"))
jason.add_pet(Pet("Jimmy", "cat", "american shorthair"))

ariella = Owner("Ariella", "Napoli")
ariella.add_pet(Pet("Svetlana", "cat", "american shorthair"))
ariella.add_pet(Pet("Vivaldi", "dog", "shih tzu"))
ariella.add_pet(Pet("Iseult", "cat", "persian"))

# Add tasks deliberately OUT OF chronological order so the sort has real work
# to do (17:15, then 08:00, then 12:30, ...). If they were already ordered we
# couldn't tell whether sort_by_time() actually did anything.
jason.get_pet("Sapphy").add_task(Task("Walk Sapphy", time(17, 15), Frequency.DAILY, Priority.HIGH))
jason.get_pet("Pandora").add_task(Task("Feed Pandora", time(8, 0), Frequency.DAILY, Priority.HIGH))
jason.get_pet("Jimmy").add_task(Task("Pet Jimmy", time(12, 30), Frequency.DAILY, Priority.HIGH))
jason.get_pet("Pandora").add_task(Task("Meds Pandora", time(6, 45), Frequency.DAILY, Priority.MEDIUM))
jason.get_pet("Jimmy").add_task(Task("Groom Jimmy", time(21, 0), Frequency.WEEKLY, Priority.LOW))

# Mark a couple complete so the completion filter has both states to show.
jason.get_pet("Pandora").tasks[0].mark_complete()   # Feed Pandora
jason.get_pet("Jimmy").tasks[0].mark_complete()      # Pet Jimmy

scheduler = Scheduler(jason)


def show(title, tasks):
    """Print a titled section listing tasks as date time - description (pet, status)."""
    print(title)
    if not tasks:
        print("  (none)")
    for t in tasks:
        status = "done" if t.completed else "pending"
        pet_name = t.pet.name if t.pet else "unassigned"
        print(f"  {t.due_date} {t.scheduled_time:%H:%M} - {t.description} ({pet_name}, {status})")
    print()


# --- Sorting ---------------------------------------------------------------
show("All tasks, sorted by time of day:", scheduler.sort_by_time())

# --- Filtering -------------------------------------------------------------
show("Pending tasks only (completed=False):", scheduler.filter_tasks(completed=False))
show("Completed tasks only (completed=True):", scheduler.filter_tasks(completed=True))
show("Tasks for Pandora (pet_name='Pandora'):", scheduler.filter_tasks(pet_name="Pandora"))
show(
    "Pending tasks for Pandora (both filters, AND):",
    scheduler.filter_tasks(completed=False, pet_name="Pandora"),
)

# --- Compose: filter, then sort -------------------------------------------
pending_by_time = sorted(
    scheduler.filter_tasks(completed=False),
    key=lambda t: t.scheduled_time.strftime("%H:%M"),
)
show("Pending tasks, sorted by time:", pending_by_time)

# --- Recurrence: completing a recurring task spawns the next occurrence -----
print("=" * 60)
print("Recurrence demo (complete a task -> next occurrence appears)")
print("=" * 60)

# Give Sapphy a brand-new DAILY task and complete it. mark_complete() returns
# the follow-up Task it auto-created for tomorrow.
sapphy = jason.get_pet("Sapphy")
brush = sapphy.add_task(Task("Brush Sapphy", time(19, 0), Frequency.DAILY, Priority.MEDIUM))
print(f"Created:   {brush.description} due {brush.due_date} ({brush.frequency.value})")

next_brush = brush.mark_complete()
print(f"Completed: {brush.description} due {brush.due_date} -> completed={brush.completed}")
print(f"Spawned:   {next_brush.description} due {next_brush.due_date}   "
      f"<- advanced by timedelta(days=1)")

# A ONCE task closes with no follow-up (mark_complete returns None).
vet = sapphy.add_task(Task("Vet visit", time(15, 0), Frequency.ONCE, Priority.HIGH))
print(f"\nOne-off:   {vet.description} due {vet.due_date} ({vet.frequency.value})")
print(f"Spawned:   {vet.mark_complete()}   <- ONCE tasks do not recur")

# Double-completion is a no-op: no duplicate is spawned.
print(f"\nRe-completing the already-done daily task returns: {brush.mark_complete()}")
