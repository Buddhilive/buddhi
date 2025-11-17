import streamlit as st
from transformers import pipeline
import torch
import os

st.title("✨ Gemma Notebook")

CURRENT_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LLM_MODEL_NAME = os.path.abspath(os.path.join("models", "gemma-3-270m-it"))
LLM_SYSTEM_PROMPT = """You are an expert AI assistant providing answers based ONLY on the private documents provided in the context.
If the answer is not in the documents, state clearly that you cannot answer from the provided information."""

@st.cache_resource
def get_pipeline():
    return pipeline(
        "text-generation",
        model=LLM_MODEL_NAME,
        device=CURRENT_DEVICE,  # Use "cuda" if a GPU is available
        dtype=torch.bfloat16,  # Use torch.float32 if bfloat16 is not supported
    )


client = get_pipeline()

if "system_message" not in st.session_state:
    st.session_state.system_message = LLM_SYSTEM_PROMPT

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

# Display assistant response in chat message container
with st.chat_message("assistant"):
    stream = client(
        text_inputs="Hi",
    )
    response = st.write_stream(stream)
st.session_state.messages.append({"role": "assistant", "content": response})
