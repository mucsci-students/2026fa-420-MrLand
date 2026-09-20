from scheduler.config import CombinedConfig, OptimizerFlags


DEFAULT_LIMIT = 10
DEFAULT_OPTIMIZER_FLAGS = []


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
    combined_config.limit = DEFAULT_LIMIT
    combined_config.optimizer_flags = []

    print("Global settings reset successfully.")