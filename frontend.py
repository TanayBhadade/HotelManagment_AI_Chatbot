import streamlit as st
import requests
import os
from auth import authenticate_user

# --- CONFIGURATION ---
# Allow dynamic URL for deployment, default to localhost
API_URL = os.getenv("API_URL", "http://127.0.0.1:8001")

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

        div[data-testid="stForm"] {{ background-color: rgba(0,0,0,0.8); padding: 20px; border-radius: 10px; border: 1px solid #d4af37; }}

        .stChatMessage {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 10px; border-left: 5px solid #d4af37; color: black !important; }}
        .stChatMessage p, .stChatMessage div {{ color: #000000 !important; }}
        [data-testid="stMetric"] {{ background-color: rgba(255, 255, 255, 0.9); border-radius: 10px; text-align: center; color: black !important; }}
        [data-testid="stMetricLabel"] {{ color: #444444 !important; }}
        [data-testid="stMetricValue"] {{ color: #000000 !important; }}

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

        # MANAGER ACTIONS (Moved to Sidebar to keep main view clean)
        if st.session_state.user_role == "manager":
            st.markdown("---")
            st.subheader("⚡ Manager Actions")
            if st.button("📄 Email Daily Report"):
                with st.spinner("Generating..."):
                    try:
                        requests.post(f"{API_URL}/trigger-report")
                        st.success("Report Sent!")
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
    # ==========================
    # === MANAGER DASHBOARD ===
    # ==========================
    if st.session_state.user_role == "manager":
        st.title("📊 Manager Dashboard")

        st.info("💡 **Tip:** Ask the AI below for real-time Revenue, Occupancy, or Guest Lists.")
        st.markdown("---")

        # CHAT INTERFACE (Main View - No Tabs)
        st.subheader("🤖 AI Executive Assistant")

        if "manager_messages" not in st.session_state:
            st.session_state.manager_messages = []

        # Display Chat History (Shows up in the main area)
        for msg in st.session_state.manager_messages:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👨‍💼"):
                st.markdown(msg["content"])

        # Chat Input (Pins to bottom automatically)
        if prompt := st.chat_input("Ask about today's revenue, guest list, or availability..."):
            st.session_state.manager_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👨‍💼"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Analyzing Database..."):
                    try:
                        # Pass 'manager' role to API
                        res = requests.post(f"{API_URL}/chat", json={"message": prompt, "role": "manager"}, timeout=30)
                        if res.status_code == 200:
                            reply = res.json().get("response", "Error")
                        else:
                            reply = f"❌ Server Error: {res.status_code}"
                    except requests.exceptions.Timeout:
                        reply = "⚠️ Timeout: Server took too long."
                    except:
                        reply = "❌ Connection Error. Is main.py running?"
                    st.markdown(reply)

            st.session_state.manager_messages.append({"role": "assistant", "content": reply})

    # =============================
    # === GUEST CHAT INTERFACE ===
    # =============================
    else:
        st.title("🛎️ Grand Hotel Concierge")

        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display History
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

        # Handle New Input
        if prompt := st.chat_input("How can I help you today?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🤵"):
                with st.spinner("Thinking..."):
                    try:
                        # Pass 'guest' role (default)
                        res = requests.post(f"{API_URL}/chat", json={"message": prompt, "role": "guest"}, timeout=30)
                        if res.status_code == 200:
                            reply = res.json().get("response", "Error")
                        else:
                            reply = f"❌ Server Error: {res.status_code}"
                    except requests.exceptions.Timeout:
                        reply = "⚠️ Error: The server took too long to respond."
                    except requests.exceptions.ConnectionError:
                        reply = "❌ Connection Error. Is main.py running?"
                    except Exception as e:
                        reply = f"❌ Error: {str(e)}"

                    st.markdown(reply)

                if ".pdf" in reply:
                    for word in reply.split():
                        if word.endswith(".pdf"):
                            filename = word.rstrip(".")
                            filepath = os.path.join("receipts", filename)
                            if os.path.exists(filepath):
                                with open(filepath, "rb") as pdf:
                                    st.download_button("⬇️ Download Receipt", pdf, filename, key="new_dl")

            st.session_state.messages.append({"role": "assistant", "content": reply})