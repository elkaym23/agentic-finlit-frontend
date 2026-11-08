"""Data layer for the Streamlit app — Supabase Postgres via psycopg.

Every function the pages call lives here. Run SmartKids-backend/supabase/schema.sql
in Supabase once before using the app, and set DATABASE_URL (Session pooler URL).
"""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import secrets
import string
from contextlib import contextmanager

import bcrypt
import psycopg
from dotenv import load_dotenv
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

load_dotenv()
log = logging.getLogger(__name__)

XP_PER_LEVEL = 500
LESSON_COMPLETE_XP = 50
XP_PER_QUIZ_POINT = 10
# Calendar date in Jamaica (UTC-5, no daylight saving). Fixed offset so it works on any Postgres build.
_JM_DATE = "(({col}) at time zone 'UTC' - interval '5 hours')::date"

_pool: ConnectionPool | None = None


def _database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        try:  # also allow .streamlit/secrets.toml
            import streamlit as st
            url = st.secrets.get("DATABASE_URL")
        except Exception:
            url = None
    if not url:
        raise RuntimeError("DATABASE_URL is not set (Supabase Session pooler connection string).")
    return url


def _get_pool() -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(
            _database_url(),
            min_size=1,
            max_size=8,
            kwargs={"row_factory": dict_row, "prepare_threshold": None, "autocommit": True},
            open=True,
        )
    return _pool


@contextmanager
def _cur():
    with _get_pool().connection() as conn:
        with conn.cursor() as cur:
            yield cur


@contextmanager
def _tx():
    """Cursor inside a transaction (commit on success, rollback on error)."""
    with _get_pool().connection() as conn:
        with conn.transaction():
            with conn.cursor() as cur:
                yield cur


def _all(sql: str, params=()) -> list[dict]:
    with _cur() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def _one(sql: str, params=()) -> dict | None:
    with _cur() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def _exec(sql: str, params=()):
    with _cur() as cur:
        cur.execute(sql, params)


def _jsonb(v) -> str:
    return json.dumps(v if v is not None else {})


def _backend():
    """Best-effort hook to keep the RAG index in sync; never breaks the UI."""
    try:
        from utils import api
        return api
    except Exception:
        return None


# =============================================================================
# Connection / auth
# =============================================================================
def get_db_connection():
    """Kept for the signup/login pages: returns an open connection or None."""
    try:
        return psycopg.connect(_database_url(), prepare_threshold=None, connect_timeout=10)
    except Exception as e:
        log.error("DB connection failed: %s", e)
        return None


