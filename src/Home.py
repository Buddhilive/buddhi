import streamlit as st
from transformers import pipeline
import torch
import os

st.title("✨ Gemma Notebook")

CURRENT_DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
LLM_MODEL_NAME = os.path.abspath(os.path.join("models", "gemma-3-270m-it"))
LLM_SYSTEM_PROMPT = """You are Gemma, an advanced AI assistant."""


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

    messages = [
        {"role": "system", "content": st.session_state.system_message}
    ] + [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        with st.spinner("Thinking...", show_time=True):
            stream = client(
                text_inputs=messages,
                max_new_tokens=512,
                return_full_text=False,
            )
            response = st.markdown(stream[0]["generated_text"])
        st.session_state.messages.append({"role": "assistant", "content": stream[0]["generated_text"]})
