import streamlit as st
from utils import db as dbapi
import os
from utils import api as backend


# --- Load external CSS ---
def load_css(file_name):
    try:
        with open(file_name, 'r') as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ Stylesheet not found. Please ensure 'assets/styles.css' exists.")


# --- Data structure for lessons ---
lessons_by_level = {
    "beginner": [
        {
            "id": 1,
            "title": "Introduction to Money",
            "description": "Learn the basics of what money is, its history and how it works",
            "duration": "20 min",
            "completed": False,
            "locked": False,
            "difficulty": "Easy",
            "content": "",
            "topics": ["What is money? (coins, notes, digital money)",
                       "History of money in Jamaica (Jamaican coins, notes, and famous historical figures)",
                       "How money is used in daily life",
                       "Different types of currencies",
                       "Recognizing and counting Jamaican coins and notes",
                       "Play: Money Match","Quiz", "Summary"]
        },
        {
            "id": 2,
            "title": "Earning and Spending",
            "description": "Start building the habit of saving money",
            "duration": "8 min",
            "completed": False,
            "locked": False,
            "difficulty": "Easy",
             "topics": ["Jobs people do to earn money",
                       "Allowances and pocket money",
                       "Basic needs vs wants",
                       "Making choices when spending",
                       "Simple budget for small items",
                       "Play: Budget Builder","Quiz", "Summary"]
        },
        {
            "id": 3,
            "title": "Saving Money",
            "description": "Learn to distinguish between essential and optional purchases",
            "duration": "12 min",
            "completed": False,
            "locked": False,
            "difficulty": "Easy",
             "topics": ["Why saving is important",
                       "Where to save (piggy banks, banks)",
                       "Basic needs vs wants",
                       "Setting small savings goals",
                       "Reward of saving (buying a toy, snack, or school supplies)",
                       "Play Piggy Bank challenge","Quiz", "Summary"]
        },
         {
            "id": 4,
            "title": "Simple Financial Responsibility",
            "description": "Learn to distinguish between essential and optional purchases",
            "duration": "12 min",
            "completed": False,
            "locked": False,
            "difficulty": "Easy",
             "topics": ["Making smart choices with money",
                       "Giving and sharing (donations, helping family/friends)",
                       "Recognizing scams or unsafe spending",
                       "Introduction to keeping a simple money diary",
                       "Play Smart Shopper","Quiz", "Summary"]
        }
    ],
    "intermediate": [
        {
            "id": 5,
            "title": "Understanding Compound Interest",
            "description": "Learn how your money can grow exponentially over time",
            "duration": "15 min",
            "completed": True,
            "locked": False,
            "difficulty": "Medium",
            "content": "Compound interest is the eighth wonder of the world..."
        },
        {
            "id": 6,
            "title": "Building an Emergency Fund",
            "description": "Create a financial safety net for unexpected expenses",
            "duration": "12 min",
            "completed": False,
            "locked": False,
            "difficulty": "Medium",
            "content": "An emergency fund is your financial security blanket..."
        },
        {
            "id": 7,
            "title": "Introduction to Investing",
            "description": "Basic concepts of making your money work for you",
            "duration": "18 min",
            "completed": False,
            "locked": False,
            "difficulty": "Medium",
            "content": "Investing is putting your money to work..."
        }
    ],
    "advanced": [
        {
            "id": 8,
            "title": "Stock Market Mastery",
            "description": "Advanced strategies for stock market investing",
            "duration": "25 min",
            "completed": False,
            "locked": True,
            "difficulty": "Hard",
            "content": "Deep dive into stock analysis, market trends..."
        },
        {
            "id": 9,
            "title": "Retirement Planning Strategies",
            "description": "Advanced retirement and tax-advantaged planning",
            "duration": "30 min",
            "completed": False,
            "locked": True,
            "difficulty": "Hard",
            "content": "Advanced retirement planning strategies including 401(k)..."
        },
        {
            "id": 10,
            "title": "Real Estate Investment",
            "description": "Building wealth through property investment",
            "duration": "22 min",
            "completed": False,
            "locked": True,
            "difficulty": "Hard",
            "content": "Learn about real estate as an investment vehicle..."
        }
    ]
}

