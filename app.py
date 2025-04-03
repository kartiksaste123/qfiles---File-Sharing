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
CODE_EXPIRY_TIME = 60  # 1 minute

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load existing sessions
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

def update_code():
    if 'file_data' in st.session_state:
        st.session_state['file_data']['code'] = generate_code()
        st.session_state['file_data']['expires_at'] = datetime.now() + timedelta(seconds=CODE_EXPIRY_TIME)
        save_sessions(sessions)

# Load sessions
sessions = load_sessions()

# Streamlit page config
st.set_page_config(page_title="File Share", page_icon="📁", layout="wide")

st.title("📁 File Share")

# Tabs for Upload & Download
tab1, tab2 = st.tabs(["Upload File", "Download File"])

with tab1:
    st.header("Upload a File")
    uploaded_file = st.file_uploader("Choose a file", type=list(ALLOWED_EXTENSIONS))
    
    if uploaded_file is not None:
        if allowed_file(uploaded_file.name):
            filename = secure_filename(uploaded_file.name)
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getvalue())
            
            code = generate_code()
            expires_at = datetime.now() + timedelta(seconds=CODE_EXPIRY_TIME)
            
            # Store file details in session state
            st.session_state['file_data'] = {
                'filename': filename,
                'file_path': file_path,
                'code': code,
                'expires_at': expires_at.isoformat()
            }
            
            # Save session
            sessions[code] = st.session_state['file_data']
            save_sessions(sessions)
            
            st.success("File uploaded successfully!")

# Display the code & countdown timer if a file is uploaded
if 'file_data' in st.session_state:
    file_data = st.session_state['file_data']
    remaining_time = (datetime.fromisoformat(file_data['expires_at']) - datetime.now()).seconds
    st.markdown(f"### Share this code: `{file_data['code']}`")
    st.markdown(f"**Code expires in: {remaining_time} seconds**")
    
    # Auto update the code when expired
    if remaining_time <= 0:
        update_code()

with tab2:
    st.header("Download a File")
    code = st.text_input("Enter 6-digit code", "").strip().upper()
    
    if st.button("Download File"):
        if code in sessions:
            file_data = sessions[code]
            if datetime.now() > datetime.fromisoformat(file_data['expires_at']):
                st.error("This code has expired.")
            else:
                with open(file_data['file_path'], "rb") as f:
                    st.download_button(label="Click to Download", data=f, file_name=file_data['filename'], mime="application/octet-stream")
        else:
            st.error("Invalid or expired code.")
