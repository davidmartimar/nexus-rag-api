import streamlit as st
import requests
import time
import base64
import os
from fpdf import FPDF

# --- CONFIGURATION ---
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")
NEXUS_API_KEY = os.getenv("NEXUS_API_KEY")
API_HEADERS = {"X-NEXUS-KEY": NEXUS_API_KEY} if NEXUS_API_KEY else {}

# --- ASSET PATH RESOLUTION ---
current_dir = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(current_dir, "nexus_logo.svg")

# Fallback: Create the file if it doesn't exist
if not os.path.exists(LOGO_PATH):
    svg_content = """
    <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
      <rect width="100" height="100" rx="20" fill="#4F46E5"/>
      <text x="50" y="65" font-family="Arial, sans-serif" font-size="60" font-weight="bold" fill="white" text-anchor="middle">ネ</text>
    </svg>
    """
    try:
        with open(LOGO_PATH, "w", encoding="utf-8") as f:
            f.write(svg_content)
    except Exception as e:
        print(f"Error generating logo asset: {e}")

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="NEXUS CORE",
    page_icon="⚛️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS ---
st.markdown("""
    <style>
        /* GLOBAL STYLES */
        .stApp {
            background-color: #0f172a;
            color: #e2e8f0;
        }
        
        /* TYPOGRAPHY */
        h1, h2, h3 {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            color: #f8fafc;
        }
        
        /* LOGO STYLES */
        .nexus-logo {
            font-family: 'Inter', sans-serif;
            font-weight: 800;
            font-size: 2.2rem;
            color: #FFFFFF;
            letter-spacing: -0.05em;
            margin-bottom: 0;
            line-height: 1.2;
        }
        .nexus-accent {
            color: #6366f1;
            margin-right: 8px;
        }
        .nexus-subtitle {
            font-family: 'Inter', sans-serif;
            font-weight: 400;
            font-size: 0.85rem;
            color: #94a3b8;
            margin-top: 2px;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        /* STATUS INDICATOR */
        .status-badge {
            display: inline-flex;
            align-items: center;
            padding: 4px 12px;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }
        .status-online {
            background-color: rgba(74, 222, 128, 0.1);
            color: #4ade80;
            border: 1px solid rgba(74, 222, 128, 0.2);
        }
        .status-offline {
            background-color: rgba(248, 113, 113, 0.1);
            color: #f87171;
            border: 1px solid rgba(248, 113, 113, 0.2);
        }
        .status-waiting {
            background-color: rgba(248, 113, 113, 0.1);
            color: #f87171;
            border: 1px solid rgba(248, 113, 113, 0.2);
        }
        .status-ready {
            background-color: rgba(74, 222, 128, 0.1);
            color: #4ade80;
            border: 1px solid rgba(74, 222, 128, 0.2);
        }
        .status-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            margin-right: 8px;
        }
        .status-online .status-dot { background-color: #4ade80; box-shadow: 0 0 8px rgba(74, 222, 128, 0.5); }
        .status-offline .status-dot { background-color: #f87171; }
        .status-waiting .status-dot { background-color: #f87171; animation: pulse 2s infinite; }
        .status-ready .status-dot { background-color: #4ade80; box-shadow: 0 0 8px rgba(74, 222, 128, 0.5); }

        /* CHAT INTERFACE */
        .stChatMessage {
            background-color: rgba(30, 41, 59, 0.5);
            border: 1px solid rgba(148, 163, 184, 0.1);
            border-radius: 12px;
        }
        
        /* SIDEBAR */
        section[data-testid="stSidebar"] {
            background-color: #1e293b;
            border-right: 1px solid #334155;
        }
        
        /* BUTTONS */
        .stButton button {
            background-color: #4f46e5;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .stButton button:hover {
            background-color: #4338ca;
            box-shadow: 0 4px 12px rgba(79, 70, 229, 0.3);
        }

        /* CHAT INPUT CONTAINER */
        /* Reverted to defaults but keeping footer hidden */
        footer { visibility: hidden; }
        
        /* Remove the gray background/shadow from the bottom container AND its children */
        div[data-testid="stBottom"],
        div[data-testid="stBottom"] > div,
        section[data-testid="stBottom"] {
            background-color: transparent !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
        }

        /* Essential: Make the wrapper distinct from the input box transparent */
        .stChatInputContainer {
            background-color: transparent !important;
            padding-bottom: 20px;
        }

        /* Style the actual input box to make it distinct */
        .stChatInputContainer textarea {
            background-color: #1e293b !important;
            border: 1px solid #334155 !important;
            color: #f8fafc !important;
            border-radius: 12px !important;
        }
    </style>
""", unsafe_allow_html=True)

