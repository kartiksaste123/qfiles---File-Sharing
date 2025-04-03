import os
import random
import string
import json
from datetime import datetime, timedelta
import streamlit as st
import time
import pyperclip  # To copy code to clipboard

# Configuration
UPLOAD_FOLDER = 'uploads'
SESSIONS_FILE = 'sessions.json'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'xls', 'xlsx', 'zip', 'rar'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
CODE_EXPIRATION_TIME = timedelta(minutes=1)  # Code expires after 1 minute

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_sessions():
    """Load sessions from the JSON file."""
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            try:
                sessions_data = json.load(f)
                if not isinstance(sessions_data, dict):
                    return {}

                for code, session in sessions_data.items():
                    session['created_at'] = datetime.fromisoformat(session['created_at'])
                    session['last_code_time'] = datetime.fromisoformat(session['last_code_time'])
                    session.setdefault('downloads', 0)

                return sessions_data
            except (json.JSONDecodeError, ValueError, TypeError):
                return {}  # Return empty dict if file is corrupted
    return {}

def save_sessions(sessions):
    """Save sessions to the JSON file."""
    sessions_data = {
        code: {
            'filename': session['filename'],
            'file_path': session['file_path'],
            'created_at': session['created_at'].isoformat(),
            'last_code_time': session['last_code_time'].isoformat(),
            'downloads': session.get('downloads', 0)
        }
        for code, session in sessions.items()
    }
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions_data, f)

def allowed_file(filename):
    """Check if a file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_code():
    """Generate a random 6-character code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def cleanup_expired_sessions():
    """Delete expired sessions and files (older than 24 hours)."""
    current_time = datetime.now()
    expired_sessions = []

    for code, session in sessions.items():
        if current_time - session['created_at'] > timedelta(hours=24):
            expired_sessions.append(code)
            try:
                os.remove(session['file_path'])  # Delete file
            except:
                pass

    for code in expired_sessions:
        del sessions[code]

    save_sessions(sessions)

def regenerate_codes():
    """Regenerate expired codes without affecting active ones."""
    current_time = datetime.now()
    for code, session in list(sessions.items()):
        if current_time - session['last_code_time'] > CODE_EXPIRATION_TIME:
            new_code = generate_code()
            sessions[new_code] = session  # Keep session details
            sessions[new_code]['last_code_time'] = current_time  # Reset timer
            del sessions[code]  # Remove old code

    save_sessions(sessions)

# Load existing sessions
sessions = load_sessions()

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
    .timer {
        font-size: 1rem;
        color: red;
        font-weight: bold;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Page Title
st.title("📁 File Share")

# Tabs for Upload and Download
tab1, tab2 = st.tabs(["Upload File", "Download File"])

# Upload Tab
with tab1:
    st.header("Upload a File")
    st.write("Select a file to share (max 50MB)")

    uploaded_file = st.file_uploader("Choose a file", type=list(ALLOWED_EXTENSIONS))

    if uploaded_file is not None:
        if allowed_file(uploaded_file.name):
            filename = uploaded_file.name
            code = generate_code()

            # Save file
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())

            # Store session info
            sessions[code] = {
                'filename': filename,
                'file_path': file_path,
                'created_at': datetime.now(),
                'last_code_time': datetime.now(),
                'downloads': 0
            }

            save_sessions(sessions)

            # Show the code
            st.success("File uploaded successfully!")
            st.markdown("### Share this code with others:")
            st.markdown(f'<div class="code-display" id="code">{code}</div>', unsafe_allow_html=True)

            # Countdown timer
            for remaining_time in range(60, 0, -1):
                st.markdown(f'<div class="timer">Code expires in: {remaining_time} sec</div>', unsafe_allow_html=True)
                time.sleep(1)
                st.experimental_rerun()

            # Copy button
            if st.button("Copy Code"):
                pyperclip.copy(code)  # Copy code to clipboard
                st.success(f"Copied: {code}")

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
                except:
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

# Cleanup expired sessions and regenerate codes
cleanup_expired_sessions()
regenerate_codes()

# Footer
st.markdown("---")
st.markdown("Files are automatically deleted after 24 hours. Codes expire every 1 minute.") 
