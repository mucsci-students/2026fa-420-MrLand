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
│   ├── controllers/
│   │   ├── config_controller.py
│   │   ├── schedule_generator_controller.py
│   │   └── schedule_viewer_controller.py
│   ├── models/
│   │   ├── config_model.py
│   │   ├── schedule_generator_model.py
│   │   └── ...
│   ├── services/
│   │   ├── __init__.py
│   │   ├── config_io.py
│   │   ├── config_service.py
│   │   ├── course_service.py
│   │   ├── faculty_service.py
│   │   ├── lab_service.py
│   │   ├── rooms_service.py
│   │   ├── schedule_service.py
│   │   └── ...
│   ├── views/
│   │   ├── common.py
│   │   ├── configuration_editor.py
│   │   ├── gui.py
│   │   ├── schedule_generator.py
│   │   ├── schedule_viewer.py
│   │   └── ...
│   ├── navmenu.py
│   └── run_scheduler.py
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

Note: the legacy CLI menu files are no longer the primary application entry point. The current user workflow uses the GUI app in `src/views/gui.py`.

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

2. Install dependencies:
```bash
uv sync
```

3. Start the application:
```bash
uv run python -m src.views.gui
```

4. Open the app in a browser at:
```text
http://localhost:8080
```

If needed, change the port:
```bash
MRLAND_GUI_PORT=8080 uv run python -m src.views.gui
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

