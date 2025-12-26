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
    initial_sidebar_state="expanded"
)

# --- 1. INITIALIZE SESSION STATE ---
defaults = {
    "authenticated": False,
    "user_role": None,
    "username": None,
    "messages": [],
    "manager_messages": [],
    "booking_mode": False,
    "selected_room": None,
    "show_success_animation": False
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


lottie_concierge_url = "https://lottie.host/1c108e9a-603c-40ac-8b4a-be7fbe02fa25/8HSveeLcSU.json"
lottie_hotel_url = "https://lottie.host/c4f91792-610c-4db5-ad37-9b3023a4acbb/yPmjEtejH0.json"
# Updated to a highly reliable success checkmark URL
lottie_success_url = "https://lottie.host/8627b003-8994-406c-8519-74e2d36d4e28/V1C2O4qE9X.json"

lottie_concierge = load_lottieurl(lottie_concierge_url)
lottie_hotel = load_lottieurl(lottie_hotel_url)
lottie_success = load_lottieurl(lottie_success_url)


# --- 3. AUTH & BACKEND FUNCTIONS ---
def login(username, password):
    user = authenticate_user(username, password)
    time.sleep(2)
    if user:
        try:
            requests.post(f"{API_URL}/reset", json={"message": "reset", "role": user.role}, timeout=2)
        except:
            pass
        st.session_state.authenticated = True
        st.session_state.user_role = user.role
        st.session_state.username = user.username
        st.rerun()
    else:
        st.error("❌ Invalid credentials")


def logout():
    with st.status("🛎️ Checking out...", expanded=True) as status:
        if st.session_state.user_role:
            try:
                requests.post(f"{API_URL}/reset", json={"message": "reset", "role": st.session_state.user_role},
                              timeout=2)
            except:
                pass
        st.session_state.authenticated = False
        st.session_state.user_role = None
        st.session_state.messages = []
        st.session_state.manager_messages = []
        status.update(label="✅ Check-out Complete", state="complete")
        st.rerun()


# --- 4. CSS STYLING ---
def add_custom_style():
    st.markdown("""<style>
        .stApp { background-image: url("https://images.unsplash.com/photo-1722763529109-2bcb289a47c3?q=80&w=1615&auto=format&fit=cover"); background-attachment: fixed; background-size: cover; }
        div[data-testid="stSidebar"] { background-color: rgba(0, 0, 0, 0.9) !important; border-right: 2px solid #d4af37; }
        div[data-testid="stForm"] { background: rgba(0, 0, 0, 0.85) !important; backdrop-filter: blur(20px); border: 1px solid #d4af37 !important; border-radius: 15px; }
        .stChatMessage { background: rgba(255, 255, 255, 0.1) !important; border-radius: 15px; margin-bottom: 10px; border-left: 5px solid #d4af37; }
        .stButton button { background-color: #d4af37 !important; color: black !important; font-weight: bold !important; width: 100%; }

        /* Full screen overlay for success */
        .success-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background-color: rgba(0, 0, 0, 0.85);
            z-index: 999999;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
    </style>""", unsafe_allow_html=True)


add_custom_style()


# --- UI HELPER: ROOM CARDS ---
def render_room_cards(bot_response):
    if "Available Rooms:" in bot_response:
        st.markdown("### 🛏️ Select Your Room")
        rooms = bot_response.split("- Room ")[1:]
        cols = st.columns(len(rooms) if len(rooms) > 0 else 1)
        for i, room_str in enumerate(rooms):
            with cols[i]:
                room_number = room_str.split(" ")[0]
                st.info(f"**Room {room_number}**")
                if st.button(f"Book {room_number}", key=f"btn_{room_number}"):
                    st.session_state.selected_room = room_number
                    st.toast(f"Room {room_number} selected!", icon="🛎️")


# --- 5. MAIN LOGIC ---

# 🛑 SUCCESS ANIMATION OVERLAY 🛑
if st.session_state.show_success_animation:
    overlay = st.empty()
    with overlay.container():
        st.markdown(f"""
            <div class="success-overlay">
                <h1 style="color: #d4af37; font-size: 3rem;">BOOKING SUCCESSFUL!</h1>
                <p style="color: white; font-size: 1.5rem;">We look forward to your arrival at the Grand Hotel.</p>
            </div>
        """, unsafe_allow_html=True)
        # Place the Lottie inside the overlay container
        if lottie_success:
            st_lottie(lottie_success, height=400, key="success_lottie")
        time.sleep(4)
        st.session_state.show_success_animation = False
        overlay.empty()  # Clear the overlay
        st.rerun()

if not st.session_state.authenticated:
    _, col2, _ = st.columns([1, 1.5, 1])
    with col2:
        if lottie_hotel: st_lottie(lottie_hotel, height=200)
        with st.form("login"):
            user = st.text_input("Username")
            pw = st.text_input("Password", type="password")
            if st.form_submit_button("ENTER THE GRAND HOTEL"): login(user, pw)
else:
    # --- SIDEBAR ---
    with st.sidebar:
        st.title("🏨 Grand Hotel")
        st.write(f"Logged in as: **{st.session_state.username}**")

        if st.session_state.user_role == "guest":
            st.markdown("---")
            st.markdown("### 📝 Reservation Form")
            if not st.session_state.booking_mode:
                st.info("The form will appear here once you confirm details with the concierge.")
            else:
                with st.form("sidebar_booking"):
                    name = st.text_input("Full Name", value=st.session_state.username)
                    email = st.text_input("Email")
                    room_val = st.text_input("Room #", value=st.session_state.get("selected_room", ""))

                    col_a, col_c = st.columns(2)
                    with col_a:
                        adults = st.number_input("Adults", min_value=1, max_value=10, value=1)
                    with col_c:
                        children = st.number_input("Children", min_value=0, max_value=10, value=0)

                    dates = st.date_input("Stay Dates", value=(datetime.now(), datetime.now() + timedelta(days=2)))

                    if st.form_submit_button("Confirm Booking"):
                        payload = {
                            "room_number": room_val,
                            "name": name,
                            "email": email,
                            "start_date": str(dates[0]),
                            "end_date": str(dates[1]),
                            "adults": int(adults),
                            "children": int(children)
                        }
                        res = requests.post(f"{API_URL}/book", json=payload)
                        if res.status_code == 200:
                            st.balloons()
                            # Notify AI system
                            requests.post(f"{API_URL}/chat",
                                          json={"message": f"SYSTEM ALERT: User {name} booked Room {room_val}.",
                                                "role": "guest"})
                            # Set flags
                            st.session_state.booking_mode = False
                            st.session_state.show_success_animation = True
                            st.rerun()
                        else:
                            st.error(f"Error: {res.json().get('detail', 'Booking failed')}")

        if st.button("Logout"): logout()

    # --- MAIN CONTENT AREA ---
    if st.session_state.user_role == "manager":
        st.title("📊 Manager Insights")
        for msg in st.session_state.manager_messages:
            with st.chat_message(msg["role"]): st.write(msg["content"])
        if prompt := st.chat_input("Ask about bookings..."):
            st.session_state.manager_messages.append({"role": "user", "content": prompt})
            res = requests.post(f"{API_URL}/chat", json={"message": prompt, "role": "manager"})
            st.session_state.manager_messages.append({"role": "assistant", "content": res.json().get("response")})
            st.rerun()

    elif st.session_state.user_role == "guest":
        st.title("🛎️ Grand Hotel Service")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                if msg["role"] == "assistant": render_room_cards(msg["content"])

        if prompt := st.chat_input("How can I help?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            res = requests.post(f"{API_URL}/chat", json={"message": prompt, "role": "guest"})
            reply = res.json().get("response", "Error")
            if "<SHOW_BOOKING_FORM>" in reply:
                st.session_state.booking_mode = True
                reply = reply.replace("<SHOW_BOOKING_FORM>", "✅ **Form opened in the sidebar!**")
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()