# --- SECURITY: LOGIN SCREEN ---
def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        # CLOUD-NATIVE AUTH: Priority to Environment Variables
        env_password = os.getenv("NEXUS_FRONTEND_PASSWORD")
        
        # Local Fallback: secrets.toml (for dev)
        if not env_password:
            try:
                env_password = st.secrets["general"]["password"]
            except (FileNotFoundError, KeyError):
                pass
        
        if not env_password:
             st.error("🚨 Configuration Error: NEXUS_FRONTEND_PASSWORD not set in Environment or secrets.toml")
             return

        if st.session_state["password"] == env_password:
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password.
        st.write("") # Spacer
        st.write("") 
        st.write("")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("""
                <div style="text-align: center; margin-bottom: 30px;">
                    <div class="nexus-logo" style="font-size: 3.5rem;"><span class="nexus-accent">ネ</span>NEXUS</div>
                    <div class="nexus-subtitle">System Locked • Authorization Required</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown(
                """
                <style>
                .stTextInput > div > div > input {
                    background-color: #1e293b;
                    color: #f8fafc;
                    border: 1px solid #334155;
                    text-align: center;
                }
                </style>
                """, unsafe_allow_html=True)
            
            st.text_input(
                "Access Code", 
                type="password", 
                on_change=password_entered, 
                key="password",
                label_visibility="collapsed",
                placeholder="Enter Access Key"
            )
        return False
        
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error.
        st.write("") # Spacer
        st.write("") 
        st.write("")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            st.markdown("""
                <div style="text-align: center; margin-bottom: 30px;">
                    <div class="nexus-logo" style="font-size: 3.5rem;"><span class="nexus-accent">ネ</span>NEXUS</div>
                    <div class="nexus-subtitle" style="color: #f87171;">⛔ Access Denied</div>
                </div>
            """, unsafe_allow_html=True)
            
            st.text_input(
                "Access Code", 
                type="password", 
                on_change=password_entered, 
                key="password", 
                label_visibility="collapsed",
                placeholder="Enter Access Key"
            )
        return False
    else:
        # Password correct.
        return True

if not check_password():
    st.stop()


# --- AVATAR GENERATOR ---
def get_nexus_avatar_b64():
    try:
        with open(LOGO_PATH, "r", encoding="utf-8") as f:
            svg = f.read()
        b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
        return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        return None

NEXUS_AVATAR_URL = get_nexus_avatar_b64()



# --- HELPER FUNCTIONS ---
def render_logo(size="large"):
    if size == "small":
        st.markdown('<div style="font-weight:800; font-size:1.5rem; color:#fff; margin-bottom: 20px;"><span style="color:#6366f1">ネ</span> NEXUS</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="margin-bottom: 20px;">
                <div class="nexus-logo"><span class="nexus-accent">ネ</span>NEXUS</div>
                <div class="nexus-subtitle">Enterprise Knowledge Engine</div>
            </div>
        """, unsafe_allow_html=True)

def typewriter_effect(text, placeholder):
    displayed_text = ""
    for word in text.split(" "):
        displayed_text += word + " "
        placeholder.markdown(displayed_text + "▌")
        time.sleep(0.02)
    placeholder.markdown(displayed_text)

def check_system_status(collection_name="nexus_slot_1"):
    try:
        params = {"collection_name": collection_name}
        response = requests.get(f"{BACKEND_URL}/api/v1/status", params=params, headers=API_HEADERS, timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"status": "offline", "ready": False, "document_count": 0}



