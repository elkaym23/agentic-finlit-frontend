# phase/Student_view/teacherlink.py
import os
import streamlit as st
from utils import db as dbapi

def load_css(file_name: str):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass

def _progress_0_1(v):
    try:
        f = float(v)
    except Exception:
        return 0.0
    # accept 0..1 or 0..100
    return max(0.0, min(1.0, f if f <= 1.0 else f / 100.0))

def show_code():
    load_css(os.path.join("assets", "styles.css"))

    if "user" not in st.session_state or not st.session_state.user:
        st.error("Please log in as a student.")
        return
    if st.session_state.user["role"] != "Student":
        st.error("This page is for students.")
        return

    student_id = st.session_state.user["user_id"]
    st.markdown("## 👥 Join a Class")
    st.caption("Enter class code from your teacher")

    raw = st.text_input(
        label="Class Code", 
        placeholder="e.g. FIN5A2024",
        key="class_code_input",
        label_visibility="collapsed"
    )

    # custom button style
    st.markdown(
        """
        <style>
        .stButton>button#join_class_btn {
            background-color: #28a745; /* Bootstrap green */
            color: white;
            border-radius: 5px;
            padding: 10px 16px;
            font-weight: 600;
        }
        .stButton>button#join_class_btn:hover {
            background-color: #218838;
            color: white;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Join Class", key="join_class_btn"):
        code = (raw or "").strip().upper()
        if not code:
            st.error("Enter a class code.")
        else:
            try:
                class_id = dbapi.join_class_by_code(student_id, code)
                st.success("🎉 Joined the class!")
                st.rerun()
            except ValueError as e:
                st.error(str(e))

    st.markdown("---")
    st.markdown("## Your Classes")

    classes = dbapi.list_classes_for_student(student_id)
    if not classes:
        st.info("You haven’t joined any classes yet. Ask your teacher for a class code.")
        return

    # one card per class
    for c in classes:
        class_id = c["class_id"]
        counts   = dbapi.class_content_counts(class_id)      # lessons/quizzes count
        prog     = dbapi.student_class_progress(student_id, class_id)

        st.markdown(f"### {c['name']}")
        st.caption(f"Teacher: {c['teacher_name']} • Code: {c['code']} • Joined: {str(c['joined_at'])[:10]}")

        st.progress(_progress_0_1(prog["overall_progress"]))
        st.caption(
            f"{prog['lessons_completed']}/{prog['total_assigned_lessons']} lessons completed • "
            f"Avg quiz: {int(round(100 * (prog['avg_score'] or 0)))}%"
        )

        # top metrics
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Lessons", counts.get("lessons", 0))
        m2.metric("Quizzes", counts.get("quizzes", 0))
        m3.metric("Overall", f"{int(round(100*_progress_0_1(prog['overall_progress'])))}%")
        m4.metric("Avg Quiz", f"{int(round(100*(prog['avg_score'] or 0)))}%")

        # Leave class
        leave_col, _ = st.columns([1,3])
        with leave_col:
            if st.button("🚪 Leave Class", key=f"leave_{class_id}"):
                dbapi.leave_class(student_id, class_id)
                st.toast("Left class.", icon="👋")
                st.rerun()

        # Assignments for THIS class with THIS student's progress
        st.markdown("#### Teacher Lessons & Quizzes")
        rows = dbapi.student_assignments_for_class(student_id, class_id)
        if not rows:
            st.info("No assignments yet.")
        else:
            lessons_tab, quizzes_tab = st.tabs(["📘 Lessons", "🏆 Quizzes"])

            with lessons_tab:
                for r in rows:
                    if r["lesson_id"] is None:
                        continue

                    status = r.get("status") or "not_started"
                    pos = r.get("current_pos") or 0
                    pct = 1.0 if status == "completed" else min(0.95, float(pos or 0) * 0.1)

                    st.subheader(r["title"])
                    st.caption(f"{r['subject']} • {r['level']} • Due: {str(r['due_at'])[:10] if r.get('due_at') else '—'}")
                    st.progress(_progress_0_1(pct))

                    c1, c2 = st.columns(2)
                    with c1:
                        #  pass lesson & assignment to the Lessons page
                        if st.button("▶️ Start Lesson", key=f"start_lesson_{r['assignment_id']}"):
                            st.session_state.selected_lesson = r["lesson_id"]
                            st.session_state.selected_assignment = r["assignment_id"]
                            st.session_state.current_page = "Lessons"
                            st.rerun()
                    with c2:
                        st.write(f"Status: **{status}**")

            with quizzes_tab:
                any_quiz = False
                for r in rows:
                    if not r.get("quiz_id"):
                        continue
                    any_quiz = True

                    st.subheader(r["title"])
                    score, total = r.get("score"), r.get("total")
                    if score is not None and total:
                        st.caption(f"Last score: {int(round(100*float(score)/float(total)))}%")
                    else:
                        st.caption("No submission yet")

                    #  pass quiz & assignment to the Quiz page
                    if st.button("📝 Start Quiz", key=f"start_quiz_{class_id}_{r['quiz_id']}"):
                        st.session_state.selected_quiz = r["quiz_id"]            # numeric quiz_id from DB
                        st.session_state.current_assignment = r["assignment_id"] # you’ll need this when submitting
                        st.session_state.current_page = "Quiz"
                        st.rerun()

                if not any_quiz:
                    st.info("No quizzes yet for this class.")

        st.markdown("---")
