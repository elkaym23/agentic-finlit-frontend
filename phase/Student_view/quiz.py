import streamlit as st
from utils.quizdata import quizzes_data
import datetime
import json
from utils import db as dbapi




def _load_quiz_obj(quiz_id):
    """
    Return a normalized quiz object from either quizzes_data (built-in)
    or the DB (utils.db.get_quiz). Always shape as:
      {"title": str, "questions": [{"question","options","answer","points"}...]}
    For DB rows, convert answer_key letters (e.g., "A") into the option text.
    """
    # Prefer the built-in quizzes when present (IDs 1..5)
    if quiz_id in quizzes_data:
        q = quizzes_data[quiz_id]
        # ensure each question has points
        for qq in q.get("questions", []):
            qq.setdefault("points", 1)
        return q

    # Fallback: DB quiz
    data = dbapi.get_quiz(quiz_id)  # {'quiz': {...}, 'items': [...]}
    if not data:
        return {"title": f"Quiz {quiz_id}", "questions": []}

    items_out = []
    for it in (data.get("items") or []):
        # decode JSON if needed
        opts = it.get("options")
        if isinstance(opts, (str, bytes)):
            try:
                opts = json.loads(opts)
            except Exception:
                opts = []
        opts = opts or []

        ans = it.get("answer_key")
        if isinstance(ans, (str, bytes)):
            try:
                ans = json.loads(ans)
            except Exception:
                # allow a single letter like "A"
                pass

        # convert letter(s) -> option text
        def letter_to_text(letter):
            if isinstance(letter, str):
                idx = ord(letter.upper()) - 65  # A->0, B->1...
                return opts[idx] if 0 <= idx < len(opts) else letter
            return letter

        if isinstance(ans, list):
            ans_text = [letter_to_text(a) for a in ans]
        else:
            ans_text = letter_to_text(ans)

        items_out.append({
            "question": it.get("question", ""),
            "options":  opts,
            "answer":   ans_text,                 # text or list of texts
            "points":   int(it.get("points", 1)),
        })

    title = (data.get("quiz") or {}).get("title", f"Quiz {quiz_id}")
    return {"title": title, "questions": items_out}

def _letter_to_index(ch: str) -> int:
    return ord(ch.upper()) - 65  # 'A'->0, 'B'->1, ...

def _correct_to_indices(correct, options: list[str]):
    """
    Map 'correct' (letters like 'A' or ['A','C'] OR option text(s)) -> list of indices.
    """
    idxs = []
    if isinstance(correct, list):
        for c in correct:
            if isinstance(c, str):
                if len(c) == 1 and c.isalpha():
                    idxs.append(_letter_to_index(c))
                elif c in options:
                    idxs.append(options.index(c))
    elif isinstance(correct, str):
        if len(correct) == 1 and correct.isalpha():
            idxs.append(_letter_to_index(correct))
        elif correct in options:
            idxs.append(options.index(correct))
    # keep only valid unique indices
    return sorted({i for i in idxs if 0 <= i < len(options)})

def _normalize_user_to_indices(user_answer, options: list[str]):
    """
    user_answer can be option text (or list of texts), or letters; return indices.
    """
    idxs = []
    if isinstance(user_answer, list):
        for a in user_answer:
            if isinstance(a, str):
                if a in options:
                    idxs.append(options.index(a))
                elif len(a) == 1 and a.isalpha():
                    idxs.append(_letter_to_index(a))
    elif isinstance(user_answer, str):
        if user_answer in options:
            idxs.append(options.index(user_answer))
        elif len(user_answer) == 1 and user_answer.isalpha():
            idxs.append(_letter_to_index(user_answer))
    return sorted([i for i in idxs if 0 <= i < len(options)])

# --- Helper for level styling ---
def get_level_style(level):
    if level.lower() == "beginner":
        return ("#28a745", "Beginner")  # Green
    elif level.lower() == "intermediate":
        return ("#ffc107", "Intermediate")  # Yellow
    elif level.lower() == "advanced":
        return ("#dc3545", "Advanced")  # Red
    else:
        return ("#6c757d", level)


