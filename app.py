# import streamlit as st
# import requests
# from typing import Tuple
# import time
# import requests
# import os
# import json

# # ====================
# # Configuration
# # ====================
# API_BASE = "http://localhost:8000"  # Change to your FastAPI base URL
# xai_api_key = "arya-8J0kYtRh5NOTXIjT9SLy_WwhA-eHWGK8Brbpovm7nGg"


# personal_docs = {
#     "Driving License": "driving_license",
#     "SSN": "ssn",
# }

# bank_docs = {
#     "Bank Application": "application",
#     "Bank Statement": "statement",
# }

# # Merge all for iteration
# all_docs = {**personal_docs, **bank_docs}

# # ====================
# # Session Init
# # ====================
# for label, dtype in all_docs.items():
#     if f"{dtype}_status" not in st.session_state:
#         st.session_state[f"{dtype}_status"] = "not_uploaded"
#         st.session_state[f"{dtype}_msg"] = ""

# if "final_status" not in st.session_state:
#     st.session_state["final_status"] = "not_clicked"
#     st.session_state["final_result"] = ""

# # ====================
# # Upload Function
# # ====================
# def upload_file(file, dtype: str) -> Tuple[bool, str]:
#     try:
#         if dtype in ["driving_license", "ssn"]:
#             url = f"{API_BASE}/upload_personal_documents"
#             files = {"file": (file.name, file, file.type)}
#             params = {"document_type": dtype}
#         elif dtype in ["application", "statement"]:
#             url = f"{API_BASE}/upload_bank_documents"
#             files = {"file": (file.name, file, file.type)}
#             params = {"application_type": dtype}
#         else:
#             return False, "Invalid document type"

#         response = requests.post(url, files=files, params=params)
#         if response.status_code == 200:
#             return True, response.json().get("message", "Success")
#         else:
#             return False, response.json().get("detail", f"Status: {response.status_code}")
#     except Exception as e:
#         return False, str(e)

# # ====================
# # Streamlit UI
# # ====================
# st.set_page_config(page_title="📂 Upload Documents", layout="centered")
# st.title("Welcome to underwriting agent")

# st.write("Please upload all 4 required documents below to continue with the underwriting agent.")

# # Upload Buttons
# for label, dtype in all_docs.items():
#     col1, col2 = st.columns([3, 3])
#     with col1:
#         if st.session_state[f"{dtype}_status"] == "not_uploaded":
#             uploaded_file = st.file_uploader(f"Upload {label}", type=["pdf", "jpg", "jpeg", "png"], key=dtype)
#             if uploaded_file:
#                 with st.spinner(f"Uploading {label}..."):
#                     success, msg = upload_file(uploaded_file, dtype)
#                     if success:
#                         st.session_state[f"{dtype}_status"] = "success"
#                         st.session_state[f"{dtype}_msg"] = msg
#                     else:
#                         st.session_state[f"{dtype}_status"] = "error"
#                         st.session_state[f"{dtype}_msg"] = msg
#         elif st.session_state[f"{dtype}_status"] == "success":
#             st.success(f"✅ {label} uploaded successfully")
#         elif st.session_state[f"{dtype}_status"] == "error":
#             st.error(f"❌ {label} upload failed")

#     with col2:
#         msg = st.session_state[f"{dtype}_msg"]
#         if msg:
#             st.markdown(f"**Server Response**: {msg}")

# # Final Processing Button
# all_uploaded = all(st.session_state[f"{dtype}_status"] == "success" for dtype in all_docs.values())

# if all_uploaded:
#     st.markdown("---")
#     st.subheader("Run the underwriting agent")

#     if st.session_state["final_status"] == "not_clicked":
#         if st.button("📊 Process All Documents"):
#             with st.spinner("Processing..."):
#                 # try:
#                 #     # Simulate long processing
#                 #     # time.sleep(5)
#                 #     # final_result = requests.get(f"{API_BASE}/run_underwriting_flow")  # Replace with real API
#                 #     final_result = requests.get("https://3645788de497.ngrok-free.app/run_underwriting_flow", timeout=400)
#                 #     print(f'The final result obtainedzzz: {final_result}')
#                 #     final_result.raise_for_status()
#                 #     st.session_state["final_result"] = final_result.json().get("result", "Processed Successfully 🎉")
#                 #     print(f'The final result obtained: {final_result}')
#                 #     st.session_state["final_status"] = "done"
#                 # except Exception as e:  
#                 #     st.session_state["final_result"] = f"Error: {str(e)}"
#                 #     st.session_state["final_status"] = "done"
#                 try:

#                     # API endpoint
#                     url = "https://aiagents.aryaxai.com/api/v1/run/de1e6e41-d47c-422b-b388-3ca469314bac"

