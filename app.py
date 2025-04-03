import os
import random
import string
import json
from datetime import datetime, timedelta
import streamlit as st
from werkzeug.utils import secure_filename

# Configuration
UPLOAD_FOLDER = 'uploads'
SESSIONS_FILE = 'sessions.json'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

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
            for file_path in session['file_paths']:
                try:
                    os.remove(file_path)
                except:
                    pass
    for code in expired_sessions:
        del sessions[code]
    save_sessions(sessions)

# Load existing sessions
sessions = load_sessions()

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

st.title("📁 File Share")

tab1, tab2 = st.tabs(["Upload File", "Download File"])

with tab1:
    st.header("Upload a File")
    st.write("Select multiple files to share (max 200MB per file)")
    
    uploaded_files = st.file_uploader("Choose files", type=list(ALLOWED_EXTENSIONS), accept_multiple_files=True)
    
    if uploaded_files:
        code = generate_code()
        file_paths = []
        
        for uploaded_file in uploaded_files:
            if allowed_file(uploaded_file.name):
                filename = secure_filename(uploaded_file.name)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getvalue())
                file_paths.append(file_path)
            else:
                st.error(f"{uploaded_file.name} is not allowed")
                continue
        
        if file_paths:
            sessions[code] = {
                'file_paths': file_paths,
                'created_at': datetime.now(),
                'downloads': 0
            }
            save_sessions(sessions)
            
            st.success("Files uploaded successfully!")
            st.markdown("### Share this code with others:")
            st.markdown(f'<div class="code-display">{code}</div>', unsafe_allow_html=True)
            
            st.button("Copy Code", key="copy_upload", on_click=lambda: st.write("Code copied to clipboard!"))

with tab2:
    st.header("Download a File")
    st.write("Enter the code provided by the file owner")
    
    code = st.text_input("Enter 6-digit code", "").strip().upper()
    session = sessions.get(code, None)
    
    if session:
        if datetime.now() - session['created_at'] > timedelta(hours=24):
            for file_path in session['file_paths']:
                try:
                    os.remove(file_path)
                except:
                    pass
            del sessions[code]
            save_sessions(sessions)
            st.error("This file session has expired")
        else:
            selected_files = st.multiselect("Select files to download", session['file_paths'], format_func=lambda x: os.path.basename(x))
            
            if st.checkbox("Download all files"):
                selected_files = session['file_paths']
            
            if st.button("Download Selected Files"):
                if selected_files:
                    for file_path in selected_files:
                        with open(file_path, "rb") as f:
                            st.download_button(
                                label=f"Download {os.path.basename(file_path)}",
                                data=f,
                                file_name=os.path.basename(file_path),
                                mime="application/octet-stream"
                            )
                else:
                    st.warning("Select at least one file to download.")
    elif code:
        st.error("Invalid or expired code")

cleanup_expired_sessions()
st.markdown("---")
st.markdown("Files are automatically deleted after 24 hours")