# --- Sidebar Progress ---
def show_quiz_progress_sidebar(quiz_id):
    qobj = _load_quiz_obj(quiz_id)
    total_q = max(1, len(qobj.get("questions", [])))
    current_q = int(st.session_state.get("current_q", 0))
    answered_count = len(st.session_state.get("answers", {}))

    with st.sidebar:
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 20px;">
            <h3 style="margin: 0; color: #333;">Quiz Progress</h3>
            <div style="font-size: 18px;">☰</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="margin-bottom: 15px;">
            <strong style="color: #333; font-size: 14px;">{qobj.get('title','Quiz')}</strong>
        </div>
        """, unsafe_allow_html=True)

        progress_value = (current_q) / total_q if current_q < total_q else 1.0
        st.progress(progress_value)

        st.markdown(f"""
        <div style="text-align: center; margin: 10px 0; font-weight: bold; color: #333;">
            {min(current_q + 1, total_q)} of {total_q}
        </div>
        """, unsafe_allow_html=True)

        cols = st.columns(5)
        for i in range(total_q):
            col = cols[i % 5]
            with col:
                if i == current_q and current_q < total_q:
                    st.markdown(f"""
                    <div style="background-color: #28a745; color: white; text-align: center; padding: 8px; border-radius: 6px; margin: 2px; font-weight: bold; font-size: 14px;">
                        {i + 1}
                    </div>
                    """, unsafe_allow_html=True)
                elif i in st.session_state.get("answers", {}):
                    st.markdown(f"""
                    <div style="background-color: #d4edda; color: #155724; text-align: center; padding: 8px; border-radius: 6px; margin: 2px; font-size: 14px;">
                        {i + 1}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background-color: #f8f9fa; color: #6c757d; text-align: center; padding: 8px; border-radius: 6px; margin: 2px; border: 1px solid #dee2e6; font-size: 14px;">
                        {i + 1}
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown(f"""
        <div style="font-size: 12px; color: #666; margin: 15px 0;">
            <div style="margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px; background-color: #28a745; border-radius: 50%; margin-right: 8px;"></span>
                <span>Answered ({answered_count})</span>
            </div>
            <div style="margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px; background-color: #17a2b8; border-radius: 50%; margin-right: 8px;"></span>
                <span>Current</span>
            </div>
            <div style="margin: 5px 0;">
                <span style="display: inline-block; width: 12px; height: 12px; background-color: #f8f9fa; border: 1px solid #dee2e6; border-radius: 50%; margin-right: 8px;"></span>
                <span>Not answered</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("← Back to Quizzes", use_container_width=True):
            st.session_state.selected_quiz = None
            st.rerun()

# --- Quiz Question ---
def show_quiz(quiz_id):
    qobj = _load_quiz_obj(quiz_id)
    q_index = int(st.session_state.current_q)
    questions = qobj.get("questions", [])
    question_data = questions[q_index]

    st.header(qobj.get("title", "Quiz"))
    st.subheader(question_data.get("question", ""))

    options = question_data.get("options", [])
    correct_answer = question_data.get("answer")
    key = f"q_{q_index}"
    prev_answer = st.session_state.answers.get(q_index)

    if isinstance(correct_answer, list):
        # multiselect; convert any letter defaults to texts
        default_texts = []
        if isinstance(prev_answer, list):
            for a in prev_answer:
                if isinstance(a, str):
                    if a in options:
                        default_texts.append(a)
                    elif len(a) == 1 and a.isalpha():
                        i = _letter_to_index(a)
                        if 0 <= i < len(options):
                            default_texts.append(options[i])
        answer = st.multiselect("Select all that apply:", options, default=default_texts, key=key)
    else:
        # single answer; compute default index from letter or text
        if isinstance(prev_answer, str):
            if prev_answer in options:
                default_idx = options.index(prev_answer)
            elif len(prev_answer) == 1 and prev_answer.isalpha():
                i = _letter_to_index(prev_answer)
                default_idx = i if 0 <= i < len(options) else 0
            else:
                default_idx = 0
        else:
            default_idx = 0
        answer = st.radio("Select your answer:", options, index=default_idx, key=key)

    st.session_state.answers[q_index] = answer  # auto-save

    if st.button("Next Question ➡"):
        st.session_state.current_q += 1
        st.rerun()



# --- Quiz Results ---
def show_results(quiz_id):
    qobj = _load_quiz_obj(quiz_id)
    questions = qobj.get("questions", [])

    total_points = 0
    earned_points = 0
    details = {"answers": {}}

    for i, q in enumerate(questions):
        options = q.get("options", []) or []
        pts = int(q.get("points", 1))
        total_points += pts

        correct = q.get("answer")
        correct_idx = _correct_to_indices(correct, options)

        user_answer = st.session_state.answers.get(i)
        user_idx = _normalize_user_to_indices(user_answer, options)

        is_correct = (sorted(user_idx) == sorted(correct_idx))
        if is_correct:
            earned_points += pts

        # friendly display
        correct_disp = ", ".join(options[j] for j in correct_idx if 0 <= j < len(options)) or str(correct)
        user_disp = ", ".join(options[j] for j in user_idx if 0 <= j < len(options)) or (
            ", ".join(user_answer) if isinstance(user_answer, list) else str(user_answer)
        )

        if is_correct:
            st.markdown(f"✅ **Q{i+1}: {q.get('question','')}**  \nYour answer: {user_disp}")
        else:
            st.markdown(f"❌ **Q{i+1}: {q.get('question','')}**  \nYour answer: {user_disp}  \nCorrect answer: {correct_disp}")

        details["answers"][str(i+1)] = {
            "question": q.get("question", ""),
            "selected": user_answer,
            "correct": correct,
            "points": pts,
            "earned": pts if is_correct else 0
        }

    percent = int(round(100 * earned_points / max(1, total_points)))
    st.success(f"{qobj.get('title','Quiz')} - Completed! 🎉")
    st.markdown(f"### 🏆 Score: {percent}% ({earned_points}/{total_points} points)")

    # Save submission to DB for assigned quizzes
    if isinstance(quiz_id, int):
        assignment_id = st.session_state.get("current_assignment")
        if assignment_id:
            dbapi.submit_quiz(
                student_id=st.session_state.user["user_id"],
                assignment_id=assignment_id,
                quiz_id=quiz_id,
                score=int(earned_points),
                total=int(total_points),
                details=details
            )

    if st.button("🔁 Retake Quiz"):
        st.session_state.current_q = 0
        st.session_state.answers = {}
        st.rerun()

    if st.button("⬅ Back to Quizzes"):
        st.session_state.selected_quiz = None
        st.rerun()

    # tutor handoff (kept as-is)
    wrong_answers = []
    for i, q in enumerate(questions):
        user_answer = st.session_state.answers.get(i)
        correct = q.get("answer")
        if (isinstance(correct, list) and set(user_answer or []) != set(correct)) or (not isinstance(correct, list) and user_answer != correct):
            wrong_answers.append((q.get("question",""), user_answer, correct, q.get("explanation","")))
    if wrong_answers and st.button("💬 Talk to AI Financial Tutor"):
        st.session_state.selected_quiz = None
        st.session_state.current_page = "Chatbot"
        st.session_state.current_q = 0
        st.session_state.answers = {}
        if "messages" not in st.session_state:
            st.session_state.messages = []
        wrong_q_text = "\n".join(
            [f"Q: {q}\nYour answer: {ua}\nCorrect answer: {ca}\nExplanation: {ex}"
             for q, ua, ca, ex in wrong_answers])
        tutor_prompt = f"I just completed a financial quiz and got some questions wrong. Here are the details:\n{wrong_q_text}\nCan you help me understand these concepts better?"
        st.session_state.messages.append({
            "id": str(datetime.datetime.now().timestamp()),
            "text": tutor_prompt,
            "sender": "user",
            "timestamp": datetime.datetime.now()
        })
        st.session_state.is_typing = True
        st.rerun()

# --- Quiz List ---
def show_quiz_list():
    st.title("📊 Financial Knowledge Quizzes")
    st.caption("Test your financial literacy across different modules")

    cols = st.columns(3)
    for i, (quiz_id, quiz) in enumerate(quizzes_data.items()):
        col = cols[i % 3]
        with col:
            color, label = get_level_style(quiz["level"])
            st.markdown(f"""
            <div style="border:1px solid #e1e5e9; border-radius:12px; padding:20px; margin-bottom:20px; background:white; box-shadow:0 2px 6px rgba(0,0,0,0.08);">
                <span style="background-color:{color}; color:white; font-size:12px; padding:4px 8px; border-radius:6px;">{label}</span>
                <span style="float:right; color:#666; font-size:13px;">⏱ {quiz['duration']}</span>
                <h4 style="margin-top:10px; margin-bottom:6px; color:#222;">{quiz['title']}</h4>
                <p style="font-size:14px; color:#555; line-height:1.4; margin-bottom:10px;">{quiz['description']}</p>
                <p style="font-size:13px; color:#666;">📝 {len(quiz['questions'])} questions</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("Start Quiz ➡", key=f"quiz_{quiz_id}"):
                st.session_state.selected_quiz = quiz_id
                st.session_state.current_q = 0
                st.session_state.answers = {}
                st.rerun()


# --- Main Router for Quiz Page ---
def show_page():
    if "selected_quiz" not in st.session_state:
        st.session_state.selected_quiz = None
    if "current_q" not in st.session_state:
        st.session_state.current_q = 0
    if "answers" not in st.session_state:
        st.session_state.answers = {}

    if st.session_state.selected_quiz is None:
        show_quiz_list()
    else:
        quiz_id = st.session_state.selected_quiz
        qobj = _load_quiz_obj(quiz_id)
        total_q = len(qobj.get("questions", []))
        if st.session_state.current_q < total_q:
            show_quiz(quiz_id)
        else:
            show_results(quiz_id)
