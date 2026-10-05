.PHONY: help install cli gui clean

help:
	@echo "make install  - create .venv and install dependencies"
	@echo "make cli      - run the CLI"
	@echo "make gui      - run the GUI"
	@echo "make clean    - remove the virtual environment and caches"

install:
	uv sync

cli:
	uv run src/navmenu.py

gui:
	uv run src/views/gui.py

clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +