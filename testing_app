import os
import random
import string
import json
from datetime import datetime, timedelta
import streamlit as st
from werkzeug.utils import secure_filename
import time

# Configuration
UPLOAD_FOLDER = 'uploads'
SESSIONS_FILE = 'sessions.json'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB
CODE_EXPIRY = 60  # 1 minute

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            sessions_data = json.load(f)
            for code, session in sessions_data.items():
                session['created_at'] = datetime.fromisoformat(session['created_at'])
            return sessions_data
    return {}

def save_sessions(sessions):
    sessions_data = {}
    for code, session in sessions.items():
        session_copy = session.copy()
        session_copy['created_at'] = session['created_at'].isoformat()
        sessions_data[code] = session_copy
    
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions_data, f)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def cleanup_expired_sessions():
    current_time = datetime.now()
    expired_sessions = []
    
    for code, session in sessions.items():
        if current_time - session['created_at'] > timedelta(hours=24):
            expired_sessions.append(code)
            try:
                os.remove(session['file_path'])
            except:
                pass
    
    for code in expired_sessions:
        del sessions[code]
    
    save_sessions(sessions)

# Load existing sessions
sessions = load_sessions()

# Set page config
st.set_page_config(page_title="File Share", page_icon="📁", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .stButton>button { width: 100%; margin-top: 10px; }
    .code-display { background-color: #f0f2f6; padding: 15px; border-radius: 8px; font-family: monospace; font-size: 1.2rem; text-align: center; margin: 20px 0; }
    .timer { font-size: 1rem; font-weight: bold; color: red; text-align: center; }
    </style>
""", unsafe_allow_html=True)

# Main title
st.title("📁 File Share")

tab1, tab2 = st.tabs(["Upload File", "Download File"])

# Upload Tab
with tab1:
    st.header("Upload a File")
    st.write("Select a file to share (max 200MB)")
    
    uploaded_file = st.file_uploader("Choose a file", type=list(ALLOWED_EXTENSIONS))
    
    if uploaded_file is not None:
        if allowed_file(uploaded_file.name):
            filename = secure_filename(uploaded_file.name)
            if "file_code" not in st.session_state or "expiry_time" not in st.session_state or datetime.now() > st.session_state.expiry_time:
                st.session_state.file_code = generate_code()
                st.session_state.expiry_time = datetime.now() + timedelta(seconds=CODE_EXPIRY)
            code = st.session_state.file_code
            
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            sessions[code] = {
                'filename': filename,
                'file_path': file_path,
                'created_at': datetime.now(),
                'downloads': 0
            }
            
            save_sessions(sessions)
            
            st.success("File uploaded successfully!")
            st.markdown("### Share this code with others:")
            st.markdown(f'<div class="code-display">{code}</div>', unsafe_allow_html=True)
            
            time_remaining = int((st.session_state.expiry_time - datetime.now()).total_seconds())
            st.markdown(f'<div class="timer">Code expires in: {time_remaining} seconds</div>', unsafe_allow_html=True)
            
            if st.button("Copy Code"):
                st.session_state.copied = code
                st.success("Code copied to clipboard!")
        else:
            st.error("File type not allowed")

# Download Tab
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
            
            if datetime.now() - session['created_at'] > timedelta(hours=24):
                try:
                    os.remove(session['file_path'])
                except:
                    pass
                del sessions[code]
                save_sessions(sessions)
                st.error("This file has expired")
            else:
                session['downloads'] += 1
                save_sessions(sessions)
                
                with open(session['file_path'], "rb") as f:
                    st.download_button(label="Click to Download", data=f, file_name=session['filename'], mime="application/octet-stream")

cleanup_expired_sessions()
st.markdown("---")
st.markdown("Files are automatically deleted after 24 hours")
