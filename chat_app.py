import streamlit as st
import requests
from typing import List, Dict
import time
import os
import json
import threading

# ====================
# Configuration
# ====================

CUSTOM_MODEL_FLOW_URL = os.environ.get('CUSTOM_MODEL_FLOW_URL')
CUSTOM_MODEL_FLOW_API_KEY = os.environ.get('CUSTOM_MODEL_FLOW_API_KEY')
NON_CUSTOM_MODEL_FLOW_URL = os.environ.get('NON_CUSTOM_MODEL_FLOW_URL')
NON_CUSTOM_MODEL_FLOW_API_KEY = os.environ.get('NON_CUSTOM_MODEL_FLOW_API_KEY')

uw_chat_url = os.environ.get('UW_CHAT_URL')
uw_chat_api_key = os.environ.get('UW_CHAT_API_KEY')

API_BASE = os.environ.get('BACKEND_API_BASE')

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
        "next_stage": "analysis_pending"
    }
}

# ====================
# Session State
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
    if "selected_model" not in st.session_state:
        st.session_state.selected_model = "Custom Model"

# ====================
# Upload
# ====================

def upload_file(file, doc_type: str, api_type: str):
    try:
        if api_type == "personal":
            url = f"{API_BASE}/upload_personal_documents"
            params = {"document_type": doc_type}
        else:
            url = f"{API_BASE}/upload_bank_documents"
            params = {"application_type": doc_type}

        files = {"file": (file.name, file, file.type)}
        response = requests.post(url, files=files, params=params, timeout=60)

        # 🔍 DEBUG (optional but useful)
        print("STATUS:", response.status_code)
        print("RAW RESPONSE:", response.text)

        response.raise_for_status()

        # 🔥 HANDLE EMPTY / NULL RESPONSE
        if not response.text or response.text.strip() in ["null", "None", ""]:
            return True, "Upload successful (no response body)"

        # 🔥 SAFE JSON PARSE
        try:
            data = response.json()
        except Exception:
            return True, "Upload successful (non-JSON response)"

        # 🔥 HANDLE None JSON
        if data is None:
            return True, "Upload successful (empty JSON)"

        # 🔥 NORMAL CASE
        if isinstance(data, dict):
            if data.get("success") is True:
                return True, "Success"

            # fallback (some APIs use different key)
            if data.get("status") == "ok":
                return True, "Success"

            return False, data.get("message", "Upload failed")

        # 🔥 fallback (unexpected but valid)
        return True, "Upload successful"

    except requests.exceptions.HTTPError as err:
        return False, f"HTTP Error: {err.response.text}"

    except Exception as e:
        return False, f"Upload failed: {str(e)}"

# ====================
# FINAL ANALYSIS
# ====================

def run_final_analysis(model_type: str):
    if model_type == "Custom Model":
        url = CUSTOM_MODEL_FLOW_URL
        api_key = CUSTOM_MODEL_FLOW_API_KEY
    else:
        url = NON_CUSTOM_MODEL_FLOW_URL
        api_key = NON_CUSTOM_MODEL_FLOW_API_KEY

    payload = {"output_type": "chat"}
    headers = {"Content-Type": "application/json", "x-api-key": api_key}

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=None)
        response.raise_for_status()
        data = response.json()
        return data['outputs'][0]['outputs'][0]['results']['message']['data']['text']
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ====================
# CHAT
# ====================

def get_chatbot_response(user_prompt: str):
    try:
        response = requests.post(
            uw_chat_url,
            json={"input_value": user_prompt, "output_type": "chat", "input_type": "chat"},
            headers={"x-api-key": uw_chat_api_key},
            timeout=100
        )
        response.raise_for_status()
        data = response.json()
        return data['outputs'][0]['outputs'][0]['results']['message']['data']['text']
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ====================
# UI
# ====================

st.set_page_config(page_title="AI Underwriting Assistant", layout="centered")
init_session_state()

# ---------------- START ----------------
if not st.session_state.app_started:
    st.title("AI Loan Underwriting Assistant")

    if st.button("Start"):
        st.session_state.app_started = True
        st.session_state.messages = [
            {"role": "assistant", "content": "I will guide you through document submission."},
            {"role": "assistant", "content": DOC_INFO[st.session_state.doc_upload_stage]["prompt"]}
        ]
        st.rerun()

# ---------------- MAIN ----------------
else:
    st.title("AI Loan Underwriting Assistant")

    with st.sidebar:
        if st.button("Reset"):
            st.session_state.clear()
            st.rerun()

        st.radio(
            "Model",
            ("Custom Model", "Non-Custom Model"),
            key="model_selection",
            on_change=lambda: st.session_state.update(selected_model=st.session_state.model_selection)
        )

    # chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    stage = st.session_state.doc_upload_stage

    # -------- Upload --------
    if stage in DOC_INFO:
        info = DOC_INFO[stage]
        file = st.file_uploader("Upload file")

        if file:
            success, msg = upload_file(file, stage, info["api_type"])

            if success:
                st.session_state.messages.append({"role": "user", "content": file.name})
                st.session_state.doc_upload_stage = info["next_stage"]

                if st.session_state.doc_upload_stage in DOC_INFO:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": DOC_INFO[st.session_state.doc_upload_stage]["prompt"]
                    })
                else:
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": "All docs received. Running analysis..."
                    })

                st.rerun()
            else:
                st.error(msg)

    # -------- ANALYSIS (FIXED CLEAN) --------
    elif stage == "analysis_pending":

        if "analysis_started" not in st.session_state:
            st.session_state.analysis_started = True
            st.session_state.analysis_done = False
            st.session_state.final_result = None
            st.session_state.last_refresh = time.time()

            def task():
                result = run_final_analysis(st.session_state.selected_model)
                st.session_state.final_result = result
                st.session_state.analysis_done = True

            threading.Thread(target=task).start()

        if not st.session_state.analysis_done:
            st.info("⏳ Running analysis... please wait")

            if time.time() - st.session_state.last_refresh > 3:
                st.session_state.last_refresh = time.time()
                st.rerun()

            st.stop()

        if st.session_state.analysis_done:
            st.session_state.messages.append({
                "role": "assistant",
                "content": st.session_state.final_result
            })

            st.session_state.messages.append({
                "role": "assistant",
                "content": "Analysis complete. Ask questions."
            })

            st.session_state.doc_upload_stage = "chat_active"

            del st.session_state.analysis_started
            del st.session_state.analysis_done
            del st.session_state.final_result
            del st.session_state.last_refresh

            st.rerun()

    # -------- CHAT --------
    elif stage == "chat_active":
        if prompt := st.chat_input("Ask something"):
            st.session_state.messages.append({"role": "user", "content": prompt})

            response = get_chatbot_response(prompt)

            st.session_state.messages.append({"role": "assistant", "content": response})
            st.rerun()