# --- Utility functions ---

def _db_to_general_lesson_shape(L: dict, sections: list) -> dict:
    """Convert a DB lesson+sections into the same dict shape used by general lessons."""
    level = (L.get("level") or "beginner").lower()
    difficulty = {"beginner": "Easy", "intermediate": "Medium", "advanced": "Hard"}.get(level, "Easy")
    topics = [ (s.get("title") or f"Topic {i+1}") for i, s in enumerate(sections) ]

    # pick a duration heuristic if you don’t store it
    duration = L.get("duration") or f"{max(6, len(topics)*6)} min"

    return {
        "id": int(L["lesson_id"]),
        "title": L.get("title") or "Untitled",
        "description": L.get("description") or "",
        "duration": duration,
        "completed": False,
        "locked": False,
        "difficulty": difficulty,
        "topics": topics,
        # keep optional extra fields if you like:
        "_db_sections": sections,     # stash raw sections so our DB renderer can use them
        "_db_level": level,
    }


def get_difficulty_color(difficulty):
    """Return color based on difficulty level"""
    colors = {
        "Easy": "#28a745",      # Green
        "Medium": "#ffc107",    # Yellow
        "Hard": "#dc3545"       # Red
    }
    return colors.get(difficulty, "#6c757d")

def get_level_info(level):

    level_info = {
        "beginner": {
            "display": "🌱 Beginner",
            "color": "#28a745",
            "description": "Build your financial foundation"
        },
        "intermediate": {
            "display": "🚀 Intermediate", 
            "color": "#007bff",
            "description": "Grow your financial knowledge"
        },
        "advanced": {
            "display": "🎓 Advanced",
            "color": "#6f42c1",
            "description": "Master advanced strategies"
        }
    }
    return level_info.get(level, level_info["beginner"])

# --- Per-user lesson progress (in memory via session_state) ---
def _ensure_progress_state():
    if "topic_progress" not in st.session_state:
        st.session_state.topic_progress = {}  # {lesson_id: max_topic_index_seen}
    if "lesson_completed" not in st.session_state:
        st.session_state.lesson_completed = {}  # {lesson_id: True/False}

def _level_slug_from_user(user: dict | None) -> str:
    user = user or {}
    return (user.get("level_slug") or user.get("level") or "beginner").lower()

def _mark_topic_seen(lesson_id: int, topic_index: int):
    _ensure_progress_state()
    current = st.session_state.topic_progress.get(lesson_id, 0)
    st.session_state.topic_progress[lesson_id] = max(current, topic_index)
    # persist only when the student reaches a new topic (not on every rerun)
    if topic_index > current and st.session_state.get("user"):
        try:
            dbapi.update_lesson_position(st.session_state.user["user_id"], lesson_id, topic_index,
                                         st.session_state.get("selected_assignment"))
        except Exception as e:
            print(f"[lesson] could not save progress: {e}")

def _is_lesson_completed(lesson_id: int) -> bool:
    _ensure_progress_state()
    return st.session_state.lesson_completed.get(lesson_id, False)

def _complete_lesson(lesson):
    _ensure_progress_state()
    st.session_state.lesson_completed[lesson["id"]] = True
    # reflect in the in-memory lessons list too (so the cards show ✓)
    lesson["completed"] = True
    if st.session_state.get("user"):
        try:
            dbapi.complete_lesson(st.session_state.user["user_id"], lesson["id"],
                                  st.session_state.get("selected_assignment"))
        except Exception as e:
            st.warning(f"Could not save lesson completion: {e}")

