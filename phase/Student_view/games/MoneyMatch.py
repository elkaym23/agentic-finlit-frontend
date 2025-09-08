# phase\Student_view\games\MoneyMatch.py

import time
import os
import random
from pathlib import Path
import streamlit as st
from utils import db as dbapi
import time
from utils import db as db_util

# ---------- paths ----------
PROJECT_ROOT = Path(__file__).resolve().parents[3]

def _asset(*parts: str) -> str:
    # JMD image path
    return str((PROJECT_ROOT / "assets" / "images" / Path(*parts)).resolve())

def _safe_image(path: str, *, caption: str = ""):
    if not os.path.exists(path):
        st.warning(f"Image not found: {Path(path).name}. Button still works.")
        return False
    st.image(path, use_column_width=True, caption=caption)
    return True

# ---------- state helpers ----------
def _init_state():
    ss = st.session_state
    if "mm_level" not in ss: ss.mm_level = 1
    if "mm_xp" not in ss: ss.mm_xp = 0
    if "mm_matches" not in ss: ss.mm_matches = 0
    if "mm_target" not in ss: ss.mm_target = random.randint(7, 10000)  # randon goal generator
    if "mm_selected" not in ss: ss.mm_selected = []
    if "mm_total" not in ss: ss.mm_total = 0
    if "mm_start_ts" not in ss: ss.mm_start_ts = time.perf_counter()
    if "mm_saved" not in ss: ss.mm_saved = False

def _reset_round(new_target: int | None = None):
    ss = st.session_state
    ss.mm_selected = []
    ss.mm_total = 0
    ss.mm_target = new_target if new_target is not None else random.randint(7, 10000)
    ss.mm_start_ts = time.perf_counter()
    ss.mm_saved = False

def _award_xp(gained: int):
    ss = st.session_state
    ss.mm_xp += gained
    ss.mm_matches += 1
    while ss.mm_xp >= ss.mm_level * 100:
        ss.mm_level += 1

def _persist_success(gained_xp: int):
    user = st.session_state.get("user")
    if not user or "user_id" not in user:
        st.error("Not saving. No logged-in user_id in session.")
        return
    elapsed_ms = int((time.perf_counter() - st.session_state.mm_start_ts) * 1000)
    try:
        dbapi.record_money_match_play(
            user["user_id"],
            target=int(st.session_state.mm_target),
            total=int(st.session_state.mm_total),
            elapsed_ms=elapsed_ms,
            matched=True,
            gained_xp=int(gained_xp),
        )
        st.toast(f"Saved to TiDB  +{gained_xp} XP")
    except Exception as e:
        st.error(f"Save failed: {e}")

# --- CSS injection (run every render) ---
def _inject_css():
    css_path = PROJECT_ROOT / "assets" / "styles.css"
    try:
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    except Exception:
        # don't crash the page because of styling
        pass


# ---------- denominations ----------
DENOMS = [
    ("JA$1",     1,    _asset("jmd", "jmd_1.jpeg")),
    ("JA$5",     5,    _asset("jmd", "jmd_5.jpeg")),
    ("JA$10",    10,   _asset("jmd", "jmd_10.jpeg")),
    ("JA$20",    20,   _asset("jmd", "jmd_20.jpeg")),
    ("JA$50",    50,   _asset("jmd", "jmd_50.jpg")),
    ("JA$100",   100,  _asset("jmd", "jmd_100.jpg")),
    ("JA$500",   500,  _asset("jmd", "jmd_500.jpg")),
    ("JA$1000",  1000, _asset("jmd", "jmd_1000.jpeg")),
    ("JA$2000",  2000, _asset("jmd", "jmd_2000.jpeg")),
    ("JA$5000",  5000, _asset("jmd", "jmd_5000.jpeg")),
]

# ---------- main ----------
def show_page():
    _init_state()
    _inject_css()   # <- keep this here so it runs on every rerun
    ss = st.session_state


    if st.button("← Back to Games"):
        ss.current_game = None
        st.rerun()

    st.title("Money Match Challenge")

    left, right = st.columns([1.75, 1])

    with left:
        st.markdown('<div class="mm-card">', unsafe_allow_html=True)
        st.markdown(f"<h3>Target: <span class='mm-target'>JA${ss.mm_target}</span></h3>", unsafe_allow_html=True)
        st.markdown(f"<div class='mm-total'>JA${ss.mm_total}</div>", unsafe_allow_html=True)

        ratio = min(ss.mm_total / ss.mm_target, 1.0) if ss.mm_target else 0
        st.progress(ratio)

        diff = ss.mm_target - ss.mm_total
        need_text = "Perfect match. Click Next round." if diff == 0 else (f"Need JA${diff} more" if diff > 0 else f"Overshot by JA${abs(diff)}")
        st.caption(need_text)

        # autosave stats if perfect match
        if diff == 0 and not ss.mm_saved:
             gained = 10
             _persist_success(gained)
             _award_xp(gained)
             ss.mm_saved = True

        # tray
        if ss.mm_selected:
            chips = " ".join([f"<span class='mm-chip'>${v}</span>" for v in ss.mm_selected])
            st.markdown(f"<div class='mm-tray'>{chips}</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div class='mm-tray mm-empty'>Selected money will appear here</div>", unsafe_allow_html=True)

        c1, c2 = st.columns([1,1])
        with c1:
            if st.button("⟲ Reset"):
                _reset_round(ss.mm_target)
                st.rerun()
        with c2:
            if ss.mm_total == ss.mm_target:
                if st.button("Next round ▶"):
                    gained = 10
                    # avoid double insert when autosave
                    if not ss.mm_saved:
                        _persist_success(gained)
                        _award_xp(gained)
                    _reset_round()
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        # Money Collection
        st.markdown("<h4>Money Collection</h4>", unsafe_allow_html=True)
        grid_cols = st.columns(4)
        for i, (label, value, img) in enumerate(DENOMS):
            with grid_cols[i % 4]:
                _safe_image(img, caption=label)
                if st.button(label, key=f"mm_add_{value}"):
                    ss.mm_selected.append(value)
                    ss.mm_total += value
                    st.rerun()

    with right:
        st.markdown(
            f"""
            <div class="mm-side-card">
                <h4>🏆 Stats</h4>
                <div class="mm-metric"><span>Current Level</span><b>{ss.mm_level}</b></div>
                <div class="mm-metric"><span>Total XP</span><b>{ss.mm_xp}</b></div>
                <div class="mm-metric"><span>Matches Made</span><b>{ss.mm_matches}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            """
            <div class="mm-side-card">
                <h4>How to Play</h4>
                <ol class="mm-howto">
                    <li>Look at the target amount</li>
                    <li>Click coins and notes to add them</li>
                    <li>Match the target exactly to earn XP</li>
                    <li>Level up with each successful match</li>
                </ol>
            </div>
            """,
            unsafe_allow_html=True,
        )
