import os
import time
import json
import random
import string
import streamlit as st
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename

# Configuration
UPLOAD_FOLDER = 'uploads'
SESSIONS_FILE = 'sessions.json'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
CODE_EXPIRY = 60  # Code expires in 60 seconds

# Ensure uploads directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_sessions():
    """Load session data from JSON file."""
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    """Save session data to JSON file."""
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_code():
    """Generate a 6-character random code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def cleanup_expired_sessions():
    """Remove expired session files."""
    current_time = time.time()
    expired_codes = [code for code, session in sessions.items() if current_time - session["created_at"] > CODE_EXPIRY]
    
    for code in expired_codes:
        try:
            os.remove(sessions[code]["file_path"])
        except:
            pass
        del sessions[code]
    
    save_sessions(sessions)

# Load existing sessions
sessions = load_sessions()

# Initialize session state variables
if "current_code" not in st.session_state or "code_expiry_time" not in st.session_state:
    st.session_state["current_code"] = None
    st.session_state["code_expiry_time"] = 0

# Streamlit Page Configuration
st.set_page_config(page_title="File Share", page_icon="📁", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin-top: 10px;
    }
    .code-display {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        font-family: monospace;
        font-size: 1.2rem;
        text-align: center;
        margin: 20px 0;
    }
    </style>
""", unsafe_allow_html=True)

# Main title
st.title("📁 File Share")

# Tabs for Upload and Download
tab1, tab2 = st.tabs(["Upload File", "Download File"])

# --- UPLOAD TAB ---
with tab1:
    st.header("Upload a File")
    st.write("Select a file to share (max 200MB)")

    uploaded_file = st.file_uploader("Choose a file", type=list(ALLOWED_EXTENSIONS))

    if uploaded_file:
        if allowed_file(uploaded_file.name):
            # Check if current code expired, then generate a new one
            if not st.session_state["current_code"] or time.time() >= st.session_state["code_expiry_time"]:
                st.session_state["current_code"] = generate_code()
                st.session_state["code_expiry_time"] = time.time() + CODE_EXPIRY

            filename = secure_filename(uploaded_file.name)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # Store session info
            sessions[st.session_state["current_code"]] = {
                "filename": filename,
                "file_path": file_path,
                "created_at": time.time()
            }
            save_sessions(sessions)

            st.success("File uploaded successfully!")
            
            # Display file-sharing code
            st.markdown(f"### Share this code: `{st.session_state['current_code']}`")

            # Live countdown timer
            timer_placeholder = st.empty()
            
            def update_timer():
                while time.time() < st.session_state["code_expiry_time"]:
                    remaining_time = int(st.session_state["code_expiry_time"] - time.time())
                    timer_placeholder.markdown(f"**Code expires in {remaining_time} seconds**")
                    time.sleep(1)
                # Generate new code and reset timer
                st.session_state["current_code"] = generate_code()
                st.session_state["code_expiry_time"] = time.time() + CODE_EXPIRY
                st.experimental_rerun()

            st.button("Copy Code", key="copy_upload")  # No change on copy

            # Start timer in background
            st.thread(update_timer)

        else:
            st.error("File type not allowed")

# --- DOWNLOAD TAB ---
with tab2:
    st.header("Download a File")
    st.write("Enter the code provided by the file owner")

    code = st.text_input("Enter 6-digit code", "").strip().upper()

    if st.button("Download File"):
        if not code:
            st.error("Please enter a code")
        elif code not in sessions:
            st.error("Invalid or expired code")
        else:
            session = sessions[code]

            # Check if file has expired
            if time.time() - session["created_at"] > CODE_EXPIRY:
                try:
                    os.remove(session["file_path"])
                except:
                    pass
                del sessions[code]
                save_sessions(sessions)
                st.error("This file has expired")
            else:
                with open(session["file_path"], "rb") as f:
                    st.download_button(
                        label="Click to Download",
                        data=f,
                        file_name=session["filename"],
                        mime="application/octet-stream"
                    )

# Cleanup expired files
cleanup_expired_sessions()

# Footer
st.markdown("---")
st.markdown("⚠️ Files are automatically deleted after **1 minute**.")
