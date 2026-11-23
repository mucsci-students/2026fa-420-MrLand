"""Validated, non-interactive lab operations used by GUI controllers."""

from scheduler.config import LabConfig


def find_lab(labs, name, exclude=None):
    for lab in labs:
        if lab is exclude:
            continue
        if lab.name.lower() == name.lower():
            return lab
    return None


def lab_exists(labs, name, exclude=None):
    return find_lab(labs, name, exclude=exclude) is not None


def _build_lab_from_values(labs, name, capacity, features, times, exclude=None):
    name = name.strip()
    if not name:
        raise ValueError("Lab name cannot be blank.")
    if lab_exists(labs, name, exclude=exclude):
        raise ValueError("Lab name already exists.")
    if isinstance(capacity, bool) or not isinstance(capacity, int) or capacity <= 0:
        raise ValueError("Capacity must be greater than 0.")

    return LabConfig(
        name=name,
        capacity=capacity,
        features=set(features or []),
        times=times,
    )


def add_lab_from_values(labs, name, capacity, features, times):
    """Validate and append lab values supplied by a non-interactive caller."""
    lab = _build_lab_from_values(labs, name, capacity, features, times)
    labs.append(lab)
    return lab


def update_lab_from_values(labs, existing_lab, name, capacity, features, times):
    """Replace a lab after validating all replacement values."""
    if not any(lab is existing_lab for lab in labs):
        raise ValueError("Lab no longer exists.")

    updated_lab = _build_lab_from_values(
        labs, name, capacity, features, times, exclude=existing_lab
    )
    existing_lab.name = updated_lab.name
    existing_lab.capacity = updated_lab.capacity
    existing_lab.features = updated_lab.features
    existing_lab.times = updated_lab.times
    return existing_lab


def delete_lab_from_values(labs, lab_to_delete):
    """Remove and return a selected lab by object identity."""
    try:
        index = next(i for i, lab in enumerate(labs) if lab is lab_to_delete)
    except StopIteration as exc:
        raise ValueError("Lab no longer exists.") from exc
    return labs.pop(index)
