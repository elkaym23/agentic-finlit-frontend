# phase/Teacher_view/studentlist.py
import streamlit as st
from utils import db as dbapi

# ---------- tiny helpers ----------
def _avatar(name: str) -> str:
    
    return "🧑‍🎓" if hash(name) % 2 else "👩‍🎓"

def _report_text(r, level, avg_pct):
    return (
        "STUDENT PROGRESS REPORT\n"
        "======================\n"
        f"Student: {r['name']}\n"
        f"Email: {r['email']}\n"
        f"Joined: {str(r['joined_at'])[:10]}\n\n"
        "PROGRESS OVERVIEW\n"
        "-----------------\n"
        f"Lessons Completed: {int(r['lessons_completed'] or 0)}/{int(r['total_assigned_lessons'] or 0)}\n"
        f"Average Quiz Score: {avg_pct}%\n"
        f"Total XP: {int(r['total_xp'] or 0)}\n"
        f"Current Level: {level}\n"
        f"Study Streak: {int(r['streak_days'] or 0)} days\n"
    )

def _level_from_xp(total_xp: int) -> int:
    try:
        xp = int(total_xp or 0)
    except Exception:
        xp = 0
    return 1 + xp // 500


ROW_CSS = """
<style>
.sm-chip{display:inline-block;padding:4px 10px;border-radius:999px;background:#eef7f1;color:#0b8f5d;font-weight:600;font-size:.80rem;margin-left:8px}
.sm-pill{display:inline-flex;align-items:center;gap:6px;padding:6px 12px;border:1px solid #e6e6e6;border-radius:8px;background:#fff}
.sm-row{border:1px solid #eee;border-radius:12px;padding:16px 16px;margin:10px 0;background:#fff}
.sm-row:hover{box-shadow:0 2px 10px rgba(0,0,0,.04)}
.sm-right{display:flex;gap:16px;align-items:center;justify-content:flex-end}
.sm-metric{min-width:90px;text-align:right}
.sm-metric .label{color:#777;font-size:.75rem}
.sm-metric .value{font-weight:700;font-size:1.1rem}
.sm-name{font-size:1.05rem;font-weight:700}
.sm-sub{color:#6c6c6c;font-size:.85rem}
</style>
"""

# ---------- page ----------
def show_page():
    st.title("🎓 Student Management")
    st.caption("Monitor and manage your students' progress")
    st.markdown(ROW_CSS, unsafe_allow_html=True)

    teacher = st.session_state.user
    teacher_id = teacher["user_id"]

    classes = dbapi.list_classes_by_teacher(teacher_id)
    if not classes:
        st.info("No classes yet. Create one in Classroom Management.")
        return

    # class selector
    idx = st.selectbox(
        "Choose a class",
        list(range(len(classes))),
        index=0,
        format_func=lambda i: f"{classes[i]['name']}"
    )
    selected = classes[idx]
    class_id = selected["class_id"]
    code_row = dbapi.get_class(class_id)

    # get students before drawing chips
    rows = dbapi.class_student_metrics(class_id)

    # code + student chip row
    chip1, chip2 = st.columns([1, 1])
    with chip1:
        st.markdown(
            f'<div class="sm-chip">Code: {code_row.get("code","")}</div>',
            unsafe_allow_html=True
        )
    with chip2:
        st.markdown(
            f'<div class="sm-chip">👥 {len(rows)} Students</div>',
            unsafe_allow_html=True
        )
        
    st.markdown("---")

    # search line
    query = st.text_input(
        "Search students by name or email",
        placeholder="Type a name or email..."
    ).strip().lower()

    if query:
        rows = [r for r in rows if query in r["name"].lower() or query in r["email"].lower()]

    # student rows
    for r in rows:
        name = r["name"]
        email = r["email"]
        joined = str(r["joined_at"])[:10]
        total_xp = int(r["total_xp"] or 0)
        level = _level_from_xp(total_xp)
        lessons_completed = int(r["lessons_completed"] or 0)
        total_assigned = int(r["total_assigned_lessons"] or 0)
        avg_pct = round((r["avg_score"] or 0) * 100)
        streak = int(r["streak_days"] or 0)

        with st.container():
            st.markdown('<div class="sm-row">', unsafe_allow_html=True)

            # top bar: avatar + name/email + right metrics
            a, b, c = st.columns([0.7, 4, 3])
            with a:
                st.markdown(f"### {_avatar(name)}")
            with b:
                st.markdown(f'<div class="sm-name">{name}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="sm-sub">{email}  ·  Joined {joined}</div>', unsafe_allow_html=True)
            with c:
                st.markdown(
                    '<div class="sm-right">'
                    f'<div class="sm-metric"><div class="value">{level}</div><div class="label">Level</div></div>'
                    f'<div class="sm-metric"><div class="value">{avg_pct}%</div><div class="label">Avg Score</div></div>'
                    f'<div class="sm-metric"><div class="value">{streak}</div><div class="label">Streak</div></div>'
                    "</div>",
                    unsafe_allow_html=True
                )

            # progress bar
            st.caption("Overall Progress")
            frac = (lessons_completed / total_assigned) if total_assigned > 0 else 0.0
            st.progress(min(1.0, frac))
            st.caption(f"{lessons_completed}/{total_assigned} lessons")

            # actions row
            d1, d2, spacer = st.columns([2, 1.3, 5])
            with d1:
                with st.popover("👁️ View Details"):
                    # list the student's assignments
                    items = dbapi.list_assignments_for_student(r["student_id"])
                    if items:
                        for it in items[:25]:
                            tag = " + Quiz" if it["quiz_id"] else ""
                            st.markdown(f"- **{it['title']}** · {it['subject']} · {it['level']}{tag} · Status: {it['status']}")
                    else:
                        st.info("No assignments yet.")
            with d2:
                rep = _report_text(r, level, avg_pct)
                st.download_button(
                    "⬇️ Export",
                    data=rep,
                    file_name=f"{name.replace(' ','_')}_report.txt",
                    mime="text/plain",
                    key=f"dl_{r['student_id']}"
                )

            st.markdown('</div>', unsafe_allow_html=True)  