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
A CLI based interface for generating and viewing class schedules. The program is driven by a user created or loaded JSON config file.

---

## Project Structure
```text
.
├── LICENSE
├── README.md
├── pytest.ini
├── src
│   ├── __init__.py
│   ├── config.py
│   ├── configs
│   │   ├── test_config.json
│   │   └── test_config2.json
│   ├── conflict.py
│   ├── course.py
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
1. **Python**
  - Check with `python --version`
  - Download from
2. **Git**
    - Check with `git --version`
    - Download from
3. **uv**
    - Check with `uv --version`
    - Download from

---

## Getting Started
1. Clone the Repository
  git clone repo "https://github.com/mucsci-students/2026fa-420-MrLand"

2. Navigate to the Repository
  cd 2026fa-420-MrLand

3. Create Virtual Environment and Install Dependencies
  uv sync

4. Activate Virtual Environment, If Not Already Done   
  - Mac/Linux: source .venv/bin/activate
  - Windows: source .venv/Scripts/activate

5. Run the CLI
   uv run src/main.py

6. Type 'deactivate' to Deactivate the Virtual Environment

---

## Features

