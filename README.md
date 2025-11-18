# Gemma Notebook

A locally running RAG chatbot powered by Google's Gemma models.

## Development Setup

### Download Models

```bash
mkdir -p models
cd models
# Download the Gemma language model and its corresponding embedding model
hf download google/gemma-3-270m-it --local-dir "./gemma-3-270m-it"

# Download the embedding model
hf download google/embeddinggemma-300m --local-dir "./embeddinggemma-300m"
cd ..
```

### Install Dependencies

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