def _finish_lesson_with_agent(lesson):
    """Mark complete, then ask the RAG agent for a summary + mini-quiz and open the Mini Quiz page."""
    _complete_lesson(lesson)
    s = st.session_state.user
    level_slug = _level_slug_from_user(s)
    st.session_state.mini_quiz_ctx = {
        "lesson_id": lesson["id"], "lesson_title": lesson["title"], "level_slug": level_slug,
        "assignment_id": st.session_state.get("selected_assignment"),
    }
    try:
        with st.spinner("FinBuddy is reviewing the lesson and making your mini-quiz..."):
            resp = backend.start_agent(s["user_id"], lesson["id"], level_slug, lesson_title=lesson["title"])
            st.session_state.lesson_summary = resp.get("summary", "")
            st.session_state.generated_quiz = backend.get_quiz(
                s["user_id"], lesson["id"], level_slug, lesson_title=lesson["title"]
            )
    except Exception as e:
        st.success("🎉 Module completed! Great job.")
        st.error(f"The AI tutor couldn't build a mini-quiz right now: {e}")
        return
    st.session_state.mini_quiz_answers = {}
    st.session_state.mini_quiz_result = None
    st.session_state.current_page = "Mini Quiz"
    st.rerun()  # outside try: st.rerun() works by raising an exception


#-----

