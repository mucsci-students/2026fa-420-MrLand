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
- Sohil Ramani

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
  - Clear generated results without removing schedules loaded from files
- **Scheduler AI Assistant**
  - Use the floating chat box from any GUI screen to inspect or edit the active configuration in natural language
  - Inspect and manage rooms, labs, courses, faculty, class patterns, meetings, time blocks, and global settings; validate and generate schedules with defined scheduler tools
  - A failed multi-operation request is rolled back; delete and overwrite actions require confirmation
  - The chat reports whether edits are applied to the editor or saved to disk; generated results appear in the Schedule Viewer
  - Requires `OPENAI_API_KEY` in a `.env` file (see AI assistant setup below); model requests may incur API charges

- **Domain Management**
  - Add, modify, view, and delete faculty, courses, rooms, labs, class patterns, and time blocks
  - Track conflicts and scheduling constraints

- **JSON-based Persistence**
  - Store scheduler data in configuration files under the project config directories
- **Whole-configuration validation**
  - Validate edits against the published [combined configuration JSON Schema](https://raw.githubusercontent.com/mucsci/scheduler/main/fern/docs/assets/combined-config.schema.json) and scheduler model rules
  - Preserve incomplete new drafts until valid; reject edits that would invalidate an already-valid configuration

## Design pattern: Strategy

The Schedule Viewer supports exporting the selected schedule or all generated
schedules as either CSV or JSON. Each format requires different serialization,
so keeping format-specific branches in the viewer model would couple export
workflows to every supported format. The Strategy pattern lets those workflows
use the selected serialization behavior through a shared interface.

- **Relevant code:** [`schedule_files.py`](src/models/schedule_files.py) defines
  `ScheduleExportStrategy`, `CsvScheduleExportStrategy`,
  `JsonScheduleExportStrategy`, and the `SCHEDULE_EXPORT_STRATEGIES` registry.
  [`schedule_viewer_model.py`](src/models/schedule_viewer_model.py) selects and
  invokes the strategy in `ScheduleViewerModel.serialize`; both single-schedule
  exports and ZIP exports use that method. The format choice is passed from
  [`schedule_viewer.py`](src/views/schedule_viewer.py) through
  [`schedule_controller.py`](src/controllers/schedule_controller.py).
- **Participants and interaction:** `ScheduleViewerModel` is the context. It
  requests serialization from the `ScheduleExportStrategy` interface. The
  CSV and JSON concrete strategies delegate to their respective record
  serializers, and the registry selects the concrete strategy by the user's
  format choice.
- **Why this fits:** CSV and JSON are interchangeable ways to serialize the
  same schedule records. The viewer uses each strategy in actual download
  behavior without needing format-specific serialization branches.

## AI assistant setup
1. Run `uv sync` to install dependencies.
2. Copy `.env.example` to a new file named `.env` in the project root.
3. Replace `your-key-here` with your OpenAI API key found in the resources page on discord.

---

## Project Structure
```text
.
├── LICENSE
├── README.md
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
│   │   └── ...
│   ├── models/
│   │   ├── configuration_model.py
│   │   ├── configuration_repository.py
│   │   ├── schedule_generator_model.py
│   │   └── ...
│   ├── views/
│   │   ├── common.py
│   │   ├── configuration_editor.py
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
│   └── ...
└── .venv/
```

Application implementations are organized into MVC packages. Configuration
validation and persistence live in `models`, domain actions in `controllers`,
and user interfaces in `views`. The former services implementations have been
moved into those MVC packages. Use the `mrland-gui` project command to launch the
application.

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

2. Launch the GUI from the project directory. `uv run` creates and
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

   Or run the tests
   ```bash
   uv run pytest
   ```

---

## Development

For development, install/synchronize dependencies without starting the app:
```bash
uv sync
```

Before pushing, run the same checks CI runs:

    uv run ruff format .
    uv run ruff check --fix .
    uv run ty check
    uv run pytest --cov

Add dependencies with `uv add <pkg>` (or `uv add --dev <pkg>`), never pip,
and commit `pyproject.toml` and `uv.lock` together.

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

## Test Coverage

CI requires at least 80% line coverage of the team-written Model code.

- **In scope:** `src/models/` (configuration state, generated schedule
  state, and Model behavior)
- **Out of scope:** the third-party `course-constraint-scheduler` library,
  views/controllers, and tests

Scope and threshold are set in `pyproject.toml` under `[tool.coverage.*]`.
Reproduce locally with `uv run pytest --cov`. The run fails below 80%.
Results appear on Codecov under the `model` flag.

---

## License
This project is licensed under the terms of the included LICENSE file.

---
