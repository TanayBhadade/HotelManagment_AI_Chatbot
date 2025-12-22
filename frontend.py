import streamlit as st
import requests
import os

# --- CONFIGURATION ---
# Ensure this matches the port in main.py
API_URL = "http://127.0.0.1:8001"

# --- PAGE SETUP ---
st.set_page_config(
    page_title="Grand Hotel AI",
    page_icon="🏨",
    layout="wide",
    initial_sidebar_state="expanded"
)


# --- 🎨 CSS STYLING (FIXED VISIBILITY) ---
def add_bg_from_url():
    st.markdown(
        f"""
        <style>
        /* 1. IMPORT FONT */
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');

        /* 2. GENERAL TEXT STYLING */
        html, body, [class*="css"] {{
            font-family: 'Poppins', sans-serif;
        }}

        /* 3. BACKGROUND IMAGE */
        .stApp {{
            background-image: url("https://images.unsplash.com/photo-1542314831-068cd1dbfeeb?q=80&w=2070&auto=format&fit=crop");
            background-attachment: fixed;
            background-size: cover;
        }}

        /* 4. SIDEBAR STYLING */
        [data-testid="stSidebar"] {{
            background-color: rgba(0, 0, 0, 0.85);
            border-right: 1px solid rgba(255, 215, 0, 0.3);
        }}

        /* Sidebar Text Color */
        [data-testid="stSidebar"] .css-17lntkn, [data-testid="stSidebar"] p {{
            color: #d4af37 !important;
            font-size: 1.1rem;
        }}

        /* 5. CHAT MESSAGES (FIXED: Force Black Text) */
        .stChatMessage {{
            background-color: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 10px;
            border-left: 5px solid #d4af37;
            color: black !important;
        }}

        /* Force all paragraphs/spans inside chat to be black */
        .stChatMessage p, .stChatMessage div, .stChatMessage span {{
            color: #000000 !important;
        }}

        /* 6. METRIC CARDS */
        [data-testid="stMetric"] {{
            background-color: rgba(255, 255, 255, 0.9);
            padding: 15px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
            text-align: center;
            color: black !important;
        }}

        /* Metric Labels */
        [data-testid="stMetricLabel"] {{
            color: #444444 !important;
        }}

        /* Metric Values */
        [data-testid="stMetricValue"] {{
            color: #000000 !important;
        }}

        /* Hide Default Header/Footer */
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}

        /* Button Styling */
        .stButton button {{
            background-color: #d4af37;
            color: black;
            font-weight: bold;
            border-radius: 20px;
            border: none;
            transition: all 0.3s ease;
        }}
        .stButton button:hover {{
            background-color: #bfa15f;
            transform: scale(1.05);
        }}

        </style>
        """,
        unsafe_allow_html=True
    )


add_bg_from_url()

# --- SIDEBAR (LOGIN LOGIC) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/201/201623.png", width=80)
    st.title("Grand Hotel")
    st.markdown("*Experience Luxury & AI*")
    st.markdown("---")

    user_role = st.radio("Select Mode:", ["👤 Guest", "🔐 Admin / Staff"])
    st.markdown("---")

    if user_role == "🔐 Admin / Staff":
        st.success("Admin Mode Active")
        if st.button("📄 Generate PDF Report"):
            with st.spinner("Generating..."):
                try:
                    res = requests.post(f"{API_URL}/trigger-report")
                    if res.status_code == 200:
                        st.success("✅ PDF Saved!")
                    else:
                        st.error("❌ Failed.")
                except:
                    st.error("❌ Connection Error.")
    else:
        st.info("Guest Mode Active")
        st.write("Book rooms, check rates, and get instant receipts.")

# --- MAIN PAGE LOGIC ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- 🔐 ADMIN DASHBOARD ---
if user_role == "🔐 Admin / Staff":
    st.title("📊 Manager Dashboard")
    st.markdown("### 📈 Live Performance Metrics")

    # VISUAL METRICS (Mock Data for UI Demo)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="💰 Today's Revenue", value="₹ 12,500", delta="+15%")
    with col2:
        st.metric(label="👥 Active Guests", value="8", delta="2 checking in")
    with col3:
        st.metric(label="🛏️ Occupancy Rate", value="75%", delta="-5%")

    st.markdown("---")

# --- 👤 GUEST / CHAT INTERFACE ---
else:
    st.title("🛎️ Concierge Service")
    st.markdown("Welcome! I am your AI assistant. How can I make your stay perfect?")

# --- CHAT HISTORY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="🤵" if msg["role"] == "assistant" else "👤"):
        st.markdown(msg["content"])

        # PDF Logic
        if msg["role"] == "assistant" and ".pdf" in msg["content"]:
            for word in msg["content"].split():
                if word.endswith(".pdf"):
                    filename = word.rstrip(".")
                    filepath = os.path.join("receipts", filename)
                    if os.path.exists(filepath):
                        with open(filepath, "rb") as pdf_file:
                            st.download_button(
                                label=f"⬇️ Download {filename}",
                                data=pdf_file,
                                file_name=filename,
                                mime="application/pdf",
                                key=filename
                            )

# --- USER INPUT ---
if prompt := st.chat_input("Ask me about rooms, booking, or services..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🤵"):
        message_placeholder = st.empty()
        with st.spinner("Thinking..."):
            try:
                response = requests.post(f"{API_URL}/chat", json={"message": prompt})
                if response.status_code == 200:
                    bot_reply = response.json().get("response", "Error")
                else:
                    bot_reply = f"❌ Error {response.status_code}"
            except:
                bot_reply = "❌ Connection Error. Is main.py running?"

            message_placeholder.markdown(bot_reply)

            # Check for PDF
            if ".pdf" in bot_reply:
                for word in bot_reply.split():
                    if word.endswith(".pdf"):
                        filename = word.rstrip(".")
                        filepath = os.path.join("receipts", filename)
                        if os.path.exists(filepath):
                            with open(filepath, "rb") as pdf_file:
                                st.download_button(
                                    label="⬇️ Download Receipt",
                                    data=pdf_file,
                                    file_name=filename,
                                    mime="application/pdf",
                                    key="new_download_btn"
                                )

    st.session_state.messages.append({"role": "assistant", "content": bot_reply})