def show_lesson_cards(lessons, user_level):

    level_info = get_level_info(user_level)
    
    # Level header
    st.markdown(f"""
    <div style="background-color: {level_info['color']}; color: white; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem;">
        <h2 style="margin: 0; font-size: 2rem;">{level_info['display']}</h2>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem; opacity: 0.9;">{level_info['description']}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Stats
    total_lessons = len(lessons)
    completed_lessons = sum(1 for lesson in lessons if lesson["completed"])
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📚 Total Lessons", total_lessons)
    with col2:
        st.metric("✅ Completed", completed_lessons)
    with col3:
        st.metric("📈 Progress", f"{int((completed_lessons/total_lessons)*100)}%")
    with col4:
        available_lessons = sum(1 for lesson in lessons if not lesson["locked"])
        st.metric("🔓 Available", available_lessons)
    
    st.markdown("---")
    
    # Display lessons in a 3-column grid like Microsoft Learn
    cols = st.columns(3)
    
    for i, lesson in enumerate(lessons):
        lesson["completed"] = lesson.get("completed") or _is_lesson_completed(lesson["id"])

        with cols[i % 3]:
            # Determine card status and styling
            if lesson["locked"]:
                icon_html = '🔒'
                card_opacity = "0.6"
            elif lesson["completed"]:
                icon_html = '✓'
                card_opacity = "1"
            else:
                icon_html = '📖'
                card_opacity = "1"
            
            card_html = f"""
            <div class="lesson-card" style="
                background: white; 
                border: 1px solid #e1e5e9; 
                border-radius: 8px; 
                padding: 24px; 
                margin-bottom: 15px; 
                opacity: {card_opacity}; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                height: 250px;
                transition: all 0.3s ease;
                cursor: pointer;
            ">
                <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                    <h3 style="margin: 0; font-size: 18px; font-weight: 600; color: #323130; line-height: 1.3;">{lesson['title']}</h3>
                    <div style="color: #28a745; font-size: 24px;">{icon_html}</div>
                </div>
                <p style="margin: 0 0 16px 0; color: #605e5c; font-size: 14px; line-height: 1.4;">{lesson['description']}</p>
                <div style="margin-bottom: 16px;">
                    <span style="background-color: #f3f2f1; color: #323130; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: 500;">{lesson['difficulty']}</span>
                </div>
                <div style="color: #0078d4; font-size: 14px; font-weight: 500;">{lesson['duration']}</div>
            </div>
            """
            
            st.markdown(card_html, unsafe_allow_html=True)
            
            # Native Streamlit buttons that actually work
            if lesson["locked"]:
                st.button("🔒 Locked", key=f"lesson_locked_{lesson['id']}", disabled=True, use_container_width=True)
            elif lesson["completed"]:
                if st.button("✅ Review", key=f"lesson_review_{lesson['id']}", use_container_width=True, type="secondary"):
                    st.session_state.selected_lesson = lesson["id"]
                    st.rerun()
            else:
                if st.button("▶ Start Lesson", key=f"lesson_btn_{lesson['id']}", type="primary", use_container_width=True):
                    st.session_state.selected_lesson = lesson["id"]
                    st.rerun()



def show_lesson_detail(lesson):
    st.markdown(f"""
        <h1 style="font-size:2.5rem; margin-bottom:0;">{lesson['title']}</h1>
        <p style="color: #666; margin-top:0;">{lesson['duration']} &nbsp;•&nbsp; Module &nbsp;•&nbsp; {len(lesson.get("topics", []))} units</p>
        <hr style="margin:1rem 0;"/>
    """, unsafe_allow_html=True)

    # Learning objectives section
    st.subheader("Learning objectives")
    st.markdown("""
    <p style="color:#888; margin-bottom:0.5rem;">In this module, you'll</p>
    """, unsafe_allow_html=True)
    
    st.markdown(
        "- Focus on: Basic money concepts  \n"
        "- Saving  \n"
        "- Spending  \n"
        "- Understanding simple financial transactions"
    )

    # Start button
    if st.button("▶ Start", key=f"start_{lesson['id']}", type="primary"):
        st.session_state.start_lesson = True
        st.session_state.current_topic = 1
        # reset progress for this lesson only if not previously completed
        _ensure_progress_state()
        if not _is_lesson_completed(lesson["id"]):
            st.session_state.topic_progress[lesson["id"]] = 1
        st.rerun()


    st.markdown("---")

    # Topics list (with clickable links)
    st.subheader("Topics")
    for i, t in enumerate(lesson.get("topics", []), start=1):
        st.markdown(f"- [{t}](#topic-{i})")

    st.markdown("---")

    # Back button
    if st.button("⬅ Back to Lessons", key=f"back_{lesson['id']}"):
        st.session_state.selected_lesson = None
        st.rerun()



def load_topic_content(lesson_id, topic_index):
    """Load topic content for a specific lesson and topic index"""
    file_path = os.path.join("phase", "Student_view", "lessons", f"lesson_{lesson_id}", f"topic_{topic_index}.txt")
    if os.path.exists(file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            return f"⚠️ Error loading topic content: {e}"
    return "⚠️ Topic content not available."


def show_lesson_page(lesson, lessons):
    # Back link
    if st.button("⬅ Back to Lessons", key=f"back_top_{lesson['id']}"):
        st.session_state.selected_lesson = None
        st.session_state.current_topic = 1
        st.session_state.current_lesson = None
        st.session_state.start_lesson = False
        st.rerun()

    # Header
    st.markdown(f"""
    <div style="background: linear-gradient(135deg,#20c997,#17a2b8); padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
        <h2 style="margin:0;">{lesson['title']}</h2>
        <p style="margin:0.3rem 0;">{lesson['description']}</p>
        <div style="margin-top:0.5rem;">
            <span style="background:#ffffff22; padding:6px 12px; border-radius:6px; margin-right:6px;">⏱ {lesson['duration']}</span>
            <span style="background:#ffffff22; padding:6px 12px; border-radius:6px; margin-right:6px;">📘 Module {lesson['id']}</span>
            <span style="background:#ffffff22; padding:6px 12px; border-radius:6px;">⭐ {lesson['difficulty']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Two-column layout
    col1, col2 = st.columns([2, 1])

    # --- LEFT COLUMN: Lesson content ---
    with col1:
        topics = lesson.get("topics", [])
        if "current_topic" not in st.session_state:
            st.session_state.current_topic = 1

        # Clamp to valid range in case topics changed
        st.session_state.current_topic = max(1, min(st.session_state.current_topic, len(topics)))
        topic_idx = st.session_state.current_topic - 1
        topic_name = topics[topic_idx]

        # Track progress (max topic reached)
        _mark_topic_seen(lesson["id"], st.session_state.current_topic)

        st.subheader(f"Topic {st.session_state.current_topic}: {topic_name}")

        # --- Special handling for Play / Quiz / Normal ---
        if topic_name.lower().startswith("play"):
            st.info("🎮 This is a game-based activity to reinforce learning.")
            st.write("👉 Instructions on how to play go here.")
            if st.button("▶ Play Game", key=f"play_game_{lesson['id']}_{topic_idx}"):
                st.markdown(
                    '<a href="http://your-game-url.com" target="_blank">Open Game in New Tab</a>',
                    unsafe_allow_html=True
                )

        elif "quiz" in topic_name.lower():
            st.info("📝 Time for a quick quiz!")
            st.write("👉 Answer the following questions to test your knowledge.")
            answer = st.radio("Q1. What is money?", ["Coins", "Bananas", "Shoes"])
            if st.button("Submit Answer", key=f"quiz_submit_{lesson['id']}_{topic_idx}"):
                if answer == "Coins":
                    st.success("✅ Correct!")
                else:
                    st.error("❌ Try again.")
        else:
            content = load_topic_content(lesson["id"], st.session_state.current_topic)
            st.markdown(f"""
            <div class="topic-content">
                {content}
            </div>
            """, unsafe_allow_html=True)

        # Topic navigation buttons
        prev_col, next_col = st.columns([1, 1])

        with prev_col:
            st.markdown("<div class='topic-nav-btn prev-btn'>", unsafe_allow_html=True)
            if st.session_state.current_topic > 1:
                if st.button("⬅ Previous Topic", key=f"prev_topic_{lesson['id']}", type="secondary"):
                    st.session_state.current_topic -= 1
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with next_col:
            st.markdown("<div class='topic-nav-btn next-btn'>", unsafe_allow_html=True)
            is_last_topic = (st.session_state.current_topic >= len(topics))

            if not is_last_topic:
                # Normal next
                if st.button("Next Topic ➡", key=f"next_topic_{lesson['id']}", type="primary"):
                    st.session_state.current_topic += 1
                    st.rerun()
            else:
                # Last topic - finish and jump into agent + mini-quiz
                if not _is_lesson_completed(lesson["id"]):
                    if st.button("✅ Complete Module", key=f"complete_{lesson['id']}", type="primary"):
                        _finish_lesson_with_agent(lesson)
                else:
                    st.button("✅ Completed", key=f"completed_{lesson['id']}", disabled=True)
            st.markdown("</div>", unsafe_allow_html=True)


    # --- RIGHT COLUMN: Progress + Lesson navigation ---
    with col2:
        st.subheader("📊 Progress")
        _ensure_progress_state()
        topics_count = max(1, len(lesson.get("topics", [])))
        seen = st.session_state.topic_progress.get(lesson["id"], 0)
        # progress is capped at total topics, and if marked complete, force to full
        if _is_lesson_completed(lesson["id"]):
            pct = 1.0
        else:
            pct = min(seen / topics_count, 1.0)
        st.progress(pct)

        st.subheader("➡ Lesson Navigation")
        idx = next((i for i, l in enumerate(lessons) if l["id"] == lesson["id"]), 0)

        if idx > 0:
            if st.button("⬅ Previous Lesson", key=f"prev_lesson_{lesson['id']}"):
                st.session_state.selected_lesson = lessons[idx - 1]["id"]
                st.session_state.current_topic = 1
                st.rerun()

        if idx < len(lessons) - 1:
            if st.button("Next Lesson ➡", key=f"next_lesson_{lesson['id']}"):
                st.session_state.selected_lesson = lessons[idx + 1]["id"]
                st.session_state.current_topic = 1
                st.rerun()


    st.markdown("---")
   

def render_assigned_lesson(lesson_id: int, assignment_id: int | None = None):
    """Render a teacher-assigned lesson from the DB using the SAME structure/CSS as general lessons."""
    user = st.session_state.user
    user_id = user["user_id"]

    data = dbapi.get_lesson(lesson_id)   # {"lesson": {...}, "sections":[...] }
    if not data or not data.get("lesson"):
        st.error("Lesson not found.")
        if st.button("⬅ Back to classes"):
            st.session_state.current_page = "Teacher Link"
            st.rerun()
        return

    L = data["lesson"]
    sections = sorted(data.get("sections", []), key=lambda s: int(s.get("position", 0)))
    # 👉 adapt to the same card/page structure used by general lessons
    lesson = _db_to_general_lesson_shape(L, sections)

    # initialization flags (mirror general flow)
    if "start_lesson" not in st.session_state:
        st.session_state.start_lesson = False
    if "selected_lesson" not in st.session_state:
        st.session_state.selected_lesson = lesson["id"]

    # Show like general: first a detail screen with Start, then topic pages
    if st.session_state.start_lesson:
        show_db_lesson_page(lesson)
    else:
        show_db_lesson_detail(lesson)


def show_db_lesson_detail(lesson):
    # Same header + objectives block as your general detail view
    st.markdown(f"""
        <h1 style="font-size:2.5rem; margin-bottom:0;">{lesson['title']}</h1>
        <p style="color: #666; margin-top:0;">{lesson['duration']} &nbsp;•&nbsp; Module &nbsp;•&nbsp; {len(lesson.get("topics", []))} units</p>
        <hr style="margin:1rem 0;"/>
    """, unsafe_allow_html=True)

    st.subheader("Learning objectives")
    st.markdown("<p style='color:#888;margin-bottom:.5rem;'>In this module, you'll</p>", unsafe_allow_html=True)
    st.markdown(
        "- Focus on: Key ideas from this lesson  \n"
        "- Build understanding step by step  \n"
        "- Practice and check your knowledge"
    )

    if st.button("▶ Start", key=f"db_start_{lesson['id']}", type="primary"):
        st.session_state.start_lesson = True
        st.session_state.current_topic = 1
        _ensure_progress_state()
        if not _is_lesson_completed(lesson["id"]):
            st.session_state.topic_progress[lesson["id"]] = 1
        st.rerun()

    st.markdown("---")

    st.subheader("Topics")
    for i, t in enumerate(lesson.get("topics", []), start=1):
        st.markdown(f"- [{t}](#topic-{i})")

    st.markdown("---")

    if st.button("⬅ Back to Lessons", key=f"db_back_detail_{lesson['id']}"):
        st.session_state.selected_lesson = None
        st.rerun()


def show_db_lesson_page(lesson):
    # Back link – same as general
    if st.button("⬅ Back to Lessons", key=f"db_back_top_{lesson['id']}"):
        st.session_state.selected_lesson = None
        st.session_state.current_topic = 1
        st.session_state.current_lesson = None
        st.session_state.start_lesson = False
        st.rerun()

    # Header – same gradient & chips
    st.markdown(f"""
    <div style="background: linear-gradient(135deg,#20c997,#17a2b8); padding: 1.5rem; border-radius: 12px; color: white; margin-bottom: 2rem;">
        <h2 style="margin:0;">{lesson['title']}</h2>
        <p style="margin:.3rem 0;">{lesson['description']}</p>
        <div style="margin-top:.5rem;">
            <span style="background:#ffffff22;padding:6px 12px;border-radius:6px;margin-right:6px;">⏱ {lesson['duration']}</span>
            <span style="background:#ffffff22;padding:6px 12px;border-radius:6px;margin-right:6px;">📘 Module {lesson['id']}</span>
            <span style="background:#ffffff22;padding:6px 12px;border-radius:6px;">⭐ {lesson['difficulty']}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Layout
    col1, col2 = st.columns([2, 1])

    # LEFT: topic content (pulled from DB sections)
    with col1:
        topics = lesson.get("topics", [])
        sections = lesson.get("_db_sections", [])
        if "current_topic" not in st.session_state:
            st.session_state.current_topic = 1

        st.session_state.current_topic = max(1, min(st.session_state.current_topic, len(topics)))
        idx = st.session_state.current_topic - 1
        topic_name = topics[idx]
        _mark_topic_seen(lesson["id"], st.session_state.current_topic)

        st.subheader(f"Topic {st.session_state.current_topic}: {topic_name}")

        # Same content container + CSS class as general
        body = (sections[idx].get("content") or "⚠️ Topic content not available.")
        st.markdown(f"<div class='topic-content'>{body}</div>", unsafe_allow_html=True)

        # Prev/Next / Complete – identical logic
        prev_col, next_col = st.columns([1, 1])
        with prev_col:
            st.markdown("<div class='topic-nav-btn prev-btn'>", unsafe_allow_html=True)
            if st.session_state.current_topic > 1:
                if st.button("⬅ Previous Topic", key=f"db_prev_topic_{lesson['id']}", type="secondary"):
                    st.session_state.current_topic -= 1
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

        with next_col:
            st.markdown("<div class='topic-nav-btn next-btn'>", unsafe_allow_html=True)
            is_last = (st.session_state.current_topic >= len(topics))
            if not is_last:
                if st.button("Next Topic ➡", key=f"db_next_topic_{lesson['id']}", type="primary"):
                    st.session_state.current_topic += 1
                    st.rerun()
            else:
                if not _is_lesson_completed(lesson["id"]):
                    if st.button("✅ Complete Module", key=f"db_complete_{lesson['id']}", type="primary"):
                        _finish_lesson_with_agent(lesson)
                else:
                    st.button("✅ Completed", key=f"db_completed_{lesson['id']}", disabled=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # RIGHT: progress + lesson navigation – same UI
    with col2:
        st.subheader("📊 Progress")
        _ensure_progress_state()
        topics_count = max(1, len(lesson.get("topics", [])))
        seen = st.session_state.topic_progress.get(lesson["id"], 0)
        pct = 1.0 if _is_lesson_completed(lesson["id"]) else min(seen / topics_count, 1.0)
        st.progress(pct)

        st.subheader("➡ Lesson Navigation")
        # For DB lessons, we don’t have a linear list like catalog; just basic controls
        if st.button("⬅ Back to Lessons", key=f"db_back_side_{lesson['id']}"):
            st.session_state.selected_lesson = None
            st.session_state.current_topic = 1
            st.rerun()

    st.markdown("---")


def show_page():
    # Load CSS
    css_path = os.path.join("assets", "styles.css")
    load_css(css_path)

    st.markdown("""<style> .markdown { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6;} </style>""", unsafe_allow_html=True)

    # Check login
    if not st.session_state.get("user"):
        st.error("❌ Please login first to access lessons.")
        st.info("💡 Create an account to track your progress and unlock advanced content!")
        return

    user = st.session_state.user
    user_level = user.get("level", "beginner").lower()

    # Deep link from Teacher Link: if a selected_lesson isn't in the catalog,
    # render it from the DB instead.
    deep_lesson_id = st.session_state.get("selected_lesson")
    deep_assignment_id = st.session_state.get("selected_assignment")

    # Try to resolve in catalog first
    lessons = lessons_by_level.get(user_level, [])
    catalog_ids = {l["id"] for l in lessons}

    if deep_lesson_id and deep_lesson_id not in catalog_ids:
        # 👉 This is a teacher-assigned(DB) lesson. Open it directly.
        render_assigned_lesson(int(deep_lesson_id), deep_assignment_id)
        return

    # Initialize session state
    if "selected_lesson" not in st.session_state:
        st.session_state.selected_lesson = None
    if "start_lesson" not in st.session_state:
        st.session_state.start_lesson = False

    # If a lesson is selected
    if st.session_state.selected_lesson:
        lesson = next((l for l in lessons if l["id"] == st.session_state.selected_lesson), None)
        if lesson:
            if st.session_state.start_lesson:  # 🚀 Jump straight into topics
                show_lesson_page(lesson, lessons)
            else:
                show_lesson_detail(lesson)
        else:
            st.warning("⚠️ Lesson not found")
    else:
        # Otherwise → show lesson cards
        show_lesson_cards(lessons, user_level)
