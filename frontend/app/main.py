import streamlit as st
import requests
import time
import base64
import os

# --- CONFIGURATION ---
BACKEND_URL = "http://backend:8000"

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
    page_title="NEXUS Enterprise",
    page_icon=LOGO_PATH,
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    </style>
""", unsafe_allow_html=True)

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

def check_system_status():
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/status", timeout=2)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return {"status": "offline", "ready": False, "document_count": 0}

def get_uploaded_documents():
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/documents", timeout=2)
        if response.status_code == 200:
            return response.json().get("documents", [])
    except:
        pass
    return []

def delete_document(filename):
    try:
        response = requests.delete(f"{BACKEND_URL}/api/v1/documents/{filename}", timeout=5)
        return response.status_code == 200
    except:
        return False

# --- INITIALIZATION ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Welcome to Nexus. Secure connection established."})

system_status = check_system_status()
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
    
    st.markdown("### 📥 Knowledge Ingestion")
    st.caption("Upload documents to train the knowledge base.")
    
    uploaded_files = st.file_uploader(
        "Select files", 
        type=["pdf", "docx", "txt", "md", "mp3", "wav", "m4a"], 
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.markdown(f"**Selected:** {len(uploaded_files)} files")
        if st.button("Process Documents", type="primary", use_container_width=True):
            with st.spinner("Ingesting knowledge..."):
                try:
                    files = []
                    for file in uploaded_files:
                        files.append(("files", (file.name, file, file.type)))
                    
                    response = requests.post(f"{BACKEND_URL}/api/v1/ingest", files=files)
                    
                    if response.status_code == 200:
                        results = response.json().get("results", [])
                        success_count = sum(1 for r in results if r["status"] == "success")
                        if success_count > 0:
                            st.toast(f"Successfully ingested {success_count} documents!", icon="✅")
                            time.sleep(1)
                            st.rerun() # Refresh to update status
                        else:
                            st.error("Failed to ingest documents.")
                    else:
                        st.error(f"Server Error: {response.text}")
                except Exception as e:
                    st.error(f"Connection Failed: {e}")
    
    st.divider()
    
    # Knowledge Management
    st.markdown("### 📚 Current Knowledge")
    documents = get_uploaded_documents()
    
    if documents:
        for doc in documents:
            col_doc, col_del = st.columns([8, 2])
            with col_doc:
                st.markdown(f"<div style='font-size:0.8rem; padding-top:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>📄 {doc}</div>", unsafe_allow_html=True)
            with col_del:
                if st.button("🗑️", key=f"del_{doc}", help=f"Delete {doc}"):
                    if delete_document(doc):
                        st.toast(f"Deleted {doc}", icon="🗑️")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to delete.")
    else:
        st.caption("No documents indexed yet.")
    
    st.divider()
    
    # Stats
    st.markdown("### 📊 System Stats")
    st.markdown(f"**Documents Indexed:** {system_status.get('document_count', 0)}")
    
    st.divider()
    st.markdown("""<div style="font-size:0.7rem; color:#64748b;"><strong>NEXUS CORE v2.0</strong><br>&copy; 2025 Barnalytics</div>""", unsafe_allow_html=True)

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
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar=NEXUS_AVATAR_URL):
            response_placeholder = st.empty()
            
            with st.spinner("Analyzing..."):
                try:
                    payload = {"query": prompt}
                    response = requests.post(f"{BACKEND_URL}/api/v1/chat", json=payload, timeout=30)
                    
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