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
CODE_EXPIRY_TIME = 60  # 1 minute

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

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def get_remaining_time(start_time):
    elapsed = (datetime.now() - start_time).total_seconds()
    return max(0, CODE_EXPIRY_TIME - int(elapsed))

# Load existing sessions
if 'sessions' not in st.session_state:
    st.session_state.sessions = load_sessions()

if 'code' not in st.session_state:
    st.session_state.code = None

if 'upload_time' not in st.session_state:
    st.session_state.upload_time = None

def update_code():
    if st.session_state.upload_time:
        elapsed = (datetime.now() - st.session_state.upload_time).total_seconds()
        if elapsed >= CODE_EXPIRY_TIME:
            st.session_state.code = generate_code()
            st.session_state.upload_time = datetime.now()
            st.session_state.sessions[st.session_state.code] = st.session_state.sessions.pop(st.session_state.old_code, {})
            save_sessions(st.session_state.sessions)
            st.session_state.old_code = st.session_state.code

# Set page config
st.set_page_config(page_title="File Share", page_icon="📁", layout="wide")

# Main title
st.title("📁 File Share")

# Create tabs for Upload and Download
tab1, tab2 = st.tabs(["Upload File", "Download File"])

# Upload Tab
with tab1:
    st.header("Upload a File")
    uploaded_file = st.file_uploader("Choose a file", type=list(ALLOWED_EXTENSIONS))
    
    if uploaded_file:
        filename = secure_filename(uploaded_file.name)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getvalue())
        
        st.session_state.old_code = st.session_state.code
        st.session_state.code = generate_code()
        st.session_state.upload_time = datetime.now()
        
        st.session_state.sessions[st.session_state.code] = {
            'filename': filename,
            'file_path': file_path,
            'created_at': datetime.now().isoformat(),
            'downloads': 0
        }
        save_sessions(st.session_state.sessions)
        
        st.success("File uploaded successfully!")
        st.markdown(f"### Share this code: `{st.session_state.code}`")
        
# Timer Display
if st.session_state.upload_time:
    time_left = get_remaining_time(st.session_state.upload_time)
    st.write(f"Code expires in: {time_left} seconds")
    st.experimental_rerun()

# Download Tab
with tab2:
    st.header("Download a File")
    code = st.text_input("Enter 6-digit code", "").strip().upper()
    
    if st.button("Download File"):
        update_code()
        if code and code in st.session_state.sessions:
            session = st.session_state.sessions[code]
            
            with open(session['file_path'], "rb") as f:
                st.download_button(label="Click to Download", data=f, file_name=session['filename'], mime="application/octet-stream")
        else:
            st.error("Invalid or expired code")

st.markdown("---")
st.markdown("Files are available, but codes expire every 1 minute.")
