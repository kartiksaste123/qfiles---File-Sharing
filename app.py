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

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_sessions():
    if os.path.exists(SESSIONS_FILE):
        try:
            with open(SESSIONS_FILE, 'r') as f:
                sessions_data = json.load(f)
                # Convert string timestamps back to datetime objects
                valid_sessions = {}
                for code, session in sessions_data.items():
                    try:
                        # Handle missing created_at field
                        if 'created_at' not in session:
                            session['created_at'] = datetime.now().isoformat()
                        
                        # Ensure all required fields exist
                        session['created_at'] = datetime.fromisoformat(session['created_at'])
                        session['file_path'] = session.get('file_path', '')
                        session['filename'] = session.get('filename', 'unknown')
                        session['downloads'] = session.get('downloads', 0)
                        
                        valid_sessions[code] = session
                    except Exception as e:
                        print(f"Error processing session {code}: {str(e)}")
                        continue
                return valid_sessions
        except json.JSONDecodeError:
            print("Error reading sessions file, returning empty sessions")
            return {}
    return {}

def save_sessions(sessions):
    try:
        # Convert datetime objects to strings for JSON serialization
        sessions_data = {}
        for code, session in sessions.items():
            session_copy = session.copy()
            session_copy['created_at'] = session['created_at'].isoformat()
            sessions_data[code] = session_copy
        
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions_data, f)
    except Exception as e:
        print(f"Error saving sessions: {str(e)}")

# Load existing sessions with error handling
try:
    sessions = load_sessions()
except Exception as e:
    print(f"Error loading sessions: {str(e)}")
    sessions = {}

def save_sessions(sessions):
    # Convert datetime objects to strings for JSON serialization
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
        if current_time - session['created_at'] > timedelta(minutes=1):  # Changed to 1 minute expiration
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
        user-select: all;
        -webkit-user-select: all;
        -moz-user-select: all;
        -ms-user-select: all;
    }
    .timer {
        font-size: 1.1rem;
        color: #666;
        margin-top: -15px;
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
        if 'current_code' not in st.session_state:
            if allowed_file(uploaded_file.name):
                filename = secure_filename(uploaded_file.name)
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
                    'downloads': 0
                }
                
                save_sessions(sessions)
                st.session_state.current_code = code
                st.session_state.uploaded_filename = filename
            else:
                st.error("File type not allowed")
        else:
            # Check if previous upload exists and is valid
            code = st.session_state.current_code
            if code not in sessions or sessions[code]['filename'] != st.session_state.uploaded_filename:
                del st.session_state.current_code
                st.rerun()
        
        if 'current_code' in st.session_state:
            code = st.session_state.current_code
            if code in sessions:
                session = sessions[code]
                st.success("File uploaded successfully!")
                st.markdown("### Share this code with others:")
                st.markdown(f'<div class="code-display">{code}</div>', unsafe_allow_html=True)
                
                # Display timer
                expiration_time = session['created_at'] + timedelta(minutes=1)
                current_time = datetime.now()
                time_left = expiration_time - current_time
                
                if time_left.total_seconds() > 0:
                    minutes = time_left.seconds // 60
                    seconds = time_left.seconds % 60
                    st.markdown(f'<div class="timer">⏳ Code expires in: {minutes:02d}:{seconds:02d}</div>', 
                               unsafe_allow_html=True)
                else:
                    st.error("Code has expired!")
                    cleanup_expired_sessions()
                    del st.session_state.current_code
                    st.rerun()
                
                # Copy button with JavaScript
                if st.button("Copy Code", key="copy_upload"):
                    js_code = f"""
                    <script>
                    navigator.clipboard.writeText('{code}');
                    </script>
                    """
                    st.components.v1.html(js_code)
                    st.success("Code copied to clipboard!")

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
            if datetime.now() - session['created_at'] > timedelta(minutes=1):
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
st.markdown("Files are automatically deleted after 1 minute") 
