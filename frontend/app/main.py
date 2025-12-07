import streamlit as st
import requests
import time
import base64
import os

# --- CONFIGURATION ---
BACKEND_URL = "http://backend:8000"

# --- ASSET PATH RESOLUTION ---
# Based on your screenshot, the file is named 'nexus_logo.svg'
current_dir = os.path.dirname(os.path.abspath(__file__))
LOGO_PATH = os.path.join(current_dir, "nexus_logo.svg")

# Fallback: Create the file if it doesn't exist (Just-In-Time Generation)
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
    page_icon=LOGO_PATH, # Now points to the correct file
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- AVATAR GENERATOR (Base64 for Chat) ---
def get_nexus_avatar_b64():
    """
    Reads the physical SVG file and converts it to Base64 for the chat interface.
    """
    try:
        with open(LOGO_PATH, "r", encoding="utf-8") as f:
            svg = f.read()
        b64 = base64.b64encode(svg.encode('utf-8')).decode("utf-8")
        return f"data:image/svg+xml;base64,{b64}"
    except Exception:
        # Fallback to a geometric emoji if file read fails
        return "💠"

NEXUS_AVATAR_URL = get_nexus_avatar_b64()

# --- CUSTOM CSS & ANIMATIONS ---
st.markdown("""
    <style>
        .nexus-font { font-family: 'Helvetica Neue', sans-serif; }
        
        /* LOGO STYLES */
        .nexus-logo {
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 800;
            font-size: 2.5rem;
            color: #FFFFFF;
            letter-spacing: -1px;
            margin-bottom: 0;
            line-height: 1.2;
        }
        .nexus-accent {
            color: #6366f1;
            margin-right: 10px;
        }
        .nexus-subtitle {
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 300;
            font-size: 1rem;
            color: #a1a1aa;
            margin-top: -5px;
            letter-spacing: 1px;
            text-transform: uppercase;
        }

        /* STATUS PULSE ANIMATION */
        @keyframes pulse-green {
            0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.7); }
            70% { box-shadow: 0 0 0 6px rgba(74, 222, 128, 0); }
            100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            background-color: #4ade80;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse-green 2s infinite;
        }
        .status-text {
            font-family: 'Courier New', monospace;
            font-size: 0.8rem;
            color: #4ade80;
            letter-spacing: 1px;
            text-transform: uppercase;
        }
        
        /* Mobile Breakpoint */
        @media (max-width: 640px) { .nexus-logo { font-size: 1.8rem; } }
    </style>
""", unsafe_allow_html=True)

# --- HELPER FUNCTIONS ---
def render_logo(size="large"):
    """Renders the HTML/CSS Logo"""
    if size == "small":
        st.markdown('<div style="font-weight:800; font-size:1.5rem; color:#fff;"><span style="color:#6366f1">ネ</span> NEXUS</div>', unsafe_allow_html=True)
    else:
        st.markdown("""
            <div>
                <div class="nexus-logo"><span class="nexus-accent">ネ</span>NEXUS</div>
                <div class="nexus-subtitle">Enterprise Knowledge Engine</div>
            </div>
        """, unsafe_allow_html=True)

def typewriter_effect(text, placeholder):
    """
    Simulates streaming text for the UI.
    Compatible with older Streamlit versions (pre-1.31).
    """
    displayed_text = ""
    for word in text.split(" "):
        displayed_text += word + " "
        placeholder.markdown(displayed_text + "▌")
        time.sleep(0.04)
    placeholder.markdown(displayed_text)

# --- UI LAYOUT: HEADER ---
col1, col2 = st.columns([8, 2])
with col1:
    render_logo()
with col2:
    try:
        # Health Check
        if requests.get(BACKEND_URL, timeout=1).status_code == 200:
            st.markdown("""
                <div style="text-align:right; margin-top: 15px;">
                    <span class="status-indicator"></span>
                    <span class="status-text">ONLINE</span>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:right; color:#f87171; font-size:0.8rem; margin-top: 15px;">● OFFLINE</div>', unsafe_allow_html=True)
    except:
        st.markdown('<div style="text-align:right; color:#f87171; font-size:0.8rem; margin-top: 15px;">● OFFLINE</div>', unsafe_allow_html=True)

st.markdown("---")

# --- UI LAYOUT: SIDEBAR ---
with st.sidebar:
    render_logo(size="small")
    st.markdown("---")
    st.markdown("### Knowledge Injection")
    st.caption("Upload corporate PDF context.")
    
    uploaded_file = st.file_uploader("Select PDF file", type=["pdf"], label_visibility="collapsed")
    
    if uploaded_file is not None:
        st.markdown(f"**Selected:** `{uploaded_file.name}`")
        if st.button("🚀 Ingest Document", type="primary", use_container_width=True):
            with st.spinner("Vectorizing content..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                    response = requests.post(f"{BACKEND_URL}/api/v1/ingest", files=files)
                    if response.status_code == 200:
                        st.toast("Document indexed successfully!", icon="✅")
                    else:
                        st.error(f"Error: {response.text}")
                except Exception as e:
                    st.error(f"Failed: {e}")
    
    st.divider()
    st.markdown("""<div style="font-size:0.7rem; color:#71717a;"><strong>NEXUS CORE v1.0</strong><br>Powered by RAG Architecture<br>&copy; 2025 Barnalytics</div>""", unsafe_allow_html=True)

# --- UI LAYOUT: CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Systems initialized. Secure link established. Awaiting query."})

# Render Chat History
for message in st.session_state.messages:
    # Use SVG URL for assistant, Emoji for user
    avatar_icon = NEXUS_AVATAR_URL if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

# User Input Logic
if prompt := st.chat_input("Enter command..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=NEXUS_AVATAR_URL):
        response_placeholder = st.empty()
        
        with st.spinner("Processing logic..."):
            try:
                payload = {"query": prompt}
                response = requests.post(f"{BACKEND_URL}/api/v1/chat", json=payload, timeout=30)
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data["answer"]
                    sources = data.get("sources", [])
                    
                    # Construct final response
                    final_response = f"{answer}"
                    if sources:
                        final_response += "\n\n---\n**Verified Context:**\n"
                        for source in sources:
                            # Clean up newlines for better display
                            clean_source = source.replace('\n', ' ')[:150]
                            final_response += f"- `{clean_source}...`\n"
                    
                    # Apply Typewriter Effect
                    typewriter_effect(final_response, response_placeholder)
                    
                    # Append to history
                    st.session_state.messages.append({"role": "assistant", "content": final_response})
                else:
                    response_placeholder.error(f"System Error {response.status_code}: {response.text}")
            except Exception as e:
                response_placeholder.error(f"Connection lost with Backend Node. {e}")