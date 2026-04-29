from dataclasses import dataclass, field
from typing import List
from datetime import date, timedelta

@dataclass
class Task:
    description: str
    time: str          # "HH:MM" format, e.g. "08:00"
    frequency: str     # e.g. "daily", "weekly"
    completed: bool = False
    due_date: date = field(default_factory=date.today)

    def set_complete(self) -> None:
        """Mark this task as completed."""
        self.completed = True

    def __str__(self) -> str:
        """Return a human-readable summary of the task."""
        status = "Done" if self.completed else "Pending"
        return f"[{status}] {self.description} at {self.time} ({self.frequency}) — due {self.due_date}"
    
    def __post_init__(self):
        if not self.description.strip():
            raise ValueError("Task description cannot be empty")

        try:
            hour, minute = map(int, self.time.split(":"))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError
        except:
            raise ValueError(f"Invalid time format: {self.time}")

@dataclass
class Pet:
    name: str
    age: int
    breed: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet's task list."""
        self.tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove an existing task from this pet's task list."""
        self.tasks.remove(task)

    def show_tasks(self) -> List[Task]:
        """Return all tasks assigned to this pet."""
        return self.tasks

    def __str__(self) -> str:
        """Return a human-readable summary of the pet."""
        return f"{self.name} ({self.breed}, age {self.age})"

class Owner:
    def __init__(self, name: str):
        self.name = name
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to this owner's pet list."""
        self.pets.append(pet)

    def get_pets(self) -> List[Pet]:
        """Return all pets belonging to this owner."""
        return self.pets

    def get_tasks(self) -> List[Task]:
        """Aggregates all tasks across every pet this owner has."""
        return [task for pet in self.pets for task in pet.tasks]

    def __str__(self) -> str:
        """Return a human-readable summary of the owner."""
        return f"Owner: {self.name} ({len(self.pets)} pet(s))"

class Scheduler:
    def __init__(self, owner: Owner):
        self.owner = owner

    def show_todays_tasks(self) -> List[Task]:
        """Returns all incomplete tasks for today across every pet."""
        return [task for task in self.owner.get_tasks() if not task.completed]

    def show_schedule(self) -> None:
        """Prints a formatted, time-sorted schedule of today's pending tasks."""
        tasks = self.sort_by_time(self.show_todays_tasks())
        if not tasks:
            print(f"No pending tasks for {self.owner.name}'s pets today.")
            return

        print(f"--- Today's Schedule for {self.owner.name} ---")
        for pet in self.owner.get_pets():
            pending = [t for t in pet.tasks if not t.completed]
            if pending:
                print(f"\n  {pet.name}:")
                for task in self.sort_by_time(pending):
                    print(f"    {task}")

    def sort_by_time(self, tasks):
        """Sort tasks by time (HH:MM format) in ascending order."""
        return sorted(tasks, key=lambda task: task.time)
        
    def complete_task(self, pet: Pet, task: Task) -> Task | None:
        """Mark a task complete and schedule the next occurrence if recurring.

        Uses timedelta to calculate the next due date:
          - daily  → due_date + 1 day
          - weekly → due_date + 7 days

        Returns the newly created Task, or None if the frequency is not recurring.
        """
        task.set_complete()

        intervals = {"daily": timedelta(days=1), "weekly": timedelta(weeks=1)}
        delta = intervals.get(task.frequency)
        if delta is None:
            return None

        next_task = Task(
            description=task.description,
            time=task.time,
            frequency=task.frequency,
            due_date=task.due_date + delta,
        )
        pet.add_task(next_task)
        return next_task

    def find_conflicts(self) -> dict:
        """Find tasks that share the same due_date and time across all pets.

        Returns a dict where each key is a (due_date, time) slot and each
        value is the list of tasks that clash in that slot. Only slots with
        two or more tasks are included.
        """
        slots = {}
        for task in self.owner.get_tasks():
            key = (task.due_date, task.time)
            if key not in slots:
                slots[key] = []
            slots[key].append(task)

        return {key: tasks for key, tasks in slots.items() if len(tasks) > 1}

    def filter_tasks(self, pet_name=None, completed=None):
        """Filter tasks by pet name and/or completion status."""
        if pet_name is not None:
            matched = next((p for p in self.owner.get_pets() if p.name.lower() == pet_name.lower()), None)
            tasks = matched.tasks if matched else []
        else:
            tasks = self.owner.get_tasks()

        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]

        return tasks