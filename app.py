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
                valid_sessions = {}
                for code, session in sessions_data.items():
                    try:
                        session['created_at'] = datetime.fromisoformat(session['created_at'])
                        session['file_path'] = session.get('file_path', '')
                        session['filename'] = session.get('filename', 'unknown')
                        session['downloads'] = session.get('downloads', 0)
                        valid_sessions[code] = session
                    except Exception as e:
                        print(f"Error processing session {code}: {str(e)}")
                return valid_sessions
        except (json.JSONDecodeError, Exception) as e:
            print(f"Error loading sessions: {str(e)}")
            return {}
    return {}

def save_sessions(sessions):
    try:
        sessions_data = {}
        for code, session in sessions.items():
            session_copy = session.copy()
            session_copy['created_at'] = session['created_at'].isoformat()
            sessions_data[code] = session_copy
        
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions_data, f, indent=2)
    except Exception as e:
        print(f"Error saving sessions: {str(e)}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

def cleanup_expired_sessions():
    current_time = datetime.now()
    expired_sessions = []
    
    for code, session in sessions.items():
        if current_time - session['created_at'] > timedelta(minutes=1):
            expired_sessions.append(code)
            try:
                if os.path.exists(session['file_path']):
                    os.remove(session['file_path'])
            except Exception as e:
                print(f"Error deleting file {session['file_path']}: {str(e)}")
    
    for code in expired_sessions:
        del sessions[code]
    
    try:
        save_sessions(sessions)
    except Exception as e:
        print(f"Error during cleanup: {str(e)}")

# Load sessions with error handling
try:
    sessions = load_sessions()
except Exception as e:
    print(f"Critical error loading sessions: {str(e)}")
    sessions = {}

# Streamlit UI Configuration
st.set_page_config(
    page_title="File Share",
    page_icon="📁",
    layout="wide"
)

# Auto-refresh every 5 seconds
st.markdown("""
    <meta http-equiv="refresh" content="5">
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
    }
    .timer {
        font-size: 1.1rem;
        color: #666;
        margin-top: -15px;
        text-align: center;
    }
    .expired-warning {
        color: #ff4444;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# Main App
st.title("📁 File Share")
tab1, tab2 = st.tabs(["Upload File", "Download File"])

with tab1:
    st.header("Upload a File")
    uploaded_file = st.file_uploader("Choose file (max 50MB)", type=list(ALLOWED_EXTENSIONS))
    
    if uploaded_file:
        if 'current_code' not in st.session_state or 'file_data' not in st.session_state:
            if allowed_file(uploaded_file.name) and uploaded_file.size <= MAX_FILE_SIZE:
                try:
                    # Store file data in session state
                    st.session_state.file_data = uploaded_file.getvalue()
                    st.session_state.filename = secure_filename(uploaded_file.name)
                    st.session_state.current_code = generate_code()
                    st.session_state.upload_time = datetime.now()
                    
                    # Save to disk and sessions
                    file_path = os.path.join(UPLOAD_FOLDER, st.session_state.filename)
                    with open(file_path, "wb") as f:
                        f.write(st.session_state.file_data)
                    
                    sessions[st.session_state.current_code] = {
                        'filename': st.session_state.filename,
                        'file_path': file_path,
                        'created_at': st.session_state.upload_time,
                        'downloads': 0
                    }
                    save_sessions(sessions)
                except Exception as e:
                    st.error(f"Error saving file: {str(e)}")
            else:
                st.error("Invalid file type or size")
        
        if 'current_code' in st.session_state:
            code = st.session_state.current_code
            if code in sessions:
                session = sessions[code]
                time_elapsed = datetime.now() - session['created_at']
                
                # Auto-regenerate code if expired
                if time_elapsed > timedelta(minutes=1):
                    try:
                        os.remove(session['file_path'])
                    except:
                        pass
                    del sessions[code]
                    save_sessions(sessions)
                    
                    # Generate new code and resave file
                    new_code = generate_code()
                    new_file_path = os.path.join(UPLOAD_FOLDER, st.session_state.filename)
                    with open(new_file_path, "wb") as f:
                        f.write(st.session_state.file_data)
                    
                    sessions[new_code] = {
                        'filename': st.session_state.filename,
                        'file_path': new_file_path,
                        'created_at': datetime.now(),
                        'downloads': 0
                    }
                    save_sessions(sessions)
                    
                    st.session_state.current_code = new_code
                    st.rerun()

                # Display current code and timer
                st.success("File uploaded successfully!")
                st.markdown("### Share this code:")
                st.markdown(f'<div class="code-display">{code}</div>', unsafe_allow_html=True)
                
                # Timer display
                time_left = timedelta(minutes=1) - time_elapsed
                mins, secs = divmod(time_left.seconds, 60)
                st.markdown(
                    f'<div class="timer">⏳ Expires in: {mins:02d}:{secs:02d}</div>',
                    unsafe_allow_html=True
                )
                
                # Copy button
                if st.button("Copy Code"):
                    st.write(f"Copied to clipboard: {code}")
                    st.experimental_set_query_params(code=code)
                    js_code = f"""
                    <script>
                    navigator.clipboard.writeText('{code}');
                    </script>
                    """
                    st.components.v1.html(js_code)

with tab2:
    st.header("Download File")
    input_code = st.text_input("Enter 6-digit code", "").strip().upper()
    
    if st.button("Download"):
        if not input_code:
            st.error("Please enter a code")
        elif input_code not in sessions:
            st.error("Invalid code")
        else:
            session = sessions[input_code]
            if datetime.now() - session['created_at'] > timedelta(minutes=1):
                st.error("Code has expired")
                try:
                    if os.path.exists(session['file_path']):
                        os.remove(session['file_path'])
                    del sessions[input_code]
                    save_sessions(sessions)
                except Exception as e:
                    st.error(f"Error cleaning up expired file: {str(e)}")
            else:
                try:
                    with open(session['file_path'], "rb") as f:
                        st.download_button(
                            label="Download File",
                            data=f,
                            file_name=session['filename'],
                            mime="application/octet-stream"
                        )
                    sessions[input_code]['downloads'] += 1
                    save_sessions(sessions)
                except Exception as e:
                    st.error(f"File not found: {str(e)}")

# Regular cleanup
try:
    cleanup_expired_sessions()
except Exception as e:
    st.error(f"Cleanup error: {str(e)}")

st.markdown("---")
st.caption("Files auto-delete after 1 minute • Max file size: 50MB")
