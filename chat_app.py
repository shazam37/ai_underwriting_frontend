import streamlit as st
import requests
from typing import List, Dict
import time
import os
import json
import concurrent.futures

# ====================
# Configuration & Secrets
# ====================
# Ensure these are set in your environment or Streamlit secrets

# Configuration for different model flows (New)
CUSTOM_MODEL_FLOW_URL = os.environ.get('CUSTOM_MODEL_FLOW_URL')
CUSTOM_MODEL_FLOW_API_KEY = os.environ.get('CUSTOM_MODEL_FLOW_API_KEY')
NON_CUSTOM_MODEL_FLOW_URL = os.environ.get('NON_CUSTOM_MODEL_FLOW_URL')
NON_CUSTOM_MODEL_FLOW_API_KEY = os.environ.get('NON_CUSTOM_MODEL_FLOW_API_KEY')

# Chat API configuration (Unchanged)
uw_chat_url = os.environ.get('UW_CHAT_URL')
uw_chat_api_key = os.environ.get('UW_CHAT_API_KEY')

# Backend for file uploads (Unchanged)
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
    # New: Add selected_model to session state
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "Custom Model"

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

# =============================================================================
# MODIFIED FUNCTION: run_final_analysis
# =============================================================================
def run_final_analysis(model_type: str):
    """
    Triggers the main analysis based on the selected model.
    Uses a thread and loop to keep the UI updating so the connection doesn't time out.
    """
    if model_type == "Custom Model":
        url = CUSTOM_MODEL_FLOW_URL
        api_key = CUSTOM_MODEL_FLOW_API_KEY
    else:  # Non-Custom Model
        url = NON_CUSTOM_MODEL_FLOW_URL
        api_key = NON_CUSTOM_MODEL_FLOW_API_KEY

    payload = {"output_type": "chat"}
    headers = {"Content-Type": "application/json", "x-api-key": api_key}

    # Inner function that does the heavy lifting (blocking)
    def _make_request():
        return requests.post(url, json=payload, headers=headers, timeout=1000)

    try:
        # Create a placeholder for the "Loading" status
        status_placeholder = st.empty()
        start_time = time.time()
        
        # Run request in a separate thread
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(_make_request)
            
            # Loop while the thread is running.
            while not future.done():
                elapsed = int(time.time() - start_time)
                # UPDATED: Status message now includes the model type
                status_placeholder.markdown(
                    f"""
                    <div style="padding: 1rem; border: 2px solid #00BFFF; border-radius: 10px; background: #F0F8FF; color: #000000; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
                        <h3 style="margin: 0; color: #000000;">⏳ Running {model_type} Analysis...</h3>
                        <p style="margin: 5px 0 0 0;">Time elapsed: <b>{elapsed} seconds</b></p>
                        <p style="font-size: 0.8em; margin: 5px 0 0 0; color: #333333;"><i>Please do not refresh the page. This may take a few minutes.</i></p>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
                time.sleep(2) # Wait 2 seconds before updating again
            
            # Once done, get result and clear placeholder
            response = future.result()
            status_placeholder.empty()

            response.raise_for_status()
            data = response.json()
            try:
                return data['outputs'][0]['outputs'][0]['results']['message']['data']['text']
            except Exception as e:
                return f"There was an issue in fetching documents. Please try again."

    except Exception as e:
        return f"❌ An error occurred during the final analysis with {model_type}: {str(e)}"

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

    # --- Sidebar --- (MODIFIED)
    with st.sidebar:
        st.markdown("## Controls")
        if st.button("🔄 Start Over", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        
        # New: Add model selection radio button
        st.markdown("## Model Selection")
        model_choice = st.radio(
            "Choose the analysis model:",
            ("Custom Model", "Non-Custom Model"),
            key='model_selection',
            on_change=lambda: st.session_state.update(selected_model=st.session_state.model_selection)
        )

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

    # --- Handle Final Analysis Stage --- (MODIFIED)
    elif current_stage == "analysis_pending":
        # Pass the selected model from session state to the function
        analysis_result = run_final_analysis(st.session_state.selected_model)
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
