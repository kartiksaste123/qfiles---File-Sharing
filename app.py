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
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
CODE_EXPIRY = timedelta(minutes=1)  # Code expires in 1 minute

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

def get_remaining_time(session):
    elapsed = datetime.now() - session['created_at']
    remaining = CODE_EXPIRY - elapsed
    return max(remaining, timedelta(0))

def cleanup_expired_sessions():
    current_time = datetime.now()
    expired_sessions = []
    for code, session in sessions.items():
        if current_time - session['created_at'] > CODE_EXPIRY:
            new_code = generate_code()
            sessions[new_code] = {**session, 'created_at': current_time}  # Update with new code
            expired_sessions.append(code)
    for code in expired_sessions:
        del sessions[code]
    save_sessions(sessions)

# Load existing sessions
sessions = load_sessions()
cleanup_expired_sessions()

# Set page config
st.set_page_config(page_title="File Share", page_icon="📁", layout="wide")

st.title("📁 File Share")
tab1, tab2 = st.tabs(["Upload File", "Download File"])

# Upload Tab
with tab1:
    st.header("Upload a File")
    uploaded_file = st.file_uploader("Choose a file", type=list(ALLOWED_EXTENSIONS))
    
    if uploaded_file is not None:
        if allowed_file(uploaded_file.name):
            filename = secure_filename(uploaded_file.name)
            code = generate_code()
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
            remaining_time = get_remaining_time(sessions[code])
            st.markdown(f'**Code Expires in:** {remaining_time.seconds} seconds')
            
            st.button("Copy Code", key="copy_upload")
        else:
            st.error("File type not allowed")

# Download Tab
with tab2:
    st.header("Download a File")
    code = st.text_input("Enter 6-digit code", "").strip().upper()
    
    if st.button("Download File"):
        if not code:
            st.error("Please enter a code")
        elif code not in sessions:
            st.error("Invalid or expired code")
        else:
            session = sessions[code]
            if datetime.now() - session['created_at'] > CODE_EXPIRY:
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
st.markdown("Files are automatically deleted after 1 minute")
