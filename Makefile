install:
	uv venv --clear
	uv pip install -r requirements.txt

run:
	uv run main.py

.PHONY: .install .run