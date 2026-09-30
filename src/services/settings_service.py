from scheduler.config import CombinedConfig, OptimizerFlags


DEFAULT_LIMIT = 10
DEFAULT_OPTIMIZER_FLAGS = []


def update_settings_from_values(combined_config, limit, optimizer_flags):
    """Validate and apply settings supplied by a non-interactive caller."""
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("Generation limit must be a positive integer.")

    try:
        validated_flags = [OptimizerFlags(flag) for flag in optimizer_flags]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Invalid optimizer flag: {exc}") from exc

    combined_config.limit = limit
    combined_config.optimizer_flags = validated_flags
    return combined_config


def reset_settings_values(combined_config):
    """Restore default settings without CLI output for GUI callers."""
    return update_settings_from_values(
        combined_config, DEFAULT_LIMIT, list(DEFAULT_OPTIMIZER_FLAGS)
    )


def view_settings(combined_config: CombinedConfig):
    """Display the current global scheduler settings."""
    print("\nGLOBAL SETTINGS")
    print(f"Generation limit: {combined_config.limit}")

    if combined_config.optimizer_flags:
        print("Optimizer flags:")
        for flag in combined_config.optimizer_flags:
            print(f"  - {flag.value}")
    else:
        print("Optimizer flags: None")


def modify_settings(combined_config: CombinedConfig):
    """Modify the global scheduler settings."""
    print("\nMODIFY GLOBAL SETTINGS")

    while True:
        try:
            limit = int(
                input(
                    f"Enter generation limit "
                    f"(current: {combined_config.limit}): "
                ).strip()
            )

            if limit <= 0:
                print("Generation limit must be greater than 0.")
                continue

            break

        except ValueError:
            print("Please enter a valid number.")

    print("\nAvailable optimizer flags:")
    for flag in OptimizerFlags:
        print(f"  - {flag.value}")

    flag_input = input(
        "Enter optimizer flags separated by commas "
        "(leave blank for none): "
    ).strip()

    optimizer_flags = []

    if flag_input:
        for flag in flag_input.split(","):
            flag = flag.strip()

            try:
                optimizer_flags.append(OptimizerFlags(flag))
            except ValueError:
                print(f"Invalid optimizer flag: {flag}")
                return

    try:
        combined_config.limit = limit
        combined_config.optimizer_flags = optimizer_flags
    except ValueError as e:
        print(f"Unable to modify settings: {e}")
        return

    print("Global settings modified successfully.")


def reset_settings(combined_config: CombinedConfig):
    """Reset global scheduler settings to their default values."""
    reset_settings_values(combined_config)

    print("Global settings reset successfully.")