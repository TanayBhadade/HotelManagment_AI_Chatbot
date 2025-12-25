import time
import streamlit as st
import requests
import os
from auth import authenticate_user
from datetime import datetime, timedelta
from streamlit_lottie import st_lottie

# --- CONFIGURATION ---
API_URL = os.getenv("API_URL", "http://127.0.0.1:8001")

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Grand Hotel AI",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 1. INITIALIZE SESSION STATE ---
defaults = {
    "authenticated": False,
    "user_role": None,
    "username": None,
    "messages": [],
    "manager_messages": [],
    "booking_mode": False
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# --- 2. LOTTIE LOADER ---
def load_lottieurl(url: str):
    try:
        r = requests.get(url, timeout=5)
        return r.json() if r.status_code == 200 else None
    except:
        return None


# Guest-specific Lottie (A service bell or concierge)
lottie_concierge_url = "https://lottie.host/1c108e9a-603c-40ac-8b4a-be7fbe02fa25/8HSveeLcSU.json"
lottie_concierge = load_lottieurl(lottie_concierge_url)

# Main page animation
lottie_hotel = load_lottieurl("https://lottie.host/c4f91792-610c-4db5-ad37-9b3023a4acbb/yPmjEtejH0.json")


# --- 3. AUTH & BACKEND FUNCTIONS ---
def login(username, password):
    user = authenticate_user(username, password)
    time.sleep(2)  # Manually adds a 2-second 'Wait' for the user to see the loading text
    if user:
        try:
            # Sync with Backend: Reset memory on new login
            requests.post(f"{API_URL}/reset", json={"role": user.role}, timeout=2)
        except:
            pass
        st.session_state.authenticated = True
        st.session_state.user_role = user.role
        st.session_state.username = user.username
        st.rerun()
    else:
        st.error("❌ Invalid credentials")


def logout():
    # 1. Create a status container for the 'Check-out' feel
    with st.status("🛎️ Checking out of the Grand Hotel...", expanded=True) as status:
        st.write("🧹 Finalizing your room details...")

        if st.session_state.user_role:
            try:
                # Tell the backend to clear memory
                requests.post(f"{API_URL}/reset", json={"role": st.session_state.user_role}, timeout=2)
            except:
                pass

        time.sleep(0.8)  # Manual wait for user to read
        st.write("✨ We hope to see you again soon!")
        time.sleep(0.6)

        # 2. Clear frontend state
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.messages = []
        st.session_state.manager_messages = []

        status.update(label="✅ Check-out Complete", state="complete")
        time.sleep(0.5)
        st.rerun()


# --- 4. CSS STYLING ---
def add_custom_style():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
        .stApp {{
            background-image: url("https://images.unsplash.com/photo-1722763529109-2bcb289a47c3?q=80&w=1615&auto=format&fit=cover&ixlib=rb-4.1.0&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D");
            background-attachment: fixed; background-size: cover;
        }}
        h1, h2, h3, p, span, label {{
            color: white !important;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.7);
            font-family: 'Poppins', sans-serif;
        }}
        div[data-testid="stForm"] {{
            background: rgba(0, 0, 0, 0.75) !important;
            backdrop-filter: blur(15px);
            border: 2px solid #d4af37 !important;
            border-radius: 20px;
            padding: 40px;
        }}
        /* Unified Luxury Container for the Icon */
        .lottie-container {{
            background: rgba(0, 0, 0, 0.4) !important;
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border-radius: 50%;
            box-shadow: 0px 0px 35px rgba(212, 175, 55, 0.5);
            border: 2px solid rgba(212, 175, 55, 0.3);
            width: 220px;
            height: 220px;
            margin: 0 auto 20px auto;
            display: flex;
            align-items: center;
            justify-content: center;
            overflow: hidden;
        }}
        .stChatMessage {{
            background: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-left: 5px solid #d4af37;
            border-radius: 15px;
            margin-bottom: 10px;
        }}
        .stButton button {{
            background-color: #d4af37 !important;
            color: black !important;
            font-weight: bold !important;
            border-radius: 10px !important;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


add_custom_style()

# --- 5. MAIN LOGIC ---
if not st.session_state.authenticated:
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        if lottie_hotel:
            st_lottie(lottie_hotel, height=200, key="login_anim")
        st.markdown("<h1 style='text-align: center;'>Grand Hotel AI</h1>", unsafe_allow_html=True)
        with st.form("centered_login"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("ENTER THE GRAND HOTEL"):
                with st.status("🏨 Connecting to Grand Hotel Systems...", expanded=True) as status:
                    st.write("🔐 Verifying secure credentials...")
                    login(user, pw)
                    status.update(label="✅ Welcome to the Grand Hotel!", state="complete")
        st.markdown(
            "<div style='text-align:center;'><small style='color:#d4af37;'>manager/admin123 | guest/guest123</small></div>",
            unsafe_allow_html=True)

else:
    # --- LOGGED IN CONTENT ---
    with st.sidebar:
        # Move this to the VERY TOP of the sidebar
        if st.session_state.user_role == "guest":
            if lottie_concierge:
                st_lottie(lottie_concierge, height=150, key="guest_sidebar_anim")
            else:
                # Fallback if URL fails
                st.markdown("🛎️")

        st.title("🏨 Grand Hotel")

        st.write(f"Welcome, **{st.session_state.username}**")
        if st.session_state.user_role == "manager":
            if st.button("📄 Send Daily Report"):
                try:
                    requests.post(f"{API_URL}/trigger-report")
                    st.toast("Report Sent to Admin!", icon="📧")
                except:
                    st.error("Backend offline")
        if st.button("Logout"):
            logout()

    # MANAGER DASHBOARD
    if st.session_state.user_role == "manager":
        st.title("📊 Manager Insights")
        for msg in st.session_state.manager_messages:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👨‍💼"):
                st.write(msg["content"])

        if prompt := st.chat_input("Ask about bookings..."):
            st.session_state.manager_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👨‍💼"):
                st.write(prompt)

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Querying Database..."):
                    try:
                        res = requests.post(f"{API_URL}/chat", json={"message": prompt, "role": "manager"})
                        reply = res.json().get("response", "Error")
                        st.write(reply)
                        st.session_state.manager_messages.append({"role": "assistant", "content": reply})
                    except:
                        st.error("Connection Lost.")

    # GUEST CONCIERGE
    elif st.session_state.user_role == "guest":
        st.title("🛎️ Grand Hotel Service")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🤵" if msg["role"] == "assistant" else "👤"):
                st.write(msg["content"])

        if st.session_state.booking_mode:
            with st.form("guest_booking"):
                st.markdown("<h3 style='color:#d4af37;'>Complete Reservation</h3>", unsafe_allow_html=True)
                name = st.text_input("Name")
                email = st.text_input("Email")
                room = st.text_input("Room #")
                dates = st.date_input("Stay Dates", value=(datetime.now(), datetime.now() + timedelta(days=2)))
                if st.form_submit_button("Confirm Booking"):
                    # NOTE: This endpoint (/book) needs to exist in your API!
                    # If you are using the Chat-Only flow, you might want to disable this section.
                    payload = {
                        "room_number": room, "name": name, "email": email,
                        "start_date": str(dates[0]), "end_date": str(dates[1]),
                        "adults": 1, "children": 0
                    }
                    try:
                        res = requests.post(f"{API_URL}/book", json=payload)
                        if res.status_code == 200:
                            st.balloons()
                            st.success("Booking Confirmed!")
                            st.session_state.booking_mode = False
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error(f"Error: {res.text}")
                    except:
                        st.error("Could not connect to Booking Server.")

        if prompt := st.chat_input("How can I help?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.write(prompt)

            with st.chat_message("assistant", avatar="🤵"):
                with st.spinner("The bot is typing..."):
                    try:
                        res = requests.post(f"{API_URL}/chat", json={"message": prompt, "role": "guest"})
                        reply = res.json().get("response", "Error")

                        # Logic to trigger the Manual Booking Form if the bot asks for it
                        if "<SHOW_BOOKING_FORM>" in reply:
                            st.session_state.booking_mode = True
                            reply = reply.replace("<SHOW_BOOKING_FORM>", "")

                        st.write(reply)
                        st.session_state.messages.append({"role": "assistant", "content": reply})
                        if st.session_state.booking_mode: st.rerun()
                    except:
                        st.error("Hotel desk is busy.")