def get_uploaded_documents(collection_name="nexus_slot_1"):
    try:
        params = {"collection_name": collection_name}
        response = requests.get(f"{BACKEND_URL}/api/v1/documents", params=params, headers=API_HEADERS, timeout=2)
        if response.status_code == 200:
            return response.json().get("documents", [])
    except:
        pass
    return []

def get_slot_config():
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/config", headers=API_HEADERS, timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def save_slot_config(config):
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/config", json=config, headers=API_HEADERS, timeout=5)
        return response.status_code == 200
    except:
        return False

def add_new_slot(name):
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/slots", json={"name": name}, headers=API_HEADERS, timeout=5)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

def remove_slot(slot_id):
    try:
        response = requests.delete(f"{BACKEND_URL}/api/v1/slots/{slot_id}", headers=API_HEADERS, timeout=5)
        return response.status_code == 200
    except:
        return False

def delete_document(filename, collection_name="nexus_slot_1"):
    try:
        params = {"collection_name": collection_name}
        response = requests.delete(f"{BACKEND_URL}/api/v1/documents/{filename}", params=params, headers=API_HEADERS, timeout=5)
        return response.status_code == 200
    except:
        return False



def reset_knowledge_base(collection_name):
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/reset", json={"collection_name": collection_name}, headers=API_HEADERS, timeout=10)
        return response.status_code == 200
    except:
        return False

def download_backup():
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/backup", headers=API_HEADERS, timeout=60)
        if response.status_code == 200:
            return response.content
    except:
        pass
    return None

def restore_backup(file):
    try:
        files = {"file": ("backup.zip", file, "application/zip")}
        response = requests.post(f"{BACKEND_URL}/api/v1/restore", files=files, headers=API_HEADERS, timeout=60)
        return response.status_code == 200
    except:
        return False

def create_pdf(messages):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.cell(200, 10, txt="NEXUS Conversation Log", ln=True, align='C')
    pdf.ln(10)
    
    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"]
        
        # Simple sanitization
        content = content.encode('latin-1', 'replace').decode('latin-1')
        
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, txt=f"{role}:", ln=True)
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, txt=content)
        pdf.ln(5)
        
    return pdf.output(dest="S").encode("latin-1")

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Welcome to Nexus. Secure connection established."})

if "uploader_key" not in st.session_state:
    st.session_state["uploader_key"] = 0

if "selected_slot" not in st.session_state:
    st.session_state["selected_slot"] = "nexus_slot_1"

if "slot_names" not in st.session_state:
    # Try fetching from backend with retries (important after restart)
    remote_config = None
    with st.spinner("Connecting to Neural Core..."):
        for i in range(60):
            remote_config = get_slot_config()
            if remote_config:
                break
            time.sleep(1)
        
    if remote_config:
        st.session_state["slot_names"] = remote_config
    else:
        # Fallback default
        st.error("⚠️ Connection to Neural Core timed out. Using offline defaults.")
        st.session_state["slot_names"] = {
            "nexus_slot_1": "Memory Slot 1"
        }
        st.session_state["selected_slot"] = "nexus_slot_1"

SLOTS = st.session_state["slot_names"]



system_status = check_system_status(st.session_state["selected_slot"])
is_online = system_status.get("status") == "online"
has_knowledge = system_status.get("ready", False)

# --- UI LAYOUT: HEADER ---
col1, col2 = st.columns([8, 2])
with col1:
    render_logo()
