import streamlit as st
import requests
import os
from auth import authenticate_user
from datetime import datetime, timedelta

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
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "username" not in st.session_state:
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "manager_messages" not in st.session_state:
    st.session_state.manager_messages = []
if "booking_mode" not in st.session_state:
    st.session_state.booking_mode = False


# --- 2. AUTH FUNCTIONS ---
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
    st.session_state.messages = []
    st.session_state.booking_mode = False
    st.rerun()


# --- 3. CSS STYLING (THEME OVERHAUL) ---
def add_bg_from_url():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
        html, body, [class*="css"] {{ font-family: 'Poppins', sans-serif; }}

        /* Main Background */
        .stApp {{
            background-image: url("https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?q=80&w=2070&auto=format&fit=crop");
            background-attachment: fixed; background-size: cover;
        }}

        /* Sidebar Styling */
        [data-testid="stSidebar"] {{ background-color: rgba(20, 20, 20, 0.95); border-right: 2px solid #d4af37; }}
        [data-testid="stSidebar"] * {{ color: #d4af37 !important; }}

        /* FORM STYLING - The "Luxury Card" Look */
        div[data-testid="stForm"] {{
            background-color: rgba(255, 255, 255, 0.98); /* Bright White Background */
            padding: 30px;
            border-radius: 15px;
            border: 2px solid #d4af37; /* Gold Border */
            box-shadow: 0px 4px 20px rgba(0,0,0,0.3);
        }}

        /* Input Fields (Text, Number, Date) inside Form */
        div[data-testid="stForm"] input, div[data-testid="stForm"] textarea {{
            background-color: #f8f9fa !important; /* Light Gray Input BG */
            color: #333333 !important; /* Dark Text */
            border: 1px solid #ccc !important;
            border-radius: 5px;
        }}
        div[data-testid="stForm"] label {{
            color: #d4af37 !important; /* Gold Labels */
            font-weight: 600 !important;
        }}

        /* Chat Messages */
        .stChatMessage {{ background-color: rgba(255, 255, 255, 0.95); border-radius: 15px; padding: 10px; border-left: 5px solid #d4af37; color: black !important; }}
        .stChatMessage p, .stChatMessage div {{ color: #000000 !important; }}

        /* Buttons */
        .stButton button {{
            background-color: #d4af37; 
            color: white; 
            font-weight: bold; 
            border-radius: 8px; 
            border: none;
            padding: 0.5rem 1rem;
            transition: all 0.3s ease;
        }}
        .stButton button:hover {{ 
            background-color: #bfa15f; 
            box-shadow: 0px 2px 10px rgba(212, 175, 55, 0.5);
            transform: translateY(-2px);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


add_bg_from_url()

# --- 4. SIDEBAR CONTENT ---
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
        st.info("Logins:\nManager: `manager`/`admin123`\nGuest: `guest`/`guest123`")

    else:
        st.success(f"Welcome, {st.session_state.username}")
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

# --- 5. MAIN CONTENT AREA ---
if not st.session_state.authenticated:
    st.title("🏨 Welcome to Grand Hotel")
    st.markdown("### Please login via the sidebar to continue.")

else:
    # === MANAGER DASHBOARD ===
    if st.session_state.user_role == "manager":
        st.title("📊 Manager Dashboard")
        st.info("💡 **Tip:** Ask the AI below for real-time Revenue, Occupancy, or Guest Lists.")
        st.markdown("---")

        for msg in st.session_state.manager_messages:
            with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👨‍💼"):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask about today's revenue, guest list, or availability..."):
            st.session_state.manager_messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👨‍💼"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🤖"):
                with st.spinner("Analyzing Database..."):
                    try:
                        res = requests.post(f"{API_URL}/chat", json={"message": prompt, "role": "manager"}, timeout=30)
                        if res.status_code == 200:
                            reply = res.json().get("response", "Error")
                        else:
                            reply = f"❌ Server Error: {res.status_code}"
                    except:
                        reply = "❌ Connection Error. Is main.py running?"
                    st.markdown(reply)
            st.session_state.manager_messages.append({"role": "assistant", "content": reply})

    # === GUEST CONCIERGE ===
    elif st.session_state.user_role == "guest":
        st.title("🛎️ Concierge Service")

        # 1. Chat History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"], avatar="🤵" if msg["role"] == "assistant" else "👤"):
                st.markdown(msg["content"])

        # 2. DETAILED BOOKING FORM (Conditional)
        if st.session_state.booking_mode:
            st.markdown("---")
            with st.container():
                # Form Header
                st.markdown("<h3 style='color: #d4af37; text-align: center;'>✨ Finalize Your Reservation</h3>",
                            unsafe_allow_html=True)

                with st.form("booking_form"):
                    # Section 1: Guest Details
                    st.markdown("#### 👤 Guest Details")
                    c1, c2 = st.columns(2)
                    with c1:
                        name = st.text_input("Full Name", placeholder="e.g. John Doe")
                    with c2:
                        email = st.text_input("Email Address", placeholder="e.g. john@example.com")

                    st.markdown("---")

                    # Section 2: Room & Dates
                    st.markdown("#### 🛏️ Stay Details")
                    c3, c4 = st.columns(2)
                    with c3:
                        room_no = st.text_input("Room Number", placeholder="e.g. 101")
                    with c4:
                        # Improved Date Picker
                        tomorrow = datetime.now() + timedelta(days=1)
                        dates = st.date_input(
                            "Select Check-in & Check-out",
                            value=(tomorrow, tomorrow + timedelta(days=2)),
                            min_value=datetime.now()
                        )

                    c5, c6 = st.columns(2)
                    with c5:
                        adults = st.number_input("Adults", 1, 4, 1)
                    with c6:
                        children = st.number_input("Children", 0, 4, 0)

                    # Section 3: Special Requests
                    st.markdown("#### 💬 Special Requests (Optional)")
                    requests_text = st.text_area("Any preferences?",
                                                 placeholder="e.g. Late check-in, extra pillows, quiet room...")

                    # Submit Button
                    submitted = st.form_submit_button("✅ Confirm Booking", type="primary")

                    if submitted:
                        # Validation
                        if not name or not email or not room_no:
                            st.error("⚠️ Please fill in all required fields (Name, Email, Room).")
                        elif len(dates) != 2:
                            st.error("⚠️ Please select both a Start Date and End Date.")
                        else:
                            try:
                                # Convert Date Objects to String for API
                                start_str = dates[0].strftime("%Y-%m-%d")
                                end_str = dates[1].strftime("%Y-%m-%d")

                                payload = {
                                    "room_number": room_no,
                                    "name": name,
                                    "email": email,
                                    "start_date": start_str,
                                    "end_date": end_str,
                                    "adults": adults,
                                    "children": children
                                }

                                with st.spinner("Processing your reservation..."):
                                    res = requests.post(f"{API_URL}/book", json=payload)
                                    status = res.json().get("status", "")

                                    if res.status_code == 200 and "Success" in status:
                                        st.success("🎉 Booking Confirmed! We have emailed you the receipt.")
                                        st.session_state.booking_mode = False
                                        st.session_state.messages.append({"role": "assistant",
                                                                          "content": f"✅ Confirmed! {name} is booked for Room {room_no} from {start_str} to {end_str}."})
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Booking Failed: {status}")
                            except Exception as e:
                                st.error(f"System Error: {str(e)}")

        # 3. Chat Input
        if prompt := st.chat_input("How can I help you?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="👤"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🤵"):
                with st.spinner("Thinking..."):
                    try:
                        res = requests.post(f"{API_URL}/chat", json={"message": prompt, "role": "guest"}, timeout=30)
                        reply = res.json().get("response", "Error")

                        if "<SHOW_BOOKING_FORM>" in reply:
                            st.session_state.booking_mode = True
                            reply = reply.replace("<SHOW_BOOKING_FORM>", "")

                        st.markdown(reply)
                    except Exception as e:
                        reply = "❌ Connection Error. Is the backend running?"
                        st.error(reply)

            st.session_state.messages.append({"role": "assistant", "content": reply})
            if st.session_state.booking_mode:
                st.rerun()