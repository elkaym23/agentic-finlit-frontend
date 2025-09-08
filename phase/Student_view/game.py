import streamlit as st
from utils import db as dbapi
import os


# --- Load external CSS (optional) ---
def load_css(file_name: str):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ Stylesheet not found. Please ensure 'assets/styles.css' exists.")


st.session_state.setdefault("current_game", None)


# --- GAME RENDERERS ---
def _render_budget_builder():
    try:
        from phase.Student_view.games import budgetbuilder as budget_module
    except Exception as e:
        st.error(f"Couldn't import Budget Builder module: {e}")
        return

    if hasattr(budget_module, "show_budget_builder"):
        budget_module.show_budget_builder()
    elif hasattr(budget_module, "show_page"):
        budget_module.show_page()
    else:
        st.error("Budget Builder module found, but no show function (show_budget_builder/show_page).")

def _render_debt_dilemma():
    try:
        from phase.Student_view.games import debtdilemma as debt_module
    except Exception as e:
        st.error(f"Couldn't import Debt Dilemma module: {e}")
        return

    if hasattr(debt_module, "show_debt_dilemma"):
        debt_module.show_debt_dilemma()
    elif hasattr(debt_module, "show_page"):
        debt_module.show_page()
    else:
        st.error("Debt Dilemma module found, but no show function (show_debt_dilemma/show_page).")

def _render_money_match():
    """
    Renders Money Match if the file exists at phase/games/MoneyMatch.py
    and exposes a show_page() function.
    """
    try:
        
        from phase.Student_view.games  import MoneyMatch as mm_module
    except Exception as e:
        st.error(f"Couldn't import Money Match module: {e}")
        st.info("Tip: ensure phase/games/MoneyMatch.py exists and defines show_page()")
        return

    if hasattr(mm_module, "show_page"):
        mm_module.show_page()
    else:
        st.error("Money Match module found, but no show_page() function.")

#render for profit puzzle 
def _render_profit_puzzle():
    try:
        from phase.Student_view.games import profitpuzzle as pp_module
    except Exception as e:
        st.error(f"Couldn't import Profit Puzzle module: {e}")
        return

    if hasattr(pp_module, "show_profit_puzzle"):
        pp_module.show_profit_puzzle()
    elif hasattr(pp_module, "show_page"):
        pp_module.show_page()
    else:
        st.error("Profit Puzzle module found, but no show function (show_profit_puzzle/show_page).")


import textwrap

def render_leaderboard(leaderboard):
    def rank_symbol(rank):
        if rank == "You":
            return "🟢"
        if isinstance(rank, int):
            return "🥇" if rank == 1 else "🥈" if rank == 2 else "🥉" if rank == 3 else f"#{rank}"
        return str(rank)

    def rank_medal_class(rank):
        if isinstance(rank, int) and rank in (1, 2, 3):
            return f"medal-{rank}"
        return ""

    rows = []
    head = '<div class="lb-head">🏆 Leaderboard</div>'
    for p in leaderboard:
        is_you = p["rank"] == "You"
        medal_cls = rank_medal_class(p["rank"])
        symbol = rank_symbol(p["rank"])
        you_pill = '<span class="lb-you-pill">YOU</span>' if is_you else ""
        rows.append(
            textwrap.dedent(f"""
            <div class="lb-row {'is-you' if is_you else ''}">
              <div class="lb-rank {medal_cls}">{symbol}</div>
              <div class="lb-name">{p['name']}</div>
              <div class="lb-level">Lvl {p['level']}</div>
              <div class="lb-xp">{p['xp']:,} XP</div>
              {you_pill}
            </div>
            """).strip()
        )

    html = textwrap.dedent(f"""
    <div class="leaderboard">
      {head}
      {''.join(rows)}
    </div>
    """).strip()

    st.markdown(html, unsafe_allow_html=True)