with col2:
    if is_online:
        if has_knowledge:
             st.markdown("""
                <div style="text-align:right; margin-top: 15px;">
                    <div class="status-badge status-ready">
                        <span class="status-dot"></span>
                        KNOWLEDGE IS READY
                    </div>
                </div>
            """, unsafe_allow_html=True)
        else:
             st.markdown("""
                <div style="text-align:right; margin-top: 15px;">
                    <div class="status-badge status-waiting">
                        <span class="status-dot"></span>
                        WAITING FOR KNOWLEDGE
                    </div>
                </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("""
            <div style="text-align:right; margin-top: 15px;">
                <div class="status-badge status-offline">
                    <span class="status-dot"></span>
                    DISCONNECTED
                </div>
            </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# --- UI LAYOUT: SIDEBAR ---
with st.sidebar:
    render_logo(size="small")
    
    # Memory Slot Selector
    # Use key='selected_slot' to ensure session_state is updated BEFORE script run (fixes lag)
    # We need to find the index of the current slot in the keys list
    slot_keys = list(st.session_state["slot_names"].keys())
    current_index = 0
    if st.session_state.get("selected_slot") in slot_keys:
        current_index = slot_keys.index(st.session_state["selected_slot"])

    st.selectbox(
        "Active Memory Slot",
        options=slot_keys,
        format_func=lambda x: st.session_state["slot_names"][x],
        index=current_index,
        key="selected_slot"
    )
    st.markdown("---")
    
    st.markdown("### Knowledge Ingestion")
    st.caption("Upload documents to train the knowledge base.")
    
    uploaded_files = st.file_uploader(
        "Select files", 
        type=["pdf", "docx", "txt", "md", "mp3", "wav", "m4a"], 
        accept_multiple_files=True,
        label_visibility="collapsed",
        key=f"uploader_{st.session_state['uploader_key']}"
    )
    
    if uploaded_files:
        st.markdown(f"**Selected:** {len(uploaded_files)} files")
        if st.button("Process Documents", type="primary", use_container_width=True):
            with st.spinner("Ingesting knowledge..."):
                try:
                    files = []
                    for file in uploaded_files:
                        files.append(("files", (file.name, file.getvalue(), file.type)))
                    
                    params = {"collection_name": st.session_state["selected_slot"]}
                    response = requests.post(f"{BACKEND_URL}/api/v1/ingest", files=files, params=params, headers=API_HEADERS)
                    
                    if response.status_code == 200:
                        # st.write("Debug Response:", response.json()) # DEBUG REMOVED
                        results = response.json().get("results", [])
                        success_count = sum(1 for r in results if r["status"] == "success")
                        if success_count > 0:
                            st.toast(f"Successfully ingested {success_count} documents!", icon="✅")
                            time.sleep(1)
                            st.session_state["uploader_key"] += 1
                            st.rerun() # Refresh to update status
                        else:
                            st.error("Failed to ingest documents.")
                    else:
                        st.error(f"Server Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection Failed: {e}")
    
    
    # Only show Divider if we have something below to separate, or just keep spacing clean
    if get_uploaded_documents(st.session_state["selected_slot"]):
         st.divider()
    
    # Knowledge Management
    # Persist expander state
    if "expander_knowledge_open" not in st.session_state:
        st.session_state["expander_knowledge_open"] = False
        
    with st.expander("Current Knowledge", expanded=st.session_state["expander_knowledge_open"]):
        documents = get_uploaded_documents(st.session_state["selected_slot"])
        
        if documents:
            for doc in documents:
                col_doc, col_del = st.columns([8, 2])
                with col_doc:
                    st.markdown(f"<div style='font-size:0.8rem; padding-top:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>📄 {doc}</div>", unsafe_allow_html=True)
                with col_del:
                    if st.button("🗑️", key=f"del_{doc}", help=f"Delete {doc}"):
                        if delete_document(doc, st.session_state["selected_slot"]):
                            st.toast(f"Deleted {doc}", icon="🗑️")
                            st.session_state["expander_knowledge_open"] = True # Keep open
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Failed to delete.")
        else:
             pass # Don't show anything if empty, keeps layout clean
            
    st.divider()
    
    # Advanced Options
    if "expander_advanced_open" not in st.session_state:
        st.session_state["expander_advanced_open"] = False

    with st.expander("Advanced Options", expanded=st.session_state["expander_advanced_open"]):
        
        # 1. Manage Memory Slots
        st.caption("Manage Memory Slots")
        
        # Dynamic inputs for renaming
        # We'll use a form or just loop through them
        # Note: We need to handle the dict carefully
        
        slot_ids = list(st.session_state["slot_names"].keys())
        
        for s_id in slot_ids:
            col_name, col_del = st.columns([8, 2])
            with col_name:
                 st.session_state["slot_names"][s_id] = st.text_input(f"Name for {s_id}", value=st.session_state["slot_names"][s_id], key=f"in_{s_id}", label_visibility="collapsed")
            with col_del:
                # Don't delete if it's the last one? Or allow it?
                # Let's prevent deleting the currently selected one to avoid errors, or handle it.
                # Delete Button
                # Use a unique key. If clicked, we handle it here.
                # Issue: st.button return True only on the run it is clicked.
                
                if st.button("🗑️", key=f"del_slot_{s_id}", help="Delete this memory slot"):
                    if len(st.session_state["slot_names"]) <= 1:
                        st.toast("Cannot delete the last memory slot!", icon="🚫")
                    elif s_id == st.session_state["selected_slot"]:
                        st.toast("Cannot delete active slot. Switch first.", icon="🚫")
                    else:
                        if remove_slot(s_id):
                             del st.session_state["slot_names"][s_id]
                             st.toast("Memory slot deleted.", icon="🗑️")
                             st.session_state["expander_advanced_open"] = True # Keep open
                             time.sleep(0.5)
                             st.rerun()
                        else:
                            st.toast("Failed to delete from backend.", icon="❌")

        # Save Button for Renames
        if st.button("💾 Save Names", help="Save name changes"):
            if save_slot_config(st.session_state["slot_names"]):
                st.toast("Configuration Saved!", icon="💾")
                st.session_state["expander_advanced_open"] = True # Keep open
                time.sleep(1)
                st.rerun()
            else:
                 st.error("Failed to save.")
        
        st.markdown("---")
        
        # Add New Memory Slot
        col_new, col_add = st.columns([8, 2])
        with col_new:
            new_brain_name = st.text_input("New Brain Name", placeholder="e.g. Project X", key="new_brain_in", label_visibility="collapsed")
        with col_add:
            if st.button("➕", help="Create new memory slot"):
                if new_brain_name:
                    res = add_new_slot(new_brain_name)
                    if res:
                        st.session_state["slot_names"][res["slot_id"]] = res["name"]
                        st.toast("New Brain Created!", icon="✅")
                        st.session_state["expander_advanced_open"] = True # Keep open
                        time.sleep(1)
                        st.rerun()

        st.divider()

        # 2. Memory Export/Import
        st.caption("Export/Import Memory Slot")
        st.info("Export the current brain's knowledge to a zip file, or import knowledge from a zip file.")
        
        current_slot = st.session_state["selected_slot"]
        current_slot_name = st.session_state["slot_names"].get(current_slot, "Unknown")
        
        # EXPORT
        col_prep, col_dl = st.columns([1, 1])
        with col_prep:
            if st.button("📦 Prepare Export", help="Generate backup"):
                with st.spinner("Archiving..."):
                    try:
                        params = {"collection_name": current_slot}
                        response = requests.get(f"{BACKEND_URL}/api/v1/export", params=params, headers=API_HEADERS, timeout=120)
                        if response.status_code == 200:
                            st.session_state["export_data"] = response.content
                            st.session_state["export_name"] = f"nexus_export_{current_slot}.zip"
                            st.toast("Export Ready!", icon="✅")
                        else:
                            st.error("Export Failed")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        with col_dl:
            if "export_data" in st.session_state:
                st.download_button(
                    label="⬇️ Download",
                    data=st.session_state["export_data"],
                    file_name=st.session_state["export_name"],
                    mime="application/zip",
                    key="dl_btn_zip"
                )
        
        st.divider()
        
        # IMPORT
        def keep_advanced_open_import():
            st.session_state["expander_advanced_open"] = True

        uploaded_import = st.file_uploader(f"Import to '{current_slot_name}'", type="zip", key="import_uploader", on_change=keep_advanced_open_import)
        
        if uploaded_import:
            st.session_state["expander_advanced_open"] = True
            if st.button("Import Knowledge", type="primary"):
                with st.spinner("Importing Knowledge..."):
                    try:
                        files = {"file": (uploaded_import.name, uploaded_import.getvalue(), "application/zip")}
                        data = {"collection_name": current_slot}
                        response = requests.post(f"{BACKEND_URL}/api/v1/import", files=files, data=data, timeout=60)
                        
                        if response.status_code == 200:
                            st.toast("Import Successful!", icon="✅")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Import Failed: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
        
        st.divider()

        # 3. Danger Zone
        st.caption("Danger Zone")
        
        # Check if current slot has documents
        has_docs = len(get_uploaded_documents(st.session_state["selected_slot"])) > 0
        
        if st.button("Erase All Knowledge", help="Delete all documents in this memory slot", disabled=not has_docs):
            st.session_state["confirm_erase"] = True

        if st.session_state.get("confirm_erase", False):
            st.warning(f"Are you sure you want to delete ALL knowledge in {st.session_state['slot_names'][st.session_state['selected_slot']]}?")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Yes, Delete Everything", type="primary"):
                    if reset_knowledge_base(st.session_state["selected_slot"]):
                         st.toast("Brain washed successfully!")
                         st.session_state["confirm_erase"] = False
                         time.sleep(1)
                         st.rerun()
                    else:
                        st.error("Failed to reset.")
            with col_no:
                if st.button("Cancel"):
                    st.session_state["confirm_erase"] = False
                    st.rerun()
    
    st.divider()
    
    # Stats
    st.markdown("### System Stats")
    st.markdown(f"**Documents Indexed:** {system_status.get('document_count', 0)}")
    
    st.divider()
    

    st.markdown("""<div style="font-size:0.7rem; color:#64748b;"><strong>NEXUS CORE v4.1</strong><br>&copy; 2025 Barnalytics</div>""", unsafe_allow_html=True)

# --- UI LAYOUT: CHAT ---
# Render Chat History
for message in st.session_state.messages:
    avatar_icon = NEXUS_AVATAR_URL if message["role"] == "assistant" else None
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])



