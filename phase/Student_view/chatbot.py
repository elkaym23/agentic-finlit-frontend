import streamlit as st
import datetime
from utils import api as backend  # our HTTP client to the backend

# --- Helper to add message ---
def add_message(text: str, sender: str):
    st.session_state.messages.append(
        {
            "id": str(datetime.datetime.now().timestamp()),
            "text": text,
            "sender": sender,
            "timestamp": datetime.datetime.now(),
        }
    )

def show_page():
    st.title("🤖 AI Financial Tutor")
    st.caption("Powered by your backend using Mistral on Hugging Face")

    # --- Initialize state ---
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "id": "1",
                "text": "Hi! I'm your AI Financial Tutor. Ask me about budgeting, saving, investing, or that mysterious thing called compound interest.",
                "sender": "assistant",
                "timestamp": datetime.datetime.now(),
            }
        ]
    if "is_typing" not in st.session_state:
        st.session_state.is_typing = False

    # --- Render chat history ---
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            bubble = (
                f"<div style='background-color:#e0e0e0;color:black;padding:10px;border-radius:12px;max-width:70%;margin-bottom:5px;'>"
                f"{msg['text']}<br><sub>{msg['timestamp'].strftime('%H:%M')}</sub></div>"
                if msg["sender"] == "assistant"
                else f"<div style='background-color:#4CAF50;color:white;padding:10px;border-radius:12px;max-width:70%;margin-left:auto;margin-bottom:5px;'>"
                     f"{msg['text']}<br><sub>{msg['timestamp'].strftime('%H:%M')}</sub></div>"
            )
            st.markdown(bubble, unsafe_allow_html=True)
        if st.session_state.is_typing:
            st.markdown("🤖 _FinanceBot is typing..._")

    # --- Quick suggestions on first load ---
    if len(st.session_state.messages) == 1:
        st.markdown("Try asking about:")
        cols = st.columns(2)
        for i, q in enumerate([
            "How does compound interest work?",
            "How much should I save for emergencies?",
            "What's a good budgeting strategy?",
            "How do I start investing?"
        ]):
            if cols[i % 2].button(q):
                add_message(q, "user")
                st.session_state.is_typing = True
                st.rerun()

    # --- User input ---
    user_input = st.chat_input("Ask me anything about personal finance...")
    if user_input:
        add_message(user_input, "user")
        st.session_state.is_typing = True
        st.rerun()

    # --- Call your backend, not OpenAI ---
    if st.session_state.is_typing:
        try:
            s = st.session_state.get("user") or {}
            level_slug = (s.get("level_slug") or s.get("level") or "beginner").lower()

            with st.spinner("FinanceBot is thinking..."):
                # send the last user message only, or send the whole history if your backend supports it
                last_user = next((m for m in reversed(st.session_state.messages) if m["sender"] == "user"), None)
                payload = {
                    "user_id": s.get("user_id", 0),
                    "message": last_user["text"] if last_user else "",
                    "level_slug": level_slug,
                    # If your backend accepts history, send it too:
                    "history": [{"role": m["sender"], "content": m["text"]} for m in st.session_state.messages[-10:]],
                }

                # utils/api.py -> chat() should POST to /chat and return {"reply": "..."}
                resp = backend.chat(**payload)
                bot_reply = resp.get("reply", "(no reply)")

                add_message(bot_reply, "assistant")
        except Exception as e:
            add_message(f"⚠️ Backend error: {e}", "assistant")
        finally:
            st.session_state.is_typing = False
            st.rerun()

    if st.button("Back to Dashboard", key="ai_tutor_back_btn"):
        st.session_state.current_page = "Student Dashboard"
        st.rerun()
