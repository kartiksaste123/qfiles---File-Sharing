import os
import random
import string
import json
from datetime import datetime, timedelta
import streamlit as st
from werkzeug.utils import secure_filename
from streamlit_autorefresh import st_autorefresh

# Configuration
UPLOAD_FOLDER = "uploads"
SESSIONS_FILE = "sessions.json"
ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "doc", "docx", "xls", "xlsx", "zip", "rar"}
CODE_EXPIRY = timedelta(minutes=1)

# Create uploads directory if not exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, "r") as f:
            sessions_data = json.load(f)
            for code, session in sessions_data.items():
                session["created_at"] = datetime.fromisoformat(session["created_at"])
            return sessions_data
    return {}

def save_sessions(sessions):
    sessions_data = {code: {**session, "created_at": session["created_at"].isoformat()} for code, session in sessions.items()}
    with open(SESSIONS_FILE, "w") as f:
        json.dump(sessions_data, f)

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_code():
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=6))

def update_code():
    if "current_code" not in st.session_state or datetime.now() - st.session_state["code_created_at"] >= CODE_EXPIRY:
        st.session_state["current_code"] = generate_code()
        st.session_state["code_created_at"] = datetime.now()
        st.session_state["expired_codes"].append(st.session_state["current_code"])

# Load sessions
sessions = load_sessions()

def cleanup_expired_sessions():
    expired_codes = [code for code in sessions if datetime.now() - sessions[code]["created_at"] > CODE_EXPIRY]
    for code in expired_codes:
        del sessions[code]
    save_sessions(sessions)

st.set_page_config(page_title="File Share", page_icon="📁", layout="wide")
st.markdown("""
    <style>
    .stButton>button { width: 100%; margin-top: 10px; }
    .code-display { background-color: #f0f2f6; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 1.2rem; text-align: center; margin: 20px 0; }
    </style>
""", unsafe_allow_html=True)

st.title("📁 File Share")
tab1, tab2 = st.tabs(["Upload File", "Download File"])

if "expired_codes" not in st.session_state:
    st.session_state["expired_codes"] = []
update_code()
st_autorefresh(interval=1000, key="refresh_timer")  # Auto refresh every second

with tab1:
    st.header("Upload a File")
    uploaded_file = st.file_uploader("Choose a file", type=list(ALLOWED_EXTENSIONS))
    
    if uploaded_file is not None:
        if allowed_file(uploaded_file.name):
            filename = secure_filename(uploaded_file.name)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            sessions[st.session_state["current_code"]] = {"filename": filename, "file_path": file_path, "created_at": datetime.now(), "downloads": 0}
            save_sessions(sessions)
            st.success("File uploaded successfully!")
            st.markdown(f"### Share this code: <div class='code-display'>{st.session_state['current_code']}</div>", unsafe_allow_html=True)
            time_left = CODE_EXPIRY.total_seconds() - (datetime.now() - st.session_state["code_created_at"]).total_seconds()
            st.markdown(f"#### Code expires in: {int(time_left)} seconds", unsafe_allow_html=True)
        else:
            st.error("File type not allowed")

with tab2:
    st.header("Download a File")
    code = st.text_input("Enter 6-digit code", "").strip().upper()
    
    if st.button("Download File"):
        if not code:
            st.error("Please enter a code")
        elif code in st.session_state["expired_codes"]:
            st.error("This code has expired")
        elif code not in sessions:
            st.error("Invalid code")
        else:
            session = sessions[code]
            with open(session["file_path"], "rb") as f:
                st.download_button(label="Click to Download", data=f, file_name=session["filename"], mime="application/octet-stream")
cleanup_expired_sessions()
st.markdown("---")
st.markdown("Files are automatically deleted after 24 hours")
