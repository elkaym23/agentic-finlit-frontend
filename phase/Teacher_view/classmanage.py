# phase/Teacher_view/classmanage.py

import streamlit as st
import random
import string
from datetime import datetime
from utils import db as dbapi

def _metric_card(label: str, value: str, caption: str = ""):
    st.markdown(
        f"""
        <div class="metric-card">
          <div class="metric-value">{value}</div>
          <div class="metric-label">{label}</div>
          <div class="metric-caption">{caption}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def show_page():
    user = st.session_state.user
    teacher_id = user["user_id"]

    st.title("📚 Classroom Management")
    st.caption("Manage all your classrooms and students")

    # -------- Create Classroom --------
    with st.expander("➕ Create Classroom", expanded=False):
        new_name = st.text_input("Classroom Name", key="new_classroom_name")
        if st.button("Create Classroom"):
            name = new_name.strip()
            if name:
                out = dbapi.create_class(teacher_id, name)
                st.session_state.selected_class_id = out["class_id"]
                st.success(f'Classroom "{name}" created with code: {out["code"]}')
                st.rerun()
            else:
                st.error("Enter a real name, not whitespace.")

    # -------- Load classes for this teacher --------
    classes = dbapi.list_classes_by_teacher(teacher_id)
    if not classes:
        st.info("No classrooms yet. Create one above, then share the code.")
        return

    # Picker like your mock header bar
    st.subheader("Your Classrooms")
    options = {f"{c['name']} (Code: {c.get('code','')})": c for c in classes}
    selected_label = st.selectbox("Select a classroom", list(options.keys()))
    selected = options[selected_label]
    class_id = selected["class_id"]

    st.markdown("---")
    st.header(selected["name"])

    # -------- Code stripe --------
    st.subheader("Class Code")
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        st.markdown(f"**`{selected.get('code', 'UNKNOWN')}`**")
    with c2:
        if st.button("📋 Copy Code"):
            st.toast("Code is shown above. Copy it.")
    with c3:
        st.button("🗑️ Delete Class", disabled=True, help="Soft-delete coming later")

    # -------- Tabs --------
    tab_students, tab_content, tab_analytics = st.tabs(["👥 Students", "📘 Content", "📊 Analytics"])

    # ============== Students tab ==============
    with tab_students:
        # search input
        q = st.text_input("Search students by name or email", "")
        roster = dbapi.list_students_in_class(class_id)

        # simple filter
        if q.strip():
            ql = q.lower()
            roster = [r for r in roster if ql in r["name"].lower() or ql in r["email"].lower()]

        st.caption(f"{len(roster)} Students Found")

        if not roster:
            st.info("No students in this class yet.")
        else:
            for s in roster:
                st.subheader(f"👤 {s['name']}")
                st.caption(s["email"])
                joined = s.get("joined_at") or s.get("created_at")
                st.caption(f"📅 Joined: {str(joined)[:10]}")
                st.progress(0.0)  # placeholder bar to match your style
                cols = st.columns(3)
                cols[0].metric("⭐ Level", s["level_slug"].capitalize())
                cols[1].metric("📊 Avg Score", "—")    # can be filled per-student later
                cols[2].metric("🔥 Streak", "—")       # from streaks table if you want
                st.markdown("---")

    # ============== Content tab ==============
    with tab_content:
        counts = dbapi.class_content_counts(class_id)
        left, right = st.columns(2)
        with left:
            _metric_card("📖 Custom Lessons", str(counts["lessons"]), "Lessons created for this classroom")
        with right:
            _metric_card("🏆 Custom Quizzes", str(counts["quizzes"]), "Quizzes created for this classroom")

        # Optional list so teachers know what those numbers are
        assigs = dbapi.list_class_assignments(class_id)
        if assigs:
            st.markdown("#### Assigned items")
            for a in assigs:
                has_quiz = " + Quiz" if a["quiz_id"] else ""
                st.markdown(f"- **{a['title']}** · {a['subject']} · {a['level']}{has_quiz}")

    # ============== Analytics tab ==============
    with tab_analytics:
        stats = dbapi.class_analytics(class_id)
        g1, g2, g3 = st.columns(3)
        with g1:
            _metric_card("📊 Class Average", f"{round(stats['class_avg']*100)}%", "Average quiz performance")
        with g2:
            _metric_card("🪙 Total XP", f"{stats['total_xp']}", "Combined XP earned")
        with g3:
            _metric_card("📘 Lessons Completed", f"{stats['lessons_completed']}", "Total lessons completed")