import streamlit as st
import requests
from typing import List, Dict
import time
import os
import json

# ====================
# Configuration & Secrets
# ====================
# Ensure these are set in your environment or Streamlit secrets
uw_flow_url = os.environ.get('UW_FLOW_URL')
uw_chat_url = os.environ.get('UW_CHAT_URL')
uw_chat_api_key = os.environ.get('UW_CHAT_API_KEY')
uw_flow_api_key = os.environ.get('UW_FLOW_API_KEY')
API_BASE = os.environ.get('BACKEND_API_BASE')

# Define the sequence of documents to be collected
DOC_ORDER = ["driving_license", "ssn", "bank_application", "bank_statement"]

DOC_INFO = {
    "driving_license": {
        "prompt": "To start, please upload a copy of your **Driving License**.",
        "api_type": "personal",
        "next_stage": "ssn"
    },
    "ssn": {
        "prompt": "Great. Now, please upload a document with your **Social Security Number**.",
        "api_type": "personal",
        "next_stage": "bank_application"
    },
    "bank_application": {
        "prompt": "Thank you. Next, please upload the completed **Bank Application** form.",
        "api_type": "bank",
        "next_stage": "bank_statement"
    },
    "bank_statement": {
        "prompt": "Almost done. Finally, please upload your latest **Bank Statement**.",
        "api_type": "bank",
        "next_stage": "analysis_pending" # All docs collected, next is analysis
    }
}

# ====================
# Session State Initialization
# ====================
def init_session_state():
    if "app_started" not in st.session_state:
        st.session_state.app_started = False
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "doc_upload_stage" not in st.session_state:
        st.session_state.doc_upload_stage = DOC_ORDER[0]
    if "upload_retries" not in st.session_state:
        st.session_state.upload_retries = 0

# ====================
# API Call Functions
# ====================
def upload_file(file, doc_type: str, api_type: str):
    """Handles uploading a file to the correct backend endpoint."""
    try:
        if api_type == "personal":
            url = f"{API_BASE}/upload_personal_documents"
            params = {"document_type": doc_type}
        elif api_type == "bank":
            url = f"{API_BASE}/upload_bank_documents"
            params = {"application_type": doc_type}
        else:
            return False, "Invalid API type specified."

        files = {"file": (file.name, file, file.type)}
        response = requests.post(url, files=files, params=params, timeout=60)
        print(f'Here is the respone : {response.text}')
        response.raise_for_status()
        response = json.loads(response.text)['success']
        if response == True:
            return True, response
        elif response == False:
            return False, f"Incorrect file type provided"
    except requests.exceptions.HTTPError as err:
        return False, f"HTTP Error: {err}. Response: {err.response.text}"
    except Exception as e:
        return False, f"An unexpected error occurred: {str(e)}"

def run_final_analysis():
    """Triggers the main analysis after all documents are uploaded."""
    try:
        url = uw_flow_url
        payload = {"output_type": "chat"}
        headers = {"Content-Type": "application/json", "x-api-key": uw_flow_api_key}
        response = requests.post(url, json=payload, headers=headers, timeout=1000)
        response.raise_for_status()
        data = response.json()
        return data['outputs'][0]['outputs'][0]['results']['message']['data']['text']
    except Exception as e:
        return f"❌ An error occurred during the final analysis: {str(e)}"

def get_chatbot_response(user_prompt: str):
    """Calls the interactive chatbot API for conversation."""
    
    url = uw_chat_url
    headers = {"Content-Type": "application/json", "x-api-key": uw_chat_api_key}
    payload = {"input_value": user_prompt, "output_type": "chat", "input_type": "chat"}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=100)
        response.raise_for_status()
        response_data = response.json()
        return response_data['outputs'][0]['outputs'][0]['results']['message']['data']['text']
    except requests.exceptions.RequestException as e:
        return f"❌ **API Error:** Could not get a response. {e}"
    except (KeyError, IndexError):
        return f"❌ **Parsing Error:** The API response format was unexpected."

# ====================
# Streamlit UI
# ====================
st.set_page_config(page_title="AI Underwriting Assistant", page_icon="🤖", layout="centered")
init_session_state()

# --- Main App Logic ---
if not st.session_state.app_started:
    st.title("Welcome to the AI Loan Underwriting Assistant")
    st.markdown("Click the button below to start the guided process.")
    if st.button("Let's begin the analysis", type="primary"):
        st.session_state.app_started = True
        st.session_state.messages = [{
            "role": "assistant",
            "content": "I am a loan underwriting agent. I will guide you through the process of submitting your documents for analysis."
        }, {
            "role": "assistant",
            "content": DOC_INFO[st.session_state.doc_upload_stage]["prompt"]
        }]
        st.rerun()
else:
    st.title("AI Loan Underwriting Assistant")

    # --- Reset Button ---
    if st.sidebar.button("🔄 Start Over"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

    # --- Display Chat History ---
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # --- Handle Document Upload Stages ---
    current_stage = st.session_state.doc_upload_stage
    if current_stage in DOC_INFO:
        info = DOC_INFO[current_stage]
        uploaded_file = st.file_uploader(
            f"Upload your document",
            type=["pdf", "png", "jpg", "jpeg"],
            # key=f"uploader_{current_stage}"
            key=f"uploader_{current_stage}_{st.session_state.upload_retries}"
        )
        if uploaded_file:
            with st.spinner(f"Uploading and verifying `{uploaded_file.name}`..."):
                success, msg = upload_file(uploaded_file, current_stage, info["api_type"])
                print(f'upload_status: {success} with message: {msg}')
                if success:
                    st.session_state.messages.append({"role": "user", "content": f"Uploaded `{uploaded_file.name}`"})
                    st.session_state.doc_upload_stage = info["next_stage"]
                    # Check if we need to ask for the next doc or start analysis
                    if st.session_state.doc_upload_stage in DOC_INFO:
                        st.session_state.messages.append({"role": "assistant", "content": DOC_INFO[st.session_state.doc_upload_stage]["prompt"]})
                    else:
                        st.session_state.messages.append({"role": "assistant", "content": "All documents received. I will now begin the final analysis. Please wait a moment."})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": f"There was an error with your upload: {msg}. Please try again."})
                    st.session_state.upload_retries += 1  # Reset uploader by changing key
                    st.rerun()
                st.rerun()

    # --- Handle Final Analysis Stage ---
    elif current_stage == "analysis_pending":
        with st.spinner("Performing final analysis on all documents... This may take a moment."):
            analysis_result = run_final_analysis()
            st.session_state.messages.append({"role": "assistant", "content": analysis_result})
            st.session_state.messages.append({"role": "assistant", "content": "The initial analysis is complete. You can now ask me any questions you have."})
            st.session_state.doc_upload_stage = "chat_active"
            st.rerun()

    # --- Handle Active Chat Stage ---
    elif current_stage == "chat_active":
        if prompt := st.chat_input("Ask a question about the analysis..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = get_chatbot_response(prompt)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})