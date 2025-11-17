# Gemma Notebook

A locally running RAG chatbot powered by Google's Gemma models.

## Development Setup

1. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
   ```
2. Install the required packages:

   ```bash
   uv pip install -r requirements.txt
   ```

3. Run the Streamlit app:

   ```bash
   streamlit run src/Home.py
   ```