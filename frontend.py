import streamlit as st
import requests
import os
import time
from datetime import datetime, timedelta
from auth import authenticate_user

# --- CONFIGURATION ---
API_URL = os.getenv("API_URL", "http://127.0.0.1:8001")

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Grand Hotel AI",
    page_icon="🏨",
    layout="wide",
)

# --- INITIALIZE SESSION STATE ---
if "authenticated" not in st.session_state:
    st.session_state.update({
        "authenticated": False,
        "user_role": None,
        "username": None,
        "messages": [],
        "manager_messages": [],
        "booking_mode": False,
        "selected_room": None,
        "show_success_animation": False,
        "entering": False,
        "exiting": False,
        # Fields for auto-filling from AI context
        "extracted_start": None,
        "extracted_end": None,
        "extracted_adults": 1,
        "extracted_children": 0
    })

# --- CSS STYLING ---
st.markdown("""
<style>
    .stApp { 
        background-image: url("https://images.unsplash.com/photo-1722763529109-2bcb289a47c3?q=80&w=1615&auto=format&fit=cover"); 
        background-attachment: fixed; background-size: cover; 
    }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
    .overlay {
        position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
        background-color: rgba(0, 0, 0, 0.95); z-index: 9999;
        display: flex; flex-direction: column; align-items: center; justify-content: center;
        animation: fadeIn 0.5s ease-in;
    }
    .status-icon { font-size: 80px; color: #d4af37; animation: pulse 2s infinite ease-in-out; }
    div[data-testid="stSidebar"] { background-color: rgba(0, 0, 0, 0.8) !important; border-right: 1px solid #d4af37; }
</style>
""", unsafe_allow_html=True)


# --- UI HELPERS ---
def render_room_cards(bot_response):
    if "Available Rooms:" in bot_response:
        st.markdown("### 🛏️ Select Your Room")
        rooms = bot_response.split("- Room ")[1:]
        cols = st.columns(len(rooms) if len(rooms) > 0 else 1)
        for i, room_str in enumerate(rooms):
            with cols[i]:
                room_number = room_str.split(" ")[0]
                if st.button(f"Book {room_number}", key=f"btn_{room_number}"):
                    st.session_state.selected_room = room_number
                    st.toast(f"Room {room_number} selected!", icon="🛎️")


# --- MAIN LOGIC ---
if st.session_state.entering:
    with st.container():
        st.markdown(
            '<div class="overlay"><div class="status-icon">🛎️</div><h1 style="color: #d4af37;">WELCOME</h1></div>',
            unsafe_allow_html=True)
    time.sleep(1.2)
    st.session_state.entering, st.session_state.authenticated = False, True
    st.rerun()

if st.session_state.show_success_animation:
    with st.container():
        st.markdown(
            '<div class="overlay"><div class="status-icon">🛎️</div><h1 style="color: #d4af37;">RESERVATION CONFIRMED</h1></div>',
            unsafe_allow_html=True)
    time.sleep(2.5)
    st.session_state.show_success_animation = False
    st.rerun()

if not st.session_state.authenticated:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("ENTER THE GRAND HOTEL"):
                user = authenticate_user(u, p)
                if user:
                    st.session_state.entering, st.session_state.user_role, st.session_state.username = True, user.role, user.username
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
else:
    with st.sidebar:
        st.title("🏨 Grand Hotel")
        if st.session_state.user_role == "guest":
            st.markdown("### 📝 Reservation Form")
            if not st.session_state.booking_mode:
                st.info("The concierge will open the form here when ready.")
            else:
                with st.form("sidebar_booking"):
                    name = st.text_input("Full Name", value=st.session_state.username)
                    email = st.text_input("Email")
                    room_val = st.text_input("Room #", value=st.session_state.get("selected_room", ""))

                    # Extraction Logic: Convert date strings from AI into datetime objects
                    try:
                        start_date = datetime.strptime(st.session_state.extracted_start, "%Y-%m-%d")
                        end_date = datetime.strptime(st.session_state.extracted_end, "%Y-%m-%d")
                        default_dates = (start_date, end_date)
                    except:
                        default_dates = (datetime.now(), datetime.now() + timedelta(days=2))

                    col_a, col_c = st.columns(2)
                    with col_a:
                        adults = st.number_input("Adults", min_value=1,
                                                 value=int(st.session_state.get("extracted_adults", 1)))
                    with col_c:
                        children = st.number_input("Children", min_value=0,
                                                   value=int(st.session_state.get("extracted_children", 0)))

                    dates = st.date_input("Stay Dates", value=default_dates)

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
                            st.session_state.booking_mode, st.session_state.show_success_animation = False, True
                            st.rerun()
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.rerun()

    role = st.session_state.user_role
    msg_key = "manager_messages" if role == "manager" else "messages"
    st.title("🛎️ Guest Services" if role == "guest" else "📊 Manager Insights")

    for msg in st.session_state[msg_key]:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            if msg["role"] == "assistant" and role == "guest": render_room_cards(msg["content"])

    if prompt := st.chat_input("How may I help you?"):
        st.session_state[msg_key].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        with st.spinner("Concierge is attending to your request..."):
            try:
                res = requests.post(f"{API_URL}/chat", json={"message": prompt, "role": role}, timeout=10)
                data = res.json()
                reply = data.get("response", "Error.")

                # Check for form trigger and extract metadata
                if "<SHOW_BOOKING_FORM>" in reply:
                    st.session_state.booking_mode = True
                    # Capture extracted data from the backend response
                    extracted = data.get("extracted_data", {})
                    st.session_state.extracted_start = extracted.get("start_date")
                    st.session_state.extracted_end = extracted.get("end_date")
                    st.session_state.extracted_adults = extracted.get("adults", 1)
                    st.session_state.extracted_children = extracted.get("children", 0)

                    reply = reply.replace("<SHOW_BOOKING_FORM>", "✅ **Reservation form opened in sidebar.**")

                st.session_state[msg_key].append({"role": "assistant", "content": reply})
                st.rerun()
            except Exception:
                st.error("Server connection timeout. Ensure the backend is running on port 8001.")