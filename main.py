from datetime import time

from pawpal_system import Priority, Frequency, Task, Pet, Owner, Scheduler

jason = Owner("Jason", "Morales", [Pet("Sapphy", "cat", "american shorthair", "Jason"), Pet("Pandora", "cat", "american shorthair", "Jason"), Pet("Jimmy", "cat", "american shorthair", "Jason")])
ariella = Owner("Ariella", "Napoli", [Pet("Svetlana", "cat", "american shorthair", "Ariella"), Pet("Vivaldi", "dog", "shih tzu", "Ariella"), Pet("Iseult", "cat", "persian", "Ariella")])


jason.get_pet("Pandora").add_task(Task("Feed Pandora", time(8, 0), Frequency.DAILY, Priority.HIGH))
jason.get_pet("Jimmy").add_task(Task("Pet Jimmy", time(12, 30), Frequency.DAILY, Priority.HIGH))
jason.get_pet("Sapphy").add_task(Task("Walk Sapphy", time(17, 15), Frequency.DAILY, Priority.HIGH))


print(Scheduler(jason).explain_plan())
print()
print(Scheduler(ariella).explain_plan())

