# 2026fa-420-MrLand
## CMSC 420-f26

---

## Contributors
- Nicoletta Beltrante
- Adrian Olweiler
- Renee Watts
- Logan Kaufman
- Dylan Groff
- Micah Schafer

---

## Overview
This project is a schedule-planning application for creating and managing course configurations, generating schedules, and viewing generated results. The current interface is a NiceGUI web app with three main sections: configuration editing, schedule generation, and schedule viewing.

---

## Features

- **Configuration Editor**
  - Create and load scheduling configurations
  - Manage courses, faculty, rooms, labs, and global settings
  - Edit scheduling constraints and configuration data

- **Schedule Generation**
  - Select a saved configuration
  - Review configured generation limits and optimizer settings
  - Apply temporary overrides for a single generation run
  - Generate schedules from the current configuration
  - Save generated schedules as JSON or CSV

- **Schedule Viewer**
  - Load generated schedules from disk
  - Review schedule details and exported results

- **Domain Management**
  - Add, modify, view, and delete faculty, courses, rooms, labs, class patterns, and time blocks
  - Track conflicts and scheduling constraints

- **JSON-based Persistence**
  - Store scheduler data in configuration files under the project config directories
- **Whole-configuration validation**
  - Validate edits against the published [combined configuration JSON Schema](https://raw.githubusercontent.com/mucsci/scheduler/main/fern/docs/assets/combined-config.schema.json) and scheduler model rules
  - Preserve incomplete new drafts until valid; reject edits that would invalidate an already-valid configuration

---

## Project Structure
```text
.
├── LICENSE
├── README.md
├── pytest.ini
├── pyproject.toml
├── uv.lock
├── src
│   ├── __init__.py
│   ├── configs/
│   │   ├── example_config.json
│   │   └── ...
│   ├── schemas/
│   │   └── combined-config.schema.json
│   ├── schedules/
│   │   └── ...
│   ├── controllers/
│   │   ├── configuration_controller.py
│   │   ├── course_operations_controller.py
│   │   ├── faculty_operations_controller.py
│   │   ├── lab_operations_controller.py
│   │   ├── room_operations_controller.py
│   │   ├── class_pattern_operations_controller.py
│   │   ├── time_block_operations_controller.py
│   │   ├── settings_operations_controller.py
│   │   ├── schedule_generator_controller.py
│   │   ├── schedule_controller.py
│   │   ├── run_scheduler_controller.py
│   │   └── ...
│   ├── models/
│   │   ├── configuration.py
│   │   ├── configuration_model.py
│   │   ├── configuration_repository.py
│   │   ├── schedule_generator_model.py
│   │   └── ...
│   ├── views/
│   │   ├── common.py
│   │   ├── configuration_editor.py
│   │   ├── legacy_schedule.py
│   │   ├── navmenu.py
│   │   ├── gui.py
│   │   ├── schedule_generator.py
│   │   ├── schedule_viewer.py
│   │   └── ...
├── tests/
│   ├── test_course.py
│   ├── test_faculty.py
│   ├── test_labs.py
│   ├── test_rooms.py
│   ├── test_class_patterns.py
│   ├── test_time_blocks.py
│   ├── tests_conflicts.py
│   ├── test_run_scheduler.py
│   └── ...
└── .venv/
```

Application implementations are organized into MVC packages. Configuration
validation and persistence live in `models`, domain actions in `controllers`,
and user interfaces in `views`. The former services implementations have been
moved into those MVC packages. Use the `mrland-cli` and `mrland-gui` project
commands to launch the respective interfaces.

---

## Prerequisites
1. **Python 3.12 or newer**
   - Check with `python --version`
   - Download from [python.org](https://www.python.org/downloads/)
2. **Git**
   - Check with `git --version`
   - Download from [Git](https://github.com/git-guides/install-git)
3. **uv**
   - Check with `uv --version`
   - Download instructions at [uv](https://docs.astral.sh/uv/)

---

## Getting Started
1. Clone the repository:
```bash
git clone https://github.com/mucsci-students/2026fa-420-MrLand.git
cd 2026fa-420-MrLand
```

2. Launch the GUI or CLI from the project directory. `uv run` creates and
   synchronizes the environment from `pyproject.toml`, installing dependencies
   if needed.

   Start the GUI:
   ```bash
   uv run mrland-gui
   ```

   Open the GUI in your browser at:
   ```text
   http://localhost:8080
   ```

   Or start the interactive CLI:
   ```bash
   uv run mrland-cli
   ```

For development, install/synchronize dependencies without starting the app:
```bash
uv sync
```

---

## Usage

After starting the app, use the tabs in the interface to:

- edit configuration data
- generate schedules from a saved configuration
- view previously generated schedules

The scheduler stores configuration data in JSON files so it can be loaded and reused across runs.

---

## Configuration

The scheduler uses JSON configuration files to store scheduling information.

Configuration files can include:

- courses
- faculty members
- rooms
- labs
- class patterns
- time blocks
- conflicts
- generation settings

Example configuration files are located in the project config directory:

```text
src/configs/
```

The editor validates the complete configuration after each saved change against the
published Scheduler JSON Schema stored at
[`src/schemas/combined-config.schema.json`](src/schemas/combined-config.schema.json),
then applies the scheduler library's cross-field and cross-reference validation.
No Scheduler API server is needed for this validation.

---

## Testing

The project includes automated tests for the scheduling logic and configuration management.

Run the test suite with:
```bash
uv run pytest
```

This includes tests for:
- courses
- faculty
- labs
- rooms
- class patterns
- time blocks
- conflicts
- schedule generation
- configuration handling

---

## License
This project is licensed under the terms of the included LICENSE file.

---
