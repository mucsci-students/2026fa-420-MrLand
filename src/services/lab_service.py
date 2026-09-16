from scheduler.config import LabConfig
import re

labs_members = []

# returns the lab if exists
def find_lab(labs, name):
    for lab in labs:
        if lab.name == name:
            return lab
        return None
    
def lab_exists(labs, name):
    return find_lab(labs, name) is not None


def get_lab_name():
    name = input("Enter Lab Name: ").strip().lower()

    if not name:
        print("Lab Name Cannot Be Blank")
        return get_lab_name()

    if find_lab(labs_members, name) is not None:
        print("Lab Name Exists Already")
        return get_lab_name()

    return name

def get_lab_capacity():
    capacity_input = input("Enter Lab Capacity: ").strip()

    try:
        capacity = int(capacity_input)

        if capacity <= 0:
            print("Capacity Must Be Greater Than 0")
            return get_lab_capacity()
        return capacity
    except ValueError:
        print("Value Must Be An Integer")
        return get_lab_capacity()

def get_lab_features():
    features = set()
    print("\nEnter Lab Features")
    print("Type 'done' When Finished")

    while True:
        feature = input("Feature: ").strip()
        
        if feature.lower() == "done":
            break
        
        if feature: 
            features.add(feature)

    return features

def validate_time_range(time):
    pattern = r"^([0-1][0-9]|2[0-3]):[0-5][0-9]-([0-1][0-9]|2[0-3]):[0-5][0-9]$"

    if not re.match(pattern, time):
        print(ValueError(f"'{time}' does not match HH:MM-HH:MM"))
        return get_lab_times()
        

    return True

def get_lab_times():
    print("Enter n: Unrestricted Availability")
    print("Enter y: Add Available Times")

    choice = input().strip().lower()

    if choice == "n".lower():
        return None

    if choice != "y".lower():
        print("Invalid choice.")
        return get_lab_times()

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

            if not validate_time_range(time_range):
                return get_lab_times()

            if time_range:
                ranges.append(time_range)

        if ranges:
            times[day] = ranges

    return times


def add_lab():
    name = get_lab_name()
    capacity = get_lab_capacity()
    features = get_lab_features()
    times = get_lab_times()

    try: 
        lab = LabConfig(
            name = name,
            capacity = capacity,
            features = features,
            times = times,
        )

        labs_members.append(lab)
        print(f"'{name}' Added")

    except Exception as error:
        print(f"Failed To Create Lab: {error}")

def view_labs():
    if not labs_members:
        print("\nNo Lab Found")
        return

    print("\nLabs")

    for i, lab in enumerate(labs_members, start = 1):
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
    if not labs_members:
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

    if not 0 <= index < len(labs_members):
        print("Invalid Selection.")
        return

    lab = labs_members[index]

    print(f"\nModifying lab: {lab.name}")

    print("1. Name")
    print("2. Capacity")
    print("3. Features")
    print("4. Availability")
    print("5. Cancel")

    choice = input("Choose What To Modify: ").strip()

    if choice == "1":
        new_name = get_lab_name()

        lab.name = new_name
        print(f"Name Updated to '{lab.name}'")
        
    elif choice == "2":
        new_capacity = get_lab_capacity()
        lab.capacity = new_capacity
        print(f"Capacity Updated to '{lab.capacity}'")

    elif choice == "3":
        new_features = set()

        print("Enter New Features. Type 'done' When Finished.")

        while True:
            feature = input("Feature: ").strip()

            if feature.lower() == "done":
                break

            if feature:
                new_features.add(feature)

        lab.features = new_features
        print("Features Updated")

    elif choice == "4":
        new_times = get_lab_times()
        lab.times = new_times
        print("Availability Updated")

    elif choice == "5":
        print("Modification Cancelled.")

    else:
        print("Invalid Option.")


def delete_lab():
    if not labs_members:
        print("\nNo Labs Found.")
        return

    view_labs()

    # test for validity
    try:
        index = int(
            input("\nEnter Number of Lab To Delete: ")
        ) - 1
    except ValueError:
        print("Enter Valid Number.")
        return

    if not 0 <= index < len(labs_members):
        print("Invalid Selection.")
        return

    # delete confirmation 

    lab = labs_members[index]

    confirm = input(
        f"Delete '{lab.name}'? (y/n): "
    ).strip().lower()

    if confirm == "y":
        labs_members.pop(index)
        print(f"Deleted '{lab.name}'.")
    else:
        print("Deletion Cancelled.")


        
