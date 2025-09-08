import os
import streamlit as st
from phase.Student_view import chatbot, lesson, quiz
from utils import db as dbapi

# --- Load external CSS ---
def load_css(file_name: str):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ Stylesheet not found. Please ensure 'assets/styles.css' exists.")

def show_student_dashboard():
    # Load CSS
    css_path = os.path.join("assets", "styles.css")
    load_css(css_path)

    # Current user
    user = st.session_state.user
    name = user["name"]
    student_id = user["user_id"]

    # --- Real metrics from DB ---
    # Requires helper funcs in utils/db.py: user_xp_and_level, recent_lessons_for_student, list_assignments_for_student
    stats = dbapi.user_xp_and_level(student_id) if hasattr(dbapi, "user_xp_and_level") else {"xp": 0, "level": 1, "streak": 0}
    xp = int(stats.get("xp", 0))
    level = int(stats.get("level", 1))
    study_streak = int(stats.get("streak", 0))

    # Cap for the visual bar
    max_xp = max(500, ((xp // 500) + 1) * 500)

    # Assignments for “My Work”
    rows = dbapi.list_assignments_for_student(student_id) if hasattr(dbapi, "list_assignments_for_student") else []

    def _pct_from_row(r: dict):
        sp = r.get("score_pct")
        if sp is not None:
            try:
                return int(round(float(sp)))
            except Exception:
                pass
        s, t = r.get("score"), r.get("total")
        if s is not None and t not in (None, 0):
            try:
                return int(round((float(s) / float(t)) * 100))
            except Exception:
                return None
        return None

    quiz_score = dbapi.student_quiz_average(student_id) if hasattr(dbapi, "student_quiz_average") else 0
    lessons_completed = sum(1 for r in rows if r.get("status") == "completed" or _pct_from_row(r) == 100)
    total_lessons = len(rows)

    # Recent lessons assigned to this student
    recent_lessons = dbapi.recent_lessons_for_student(student_id, limit=5) if hasattr(dbapi, "recent_lessons_for_student") else []

    # Daily Challenge derived from real data
    challenge_difficulty = "Easy" if level < 3 else ("Medium" if level < 6 else "Hard")
    challenge_title = "Complete 1 quiz with 80%+"
    challenge_desc = "Prove you remember yesterday's key points."
    challenge_progress = 100 if quiz_score >= 80 else 0
    reward = "+50 XP"
    time_left = "Ends 11:59 PM"

    # Achievements from real data
    achievements = [
        {"title": "First Steps", "desc": "Complete your first lesson", "earned": lessons_completed > 0},
        {"title": "Quiz Whiz", "desc": "Score 80%+ on any quiz", "earned": quiz_score >= 80},
        {"title": "On a Roll", "desc": "Study 3 days in a row", "earned": study_streak >= 3},
        {"title": "Consistency", "desc": "Finish 5 assignments", "earned": total_lessons >= 5 and lessons_completed >= 5},
    ]

    # --- Welcome Card ---
    st.markdown(
        f"""
        <div class="welcome-card">
            <h2>Welcome back, {name}!</h2>
            <p style="font-size: 20px;">{"Ready to continue your financial journey?" if lessons_completed > 0 else "Start your financial journey."}</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")

    # --- Quick Action Buttons ---
    actions = [
        ("📚 Start a Lesson", "Lessons"),
        ("📝 Attempt a Quiz", "Quiz"),
        ("💬 Talk to AI Tutor", "Chatbot"),
    ]

    # 5 columns: spacer, button, button, button, spacer
    cols = st.columns([1, 2, 2, 2, 1])
    for i, (label, page) in enumerate(actions):
        with cols[i+1]:  # skip the left spacer
            if st.button(label, key=f"action_{i}"):
                st.session_state.current_page = page
                st.rerun()

    st.write("")

    # --- Progress Summary Cards ---
    progress_cols = st.columns(3)
    progress_cols[0].metric("📘 Lessons Completed", f"{lessons_completed}/{total_lessons}")
    progress_cols[1].metric("📊 Quiz Score", f"{quiz_score}/100")
    progress_cols[2].metric("🔥 Study Streak", f"{study_streak} days")
    st.write("")

    # --- My Assignments (from DB) ---
    st.markdown("---")
    st.subheader("📘 My Work")
    if not rows:
        st.info("No assignments yet. Ask your teacher to assign a lesson.")
    else:
        for a in rows:
            title  = a.get("title", "Untitled")
            subj   = a.get("subject", "General")
            lvl    = a.get("level", "Beginner")
            status = a.get("status", "not_started")
            due    = a.get("due_at")
            due_txt = f" · Due {str(due)[:10]}" if due else ""
            st.markdown(f"**{title}** · {subj} · {lvl}{due_txt}")
            st.caption(f"Status: {status}  ·  Resume at section {a.get('current_pos', 1)}")
            st.markdown("---")

    # --- XP Bar ---
    pct = 0 if max_xp <= 0 else min(100, int(round((xp / max_xp) * 100)))
    st.markdown(
        f"""
        <div class="xp-card">
            <span class="xp-level">Level {level}</span>
            <span class="xp-text">{xp} / {max_xp} XP</span>
            <div class="xp-bar">
                <div class="xp-fill" style="width: {pct}%;"></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.write("")


    # --- Recent Lessons & Achievements ---
    col1, col2 = st.columns(2)

    def _progress_value(v):
        try:
            f = float(v)
        except Exception:
            return 0.0
        # streamlit accepts 0–1 float; if someone passes 0–100, scale it
        return max(0.0, min(1.0, f if f <= 1.0 else f / 100.0))

    with col1:
        st.subheader("📖 Recent Lessons")
        st.caption("Continue where you left off")
        if not recent_lessons:
            st.info("No recent lessons yet.")
        else:
            for lesson in recent_lessons:
                prog = lesson.get("progress", 0)
                st.progress(_progress_value(prog))
                status = "✅ Complete" if (isinstance(prog, (int, float)) and prog >= 100) else f"{int(prog)}% complete"
                st.write(f"**{lesson.get('title','Untitled Lesson')}** — {status}")

    with col2:
        st.subheader("🏆 Achievements")
        st.caption("Your learning milestones")
        for ach in achievements:
            if ach["earned"]:
                st.success(f"✔ {ach['title']} — {ach['desc']}")
            else:
                st.info(f"🔒 {ach['title']} — {ach['desc']}")
