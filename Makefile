.PHONY: help install cli gui clean

help:
	@echo "make install  - create .venv and install dependencies"
	@echo "make cli      - run the CLI"
	@echo "make gui      - run the GUI"
	@echo "make clean    - remove the virtual environment and caches"

install:
	uv sync

cli:
	uv run python -m src.views.navmenu

gui:
	uv run python -m src.views.gui

clean:
	rm -rf .venv
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +