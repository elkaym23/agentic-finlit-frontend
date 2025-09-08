import streamlit as st
import datetime
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file if present
load_dotenv()

# Ensure OPENAI_API_KEY is set
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    st.error("⚠️ Please set the OPENAI_API_KEY environment variable or .env file before running the app.")

client = OpenAI(api_key=api_key)

# --- Helper to add message ---
def add_message(text: str, sender: str):
    st.session_state.messages.append(
        {
            "id": str(datetime.datetime.now().timestamp()),
            "text": text,
            "sender": sender,
            "timestamp": datetime.datetime.now()
        }
    )

def show_page():
    st.title("🤖 AI Financial Tutor")
    st.caption("Get personalized help with your financial questions")

    # --- Initialize state ---
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "id": "1",
                "text": "Hi! I'm your AI Financial Tutor. I'm here to help you learn about personal finance, investing, budgeting, and more. What would you like to know?",
                "sender": "assistant",
                "timestamp": datetime.datetime.now()
            }
        ]
    if "is_typing" not in st.session_state:
        st.session_state.is_typing = False

    # --- Chat Container ---
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            if msg["sender"] == "assistant":
                st.markdown(f"<div style='background-color:#e0e0e0; color:black; padding:10px; border-radius:12px; max-width:70%; margin-bottom:5px;'>{msg['text']}<br><sub>{msg['timestamp'].strftime('%H:%M')}</sub></div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='background-color:#4CAF50; color:white; padding:10px; border-radius:12px; max-width:70%; margin-left:auto; margin-bottom:5px;'>{msg['text']}<br><sub>{msg['timestamp'].strftime('%H:%M')}</sub></div>", unsafe_allow_html=True)

        if st.session_state.is_typing:
            st.markdown("🤖 _FinanceBot is typing..._")

    # --- Quick Questions ---
    if len(st.session_state.messages) == 1:
        st.markdown("Try asking about:")
        cols = st.columns(2)
        quick_questions = [
            "How does compound interest work?",
            "How much should I save for emergencies?",
            "What's a good budgeting strategy?",
            "How do I start investing?"
        ]
        for i, q in enumerate(quick_questions):
            if cols[i % 2].button(q):
                add_message(q, "user")
                st.session_state.is_typing = True
                st.rerun()

    # --- Input Box ---
    user_input = st.chat_input("Ask me anything about personal finance...")
    if user_input:
        add_message(user_input, "user")
        st.session_state.is_typing = True
        st.rerun()

    # --- Call OpenAI API directly ---
    if st.session_state.is_typing:
        try:
            with st.spinner("FinanceBot is thinking..."):
                messages_payload = [
                    {"role": m['sender'], "content": m['text']} for m in st.session_state.messages
                ]
                # Ensure role is either 'user' or 'assistant'
                for m in messages_payload:
                    if m['role'] not in ['user', 'assistant']:
                        m['role'] = 'user'

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages_payload
                )
                bot_reply = response.choices[0].message.content
                add_message(bot_reply, "assistant")
        except Exception as e:
            add_message(f"⚠️ Error: {e}", "assistant")
        finally:
            st.session_state.is_typing = False
            st.rerun()

    # --- Navigation Button ---
    if st.button("Back to Dashboard", key="ai_tutor_back_btn"):
        st.session_state.current_page = "Student Dashboard"
        st.rerun()
