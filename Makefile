install:
	uv pip install -r requirements.txt

run:
	uv run main.py

test:
	uv run compare.py

start:
	uv run streamlit run app.py

.PHONY: install run start