def _load_leaderboard(user_id: int, limit: int = 10) -> list[dict]:
    """
    Shape returned fits render_leaderboard:
      [{"rank": int|"You", "name": str, "level": int, "xp": int, "user_id": int}, ...]
    Prefers class leaderboard if current_class_id is set; else global.
    Ensures current user is included and labeled "You".
    """
    you_name = (st.session_state.get("user") or {}).get("name") or "You"
    class_id = st.session_state.get("current_class_id")

    # try to pick a class automatically if none set (optional)
    if not class_id and hasattr(dbapi, "list_classes_for_student"):
        try:
            classes = dbapi.list_classes_for_student(user_id) or []
            if classes:
                class_id = classes[0]["class_id"]
                st.session_state.current_class_id = class_id
        except Exception:
            pass

    # fetch rows from DB
    try:
        if class_id and hasattr(dbapi, "leaderboard_for_class"):
            rows = dbapi.leaderboard_for_class(class_id, limit=limit) or []
        elif hasattr(dbapi, "leaderboard_global"):
            rows = dbapi.leaderboard_global(limit=limit) or []
        else:
            # fallback using existing function if needed
            rows = []
            if class_id and hasattr(dbapi, "class_student_metrics"):
                for m in dbapi.class_student_metrics(class_id) or []:
                    xp = int(m.get("total_xp", 0))
                    rows.append({
                        "user_id": m.get("student_id"),
                        "name": m.get("name") or m.get("email") or "Student",
                        "xp": xp,
                        "level": dbapi.level_from_xp(xp),
                    })
    except Exception as e:
        st.warning(f"Leaderboard error: {e}")
        rows = []

    # ensure current user present
    if not any(r.get("user_id") == user_id for r in rows):
        try:
            stats = dbapi.user_xp_and_level(user_id) or {}
            rows.append({
                "user_id": user_id,
                "name": you_name,
                "xp": int(stats.get("xp", 0)),
                "level": int(stats.get("level", 1)),
            })
        except Exception:
            rows.append({"user_id": user_id, "name": you_name, "xp": 0, "level": 1})

    # sort, rank, and mark "You"
    rows.sort(key=lambda r: int(r.get("xp", 0)), reverse=True)
    ranked = []
    for i, r in enumerate(rows, start=1):
        ranked.append({
            "rank": i,
            "user_id": r["user_id"],
            "name": r["name"],
            "level": int(r["level"]),
            "xp": int(r["xp"]),
        })
    for r in ranked:
        if r["user_id"] == user_id:
            r["rank"] = "You"
            break

    # "You" first visually, then others by rank
    you = [r for r in ranked if r["rank"] == "You"]
    others = [r for r in ranked if r["rank"] != "You"]
    return (you + others)[:limit]


