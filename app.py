import streamlit as st
import requests
from typing import Tuple, List, Dict
import time
import os
import json

# ====================
# Configuration & Secrets
# ====================

uw_flow_api_key = os.environ.get('UW_FLOW_API_KEY')
uw_chat_api_key = os.environ.get('UW_CHAT_API_KEY')
API_BASE = os.environ.get('BACKEND_API_BASE')

personal_docs = {
    "Driving License": "driving_license",
    "SSN": "ssn",
}

bank_docs = {
    "Bank Application": "application",
    "Bank Statement": "statement",
}

all_docs = {**personal_docs, **bank_docs}

# ====================
# Session Init
# ====================
# Initialize document upload status
for dtype in all_docs.values():
    if f"{dtype}_status" not in st.session_state:
        st.session_state[f"{dtype}_status"] = "Not Uploaded"
        st.session_state[f"{dtype}_msg"] = ""
        st.session_state[f"{dtype}_filename"] = ""

# Initialize final processing and chat state
if "final_status" not in st.session_state:
    st.session_state.final_status = "not_clicked"
    st.session_state.final_result = ""
if "show_chat" not in st.session_state:
    st.session_state.show_chat = False
if "messages" not in st.session_state:
    st.session_state.messages = []


# ====================
# API Call Functions
# ====================
def upload_file(file, dtype: str) -> Tuple[bool, str]:
    """Handles uploading a file to the correct backend endpoint."""
    try:
        if dtype in ["driving_license", "ssn"]:
            url = f"{API_BASE}/upload_personal_documents"
            files = {"file": (file.name, file, file.type)}
            params = {"document_type": dtype}
        elif dtype in ["application", "statement"]:
            url = f"{API_BASE}/upload_bank_documents"
            files = {"file": (file.name, file, file.type)}
            params = {"application_type": dtype}
        else:
            return False, "Invalid document type"

        response = requests.post(url, files=files, params=params)
        if response.status_code == 200:
            return True, response.json().get("message", "Success")
        else:
            return False, response.json().get("detail", f"Status: {response.status_code}")
    except Exception as e:
        return False, str(e)


def get_chatbot_response(user_prompt: str, analysis_context: str, chat_history: List[Dict]) -> str:
    """
    Calls the Aryaxai chatbot API to get a response.
    """
    # --- API Configuration ---
    # TODO: For better security, move your API key to Streamlit secrets (`st.secrets["CHAT_API_KEY"]`)
    # and avoid hardcoding it in the script.
    
    url = "https://underwritingagentchatoyzy1b9xjp.aryaxai.com/api/v1/run/cbf60110-1c17-4951-b5ee-170ca3624694"

    headers = {
        "Content-Type": "application/json",
        "x-api-key": uw_chat_api_key
    }

    # NOTE: The provided API structure takes a single 'input_value'.
    # It does not appear to have a field for sending the conversation history or the analysis context.
    # If your API supports history (e.g., via a session_id), you would modify the payload here.
    payload = {
        "input_value": user_prompt,
        "output_type": "chat",
        "input_type": "chat",
    }

    try:
        # --- Send API Request ---
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)

        # --- Parse the Response ---
        response_data = response.json()
        
        # Navigate through the nested JSON to get the final text message
        chat_response = response_data['outputs'][0]['outputs'][0]['results']['message']['data']['text']
        return chat_response

    except requests.exceptions.HTTPError as http_err:
        return f"❌ **HTTP Error:** {http_err}. Response: `{response.text}`"
    except requests.exceptions.RequestException as req_err:
        return f"❌ **Request Error:** An error occurred while communicating with the API: {req_err}"
    except (KeyError, IndexError, TypeError):
        # This handles cases where the response JSON structure is not what we expect
        return f"❌ **Parsing Error:** The API response format was unexpected. Full response: `{response.text}`"
    except json.JSONDecodeError:
        return f"❌ **JSON Error:** Failed to decode the API response. Response: `{response.text}`"


# ====================
# Helper UI Functions
# ====================
def get_status_ui(status: str, filename: str):
    """Displays the status of a document upload."""
    if status == "Success":
        st.success(f"✅ Success! `{filename}` is uploaded.", icon="✅")
    elif status == "Error":
        st.error("❌ Error! Please re-upload this document.", icon="❌")
    else:
        st.warning("⏳ Waiting for document upload.", icon="⏳")

def doc_uploader_ui(label: str, dtype: str, file_types=["pdf", "png", "jpg"]):
    """Renders the UI for a single document uploader."""
    with st.container(border=True):
        col1, col2 = st.columns([5, 4])
        with col1:
            st.markdown(f"**{label}**")
            status = st.session_state[f"{dtype}_status"]
            filename = st.session_state[f"{dtype}_filename"]
            get_status_ui(status, filename)

        with col2:
            uploaded_file = st.file_uploader(
                f"Upload your {label}",
                type=file_types,
                key=f"{dtype}_uploader",
                label_visibility="collapsed"
            )

        if uploaded_file and st.session_state[f"{dtype}_status"] != "Success":
            with st.spinner(f"Uploading {uploaded_file.name}..."):
                success, msg = upload_file(uploaded_file, dtype)
                st.session_state[f"{dtype}_status"] = "Success" if success else "Error"
                st.session_state[f"{dtype}_filename"] = uploaded_file.name if success else ""
                st.session_state[f"{dtype}_msg"] = msg
                st.rerun()
        
        if st.session_state[f"{dtype}_msg"]:
            with st.expander("Show Server Response"):
                st.code(st.session_state[f"{dtype}_msg"], language="text")


