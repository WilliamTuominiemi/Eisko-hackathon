install:
	uv pip install -r requirements.txt

run:
	uv run main.py

streamlit:
	uv run streamlit run streamlit_app.py

.PHONY: install run streamlit