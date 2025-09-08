# dashboards/teacher_db.py
import streamlit as st
import os
import plotly.express as px
import plotly.graph_objects as go
import csv
import io
import datetime
from utils import db as dbapi

def load_css(file_name):
    try:
        with open(file_name, 'r') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ Stylesheet not found. Please ensure 'assets/styles.css' exists.")

def tile(icon, label, value):
    return f"""
    <div class="metric-card">
      <div class="metric-icon">{icon}</div>
      <div class="metric-value">{value}</div>
      <div class="metric-label">{label}</div>
    </div>
    """

def show_teacher_dashboard():
    css_path = os.path.join("assets", "styles.css")
    load_css(css_path)

    user = st.session_state.user
    teacher_id = user["user_id"]
    name = user["name"]

    # ========== HEADER / HERO ==========
    colH1, colH2 = st.columns([5, 2])
    with colH1:
        st.markdown(f"""
            <div class="header-container">
              <div class="header-content">
                <div class="header-left">
                  <div class="header-title">Welcome back, Teacher {name}!</div>
                  <div class="header-subtitle">Managing your classrooms</div>
                </div>
              </div>
            </div>
        """, unsafe_allow_html=True)
    with colH2:
        with st.popover("➕ Create Classroom"):
            new_class_name = st.text_input("Classroom Name", key="new_class_name")
            if st.button("Create Classroom", key="create_classroom_btn"):
                if new_class_name.strip():
                    out = dbapi.create_class(teacher_id, new_class_name.strip())
                    st.success(f"Classroom created. Code: **{out['code']}**")

    # ========== TILES ==========
    tiles = dbapi.teacher_tiles(teacher_id)
    c1,c2,c3,c4 = st.columns(4)
    c1.markdown(tile("👥","Total Students", tiles["total_students"]), unsafe_allow_html=True)
    c2.markdown(tile("📊","Class Average", f"{int(tiles['class_avg']*100)}%"), unsafe_allow_html=True)
    c3.markdown(tile("📚","Lessons Created", tiles["lessons_created"]), unsafe_allow_html=True)
    c4.markdown(tile("📈","Active Students", tiles["active_students"]), unsafe_allow_html=True)

    # ========== CLASS PICKER ==========
    classes = dbapi.list_classes_by_teacher(teacher_id)
    if not classes:
        st.info("No classes yet. Create one above, then share the code with students.")
        return

    idx = st.selectbox(
        "Choose a class",
        list(range(len(classes))),
        index=0,
        format_func=lambda i: f"{classes[i]['name']} (Code: {classes[i].get('code','')})"
    )
    selected = classes[idx]
    class_id = selected["class_id"]
    class_code = selected.get("code","")

    # secondary hero controls
    cTop1, cTop2, cTop3 = st.columns([2,1,1])
    with cTop1:
        st.button(f"Class Code: {class_code}", disabled=True)
    with cTop2:
        if st.button("📋 Copy Code"):
            st.toast("Code copied. Paste it anywhere your heart desires.")
    with cTop3:
        rows = dbapi.class_student_metrics(class_id)
        if rows:
            headers = []
            for r in rows:
                for k in r.keys():
                    if k not in headers:
                        headers.append(k)
            buf = io.StringIO()
            writer = csv.DictWriter(buf, fieldnames=headers)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
            st.download_button(
                "📤 Export Class Report",
                data=buf.getvalue(),
                file_name=f"class_{class_id}_report.csv",
                mime="text/csv"
            )
        else:
            st.button("📤 Export Class Report", disabled=True)

    # ========== TOP ROW: WEEKLY ACTIVITY + CLASS PROGRESS ==========
    left, right = st.columns([3,2])

    with left:
        st.subheader("Weekly Activity")
        st.caption("Student engagement throughout the week")
        activity = dbapi.class_weekly_activity(class_id)
        if activity:
            days = []
            lessons, quizzes, games = [], [], []
            for row in activity:
                date_str = row.get("date")
                try:
                    day = datetime.datetime.fromisoformat(date_str).strftime("%a")
                except Exception:
                    day = str(date_str)
                days.append(day)
                lessons.append(row.get("lessons",0))
                quizzes.append(row.get("quizzes",0))
                games.append(row.get("games",0))
            fig = go.Figure(data=[
                go.Bar(name="Lessons", x=days, y=lessons),
                go.Bar(name="Quizzes", x=days, y=quizzes),
                go.Bar(name="Games", x=days, y=games),
            ])
            fig.update_layout(barmode="group",
                              xaxis_title="Day",
                              yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No activity in the last 7 days.")

    with right:
        st.subheader("Class Progress Overview")
        st.caption("How your students are performing")

        prog = dbapi.class_progress_overview(class_id)
        overall_pct = int(round((prog["overall_progress"] or 0) * 100))
        quiz_pct    = int(round((prog["quiz_performance"] or 0) * 100))

        st.text("Overall Progress")
        st.progress(min(1.0, overall_pct/100.0))
        st.caption(f"{overall_pct}%")

        st.text("Quiz Performance")
        st.progress(min(1.0, quiz_pct/100.0))
        st.caption(f"{quiz_pct}%")

        k1, k2 = st.columns(2)
        k1.metric("📖 Lessons Completed", prog["lessons_completed"])
        k2.metric("🪙 Total Class XP", prog["class_xp"])

    # ========== BOTTOM ROW: RECENT ACTIVITY + QUICK ACTIONS ==========
    b1, b2 = st.columns([3,2])

    with b1:
        st.subheader("Recent Student Activity")
        st.caption("Latest activity from your students")
        feed = dbapi.class_recent_activity(class_id, limit=6, days=30)
        if not feed:
            st.caption("Nothing yet. Assign something, chief.")
        else:
            for r in feed:
                icon = "📘" if r["kind"] == "lesson" else "🏆" if r["kind"] == "quiz" else "🎮"
                lvl = dbapi.level_from_xp(r.get("total_xp", 0))
                tail = f" · {r['extra']}" if r.get("extra") else ""
                st.write(f"{icon} **{r['student_name']}** — {r['item_title']}{tail}  \n"
                         f"*Level {lvl}*")

    with b2:
        st.subheader("Quick Actions")
        st.caption("Manage your classroom")
        if st.button("📖 Create New Lesson", use_container_width=True):
            st.session_state.current_page = "Content Management"
            st.rerun()
        if st.button("🏆 Create New Quiz", use_container_width=True):
            st.session_state.current_page = "Content Management"
            st.rerun()
        if st.button("🗓️ Schedule Assignment", use_container_width=True):
            st.session_state.current_page = "Class management"
            st.rerun()
        if st.button("📄 Generate Reports", use_container_width=True):
            st.session_state.current_page = "Students List"
            st.rerun()

    # optional: keep your per-class expanders below
    for c in classes:
        with st.expander(f"{c['name']}  · Code **{c.get('code','')}**"):
            st.write(f"Students: {c['total_students']}")
            st.write(f"Average score: {round(c['class_avg']*100)}%")
            roster = dbapi.list_students_in_class(c["class_id"])
            if roster:
                for s in roster:
                    st.write(f"- {s['name']} · {s['email']} · Level {s['level_slug'].capitalize()}")
            else:
                st.caption("No students yet. Share the code.")
