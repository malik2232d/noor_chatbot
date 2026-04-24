import os
import json
import uuid
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Urban Vogue Boutique", page_icon="👗", layout="wide")

st.markdown("""
    <style>
        .block-container { padding-bottom: 100px; }
        div[data-testid="stChatInput"] { position: fixed; bottom: 20px; z-index: 99; }
    </style>
""", unsafe_allow_html=True)

DATA_DIR = "clothing_sessions"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def save_session(session_id, messages):
    with open(f"{DATA_DIR}/{session_id}.json", "w") as f:
        json.dump(messages, f)

def load_session(session_id):
    path = f"{DATA_DIR}/{session_id}.json"
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return []

def list_sessions():
    files = os.listdir(DATA_DIR)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(DATA_DIR, x)), reverse=True)
    return [f.replace(".json", "") for f in files if f.endswith(".json")]

if "current_session_id" not in st.session_state:
    st.session_state.current_session_id = str(uuid.uuid4())
    st.session_state.messages = []

# UPDATED BOUTIQUE SYSTEM INSTRUCTIONS
system_instruction = """
You are the Virtual Stylist for 'URBAN VOGUE BOUTIQUE'. 

STRICT WORKFLOW:
1. Ask for the OCCASION (Wedding, Casual, Formal, Party).
2. Ask for the GENDER (Male, Female, Unisex).
3. Ask for the SEASON (Summer or Winter).
4. Ask for the BUDGET.
5. VALIDATION: If budget < Rs. 1000, say: "Your budget is too low. Our collection starts from Rs. 1000."
6. SUGGESTION: Suggest items like Shirts, Pants, or Hoodies based on the season and gender.
7. CONFIRMATION: Ask to place the order.

INVENTORY REFERENCE:
- WINTER (Male/Female): 
  * Premium Fleece Hoodie: Rs. 3,500
  * Woolen Pants: Rs. 4,000
  * Flannel Shirt: Rs. 2,500
  * Leather Jacket: Rs. 8,000
- SUMMER (Male/Female):
  * Cotton T-Shirt: Rs. 1,500
  * Lightweight Chinos/Pants: Rs. 3,000
  * Linen Casual Shirt: Rs. 2,800
  * Denim Shorts: Rs. 2,000

Note: If the occasion is 'Wedding' but season is 'Winter', suggest heavy fabrics or shawls/blazers.
"""

with st.sidebar:
    st.title("🛍️ Order History")
    if st.button("➕ New Shopping Session", use_container_width=True):
        st.session_state.current_session_id = str(uuid.uuid4())
        st.session_state.messages = []
        st.rerun()
    st.write("---")
    for s_id in list_sessions():
        saved_msgs = load_session(s_id)
        user_msgs = [m['content'] for m in saved_msgs if m['role'] == 'user']
        title = user_msgs[0][:25] + "..." if user_msgs else "New Session"
        if st.button(f"👗 {title}", key=f"hist_{s_id}", use_container_width=True):
            st.session_state.current_session_id = s_id
            st.session_state.messages = saved_msgs
            st.rerun()

st.title("👗 URBAN VOGUE BOUTIQUE")
st.markdown("#### *Personalized Style for Every Season*")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

prompt = st.chat_input("Tell me what occasion you are shopping for...")

api_key = os.getenv("groq_api") or st.secrets.get("groq_api")
client = Groq(api_key=api_key)

if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    try:
        response = client.chat.completions.create(
            messages=[{"role": "system", "content": system_instruction}] + st.session_state.messages,
            model="llama-3.1-8b-instant"
        )
        reply = response.choices[0].message.content
        st.session_state.messages.append({"role": "assistant", "content": reply})
        save_session(st.session_state.current_session_id, st.session_state.messages)
        st.rerun()
    except Exception as e:
        st.error(f"Error connecting to AI: {e}")