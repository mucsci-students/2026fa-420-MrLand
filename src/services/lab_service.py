from scheduler.config import LabConfig
from models.lab import find_lab

labs = []

def get_lab_times():
    choice = input().strip().lower()

    if choice == "n":
        return None

    if choice != "y":
        print("Invalid choice. Using unrestricted availability.")
        return None

    times = {}

    days = ["MON", "TUE", "WED", "THU", "FRI"]

    for day in days:
        ranges = []

        print(f"\nAvailability for {day}")
        print("Enter 'done' when finished with this day.")

        while True:
            time_range = input("Enter time range (HH:MM-HH:MM): ").strip()

            if time_range.lower() == "done":
                break

            if time_range:
                ranges.append(time_range)

        if ranges:
            times[day] = ranges

    return times


def add_lab():
    print("\nAdd New Lab")

    name = input("Enter Lab Name: ").strip()

    if not name:
        print("Lab Name Cannot Be Blank")

    if find_lab(labs, name) is not None:
        print("Lab Name Exists Already")
        return

    while True:
        capacity_input = input("Enter Lab Capacity: ").strip()
        while (capacity < 1):
            print("Capacity must be greater than 0")
            capacity_input = input("Enter Lab Capacity: ").strip()
            


            capacity = int(capacity_input)
            if capacity <= 0:
                print("Capacity must be greater than 0")
                continue

        

        features = set()

        print("\nEnter Lab Features")
        print("Type 'done' When Finished")

        while True:
            feature = input("Feature: ").strip()

            if feature.lower() == "done":
                break

            if feature: 
                features.add(feature)

        times = get_lab_times()

        try: 
            lab = LabConfig(
                name = name,
                capacity = capacity,
                features = features,
                times = times,
            )

            labs.append(lab)
            print(f"'{name}' Added")

        except Exception as error:
            print(f"Failed To Create Lab: {error}")

def view_labs():
    if not labs:
        print("\nNo Lab Found")
        return

    print("\nLabs")

    for i, lab in enumerate(labs, start = 1):
        print(f"\n{i}. {lab.name}")
        print(f"Capacity: {lab.capacity}")

        if lab.features:
            print(f"Features: {', '.join(sorted(lab.features))}")
        else:
            print("Features: None")

        if lab.times is None:
            print("Availability: Unrestricted")
        else:
            print("Availability: ")

            for day, ranges in lab.times.items():
                print(f" {day}: {ranges}")

def modify_lab():
    if not labs:
        print("\nNo labs found.")
        return

    view_labs()

    try:
        index = int(
            input("\nEnter Number Of Lab To Modify: ")
        ) - 1
    except ValueError:
        print("Enter Valid Number.")
        return

    if not 0 <= index < len(labs):
        print("Invalid Selection.")
        return

    lab = labs[index]

    print(f"\nModifying lab: {lab.name}")

    print("1. Name")
    print("2. Capacity")
    print("3. Features")
    print("4. Availability")
    print("5. Cancel")

    choice = input("Choose What To Modify: ").strip()

    if choice == "1":
        new_name = input("Enter New Name: ").strip()

        if not new_name:
            print("Name Cannot Be Blank.")
            return

        existing = find_lab(labs, new_name)

        if existing is not None and existing is not lab:
            print("Lab Name Exists Already.")
            return
        
    elif choice == "2":
        try:
            new_capacity = int(
                input("Enter New Capacity: ")
            )

            if new_capacity <= 0:
                print("Capacity Must Be Greater Than 0.")
                return

        except ValueError:
            print("Enter Valid Number")

    elif choice == "3":
        new_features = set()

        print("Enter New Features. Type 'done' When Finished.")

        while True:
            feature = input("Feature: ").strip()

            if feature.lower() == "done":
                break

            if feature:
                new_features.add(feature)

    elif choice == "4":
        new_times = get_lab_times()

    elif choice == "5":
        print("Modification Cancelled.")

    else:
        print("Invalid Option.")


def delete_lab():
    if not labs:
        print("\nNo Labs Found.")
        return

    view_labs()

    try:
        index = int(
            input("\nEnter Number of Lab To Delete: ")
        ) - 1
    except ValueError:
        print("Enter Valid Number.")
        return

    if not 0 <= index < len(labs):
        print("Invalid Selection.")
        return

    lab = labs[index]

    confirm = input(
        f"Delete '{lab.name}'? (y/n): "
    ).strip().lower()

    if confirm == "y":
        labs.pop(index)
        print(f"Deleted '{lab.name}'.")
    else:
        print("Deletion Cancelled.")


        
