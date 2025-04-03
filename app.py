import os
import random
import string
import json
import time
from datetime import datetime, timedelta
import streamlit as st
from werkzeug.utils import secure_filename

# Configuration
UPLOAD_FOLDER = 'uploads'
SESSIONS_FILE = 'sessions.json'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}
CODE_EXPIRY = 60  # 60 seconds

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_sessions(sessions):
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def cleanup_expired_sessions():
    current_time = time.time()
    expired_codes = [code for code, session in sessions.items() if current_time - session['created_at'] > CODE_EXPIRY]
    for code in expired_codes:
        try:
            os.remove(sessions[code]['file_path'])
        except:
            pass
        del sessions[code]
    save_sessions(sessions)

# Load existing sessions
sessions = load_sessions()

def update_timer():
    if 'code_expiry_time' in st.session_state:
        remaining_time = max(0, int(st.session_state['code_expiry_time'] - time.time()))
        return remaining_time
    return 0

st.set_page_config(page_title="File Share", page_icon="📁", layout="wide")

st.title("📁 File Share")
tab1, tab2 = st.tabs(["Upload File", "Download File"])

with tab1:
    st.header("Upload a File")
    uploaded_file = st.file_uploader("Choose a file", type=list(ALLOWED_EXTENSIONS))
    
    if uploaded_file:
        if allowed_file(uploaded_file.name):
            if 'current_code' not in st.session_state or time.time() >= st.session_state.get('code_expiry_time', 0):
                st.session_state['current_code'] = generate_code()
                st.session_state['code_expiry_time'] = time.time() + CODE_EXPIRY
            
            filename = secure_filename(uploaded_file.name)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            sessions[st.session_state['current_code']] = {
                'filename': filename,
                'file_path': file_path,
                'created_at': time.time()
            }
            save_sessions(sessions)
            
            st.success("File uploaded successfully!")
            st.markdown(f"### Share this code: `{st.session_state['current_code']}`")
            
            timer_placeholder = st.empty()
            while update_timer() > 0:
                timer_placeholder.markdown(f"**Code expires in {update_timer()} seconds**")
                time.sleep(1)
                st.experimental_rerun()
        else:
            st.error("File type not allowed")

with tab2:
    st.header("Download a File")
    code = st.text_input("Enter 6-digit code", "").strip().upper()
    
    if st.button("Download File"):
        cleanup_expired_sessions()
        if not code:
            st.error("Please enter a code")
        elif code not in sessions:
            st.error("Invalid or expired code")
        else:
            session = sessions[code]
            with open(session['file_path'], "rb") as f:
                st.download_button(
                    label="Click to Download",
                    data=f,
                    file_name=session['filename'],
                    mime="application/octet-stream"
                )