# --- MAIN GAMES HUB & ROUTER ---
def show_games():
    load_css(os.path.join("assets", "styles.css"))
    
    if "user" not in st.session_state or st.session_state.user is None:
        st.error("❌ Please login first.")
        st.session_state.current_page = "Welcome"
        st.rerun()

    game_key = st.session_state.current_game

    # If a specific game is active → render it
    if game_key is not None:
        if game_key == "budget_builder":
            _render_budget_builder()
        elif game_key == "money_match":
            _render_money_match()
        elif game_key == "debt_dilemma":
             _render_debt_dilemma()
        elif game_key == "profit_puzzle":
            _render_profit_puzzle()

        st.markdown("---")
        if st.button("⬅ Back to Games Hub"):
            st.session_state.current_game = None
            st.rerun()
        return  # don’t render the hub

    # ===== Games Hub =====
    st.title("Financial Games")
    st.subheader("Learn by playing! Master financial concepts through interactive games.")

     # Progress overview
    col1, col2 = st.columns([1, 5])
    with col1:
        st.markdown(
            """
            <div style="
                width:50px; height:50px;
                border-radius:15px;
                background: linear-gradient(135deg, #22c55e, #059669);
                display:flex; align-items:center; justify-content:center;
                font-size:28px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            ">
                ✨
            </div>
            """,
            unsafe_allow_html=True
        )

    with col2:
        # pull live XP/level from DB
        user_id = st.session_state.user["user_id"]
        try:
            stats = dbapi.user_xp_and_level(user_id)   # {'xp': int, 'level': int, 'streak': int}
            total_xp = int(stats.get("xp", 0))
            level    = int(stats.get("level", 1))
            # keep session in sync (optional)
            st.session_state.xp     = total_xp
            st.session_state.streak = stats.get("streak", 0)
        except Exception:
            # safe fallback if DB hiccups
            total_xp = int(st.session_state.get("xp", 0))
            level    = max(1, (total_xp // 500) + 1)

        # leveling curve: every 500 XP is a level
        level_floor = (level - 1) * 500           # XP at start of this level
        level_cap   = level * 500                  # XP needed to reach next level
        in_level_xp = max(0, total_xp - level_floor)
        span        = max(1, level_cap - level_floor)  # usually 500
        progress_pct = int((in_level_xp / span) * 100)

        st.write(f"Level {level}  Experience Points")

        # progress bar shows progress within *current* level
        st.markdown(f"""
            <div style="background:#e0e0e0;border-radius:12px;padding:3px;width:100%;">
                <div style="
                    width:{progress_pct}%;
                    background:linear-gradient(135deg,#22c55e,#059669);
                    height:24px;border-radius:10px;text-align:right;
                    color:white;font-weight:bold;padding-right:8px;line-height:24px;">
                    {total_xp:,} / {level_cap:,} XP
                </div>
            </div>
        """, unsafe_allow_html=True)



    st.markdown("---")

        # Game list
    games = [
        {"key": "money_match", "icon": "💰", "title": "Money Match",
         "description": "Drag coins and notes to match target values. Perfect for learning denominations!",
         "difficulty": "Easy", "xp": "+10 XP", "time": "5-10 min", "color": "linear-gradient(135deg, #22c55e, #059669)"},
        {"key": "budget_builder", "icon": "📊", "title": "Budget Builder",
         "description": "Allocate your weekly allowance across different spending categories with real-time pie charts.",
         "difficulty": "Easy", "xp": "+50 XP", "time": "10-15 min", "color": "linear-gradient(135deg, #3b82f6, #06b6d4)"},
         {"key": "profit_puzzle", "icon": "🧩", "title": "Profit Puzzle",
         "description": "Solve business scenarios with interactive sliders. Calculate profit, revenue, and costs!",
         "difficulty": "Medium", "xp": "+150 XP", "time": "10-15 min", "color": "linear-gradient(135deg, #6366f1, #8b5cf6)"},
        {"key": "debt_dilemma", "icon": "⚠️", "title": "Debt Dilemma",
         "description": "Experience borrowing JA$100 and learn about interest, repayment schedules, and credit scores.",
         "difficulty": "Hard", "xp": "+200 XP", "time": "20-25 min", "color": "linear-gradient(135deg, #f97316, #dc2626)"},
        ]

    cols = st.columns(2)
    color_map = {"Easy": "green", "Medium": "orange", "Hard": "red"}

    for i, g in enumerate(games):
        with cols[i % 2]:
            st.markdown(
                f"""
                <div style="
                    width:60px; height:60px;
                    border-radius:16px;
                    background:{g['color']};
                    display:flex; align-items:center; justify-content:center;
                    font-size:28px; margin-bottom:10px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                ">
                    {g['icon']}
                </div>
                """,
                unsafe_allow_html=True
            )
            st.subheader(g["title"])
            st.write(g["description"])
            diff_color = color_map.get(g["difficulty"], "gray")
            st.markdown(
                f"<div style='color:{diff_color}; font-weight:bold'>{g['difficulty']}</div> | "
                f"{g['xp']} | {g['time']}",
                unsafe_allow_html=True
            )
            if st.button("▶ Play Now", key=f"play_{g['key']}"):
                st.session_state.current_game = g["key"]
                st.rerun()


    st.markdown("---")
    
    # Leaderboard & Tips
    col_leader, col_tips = st.columns(2)
    with col_leader:
        user_id = st.session_state.user["user_id"]
        lb = _load_leaderboard(user_id, limit=10)
        if lb:
            render_leaderboard(lb)
        else:
            st.info("No leaderboard data yet.")


       

    with col_tips:
        st.subheader("Game Tips")
        for tip in [
            "🌟 Start with easier games to build confidence",
            "⏰ Take your time to understand concepts",
            "🏆 Replay games to improve your score",
            "🌍 Apply game lessons to real life",
        ]:
            st.markdown(f"- {tip}")
