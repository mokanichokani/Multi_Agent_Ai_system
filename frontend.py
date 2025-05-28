import streamlit as st
import os
import json
from agents.classifier_agent import ClassifierAgent
from memory.shared_memory import shared_memory_instance, MEMORY_FILE

st.set_page_config(page_title="Multi-Agent Document Processor", layout="wide")

@st.cache_resource
def get_classifier_agent():
    print("Initializing ClassifierAgent for Streamlit app...")
    return ClassifierAgent()

classifier = get_classifier_agent()

st.title("📄 Multi-Agent Document Processor")
st.markdown("""
Upload a file (PDF, JSON, Email/Text) or enter raw text.
The system will classify its format and intent, then route it to the appropriate agent for processing.
Results and a running log will be displayed below.
""")

input_method = st.radio("Choose input method:", ("File Upload", "Raw Text Input"))

uploaded_file = None
raw_text_input = ""
source_identifier_manual = "raw_text_input"

if input_method == "File Upload":
    uploaded_file = st.file_uploader("Choose a PDF, JSON, or Text/Email file", type=["pdf", "json", "txt", "eml"])
    if uploaded_file:
        st.write(f"Uploaded: {uploaded_file.name} ({uploaded_file.type})")
else:
    raw_text_input = st.text_area("Enter Email Content or other Text:", height=200)
    source_identifier_manual = st.text_input("Optional: Give this input a name/identifier", value="manual_text_entry")

if st.button("Process Input"):
    if uploaded_file:
        st.session_state.last_thread_id = None
        st.session_state.last_result = None
        with st.spinner(f"Processing {uploaded_file.name}..."):
            thread_id, result = classifier.process(
                input_data=uploaded_file,
                source_identifier=uploaded_file.name,
                source_type="streamlit_upload"
            )
            st.session_state.last_thread_id = thread_id
            st.session_state.last_result = result
        if st.session_state.last_result:
            st.success(f"File '{uploaded_file.name}' processed successfully!")
        else:
            st.error("An error occurred during processing.")
    elif raw_text_input.strip():
        st.session_state.last_thread_id = None
        st.session_state.last_result = None
        with st.spinner(f"Processing raw text input '{source_identifier_manual}'..."):
            thread_id, result = classifier.process(
                input_data=raw_text_input,
                source_identifier=source_identifier_manual,
                source_type="streamlit_raw_text"
            )
            st.session_state.last_thread_id = thread_id
            st.session_state.last_result = result
        if st.session_state.last_result:
            st.success(f"Raw text input '{source_identifier_manual}' processed successfully!")
        else:
            st.error("An error occurred during processing raw text.")
    else:
        st.warning("Please upload a file or enter text to process.")

if 'last_result' in st.session_state and st.session_state.last_result:
    st.subheader("📊 Processing Result")
    st.json(st.session_state.last_result)

st.sidebar.title("📝 Shared Memory Log")
st.sidebar.markdown(f"Log file: `{MEMORY_FILE}` (updates on disk)")

if st.sidebar.button("Refresh Log from File"):
    shared_memory_instance.load_from_file()

if shared_memory_instance.log:
    for entry in reversed(shared_memory_instance.log):
        with st.sidebar.expander(f"Log ID: {entry['log_id']} ({entry['timestamp']}) - {entry['source_identifier']}"):
            st.json(entry)
else:
    st.sidebar.write("Memory log is empty.")

st.markdown("---")
st.caption("Developed as a multi-agent AI system.")