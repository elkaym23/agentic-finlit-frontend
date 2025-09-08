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


from dashboards import student_db,teacher_db
from phase.Student_view import chatbot, lesson, quiz, game, teacherlink
from phase.Teacher_view import classmanage,studentlist,contentmanage
from phase.Student_view.games import profitpuzzle
from utils import db
import os
from dotenv import load_dotenv


load_dotenv()


# --- SESSION STATE INITIALIZATION ---
for key, default in [("user", None), ("current_page", "Welcome"),
                     ("xp", 2450), ("streak", 7), ("current_game", None),
                     ("temp_user", None)]:
    if key not in st.session_state:
        st.session_state[key] = default

# --- NAVIGATION ---
def setup_navigation():
    if st.session_state.user:
        public_pages = ["Welcome", "Login"]
    else:
        public_pages = ["Welcome", "Signup", "Login"]

    nav_choice = st.sidebar.selectbox(
        "Go to",
        public_pages,
        index=public_pages.index(st.session_state.current_page) if st.session_state.current_page in public_pages else 0
    )

    # --- if quiz is in progress, show progress tracker ---
    if st.session_state.get("current_page") == "Quiz":
        qid = st.session_state.get("selected_quiz")
        if qid is not None:
            try:
                quiz.show_quiz_progress_sidebar(qid)  # renders into sidebar
            except Exception:
                pass

        
    # --- if profit puzzle game is in progress, show progress tracker ---
    if (
        st.session_state.get("current_page") == "Game"
        and st.session_state.get("current_game") == "profit_puzzle"
    ):
        profitpuzzle.show_profit_progress_sidebar()

    # Only override if user is already on a public page
    if st.session_state.current_page in public_pages:
        st.session_state.current_page = nav_choice

    if st.session_state.user:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Dashboard")
        role = st.session_state.user["role"]

        if role == "Student":
            if st.sidebar.button("📊 Student Dashboard"):
                st.session_state.current_page = "Student Dashboard"
            if st.sidebar.button("📘 Lessons"):
                st.session_state.current_page = "Lessons"
            if st.sidebar.button("📝 Quiz"):
                st.session_state.current_page = "Quiz"
            if st.sidebar.button("💬 Chatbot"):
                st.session_state.current_page = "Chatbot"
            if st.sidebar.button("🏆 Game"):
                st.session_state.current_page = "Game"
            if st.sidebar.button("⌨️​ Teacher Link"):
                st.session_state.current_page = "Teacher Link"

        elif role == "Teacher":
            if st.sidebar.button("📚 Teacher Dashboard"):
                st.session_state.current_page = "Teacher Dashboard"
            if st.sidebar.button("Class management"):
                st.session_state.current_page = "Class management"
            if st.sidebar.button("Students List"):
                st.session_state.current_page = "Students List"
            if st.sidebar.button("Content Management"):
                st.session_state.current_page = "Content Management"

        if st.sidebar.button("Logout"):
            st.session_state.user = None
            st.session_state.current_page = "Welcome"
            st.rerun()


