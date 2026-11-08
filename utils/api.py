"""HTTP client for the SmartKids backend (RAG tutor)."""
import os
import threading

import requests
from dotenv import load_dotenv

load_dotenv()

BACKEND = (os.getenv("BACKEND_URL") or "http://localhost:7860").rstrip("/")
_API_KEY = os.getenv("BACKEND_API_KEY")
_TIMEOUT = int(os.getenv("BACKEND_TIMEOUT", "90"))  # HF Spaces can cold-start slowly


def _headers():
    return {"X-API-Key": _API_KEY} if _API_KEY else {}


def _post(path: str, payload: dict | None = None, timeout: int | None = None) -> dict:
    r = requests.post(f"{BACKEND}{path}", json=payload or {}, headers=_headers(), timeout=timeout or _TIMEOUT)
    if r.status_code >= 400:
        try:
            detail = r.json().get("detail")
        except Exception:
            detail = r.text[:300]
        raise RuntimeError(f"Backend {r.status_code}: {detail}")
    return r.json()


def health() -> dict:
    r = requests.get(f"{BACKEND}/health", timeout=15)
    r.raise_for_status()
    return r.json()


# --- tutor chat ---------------------------------------------------------------
def chat(message: str, user_id: int = 0, level_slug: str = "beginner",
         history: list[dict] | None = None, lesson_id: int | None = None) -> dict:
    """Returns {"reply": str, "sources": [...]}"""
    return _post("/chat", {
        "message": message, "user_id": user_id, "level_slug": level_slug,
        "history": history or [], "lesson_id": lesson_id,
    })


# --- lesson agent -------------------------------------------------------------
def start_agent(student_id: int, lesson_id: int, level_slug: str, lesson_title: str | None = None) -> dict:
    return _post("/agent/start", {"student_id": student_id, "lesson_id": lesson_id,
                                  "level_slug": level_slug, "lesson_title": lesson_title})


def get_quiz(student_id: int, lesson_id: int, level_slug: str, lesson_title: str | None = None,
             n_questions: int = 5) -> list[dict]:
    return _post("/agent/quiz", {"student_id": student_id, "lesson_id": lesson_id, "level_slug": level_slug,
                                 "lesson_title": lesson_title, "n_questions": n_questions})["items"]


def grade_quiz(student_id: int, lesson_id: int, level_slug: str, items: list[dict], answers: list[str],
               assignment_id: int | None = None):
    d = _post("/agent/grade", {"student_id": student_id, "lesson_id": lesson_id, "level_slug": level_slug,
                               "items": items, "answers": answers, "assignment_id": assignment_id})
    return d["score"], d["total"]


def next_step(student_id: int, lesson_id: int, level_slug: str, items: list[dict], answers: list[str],
              assignment_id: int | None = None) -> dict:
    return _post("/agent/coach_or_celebrate", {"student_id": student_id, "lesson_id": lesson_id,
                                               "level_slug": level_slug, "items": items, "answers": answers,
                                               "assignment_id": assignment_id})


# --- teacher tools ------------------------------------------------------------
def generate_quiz(text: str, n_questions: int = 5, level_slug: str = "beginner") -> list[dict]:
    return _post("/quiz/generate", {"text": text, "n_questions": n_questions, "level_slug": level_slug})["items"]


def index_lesson(lesson_id: int) -> dict:
    return _post(f"/ingest/lesson/{int(lesson_id)}", timeout=180)


def _fire_and_forget(fn, *args):
    def run():
        try:
            fn(*args)
        except Exception as e:  # indexing is best-effort; never break the UI
            print(f"[api] background call failed: {e}")
    threading.Thread(target=run, daemon=True).start()


def index_lesson_async(lesson_id: int):
    _fire_and_forget(index_lesson, lesson_id)


def unindex_lesson_async(lesson_id: int):
    def _delete(lid):
        requests.delete(f"{BACKEND}/ingest/lesson/{int(lid)}", headers=_headers(), timeout=60)
    _fire_and_forget(_delete, lesson_id)
