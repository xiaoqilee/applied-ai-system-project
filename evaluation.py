from pawpal_system import Owner, Pet, Task
from ai_planner import run_ai_planner

def test_ai_planner():
    owner = Owner("Test")
    pet = Pet("Beatrice", 3, "Dog")
    owner.add_pet(pet)

    # Normal scenario
    result = run_ai_planner(pet, "exercise")

    if result["approved_tasks"]:
        print("Valid tasks")
    else:
        print("Failed to generate tasks")

    # Duplicates
    pet.add_task(Task("Feed Buddy", "08:00", "daily"))
    result = run_ai_planner(pet, "feed")

    if result["warnings"]:
        print("Duplicates were deteced and adjusted accordingly")
    else:
        print("Duplicate handling failed")

if __name__ == "__main__":
    test_ai_planner()