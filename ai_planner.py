from datetime import date, timedelta
from pawpal_system import Task


def shift_time(time_str):
    hour, minute = map(int, time_str.split(":"))
    minute += 30

    if minute >= 60:
        hour += 1
        minute -= 60

    return f"{hour:02d}:{minute:02d}"


def create_care_plan(pet, owner_goal):
    """
    Create recommended care actions based on the pet type and goals
    """
    goal = owner_goal.lower().strip()
    pet_type = pet.breed.lower().strip()
    today = str(date.today())
    recommendations = []

    rules_per_species = {
        "dog": [
            {
                "name": "Morning Walk",
                "description": f"Daily morning walk for {pet.name}",
                "due_date": today,
                "time": "08:00",
                "recurring": "daily"
            },
            {
                "name": "Feed",
                "description": f"Feed {pet.name}",
                "due_date": today,
                "time": "07:30",
                "recurring": "daily"
            }
        ],
        "cat": [
            {
                "name": "Feed",
                "description": f"Feed {pet.name}",
                "due_date": today,
                "time": "08:00",
                "recurring": "daily"
            },
            {
                "name": "Clean Litter Box",
                "description": f"Ensure litter box is clean for {pet.name}",
                "due_date": today,
                "time": "09:00",
                "recurring": "daily"
            }
        ]
    }

    if pet_type in rules_per_species:
        recommendations.extend(rules_per_species[pet_type])
    else:
        recommendations.append({
            "name": "General Wellness Check",
            "description": f"Check health and comfort for {pet.name}",
            "due_date": today,
            "time": "10:00",
            "recurring": "daily"
        })

    if "exercise" in goal or "active" in goal or "play" in goal:
        recommendations.append({
            "name": "Additional Exercise",
            "description": f"More exercise for {pet.name}",
            "due_date": today,
            "time": "16:00",
            "recurring": "daily"
        })

    if "groom" in goal:
        recommendations.append({
            "name": "Grooming",
            "description": f"Groom {pet.name}",
            "due_date": str(date.today() + timedelta(days=2)),
            "time": "14:00",
            "recurring": "weekly"
        })

    if "train" in goal or "training" in goal or "trick" in goal:
        recommendations.append({
            "name": "Training Session",
            "description": f"Practice tricks and training with {pet.name}",
            "due_date": today,
            "time": "17:00",
            "recurring": "daily"
        })

    if "doctor" in goal or "vet" in goal or "sick" in goal or "ill" in goal:
        recommendations.append({
            "name": "Vet Visit",
            "description": f"Schedule a vet check for {pet.name}",
            "due_date": str(date.today() + timedelta(days=1)),
            "time": "11:00",
            "recurring": "once"
        })

    return recommendations


def convert_plan_to_tasks(plan_items):
    tasks = []

    for item in plan_items:
        task = Task(
            description=item["description"],
            time=item["time"],
            frequency=item["recurring"],
            due_date=date.fromisoformat(item["due_date"])
        )
        tasks.append(task)

    return tasks


def validate_recommended_tasks(pet, tasks, existing_tasks=None):
    """
    Validate tasks before adding to system
    """
    if not existing_tasks:
        existing_tasks = []

    approved_tasks = []
    warnings = []
    rejected_tasks = []

    pet_type = pet.breed.lower().strip()

    rules_per_species = {
        "dog": ["walk", "feed", "exercise", "groom", "training", "trick", "vet"],
        "cat": ["feed", "litter", "groom", "training", "trick", "vet"],
    }

    allowed_keywords = rules_per_species.get(
        pet_type,
        ["wellness", "check", "feed", "clean", "training", "vet"]
    )

    existing_task_keys = set()

    for task in existing_tasks:
        task_key = (
            task.description.lower(),
            task.due_date,
            task.time
        )
        existing_task_keys.add(task_key)

    for task in tasks:
        task_key = (
            task.description.lower(),
            task.due_date,
            task.time
        )

        task_description_lower = task.description.lower()

        if not task.description or not task.due_date or not task.time:
            warnings.append(f"Incomplete task rejected for {pet.name}")
            rejected_tasks.append(task)
            continue

        if task_key in existing_task_keys:
            new_time = task.time

            while (task.description.lower(), task.due_date, new_time) in existing_task_keys:
                new_time = shift_time(new_time)

            adjusted_task = Task(
                description=task.description,
                time=new_time,
                frequency=task.frequency,
                due_date=task.due_date
            )

            approved_tasks.append(adjusted_task)
            existing_task_keys.add(
                (adjusted_task.description.lower(), adjusted_task.due_date, adjusted_task.time)
            )

            warnings.append(
                f"Adjusted duplicate task time for {pet.name}: {task.description} moved to {new_time}"
            )
            continue

        if not any(keyword in task_description_lower for keyword in allowed_keywords):
            warnings.append(f"Task may not fit {pet.breed}: {task.description}")
            rejected_tasks.append(task)
            continue

        approved_tasks.append(task)
        existing_task_keys.add(task_key)

    return approved_tasks, warnings, rejected_tasks


def run_ai_planner(pet, owner_goal, existing_tasks=None):
    """
    Create care plan, turn plan items into tasks, validate the tasks, return results
    """
    plan_items = create_care_plan(pet, owner_goal)
    proposed_tasks = convert_plan_to_tasks(plan_items)

    approved_tasks, warnings, rejected_tasks = validate_recommended_tasks(
        pet,
        proposed_tasks,
        existing_tasks
    )

    return {
        "plan_items": plan_items,
        "proposed_tasks": proposed_tasks,
        "approved_tasks": approved_tasks,
        "warnings": warnings,
        "rejected_tasks": rejected_tasks,
    }