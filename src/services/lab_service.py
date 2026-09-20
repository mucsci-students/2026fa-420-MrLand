import re

from scheduler.config import LabConfig

# returns the lab if it exists, else None
def find_lab(labs, name, exclude=None):
    for lab in labs:
        if lab is exclude:
            continue
        if lab.name.lower() == name.lower():
            return lab
    return None

def lab_exists(labs, name, exclude=None):
    return find_lab(labs, name, exclude=exclude) is not None


def get_lab_name(labs, exclude=None):
    while True:
        name = input("Enter Lab Name: ").strip()

        if not name:
            print("Lab Name Cannot Be Blank")
            continue

        if find_lab(labs, name, exclude=exclude) is not None:
            print("Lab Name Exists Already")
            continue

        return name

def get_lab_capacity():
    while True:
        capacity_input = input("Enter Lab Capacity: ").strip()

        try:
            capacity = int(capacity_input)
        except ValueError:
            print("Value Must Be An Integer")
            continue

        if capacity <= 0:
            print("Capacity Must Be Greater Than 0")
            continue

        return capacity

def delete_lab_features(lab):
    while True:
        if not lab.features:
            print("No Features To Delete")
            return
        print("\nCurrent Features:")

        features = list(lab.features)
        for number, feature in enumerate(features, start=1):
            print(f"{number}. {feature}")

        print("Enter Number of Feature To Delete or 'done' to quit")

        choice = input("==> ").strip()

        if choice == 'done':
            break

        try:
            number = int(choice)

            if number < 1 or number > len(features):
                print("Invalid Feature Number.")
                continue

            feature = features[number - 1]
            lab.features.remove(feature)

            print(f"Deleted '{feature}'.")

        except ValueError:
            print("Enter a valid feature number.")

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
        print(f"'{time}' does not match HH:MM-HH:MM")
        return False

    return True

def get_lab_times():
    while True:
        print("Enter n: Unrestricted Availability")
        print("Enter y: Add Available Times")

        choice = input().strip().lower()

        if choice == "n":
            return None

        if choice != "y":
            print("Invalid choice.")
            continue

        break

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
                continue

            ranges.append(time_range)

        if ranges:
            times[day] = ranges

    return times


def add_lab(labs):
    name = get_lab_name(labs)
    capacity = get_lab_capacity()
    features = get_lab_features()
    times = get_lab_times()

    try:
        lab = LabConfig(
            name=name,
            capacity=capacity,
            features=features,
            times=times,
        )

        labs.append(lab)
        print(f"'{name}' Added")

    except Exception as error:
        print(f"Failed To Create Lab: {error}")

def view_labs(labs):
    if not labs:
        print("\nNo Lab Found")
        return

    print("\nLabs")

    for number, lab in enumerate(labs, start=1):
        print(f"\n{number}. {lab.name}")
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

def modify_lab(labs):
    if not labs:
        print("\nNo labs found.")
        return

    view_labs(labs)

    try:
        index = int(input("\nEnter Number Of Lab To Modify: ")) - 1
    except ValueError:
        print("Enter Valid Number.")
        return

    if not 0 <= index < len(labs_members):
        print("Invalid Selection.")
        return

    lab = labs[index]
    old_lab = lab.model_dump()

    print(f"\nModifying lab: {lab.name}")
    print("1. Name")
    print("2. Capacity")
    print("3. Features")
    print("4. Availability")
    print("5. Cancel")

    choice = input("Choose What To Modify: ").strip()

    try:
        if choice == "1":
            lab.name = get_lab_name(labs, exclude=lab)
            print(f"Name Updated to '{lab.name}'")

        elif choice == "2":
            lab.capacity = get_lab_capacity()
            print(f"Capacity Updated to '{lab.capacity}'")

        elif choice == "3":
            print("Enter d: Delete Current Features")
            print("Enter a: Add More Features")

            feature_choice = input().strip().lower()

            if feature_choice == "d":
                delete_lab_features(lab)
                print("Features Updated")
                return

            if feature_choice != "a":
                print("Invalid choice. No changes made.")
                return

            print("Enter New Features. Type 'done' When Finished.")
            new_features = set()

            while True:
                feature = input("Feature: ").strip()

                if feature.lower() == "done":
                    break

                if feature:
                    new_features.add(feature)

            lab.features = lab.features | new_features
            print("Features Updated")

        elif choice == "4":
            lab.times = get_lab_times()
            print("Availability Updated")

        elif choice == "5":
            print("Modification Cancelled.")

        else:
            print("Invalid Option.")

    except Exception as error:
        labs[index] = type(lab).model_validate(old_lab)
        print(f"Update failed: {error}")
        print("Previous valid lab data was restored.")


def delete_lab(labs):
    if not labs:
        print("\nNo Labs Found.")
        return

    view_labs(labs)

    try:
        index = int(input("\nEnter Number of Lab To Delete: ")) - 1
    except ValueError:
        print("Enter Valid Number.")
        return

    if not 0 <= index < len(labs_members):
        print("Invalid Selection.")
        return

    lab = labs[index]

    confirm = input(f"Delete '{lab.name}'? (y/n): ").strip().lower()

    if confirm == "y":
        labs_members.pop(index)
        print(f"Deleted '{lab.name}'.")
    else:
        print("Deletion Cancelled.")