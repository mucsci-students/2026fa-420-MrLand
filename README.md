# 2026fa-420-MrLand
## CMSC 420-f26

---

## Contributors
- Nicoletta Beltrante
- Adrian Olweiler
- Renee Watts
- Logan Kaufman
- Dylan Groff

---

## Overview
A CLI-based interface for configuring, generating, and viewing class schedules. The program is driven by a user-created or loaded JSON configuration file and supports management of courses, faculty, rooms, labs, conflicts, class patterns, and time blocks.

---

## Features

- **Course Management**
  - Add, modify, view, and delete courses
  - Manage course IDs, section IDs, credits, capacity, modality, rooms, labs, conflicts, and faculty
  - Validate course and section IDs
  - Prevent duplicate course sections
  - Support in-person, online, and hybrid course modalities

- **Faculty Management**
  - Add, modify, view, and delete faculty members
  - Manage faculty availability and course limits
  - Validate faculty information

- **Room Management**
  - Add, modify, view, and delete rooms
  - Manage room capacity and features

- **Lab Management**
  - Add, modify, view, and delete labs
  - Manage lab capacity and features

- **Class Pattern Management**
  - Manage class meeting patterns
  - Configure days, times, and other scheduling information

- **Time Block Management**
  - Create and manage time blocks used for scheduling

- **Conflict Management**
  - Define course conflicts
  - Validate course conflict information

- **Configuration Management**
  - Load scheduling configuration from JSON files
  - Save and manage configuration data
  - Validate configuration information

- **Schedule Generation**
  - Generate schedules based on the configured courses, faculty, rooms, labs, conflicts, and scheduling constraints

- **Command-Line Interface**
  - Navigate the application through a menu-driven CLI
  - Create, view, modify, and delete scheduling information

---

## Project Structure
```text
.
├── LICENSE
├── README.md
├── pytest.ini
├── pyproject.toml
├── src
│   ├── __init__.py
│   ├── config.py
│   ├── configs
│   │   ├── test_config.json
│   │   └── test_config2.json
│   ├── conflict.py
│   ├── navmenu.py
│   ├── run_scheduler.py
│   └── services
│       ├── __init__.py
│       ├── class_pattern_service.py
│       ├── config_io.py
│       ├── config_service.py
│       ├── course_service.py
│       ├── faculty_service.py
│       ├── lab_service.py
│       ├── rooms_service.py
│       └── time_block_service.py
├── tests
│   ├── __init__.py
│   ├── config_testing.py
│   ├── test_class_patterns.py
│   ├── test_course.py
│   ├── test_faculty.py
│   ├── test_labs.py
│   ├── test_rooms.py
│   ├── test_run_scheduler.py
│   ├── test_time_blocks.py
│   └── tests_conflicts.py
└── uv.lock
```
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
    - Download instructions located at [uv](https://docs.astral.sh/uv/)

---

## Getting Started
1. Clone the Repository
``` bash
  git clone repo "https://github.com/mucsci-students/2026fa-420-MrLand"
```
3. Navigate to the Repository
``` bash
  cd 2026fa-420-MrLand
```
5. Create Virtual Environment and Install Dependencies
``` bash
  uv sync
```
7. Activate Virtual Environment, If Not Already Done (uv sync will take care of this automatically)  
  - Mac/Linux:
    ``` bash
    source .venv/bin/activate
    ```
  - Windows:
    ``` bash
    source .venv/Scripts/activate
    ```
5. Run the CLI
``` bash
   uv run src/navmenu.py
```
7. Type 'deactivate' to Deactivate the Virtual Environment
``` bash
deactivate
```
---

## Usage

After starting the application, use the command-line menu to navigate through the available scheduling options.

The application allows users to:

- Manage courses
- Manage faculty members
- Manage rooms
- Manage labs
- Manage class patterns
- Manage time blocks
- Manage course conflicts
- Load and manage configuration data
- Generate schedules

Follow the prompts displayed in the CLI to add, modify, view, or delete scheduling information.

---

## Configuration

The scheduler uses JSON configuration files to store scheduling information.

Configuration files can contain information about:

- Courses
- Faculty members
- Rooms
- Labs
- Class patterns
- Time blocks
- Course conflicts

Example configuration files are located in:

```text
src/configs/
```

---

## Testing

The project includes automated tests for the application's scheduling components.
Tests are located in the tests/ directory.
To run the test suite, use:
``` bash
uv run pytest
```
The test suite includes tests for:
  - Courses
  - Faculty
  - Labs
  - Rooms
  - Class patterns
  - Time blocks
  - Conflicts
  - Schedule generation
  - Configuration handling

---

## License
This project is licensed under the terms of the included LICENSE file.

---

