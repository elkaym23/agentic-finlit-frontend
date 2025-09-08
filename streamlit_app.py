import os
import streamlit as st
import requests

st.set_page_config(page_title="Agentic FinLit Frontend", page_icon="💹", layout="centered")

BACKEND_URL = os.getenv("BACKEND_URL", "").rstrip("/")
st.title("Agentic FinLit Frontend (Starter)")

if BACKEND_URL:
    try:
        r = requests.get(f"{BACKEND_URL}/")
        st.success(f"Backend OK: {r.json()}")
    except Exception as e:
        st.error(f"Could not reach backend: {e}")
else:
    st.info("Set BACKEND_URL in Space secrets to ping the backend here.")