# --- ROUTING ---
def main():
    setup_navigation()
    page = st.session_state.current_page

    # --- WELCOME PAGE ---
    if page == "Welcome":
        st.title("💹 Welcome to FinEdu App")
        if st.session_state.user:
            st.success(f"Welcome back, {st.session_state.user['name']}! ✅")
        st.write(
            "This app helps you improve your **financial education and numeracy skills**.  \n"
            "👉 Use the sidebar to **Signup** or **Login** to get started."
        )

    # --- SIGNUP PAGE ---
    elif page == "Signup":
        st.title("📝 Signup")

        # remember the picked role between reruns
        if "signup_role" not in st.session_state:
            st.session_state.signup_role = None

        if st.session_state.user:
            st.success(f"Already logged in as {st.session_state.user['name']}.")
            st.stop()

        # Step 1: choose role
        if not st.session_state.signup_role:
            st.subheader("Who are you signing up as?")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("👩‍🎓 Student", use_container_width=True):
                    st.session_state.signup_role = "Student"
                    st.rerun()
            with c2:
                if st.button("👨‍🏫 Teacher", use_container_width=True):
                    st.session_state.signup_role = "Teacher"
                    st.rerun()

            st.info("Pick your role to continue with the correct form.")
            st.stop()

        role = st.session_state.signup_role

        # Step 2a: Student form
        if role == "Student":
            st.subheader("Student Signup")
            with st.form("student_signup_form", clear_on_submit=False):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                country = st.selectbox("Country", ["Jamaica", "USA", "UK", "India", "Canada", "Other"])
                level = st.selectbox("Level", ["Beginner", "Intermediate", "Advanced"])
                submitted = st.form_submit_button("Create Student Account")

                if submitted:
                    if not (name.strip() and email.strip() and password.strip()):
                        st.error("⚠️ Please complete all required fields.")
                        st.stop()

                    conn = db.get_db_connection()
                    if not conn:
                        st.error("❌ Unable to connect to the database.")
                        st.stop()
                    try:
                        ok = db.create_student(
                            name=name, email=email, password=password,
                            level_label=level, country_label=country
                        )
                        if ok:
                            st.success("✅ Signup successful! Please go to the **Login** page to continue.")
                            st.session_state.current_page = "Login"
                            st.session_state.signup_role = None
                            st.rerun()
                        else:
                            st.error("❌ Failed to create user. Email may already exist.")
                    finally:
                        conn.close()

        # Step 2b: Teacher form
        elif role == "Teacher":
            st.subheader("Teacher Signup")
            with st.form("teacher_signup_form", clear_on_submit=False):
                title = st.selectbox("Title", ["Mr", "Ms", "Miss", "Mrs", "Dr", "Prof", "Other"])
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submitted = st.form_submit_button("Create Teacher Account")

                if submitted:
                    if not (title.strip() and name.strip() and email.strip() and password.strip()):
                        st.error("⚠️ Please complete all required fields.")
                        st.stop()

                    conn = db.get_db_connection()
                    if not conn:
                        st.error("❌ Unable to connect to the database.")
                        st.stop()
                    try:
                        ok = db.create_teacher(
                            title=title, name=name, email=email, password=password
                        )
                        if ok:
                            st.success("✅ Signup successful! Please go to the **Login** page to continue.")
                            st.session_state.current_page = "Login"
                            st.session_state.signup_role = None
                            st.rerun()
                        else:
                            st.error("❌ Failed to create user. Email may already exist.")
                    finally:
                        conn.close()

        # Allow changing role without going back manually
        if st.button("⬅️ Choose a different role"):
            st.session_state.signup_role = None
            st.rerun()

    # --- LOGIN PAGE ---
    elif page == "Login":
        st.title("🔑 Login")
        if st.session_state.user:
            st.success(f"Welcome, {st.session_state.user['name']}! ✅")
        else:
            with st.form("login_form"):
                email = st.text_input("Email")
                password = st.text_input("Password", type="password")
                submit = st.form_submit_button("Login")

                if submit:
                    conn = db.get_db_connection()
                    if not conn:
                        st.error("❌ Unable to connect to the database.")
                    else:
                        try:
                            user = db.check_password(email, password)
                            if user:
                                st.session_state.user = {
                                    "user_id": user["user_id"],
                                    "name": user["name"],
                                    "role": user["role"],  # "Student" or "Teacher"
                                    "email": user["email"],
                                }
                                st.success(f"🎉 Logged in as {user['name']} ({user['role']})")
                                st.session_state.current_page = (
                                    "Student Dashboard" if user["role"] == "Student" else "Teacher Dashboard"
                                )
                                st.rerun()
                            else:
                                st.error("❌ Incorrect email or password, or account not found.")
                        finally:
                            conn.close()

    # --- STUDENT DASHBOARD ---
    elif page == "Student Dashboard":
        if not st.session_state.user:
            st.error("❌ Please login first.")
            st.session_state.current_page = "Login"
            st.rerun()
        elif st.session_state.user["role"] != "Student":
            st.error("🚫 Only students can access this page.")
            st.session_state.current_page = "Welcome"
            st.rerun()
        else:
            student_db.show_student_dashboard()

    # --- TEACHER DASHBOARD ---
    elif page == "Teacher Dashboard":
        if not st.session_state.user:
            st.error("❌ Please login first.")
            st.session_state.current_page = "Login"
            st.rerun()
        elif st.session_state.user["role"] != "Teacher":
            st.error("🚫 Only teachers can access this page.")
            st.session_state.current_page = "Welcome"
            st.rerun()
        else:
            teacher_db.show_teacher_dashboard()


    # --- PRIVATE PAGES ---
    private_pages_map = {
        "Lessons": lesson.show_page,
        "Quiz": quiz.show_page,
        "Chatbot": chatbot.show_page,
        "Game": game.show_games,
        "Teacher Link": teacherlink.show_code,
        "Class management": classmanage.show_page,
        "Students List": studentlist.show_page,
        "Content Management": contentmanage.show_page
    }

    if page in private_pages_map:
        if not st.session_state.user:
            st.error("❌ Please login first.")
            st.session_state.current_page = "Login"
            st.rerun()
        elif page in ["Lessons", "Quiz", "Chatbot", "Game", "Teacher Link"] and st.session_state.user["role"] == "Student":
            private_pages_map[page]()
        elif page in ["Class management", "Students List", "Content Management"] and st.session_state.user["role"] == "Teacher":
            private_pages_map[page]()
        else:
            st.error("🚫 You don’t have access to this page.")
            st.session_state.current_page = "Welcome"
            st.rerun()



if __name__ == "__main__":
    main()