# ====================
# Streamlit UI
# ====================
st.set_page_config(page_title="Underwriting Assistant", page_icon="✨", layout="centered")

# --- Custom CSS for a gradient button ---
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        border: none;
        border-radius: 10px;
        font-size: 18px;
        font-weight: bold;
        padding: 10px 0;
        background: linear-gradient(45deg, #00f4d4, #00bcf2);
        color: #0a192f;
        transition: all 0.2s ease-in-out;
    }
    .stButton > button:hover {
        transform: scale(1.02);
        background: linear-gradient(45deg, #00bcf2, #00f4d4);
        box-shadow: 0 0 15px #00f4d4;
    }
</style>
""", unsafe_allow_html=True)


# --- Header ---
st.title("AI Loan Underwriting Assistant")
st.markdown("Welcome! Let's get started. Upload the required documents to begin the AI-powered underwriting process.")

# --- Progress Bar ---
st.markdown("---")
successful_uploads = sum(1 for dtype in all_docs.values() if st.session_state[f"{dtype}_status"] == "Success")
progress_percentage = int((successful_uploads / len(all_docs)) * 100)

if progress_percentage == 100:
    st.progress(progress_percentage, text="🎉 **All set! Ready for processing!**")
else:
    st.progress(progress_percentage, text=f"**Completion: {progress_percentage}%** ({successful_uploads}/{len(all_docs)} docs)")
st.markdown("---")


# --- Document Upload Sections ---
col1, col2 = st.columns(2)
with col1:
    st.subheader("👤 Personal Docs")
    for label, dtype in personal_docs.items():
        doc_uploader_ui(label, dtype)

with col2:
    st.subheader("🏦 Bank Docs")
    for label, dtype in bank_docs.items():
        doc_uploader_ui(label, dtype)


# --- Final Processing and Chat Section ---
all_uploaded = all(st.session_state[f"{dtype}_status"] == "Success" for dtype in all_docs.values())

if all_uploaded:
    st.markdown("<br>", unsafe_allow_html=True)
    
    if st.session_state.final_status == "not_clicked":
        if st.button("**Launch AI Analysis**"):
            st.session_state.final_status = "processing"
            st.rerun()

    if st.session_state.final_status == "processing":
        with st.spinner("The AI is analyzing the documents... This can take a moment."):
            try:
                url = "https://aiagents.aryaxai.com/api/v1/run/de1e6e41-d47c-422b-b388-3ca469314bac"
                payload = {"output_type": "chat"}
                headers = {"Content-Type": "application/json", "x-api-key": uw_flow_api_key}
                response = requests.post(url, json=payload, headers=headers, timeout=600)
                response.raise_for_status()
                try:
                    data = response.json()
                    st.session_state.final_result = data['outputs'][0]['outputs'][0]['results']['message']['data']['text']
                except (json.JSONDecodeError, KeyError, IndexError):
                    st.session_state.final_result = f"⚠️ **Failed to parse response:**\n\n```json\n{response.text}\n```"
            except requests.exceptions.Timeout:
                st.session_state.final_result = "❌ **Request Timed Out:** The process took too long to complete."
            except requests.exceptions.HTTPError as http_err:
                st.session_state.final_result = f"❌ **HTTP Error:** {http_err}\n\n**Response:**\n`{response.text}`"
            except Exception as e:
                st.session_state.final_result = f"❌ **An Unexpected Error Occurred:** {str(e)}"
            
            st.session_state.final_status = "done"
            st.rerun()

    if st.session_state.final_status == "done":
        st.markdown("---")
        st.subheader("Analysis & Chat")

        # Make the analysis results collapsible
        with st.expander("📄 View AI Analysis", expanded=True):
            st.markdown(st.session_state.final_result)

        # Show button to initiate chat
        if not st.session_state.show_chat:
            if st.button("💬 Chat with your analysis"):
                st.session_state.show_chat = True
                # Add a welcome message to the chat
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": "Hello! I'm ready to answer your questions about the analysis. What would you like to know?"
                })
                st.rerun()

        # Chat interface logic
        if st.session_state.show_chat:
            st.markdown("---")
            
            # Display existing chat messages
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

            # Get user input via st.chat_input
            if prompt := st.chat_input("Ask a follow-up question..."):
                # Add user message to history and display it
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get and display assistant response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        response = get_chatbot_response(
                            user_prompt=prompt,
                            analysis_context=st.session_state.final_result,
                            chat_history=st.session_state.messages
                        )
                        st.markdown(response)
                
                # Add assistant response to history
                st.session_state.messages.append({"role": "assistant", "content": response})
        
        # Reset button at the bottom
        # st.markdown("<br>", unsafe_allow_html=True)
        # if st.button("🔄 Start New Application"):
        #     # Clear all session state to reset the app
        #     for key in list(st.session_state.keys()):
        #         del st.session_state[key]
        #     st.rerun()

        # Reset button at the side
        st.sidebar.markdown("---")
        st.sidebar.header("Actions")
        if st.sidebar.button("🔄 Start New Application"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()