# Chat Input
if not is_online:
    st.chat_input("System Offline - Reconnecting...", disabled=True)
elif not has_knowledge:
    st.chat_input("Upload documents to train the knowledge before querys", disabled=True)
else:
    if prompt := st.chat_input("Enter your query..."):
        
        # Display Active Memory Slot (Visual Cue)
        current_brain = st.session_state["slot_names"].get(st.session_state["selected_slot"], "Unknown Brain")
        st.caption(f"Answering from: **{current_brain}**")
        
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=NEXUS_AVATAR_URL):
            response_placeholder = st.empty()
            
            with st.spinner("Analyzing..."):
                try:
                    # Construct History
                    # We skip the first message if it's the welcome message or if structure is unexpected
                    history = []
                    for i in range(len(st.session_state.messages) - 1):
                        msg = st.session_state.messages[i]
                        next_msg = st.session_state.messages[i+1]
                        
                        if msg["role"] == "user" and next_msg["role"] == "assistant":
                            history.append({"user": msg["content"], "assistant": next_msg["content"]})
                    
                    payload = {
                        "message": prompt, 
                        "collection_name": st.session_state["selected_slot"],
                        "history": history
                    }
                    response = requests.post(f"{BACKEND_URL}/api/v1/chat", json=payload, headers=API_HEADERS, timeout=30)
                    
                    if response.status_code == 200:
                        data = response.json()
                        answer = data["answer"]
                        sources = data.get("sources", [])
                        
                        final_response = f"{answer}"
                        if sources:
                            final_response += "\n\n---\n**Verified Sources:**\n"
                            for source in sources:
                                clean_source = source.replace('\n', ' ')[:150]
                                final_response += f"- `{clean_source}...`\n"
                        
                        typewriter_effect(final_response, response_placeholder)
                        st.session_state.messages.append({"role": "assistant", "content": final_response})
                    else:
                        response_placeholder.error(f"System Error {response.status_code}")
                except Exception as e:
                    response_placeholder.error(f"Network Error: {e}")
# Download Chat Button (Moved to End)
if len(st.session_state.messages) > 1:
    # Spacer to separate from chat
    st.markdown("---")
    pdf_bytes = create_pdf(st.session_state.messages)
    # Check if download button click triggered (auto-rerun handled by streamlit)
    st.download_button(
        label="Download Conversation",
        data=pdf_bytes,
        file_name="nexus_conversation.pdf",
        mime="application/pdf"
    )
