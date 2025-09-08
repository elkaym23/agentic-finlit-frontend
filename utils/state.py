import streamlit as st

def get_user():
    return st.session_state.get('user', None)

def set_user(user):
    st.session_state.user = user

def get_current_page():
    return st.session_state.get('current_page', 'Welcome')

def set_current_page(page):
    st.session_state.current_page = page