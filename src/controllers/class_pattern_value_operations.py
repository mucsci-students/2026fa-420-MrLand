"""Validated, non-interactive class-pattern operations."""

from scheduler.config import ClassPattern, Meeting


def _build_class_pattern_from_values(
    patterns, credits, meetings, disabled, start_time, exclude=None
):
    if isinstance(credits, bool) or not isinstance(credits, int) or credits <= 0:
        raise ValueError("Credits must be a positive integer.")

    validated_meetings = [
        meeting if isinstance(meeting, Meeting) else Meeting(**meeting) for meeting in meetings
    ]
    start_time = start_time.strip() if start_time and start_time.strip() else None
    return ClassPattern(
        credits=credits,
        meetings=validated_meetings,
        disabled=disabled,
        start_time=start_time,
    )


def add_class_pattern_from_values(patterns, credits, meetings, disabled=False, start_time=None):
    """Validate and append a class pattern supplied by a non-interactive caller."""
    pattern = _build_class_pattern_from_values(patterns, credits, meetings, disabled, start_time)
    patterns.append(pattern)
    return pattern


def update_class_pattern_from_values(
    patterns, existing_pattern, credits, meetings, disabled=False, start_time=None
):
    """Replace a class pattern after validating all replacement values."""
    try:
        index = next(i for i, pattern in enumerate(patterns) if pattern is existing_pattern)
    except StopIteration as exc:
        raise ValueError("Class pattern no longer exists.") from exc

    updated_pattern = _build_class_pattern_from_values(
        patterns,
        credits,
        meetings,
        disabled,
        start_time,
        exclude=existing_pattern,
    )
    patterns[index] = updated_pattern
    return updated_pattern


def delete_class_pattern_from_values(patterns, pattern_to_delete):
    """Remove and return a selected class pattern by object identity."""
    try:
        index = next(i for i, pattern in enumerate(patterns) if pattern is pattern_to_delete)
    except StopIteration as exc:
        raise ValueError("Class pattern no longer exists.") from exc
    return patterns.pop(index)
