install:
	uv pip install -r requirements.txt

run:
	uv run main.py

app:
	uv run streamlit run app.py

.PHONY: install run app