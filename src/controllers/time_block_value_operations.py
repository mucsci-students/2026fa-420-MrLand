"""Validated, non-interactive time-block operations."""

from scheduler.config import TimeBlock

VALID_DAYS = {"MON", "TUE", "WED", "THU", "FRI"}


def _build_time_block(day, start, spacing, end):
    day = day.strip().upper()
    if day not in VALID_DAYS:
        raise ValueError("Day must be MON, TUE, WED, THU, or FRI.")
    if isinstance(spacing, bool) or not isinstance(spacing, int) or spacing <= 0:
        raise ValueError("Spacing must be a positive integer.")
    return day, TimeBlock(start=start, spacing=spacing, end=end)


def add_time_block_from_values(times, day, start, spacing, end):
    """Validate and append a time block to a weekday's block list."""
    day, block = _build_time_block(day, start, spacing, end)
    times.setdefault(day, []).append(block)
    return block


def update_time_block_from_values(times, existing_day, existing_block, day, start, spacing, end):
    """Replace a block, optionally moving it to another weekday."""
    existing_day = existing_day.strip().upper()
    try:
        blocks = times[existing_day]
        index = next(i for i, block in enumerate(blocks) if block is existing_block)
    except (KeyError, StopIteration) as exc:
        raise ValueError("Time block no longer exists.") from exc

    day, updated_block = _build_time_block(day, start, spacing, end)
    if day == existing_day:
        blocks[index] = updated_block
    else:
        blocks.pop(index)
        times.setdefault(day, []).append(updated_block)
    return updated_block


def delete_time_block_from_values(times, day, block_to_delete):
    """Remove and return a selected time block by object identity."""
    day = day.strip().upper()
    try:
        blocks = times[day]
        index = next(i for i, block in enumerate(blocks) if block is block_to_delete)
    except (KeyError, StopIteration) as exc:
        raise ValueError("Time block no longer exists.") from exc
    return blocks.pop(index)