def _hash(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def check_password(email: str, password: str) -> dict | None:
    row = _one(
        "select user_id, name, email, role, level_slug, password_hash from users where lower(email)=lower(%s)",
        (email.strip(),),
    )
    if not row:
        return None
    try:
        ok = bcrypt.checkpw(password.encode(), row["password_hash"].encode())
    except ValueError:
        ok = False
    if not ok:
        return None
    return {
        "user_id": row["user_id"], "name": row["name"], "email": row["email"],
        "role": row["role"], "level": row["level_slug"], "level_slug": row["level_slug"],
    }


def create_student(name, email, password, level_label="Beginner", country_label=None) -> bool:
    try:
        _exec(
            """insert into users (name, email, password_hash, role, country, level_slug)
               values (%s, lower(%s), %s, 'Student', %s, %s)""",
            (name.strip(), email.strip(), _hash(password), country_label, (level_label or "beginner").lower()),
        )
        return True
    except psycopg.errors.UniqueViolation:
        return False


def create_teacher(title, name, email, password) -> bool:
    try:
        _exec(
            """insert into users (name, email, password_hash, role, title)
               values (%s, lower(%s), %s, 'Teacher', %s)""",
            (name.strip(), email.strip(), _hash(password), title),
        )
        return True
    except psycopg.errors.UniqueViolation:
        return False


# =============================================================================
# XP / levels / streaks
# =============================================================================
def level_from_xp(xp) -> int:
    try:
        return 1 + int(xp or 0) // XP_PER_LEVEL
    except (TypeError, ValueError):
        return 1


def _add_xp(cur, user_id: int, xp: int):
    if xp:
        cur.execute("update users set total_xp = total_xp + %s where user_id=%s", (int(xp), user_id))


def _streaks(user_ids: list[int]) -> dict[int, int]:
    """Consecutive active days ending today (or yesterday) per user."""
    if not user_ids:
        return {}
    rows = _all(
        f"""select user_id, {_JM_DATE.format(col='created_at')} as d
           from user_activity
           where user_id = any(%s) and created_at > now() - interval '120 days'
           group by 1, 2""",
        (list(user_ids),),
    )
    days: dict[int, set] = {}
    for r in rows:
        days.setdefault(r["user_id"], set()).add(r["d"])
    today = dt.datetime.now(dt.timezone(dt.timedelta(hours=-5))).date()  # Jamaica, no DST
    out = {}
    for uid in user_ids:
        ds = days.get(uid, set())
        cursor = today if today in ds else today - dt.timedelta(days=1)
        n = 0
        while cursor in ds:
            n += 1
            cursor -= dt.timedelta(days=1)
        out[uid] = n
    return out


def user_xp_and_level(user_id: int) -> dict:
    row = _one("select total_xp from users where user_id=%s", (user_id,))
    xp = int(row["total_xp"]) if row else 0
    return {"xp": xp, "level": level_from_xp(xp), "streak": _streaks([user_id]).get(user_id, 0)}


# =============================================================================
# Classes
# =============================================================================
def _new_code(n: int = 6) -> str:
    alphabet = string.ascii_uppercase.replace("O", "").replace("I", "") + "23456789"
    return "".join(secrets.choice(alphabet) for _ in range(n))


def create_class(teacher_id: int, name: str) -> dict:
    for _ in range(10):
        try:
            row = _one(
                "insert into classes (teacher_id, name, code) values (%s, %s, %s) returning class_id, code",
                (teacher_id, name, _new_code()),
            )
            return {"class_id": row["class_id"], "code": row["code"]}
        except psycopg.errors.UniqueViolation:
            continue
    raise RuntimeError("Could not generate a unique class code")


def get_class(class_id: int) -> dict:
    return _one("select * from classes where class_id=%s", (class_id,)) or {}


def list_classes_by_teacher(teacher_id: int) -> list[dict]:
    return _all(
        """
        select c.class_id, c.name, c.code, c.created_at,
               count(distinct cs.student_id)::int as total_students,
               coalesce(avg(s.score::float / nullif(s.total, 0)), 0) as class_avg
        from classes c
        left join class_students cs on cs.class_id = c.class_id
        left join submissions s on s.student_id = cs.student_id and s.total > 0
        where c.teacher_id = %s
        group by c.class_id
        order by c.created_at desc
        """,
        (teacher_id,),
    )


def list_students_in_class(class_id: int) -> list[dict]:
    return _all(
        """select u.user_id, u.user_id as student_id, u.name, u.email, u.level_slug, u.total_xp, cs.joined_at
           from class_students cs join users u on u.user_id = cs.student_id
           where cs.class_id = %s order by u.name""",
        (class_id,),
    )


def join_class_by_code(student_id: int, code: str) -> int:
    c = _one("select class_id from classes where upper(code) = upper(%s)", ((code or "").strip(),))
    if not c:
        raise ValueError("That class code doesn't exist. Check it with your teacher.")
    existing = _one("select 1 from class_students where class_id=%s and student_id=%s", (c["class_id"], student_id))
    if existing:
        raise ValueError("You're already in this class.")
    _exec("insert into class_students (class_id, student_id) values (%s, %s)", (c["class_id"], student_id))
    return c["class_id"]


def leave_class(student_id: int, class_id: int):
    _exec("delete from class_students where class_id=%s and student_id=%s", (class_id, student_id))


def list_classes_for_student(student_id: int) -> list[dict]:
    return _all(
        """select c.class_id, c.name, c.code, cs.joined_at,
                  trim(coalesce(t.title || ' ', '') || t.name) as teacher_name
           from class_students cs
           join classes c on c.class_id = cs.class_id
           join users t on t.user_id = c.teacher_id
           where cs.student_id = %s order by cs.joined_at desc""",
        (student_id,),
    )


def list_all_students_for_teacher(teacher_id: int) -> list[dict]:
    return _all(
        """select distinct u.user_id, u.name, u.email
           from classes c join class_students cs on cs.class_id = c.class_id
           join users u on u.user_id = cs.student_id
           where c.teacher_id = %s order by u.name""",
        (teacher_id,),
    )


# =============================================================================
# Lessons
# =============================================================================
def create_lesson(teacher_id, title, description, subject, level, sections) -> int:
    with _tx() as cur:
        cur.execute(
            """insert into lessons (teacher_id, title, description, subject, level)
               values (%s, %s, %s, %s, %s) returning lesson_id""",
            (teacher_id, title, description, subject, (level or "beginner").lower()),
        )
        lesson_id = cur.fetchone()["lesson_id"]
        cur.executemany(
            "insert into lesson_sections (lesson_id, position, title, content) values (%s, %s, %s, %s)",
            [(lesson_id, i, s.get("title"), s.get("content")) for i, s in enumerate(sections, start=1)],
        )
    api = _backend()
    if api:
        api.index_lesson_async(lesson_id)
    return lesson_id


def update_lesson(lesson_id, teacher_id, title, description, subject, level, sections) -> bool:
    try:
        with _tx() as cur:
            cur.execute(
                """update lessons set title=%s, description=%s, subject=%s, level=%s, updated_at=now()
                   where lesson_id=%s and teacher_id=%s""",
                (title, description, subject, (level or "beginner").lower(), lesson_id, teacher_id),
            )
            if cur.rowcount == 0:
                return False
            cur.execute("delete from lesson_sections where lesson_id=%s", (lesson_id,))
            cur.executemany(
                "insert into lesson_sections (lesson_id, position, title, content) values (%s, %s, %s, %s)",
                [(lesson_id, i, s.get("title"), s.get("content")) for i, s in enumerate(sections, start=1)],
            )
    except Exception as e:
        log.error("update_lesson failed: %s", e)
        return False
    api = _backend()
    if api:
        api.index_lesson_async(lesson_id)
    return True


def delete_lesson(lesson_id, teacher_id):
    try:
        with _cur() as cur:
            cur.execute("delete from lessons where lesson_id=%s and teacher_id=%s", (lesson_id, teacher_id))
            if cur.rowcount == 0:
                return False, "Lesson not found or you don't own it."
    except Exception as e:
        return False, f"Delete failed: {e}"
    api = _backend()
    if api:
        api.unindex_lesson_async(lesson_id)
    return True, "Deleted"


def get_lesson(lesson_id: int) -> dict:
    L = _one("select * from lessons where lesson_id=%s", (lesson_id,))
    if not L:
        return {"lesson": None, "sections": []}
    secs = _all(
        "select section_id, position, title, content from lesson_sections where lesson_id=%s order by position",
        (lesson_id,),
    )
    return {"lesson": L, "sections": secs}


def list_lessons_by_teacher(teacher_id: int) -> list[dict]:
    return _all(
        """select lesson_id, title, description, subject, level, created_at, updated_at
           from lessons where teacher_id=%s order by created_at desc""",
        (teacher_id,),
    )


# =============================================================================
# Quizzes
# =============================================================================
def _insert_items(cur, quiz_id: int, items: list[dict]):
    cur.executemany(
        """insert into quiz_items (quiz_id, position, question, options, answer_key, points)
           values (%s, %s, %s, %s::jsonb, %s::jsonb, %s)""",
        [
            (
                quiz_id, i, it.get("question", ""),
                json.dumps(it.get("options") or []),
                json.dumps(it.get("answer_key", "A")),
                int(it.get("points", 1) or 1),
            )
            for i, it in enumerate(items, start=1)
        ],
    )


def create_quiz(lesson_id, title, items, settings=None) -> int:
    with _tx() as cur:
        cur.execute(
            "insert into quizzes (lesson_id, title, settings) values (%s, %s, %s::jsonb) returning quiz_id",
            (lesson_id, title, _jsonb(settings)),
        )
        quiz_id = cur.fetchone()["quiz_id"]
        _insert_items(cur, quiz_id, items)
    return quiz_id


def update_quiz(quiz_id, teacher_id, title, items, settings=None) -> bool:
    try:
        with _tx() as cur:
            cur.execute(
                """update quizzes q set title=%s, settings=%s::jsonb
                   from lessons l
                   where q.quiz_id=%s and l.lesson_id=q.lesson_id and l.teacher_id=%s""",
                (title, _jsonb(settings), quiz_id, teacher_id),
            )
            if cur.rowcount == 0:
                return False
            cur.execute("delete from quiz_items where quiz_id=%s", (quiz_id,))
            _insert_items(cur, quiz_id, items)
        return True
    except Exception as e:
        log.error("update_quiz failed: %s", e)
        return False


def delete_quiz(quiz_id, teacher_id):
    try:
        with _cur() as cur:
            cur.execute(
                """delete from quizzes q using lessons l
                   where q.quiz_id=%s and l.lesson_id=q.lesson_id and l.teacher_id=%s""",
                (quiz_id, teacher_id),
            )
            if cur.rowcount == 0:
                return False, "Quiz not found or you don't own it."
        return True, "Deleted"
    except Exception as e:
        return False, f"Delete failed: {e}"


def get_quiz(quiz_id: int) -> dict | None:
    Q = _one(
        """select q.*, l.title as lesson_title from quizzes q
           left join lessons l on l.lesson_id = q.lesson_id where q.quiz_id=%s""",
        (quiz_id,),
    )
    if not Q:
        return None
    items = _all(
        "select item_id, position, question, options, answer_key, points from quiz_items where quiz_id=%s order by position",
        (quiz_id,),
    )
    return {"quiz": Q, "items": items}


def list_quizzes_by_teacher(teacher_id: int) -> list[dict]:
    return _all(
        """select q.quiz_id, q.title, q.lesson_id, l.title as lesson_title, q.created_at,
                  (select count(*) from quiz_items i where i.quiz_id = q.quiz_id)::int as num_items
           from quizzes q join lessons l on l.lesson_id = q.lesson_id
           where l.teacher_id=%s order by q.created_at desc""",
        (teacher_id,),
    )


def submit_quiz(student_id, assignment_id, quiz_id, score, total, details):
    with _tx() as cur:
        cur.execute(
            "select 1 from submissions where student_id=%s and quiz_id=%s limit 1",
            (student_id, quiz_id),
        )
        first_attempt = cur.fetchone() is None
        cur.execute(
            """insert into submissions (student_id, assignment_id, quiz_id, score, total, details)
               values (%s, %s, %s, %s, %s, %s::jsonb)""",
            (student_id, assignment_id, quiz_id, int(score), int(total), _jsonb(details)),
        )
        if first_attempt:  # XP only once per quiz so retakes can't farm XP
            _add_xp(cur, student_id, int(score) * XP_PER_QUIZ_POINT)


# =============================================================================
# Assignments
# =============================================================================
def assign_to_class(lesson_id, quiz_id, class_id, teacher_id, due_at=None) -> int:
    with _tx() as cur:
        cur.execute(
            "select assignment_id from assignments where class_id=%s and lesson_id is not distinct from %s",
            (class_id, lesson_id),
        )
        row = cur.fetchone()
        if row:
            if quiz_id:
                cur.execute("update assignments set quiz_id=%s where assignment_id=%s", (quiz_id, row["assignment_id"]))
            return row["assignment_id"]
        cur.execute(
            """insert into assignments (class_id, lesson_id, quiz_id, teacher_id, due_at)
               values (%s, %s, %s, %s, %s) returning assignment_id""",
            (class_id, lesson_id, quiz_id, teacher_id, due_at),
        )
        return cur.fetchone()["assignment_id"]


def list_class_assignments(class_id: int) -> list[dict]:
    return _all(
        """select a.assignment_id, a.lesson_id, a.quiz_id, a.due_at, a.created_at,
                  coalesce(l.title, q.title, 'Untitled') as title,
                  coalesce(l.subject, 'Finance') as subject,
                  initcap(coalesce(l.level, 'beginner')) as level
           from assignments a
           left join lessons l on l.lesson_id = a.lesson_id
           left join quizzes q on q.quiz_id = a.quiz_id
           where a.class_id=%s order by a.created_at desc""",
        (class_id,),
    )


_STUDENT_ASSIGNMENT_SQL = """
    select a.assignment_id, a.class_id, a.lesson_id, a.quiz_id, a.due_at, a.created_at,
           coalesce(l.title, q.title, 'Untitled') as title,
           coalesce(l.subject, 'Finance') as subject,
           initcap(coalesce(l.level, 'beginner')) as level,
           coalesce(lp.status, 'not_started') as status,
           coalesce(lp.current_pos, 0) as current_pos,
           sub.score, sub.total,
           case when sub.total > 0 then round(100.0 * sub.score / sub.total) end as score_pct
    from assignments a
    left join lessons l on l.lesson_id = a.lesson_id
    left join quizzes q on q.quiz_id = a.quiz_id
    left join lesson_progress lp on lp.student_id = %(sid)s and lp.lesson_id = a.lesson_id
    left join lateral (
        select s.score, s.total from submissions s
        where s.student_id = %(sid)s
          and (s.assignment_id = a.assignment_id or (a.quiz_id is not null and s.quiz_id = a.quiz_id))
        order by s.submitted_at desc limit 1
    ) sub on true
"""


def student_assignments_for_class(student_id: int, class_id: int) -> list[dict]:
    return _all(_STUDENT_ASSIGNMENT_SQL + " where a.class_id = %(cid)s order by a.created_at desc",
                {"sid": student_id, "cid": class_id})


def list_assignments_for_student(student_id: int) -> list[dict]:
    return _all(
        _STUDENT_ASSIGNMENT_SQL
        + """ where a.class_id in (select class_id from class_students where student_id = %(sid)s)
              order by a.created_at desc""",
        {"sid": student_id},
    )


def _assigned_students(where: str, value: int) -> list[dict]:
    return _all(
        f"""select distinct u.user_id, u.name, u.email
            from assignments a
            join class_students cs on cs.class_id = a.class_id
            join users u on u.user_id = cs.student_id
            where {where} = %s order by u.name""",
        (value,),
    )


def list_assigned_students_for_lesson(lesson_id: int) -> list[dict]:
    return _assigned_students("a.lesson_id", lesson_id)


def list_assigned_students_for_quiz(quiz_id: int) -> list[dict]:
    return _assigned_students("a.quiz_id", quiz_id)


# =============================================================================
# Lesson progress (student side)
# =============================================================================
def update_lesson_position(student_id: int, lesson_id: int, position: int, assignment_id: int | None = None):
    _exec(
        """insert into lesson_progress (student_id, lesson_id, assignment_id, status, current_pos)
           values (%s, %s, %s, 'in_progress', %s)
           on conflict (student_id, lesson_id) do update
             set current_pos = greatest(lesson_progress.current_pos, excluded.current_pos),
                 assignment_id = coalesce(excluded.assignment_id, lesson_progress.assignment_id),
                 updated_at = now()
           where lesson_progress.status <> 'completed'""",
        (student_id, lesson_id, assignment_id, int(position)),
    )


def complete_lesson(student_id: int, lesson_id: int, assignment_id: int | None = None,
                    gained_xp: int = LESSON_COMPLETE_XP) -> bool:
    """Mark a lesson completed. Returns True if this was the first completion (XP awarded)."""
    with _tx() as cur:
        cur.execute("select status from lesson_progress where student_id=%s and lesson_id=%s",
                    (student_id, lesson_id))
        prev = cur.fetchone()
        first = not prev or prev["status"] != "completed"
        cur.execute(
            """insert into lesson_progress (student_id, lesson_id, assignment_id, status, current_pos)
               values (%s, %s, %s, 'completed', 999)
               on conflict (student_id, lesson_id) do update
                 set status='completed', updated_at=now(),
                     assignment_id = coalesce(excluded.assignment_id, lesson_progress.assignment_id)""",
            (student_id, lesson_id, assignment_id),
        )
        if first:
            _add_xp(cur, student_id, gained_xp)
    return first


def _catalog_titles() -> dict[int, str]:
    try:
        from phase.Student_view.lesson import lessons_by_level
        return {L["id"]: L["title"] for lvl in lessons_by_level.values() for L in lvl}
    except Exception:
        return {}


def recent_lessons_for_student(student_id: int, limit: int = 5) -> list[dict]:
    rows = _all(
        """select lp.lesson_id, lp.status, lp.current_pos, lp.updated_at, l.title,
                  (select count(*) from lesson_sections s where s.lesson_id = lp.lesson_id) as n_sections
           from lesson_progress lp left join lessons l on l.lesson_id = lp.lesson_id
           where lp.student_id=%s order by lp.updated_at desc limit %s""",
        (student_id, limit),
    )
    titles = _catalog_titles()
    out = []
    for r in rows:
        if r["status"] == "completed":
            pct = 100
        else:
            n = int(r["n_sections"] or 0) or 8  # catalog lessons have ~8 topics
            pct = min(95, int(100 * int(r["current_pos"] or 0) / n))
        out.append({
            "lesson_id": r["lesson_id"],
            "title": r["title"] or titles.get(r["lesson_id"], f"Lesson {r['lesson_id']}"),
            "status": r["status"],
            "progress": pct,
            "updated_at": r["updated_at"],
        })
    return out


def student_quiz_average(student_id: int) -> int:
    row = _one(
        "select avg(score::float / total) as a from submissions where student_id=%s and total > 0",
        (student_id,),
    )
    return int(round(100 * (row["a"] or 0))) if row else 0


def student_class_progress(student_id: int, class_id: int) -> dict:
    row = _one(
        """
        with al as (select distinct lesson_id from assignments where class_id=%(c)s and lesson_id is not null)
        select (select count(*) from al)::int as total_assigned_lessons,
               (select count(*) from lesson_progress lp join al using (lesson_id)
                 where lp.student_id=%(s)s and lp.status='completed')::int as lessons_completed,
               (select avg(s.score::float / s.total) from submissions s
                  join assignments a on a.assignment_id = s.assignment_id
                 where s.student_id=%(s)s and a.class_id=%(c)s and s.total > 0) as avg_score
        """,
        {"s": student_id, "c": class_id},
    )
    total = row["total_assigned_lessons"] or 0
    done = row["lessons_completed"] or 0
    return {
        "total_assigned_lessons": total,
        "lessons_completed": done,
        "overall_progress": (done / total) if total else 0.0,
        "avg_score": row["avg_score"] or 0.0,
    }


# =============================================================================
# Teacher analytics
# =============================================================================
def class_student_metrics(class_id: int) -> list[dict]:
    rows = _all(
        """
        with al as (select distinct lesson_id from assignments where class_id=%(c)s and lesson_id is not null)
        select u.user_id as student_id, u.name, u.email, u.level_slug, u.total_xp, cs.joined_at,
               (select count(*) from al)::int as total_assigned_lessons,
               (select count(*) from lesson_progress lp join al using (lesson_id)
                 where lp.student_id = u.user_id and lp.status = 'completed')::int as lessons_completed,
               (select avg(s.score::float / s.total) from submissions s
                 where s.student_id = u.user_id and s.total > 0) as avg_score
        from class_students cs join users u on u.user_id = cs.student_id
        where cs.class_id = %(c)s
        order by u.name
        """,
        {"c": class_id},
    )
    streaks = _streaks([r["student_id"] for r in rows])
    for r in rows:
        r["avg_score"] = r["avg_score"] or 0.0
        r["streak_days"] = streaks.get(r["student_id"], 0)
        r["level"] = level_from_xp(r["total_xp"])
    return rows


def teacher_tiles(teacher_id: int) -> dict:
    row = _one(
        """
        with st as (select distinct cs.student_id from classes c
                    join class_students cs on cs.class_id = c.class_id where c.teacher_id=%(t)s)
        select (select count(*) from st)::int as total_students,
               coalesce((select avg(s.score::float / s.total) from submissions s
                         where s.student_id in (select student_id from st) and s.total > 0), 0) as class_avg,
               (select count(*) from lessons where teacher_id=%(t)s)::int as lessons_created,
               (select count(distinct a.user_id) from user_activity a
                 where a.user_id in (select student_id from st)
                   and a.created_at > now() - interval '7 days')::int as active_students
        """,
        {"t": teacher_id},
    )
    return row


def class_content_counts(class_id: int) -> dict:
    row = _one(
        """select count(distinct lesson_id)::int as lessons, count(distinct quiz_id)::int as quizzes
           from assignments where class_id=%s""",
        (class_id,),
    )
    return row or {"lessons": 0, "quizzes": 0}


def class_analytics(class_id: int) -> dict:
    prog = class_progress_overview(class_id)
    return {
        "class_avg": prog["quiz_performance"],
        "total_xp": prog["class_xp"],
        "lessons_completed": prog["lessons_completed"],
    }


def class_progress_overview(class_id: int) -> dict:
    row = _one(
        """
        with st as (select student_id from class_students where class_id=%(c)s),
             al as (select distinct lesson_id from assignments where class_id=%(c)s and lesson_id is not null)
        select (select count(*) from st)::int as n_students,
               (select count(*) from al)::int as n_lessons,
               (select count(*) from lesson_progress lp join al using (lesson_id)
                 where lp.student_id in (select student_id from st) and lp.status='completed')::int as lessons_completed,
               (select avg(s.score::float / s.total) from submissions s
                 where s.student_id in (select student_id from st) and s.total > 0) as quiz_performance,
               (select coalesce(sum(total_xp), 0) from users where user_id in (select student_id from st))::int as class_xp
        """,
        {"c": class_id},
    )
    possible = (row["n_students"] or 0) * (row["n_lessons"] or 0)
    return {
        "overall_progress": (row["lessons_completed"] / possible) if possible else 0.0,
        "quiz_performance": row["quiz_performance"] or 0.0,
        "lessons_completed": row["lessons_completed"] or 0,
        "class_xp": row["class_xp"] or 0,
    }


def class_weekly_activity(class_id: int) -> list[dict]:
    rows = _all(
        f"""
        with days as (
            select generate_series({_JM_DATE.format(col='now()')} - 6,
                                   {_JM_DATE.format(col='now()')}, interval '1 day')::date as d
        ),
        act as (
            select {_JM_DATE.format(col='a.created_at')} as d, a.kind
            from user_activity a
            where a.user_id in (select student_id from class_students where class_id=%s)
              and a.created_at > now() - interval '8 days'
        )
        select days.d::text as date,
               count(*) filter (where act.kind='lesson')::int as lessons,
               count(*) filter (where act.kind='quiz')::int as quizzes,
               count(*) filter (where act.kind='game')::int as games
        from days left join act on act.d = days.d
        group by days.d order by days.d
        """,
        (class_id,),
    )
    if not any(r["lessons"] or r["quizzes"] or r["games"] for r in rows):
        return []
    return rows


def class_recent_activity(class_id: int, limit: int = 6, days: int = 30) -> list[dict]:
    return _all(
        """select a.kind, a.item_title, a.extra, a.created_at, u.name as student_name, u.total_xp
           from user_activity a
           join class_students cs on cs.student_id = a.user_id and cs.class_id = %s
           join users u on u.user_id = a.user_id
           where a.created_at > now() - make_interval(days => %s)
           order by a.created_at desc limit %s""",
        (class_id, int(days), int(limit)),
    )


# =============================================================================
# Leaderboards
# =============================================================================
def leaderboard_for_class(class_id: int, limit: int = 10) -> list[dict]:
    rows = _all(
        """select u.user_id, u.name, u.total_xp as xp from class_students cs
           join users u on u.user_id = cs.student_id
           where cs.class_id=%s order by u.total_xp desc limit %s""",
        (class_id, limit),
    )
    for r in rows:
        r["level"] = level_from_xp(r["xp"])
    return rows


def leaderboard_global(limit: int = 10) -> list[dict]:
    rows = _all(
        "select user_id, name, total_xp as xp from users where role='Student' order by total_xp desc limit %s",
        (limit,),
    )
    for r in rows:
        r["level"] = level_from_xp(r["xp"])
    return rows


# =============================================================================
# Games
# =============================================================================
def _record_game(user_id: int, slug: str, payload: dict, gained_xp: int):
    with _tx() as cur:
        cur.execute(
            "insert into game_plays (user_id, game_slug, payload, gained_xp) values (%s, %s, %s::jsonb, %s)",
            (user_id, slug, _jsonb(payload), int(gained_xp or 0)),
        )
        _add_xp(cur, user_id, int(gained_xp or 0))


def record_money_match_play(user_id, target, total, elapsed_ms, matched, gained_xp=0):
    _record_game(user_id, "money_match",
                 {"target": target, "total": total, "elapsed_ms": elapsed_ms, "matched": matched}, gained_xp)


def record_debt_dilemma_round(user_id, level, round_no, wallet, health, happiness, credit_score,
                              event_json=None, outcome=None, gained_xp=0):
    _record_game(user_id, "debt_dilemma", {
        "level": level, "round_no": round_no, "wallet": wallet, "health": health,
        "happiness": happiness, "credit_score": credit_score, "event": event_json, "outcome": outcome,
    }, gained_xp)


def record_profit_puzzle_result(user_id, scenario_id, title, units, price, cost, user_answer,
                                actual_profit, is_correct, gained_xp=0):
    _record_game(user_id, "profit_puzzle", {
        "scenario_id": scenario_id, "title": title, "units": units, "price": price, "cost": cost,
        "user_answer": user_answer, "actual_profit": actual_profit, "is_correct": is_correct,
    }, gained_xp)


def record_budget_builder_play(user_id, payload: dict | None = None, gained_xp=0):
    _record_game(user_id, "budget_builder", payload or {}, gained_xp)