#                     # Payload
#                     payload = {
#                         "output_type": "chat"
#                     }

#                     # Headers
#                     headers = {
#                         "Content-Type": "application/json",
#                         "x-api-key": xai_api_key
#                     }

#                     # Long processing call
#                     final_result = requests.request("POST", url, json=payload, headers=headers, timeout=400)
#                     final_result.raise_for_status()

#                     # Parse result
#                     try:
#                         data = json.loads(final_result.text)
                        
#                         extracted_message = data['outputs'][0]['outputs'][0]['results']['message']['data']['text']
#                         st.session_state["final_result"] = f"{extracted_message}"
                        
#                     except Exception as parse_err:
#                         st.session_state["final_result"] = (
#                             f"⚠️ Received response but failed to parse output:\n\n"
#                             f"```json\n{final_result.text}\n```"
#                         )
                    
#                     st.session_state["final_status"] = "done"

#                 except requests.exceptions.Timeout:
#                     st.session_state["final_result"] = "❌ Request timed out. The process took too long."
#                     st.session_state["final_status"] = "done"
#                 except requests.exceptions.HTTPError as http_err:
#                     st.session_state["final_result"] = (
#                         f"❌ HTTP Error: {http_err}\n\nResponse:\n{final_result.text}"
#                     )
#                     st.session_state["final_status"] = "done"
#                 except Exception as e:
#                     st.session_state["final_result"] = f"❌ Unexpected Error: {str(e)}"
#                     st.session_state["final_status"] = "done"

#     if st.session_state["final_status"] == "done":
#         st.success(st.session_state["final_result"])

# # st.title("Hello Streamlit")
# # st.write("If you're seeing this, Streamlit works!")

import streamlit as st
import requests
from typing import Tuple
import time
import os
import json

xai_api_key = "arya-8J0kYtRh5NOTXIjT9SLy_WwhA-eHWGK8Brbpovm7nGg"
API_BASE = "https://ai-loan-underwriting.onrender.com"  # Change to your FastAPI base URL

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
# Session Init (No Changes)
# ====================
for dtype in all_docs.values():
    if f"{dtype}_status" not in st.session_state:
        st.session_state[f"{dtype}_status"] = "Not Uploaded"
        st.session_state[f"{dtype}_msg"] = ""
        st.session_state[f"{dtype}_filename"] = ""

if "final_status" not in st.session_state:
    st.session_state.final_status = "not_clicked"
    st.session_state.final_result = ""


# ====================
# Upload Function (No Changes)
# ====================
def upload_file(file, dtype: str) -> Tuple[bool, str]:
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


# ====================
# Helper UI Functions
# ====================
def get_status_ui(status: str, filename: str):
    if status == "Success":
        st.success(f"✅ Success! `{filename}` is uploaded.", icon="✅")
    elif status == "Error":
        st.error("❌ Error! Please re-upload this document.", icon="❌")
    else:
        st.warning("⏳ Waiting for document upload.", icon="⏳")

def doc_uploader_ui(label: str, dtype: str, file_types=["pdf", "png", "jpg"]):
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
                if success:
                    st.session_state[f"{dtype}_status"] = "Success"
                    st.session_state[f"{dtype}_filename"] = uploaded_file.name
                else:
                    st.session_state[f"{dtype}_status"] = "Error"
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
# st.image("https://storage.googleapis.com/gemini-prod/images/1c3a7266-94b6-4b6d-8a25-45c36312a8a8", use_container_width=True)
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


# --- Final Processing Section ---
all_uploaded = all(st.session_state[f"{dtype}_status"] == "Success" for dtype in all_docs.values())

if all_uploaded:
    st.markdown("<br>", unsafe_allow_html=True)
    st.balloons()
    
    if st.session_state.final_status == "not_clicked":
        if st.button("**Launch AI Analysis**"):
            st.session_state.final_status = "processing"
            st.rerun()

    if st.session_state.final_status in ["processing", "done"]:
        with st.spinner("The AI is analyzing the documents... This can take a moment."):
            if st.session_state.final_status == "processing":
                try:
                    url = "https://aiagents.aryaxai.com/api/v1/run/de1e6e41-d47c-422b-b388-3ca469314bac"
                    payload = {"output_type": "chat"}
                    headers = {"Content-Type": "application/json", "x-api-key": xai_api_key}
                    response = requests.post(url, json=payload, headers=headers, timeout=400)
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
        st.subheader("Analysis Results")
        with st.container(border=True):
            st.markdown(st.session_state.final_result)
            if st.button("🔄 Start New Application"):
                # Clear all session state to reset the app
                for key in list(st.session_state.keys()):
                    del st.session_state[key]
                st.rerun()