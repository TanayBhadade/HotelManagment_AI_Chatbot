import streamlit as st
import requests
import os
from auth import authenticate_user

# --- CONFIGURATION ---
API_URL = "http://127.0.0.1:8001"

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Grand Hotel AI",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 🎨 CSS STYLING ---
def add_bg_from_url():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
        html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}
        .stApp {{
            background-image: url("https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?q=80&w=2070&auto=format&fit=crop");
            background-attachment: fixed; background-size: cover;
        }}
        [data-testid="stSidebar"] {{ background-color: rgba(0, 0, 0, 0.85); border-right: 1px solid rgba(255, 215, 0, 0.3); }}
        [data-testid="stSidebar"] .css-17lntkn, [data-testid="stSidebar"] p, [data-testid="stSidebar"] h1 {{ color: #d4af37 !important; }}

        /* Login Form Styling */
        div[data-testid="stForm"] {{ background-color: rgba(0,0,0,0.8); padding: 20px; border-radius: 10px; border: 1px solid #d4af37; }}

        /* Chat & Metrics */
        .stChatMessage {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 10px; border-left: 5px solid #d4af37; color: black !important; }}
        .stChatMessage p, .stChatMessage div {{ color: #000000 !important; }}
        [data-testid="stMetric"] {{ background-color: rgba(255, 255, 255, 0.9); border-radius: 10px; text-align: center; color: black !important; }}
        [data-testid="stMetricLabel"] {{ color: #444444 !important; }}
        [data-testid="stMetricValue"] {{ color: #000000 !important; }}

        /* Buttons */
        .stButton button {{ background-color: #d4af37; color: black; font-weight: bold; border-radius: 20px; border: none; }}
        .stButton button:hover {{ background-color: #bfa15f; transform: scale(1.05); }}
        </style>
        """,
        unsafe_allow_html=True
    )


add_bg_from_url()

# --- SESSION STATE & AUTH ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None


def login(username, password):
    user = authenticate_user(username, password)
    if user:
        st.session_state.authenticated = True
        st.session_state.user_role = user.role
        st.session_state.username = user.username
        st.rerun()
    else:
        st.error("❌ Invalid username or password")


def logout():
    st.session_state.authenticated = False
    st.session_state.user_role = None
    st.session_state.username = None
    st.rerun()


# --- SIDEBAR CONTENT ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/201/201623.png", width=80)
    st.title("Grand Hotel")
    st.markdown("---")

    if not st.session_state.authenticated:
        st.subheader("🔐 Login Required")
        with st.form("login_form"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")
            if submitted:
                login(user, pw)
        st.info("Default Logins:\n\nManager: `manager` / `admin123`\nGuest: `guest` / `guest123`")

    else:
        st.success(f"👤 {st.session_state.username}")
        st.caption(f"Role: {st.session_state.user_role.upper()}")

        if st.session_state.user_role == "manager":
            st.markdown("---")
            st.subheader("⚡ Manager Tools")
            if st.button("📄 Generate Report PDF"):
                with st.spinner("Processing..."):
                    try:
                        requests.post(f"{API_URL}/trigger-report")
                        st.success("Sent to Email!")
                    except:
                        st.error("Connection Failed")

        st.markdown("---")
        if st.button("Logout"):
            logout()

# --- MAIN CONTENT AREA ---
if not st.session_state.authenticated:
    st.title("🏨 Welcome to Grand Hotel")
    st.markdown("### Please login via the sidebar to continue.")
    st.image("https://images.unsplash.com/photo-1566073771259-6a8506099945?q=80&w=2070", use_column_width=True)

else:
    # === MANAGER DASHBOARD ===
    if st.session_state.user_role == "manager":
        st.title("📊 Manager Dashboard")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("💰 Today's Revenue", "₹ 12,500", "+15%")
        with col2:
            st.metric("👥 Active Guests", "8", "2 Check-ins")
        with col3:
            st.metric("🛏️ Occupancy", "75%", "-5%")
        st.markdown("---")
        st.info("Use the sidebar tools to generate daily reports.")

    # === GUEST CHAT INTERFACE ===
    else:
        st.title("🛎️ Concierge Service")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🤵" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])
                if msg["role"] == "assistant" and ".pdf" in msg["content"]:
                    for word in msg["content"].split():
                        if word.endswith(".pdf"):
                            filename = word.rstrip(".")
                            filepath = os.path.join("receipts", filename)
                            if os.path.exists(filepath):
                                with open(filepath, "rb") as pdf:
                                    st.download_button("⬇️ Download Receipt", pdf, filename)

        if prompt := st.chat_input("How can I help you?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🤵"):
                try:
                    res = requests.post(f"{API_URL}/chat", json={"message": prompt})
                    reply = res.json().get("response", "Error")
                except:
                    reply = "❌ Server Error. Is main.py running?"
                st.markdown(reply)

                # Check for PDF
                if ".pdf" in reply:
                    for word in reply.split():
                        if word.endswith(".pdf"):
                            filename = word.rstrip(".")
                            filepath = os.path.join("receipts", filename)
                            if os.path.exists(filepath):
                                with open(filepath, "rb") as pdf:
                                    st.download_button("⬇️ Download Receipt", pdf, filename, key="new_dl")

            st.session_state.messages.append({"role": "assistant", "content": reply})