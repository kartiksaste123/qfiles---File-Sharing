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
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
CODE_EXPIRATION_TIME = 60  # Code expires after 60 seconds (1 minute)

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            try:
                sessions_data = json.load(f)
                if not isinstance(sessions_data, dict):  # Ensure it's a dictionary
                    return {}
                # Convert timestamps to datetime objects
                for code, session in sessions_data.items():
                    session['created_at'] = datetime.fromisoformat(session['created_at'])
                    session['last_code_time'] = datetime.fromisoformat(session['last_code_time'])
                return sessions_data
            except json.JSONDecodeError:  # Handle corrupted JSON file
                return {}
    return {}  # Return empty dictionary if file doesn't exist

def save_sessions(sessions):
    # Convert datetime objects to strings for JSON serialization
    sessions_data = {}
    for code, session in sessions.items():
        session_copy = session.copy()
        session_copy['created_at'] = session['created_at'].isoformat()
        session_copy['last_code_time'] = session['last_code_time'].isoformat()
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

    for code, session in list(sessions.items()):
        # Delete files older than 24 hours
        if current_time - session['created_at'] > timedelta(hours=24):
            expired_sessions.append(code)
            try:
                os.remove(session['file_path'])
            except FileNotFoundError:
                pass

    for code in expired_sessions:
        del sessions[code]

    save_sessions(sessions)

# Load existing sessions
sessions = load_sessions()

# Ensure sessions is always a dictionary
if not isinstance(sessions, dict):
    sessions = {}

# Set page config
st.set_page_config(
    page_title="File Share",
    page_icon="📁",
    layout="wide"
)

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
    .timer-display {
        font-size: 1rem;
        color: red;
        text-align: center;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Main title
st.title("📁 File Share")

# Create tabs for Upload and Download
tab1, tab2 = st.tabs(["Upload File", "Download File"])

# Upload Tab
with tab1:
    st.header("Upload a File")
    st.write("Select a file to share (max 50MB)")
    
    uploaded_file = st.file_uploader("Choose a file", type=list(ALLOWED_EXTENSIONS))

    if uploaded_file is not None:
        if allowed_file(uploaded_file.name):
            filename = secure_filename(uploaded_file.name)

            # Generate a new code
            code = generate_code()
            current_time = datetime.now()

            # Save file
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # Store session info
            sessions[code] = {
                'filename': filename,
                'file_path': file_path,
                'created_at': current_time,
                'last_code_time': current_time,  # Track when the code was generated
                'downloads': 0
            }

            # Save sessions to file
            save_sessions(sessions)

            # Display success message and code
            st.success("File uploaded successfully!")
            st.markdown("### Share this code with others:")
            code_display = st.empty()
            code_display.markdown(f'<div class="code-display">{code}</div>', unsafe_allow_html=True)

            # Countdown Timer
            timer_display = st.empty()

            def update_timer():
                while (datetime.now() - sessions[code]['last_code_time']).seconds < CODE_EXPIRATION_TIME:
                    remaining_time = CODE_EXPIRATION_TIME - (datetime.now() - sessions[code]['last_code_time']).seconds
                    timer_display.markdown(f'<div class="timer-display">Code expires in {remaining_time} seconds</div>', unsafe_allow_html=True)
                    time.sleep(1)

                # Generate new code after expiration
                new_code = generate_code()
                sessions[new_code] = sessions.pop(code)
                sessions[new_code]['last_code_time'] = datetime.now()
                save_sessions(sessions)
                code_display.markdown(f'<div class="code-display">{new_code}</div>', unsafe_allow_html=True)
                timer_display.markdown(f'<div class="timer-display">New code generated!</div>', unsafe_allow_html=True)

            st.button("Copy Code", key="copy_upload")
            st.thread(update_timer)  # Start the countdown in the background

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

            # Check if file has expired
            if datetime.now() - session['created_at'] > timedelta(hours=24):
                try:
                    os.remove(session['file_path'])
                except FileNotFoundError:
                    pass
                del sessions[code]
                save_sessions(sessions)
                st.error("This file has expired")
            else:
                session['downloads'] += 1
                save_sessions(sessions)

                # Create download button
                with open(session['file_path'], "rb") as f:
                    st.download_button(
                        label="Click to Download",
                        data=f,
                        file_name=session['filename'],
                        mime="application/octet-stream"
                    )

# Cleanup expired sessions
cleanup_expired_sessions()

# Footer
st.markdown("---")
st.markdown("Files are automatically deleted after 24 hours")
