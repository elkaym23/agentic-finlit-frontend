# phase\Student_view\games\debtdilemma.py
import streamlit as st
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Literal
import random
import math
import os
from utils import db as dbapi


def load_css(file_name: str):
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ Stylesheet not found. Please ensure 'assets/styles.css' exists.")


DD_SCOPE_CLASS = "dd-scope"  

def _ensure_dd_css():
    """Inject CSS for Debt Dilemma buttons once, scoped under .dd-scope."""
    
    if st.session_state.get("_dd_css_injected"):
        return
    st.session_state["_dd_css_injected"] = True

   
    st.markdown("""
    <style>
      .dd-scope .stButton > button {
        border: none;
        border-radius: 25px;
        padding: 0.75rem 1.5rem;
        font-weight: 700;
        box-shadow: 0 4px 15px rgba(0,0,0,.2);
        transition: all .3s ease;
      }
      .dd-scope .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,.3);
      }
      .dd-scope .dd-success .stButton > button {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        color: #fff;
      }
      .dd-scope .dd-warning .stButton > button {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        color: #000;
      }
      .dd-scope .dd-danger .stButton > button {
        background: linear-gradient(135deg, #ff6b6b 0%, #ffa500 100%);
        color: #000;
      }
      .dd-scope .dd-neutral .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: #fff;
      }
    </style>
    """, unsafe_allow_html=True)

def buttondd(label: str, *, key: str, variant: str = "neutral", **kwargs) -> bool:
    """
     Scoped button wrapper. Use just like st.button but styles are limited to the Debt Dilemma container.

    Example:
      buttondd("Pay", key="btn_pay", variant="success", on_click=fn, use_container_width=True)
    """
    _ensure_dd_css()
   
    st.markdown(f'<div class="dd-{variant}">', unsafe_allow_html=True)
    clicked = st.button(label, key=key, **kwargs)
    st.markdown('</div>', unsafe_allow_html=True)
    return clicked


setattr(st, "buttondd", buttondd)


# ==== Currency & economy tuning ====
CURRENCY = "JMD$"
MONEY_SCALE = 1000  # 1 "game dollar" = 1,000 JMD

def jmd(x: int | float) -> int:
    """Scale a base unit to JMD integer."""
    return int(round(x * MONEY_SCALE))

def fmt_money(x: int | float) -> str:
    """Format with thousands separator and currency."""
    #  round instead of floor so UI doesn't show 0 while a tiny positive remains
    return f"{CURRENCY}{int(round(x)):,}"

def clamp_money(x: float) -> int:
    """Round to nearest JMD and never go negative."""
    #  helper to normalize all balances to integer JMD
    return max(0, int(round(x)))

# Fees (scaled)
LATE_FEE_BASE = jmd(10)   # ~JMD$10,000
LATE_FEE_PER_MISS = jmd(5)  # +JMD$5,000 per missed
EMERGENCY_FEE = jmd(25)   # ~JMD$25,000
SMALL_PROC_FEE = jmd(2)   # ~JMD$2,000 for event shortfalls

# ==== Starting wallet config ====
START_WALLET_MIN = 0
START_WALLET_MAX = jmd(10)  # JMD $0–10,000
DISBURSE_LOAN_TO_WALLET = False  # keep loan off-wallet by default (e.g., pays tuition)

# --- Credit-score tuning ---
CS_EVENT_DECLINE_MIN = 15   # min points to deduct when you skip an expense event
CS_EVENT_DECLINE_MAX = 100  # max points
CS_EVENT_DECLINE_PER_K = 5  # ~5 pts per JMD$1,000 of expense you duck
CS_EMERGENCY_EVENT_HIT = 60 # when an event forces an emergency loan

# --- Utilities month-end penalties ---
UTILITY_NONPAY_CS_HIT = 25
UTILITY_NONPAY_HAPPY_HIT = 8
UTILITY_RECONNECT_FEE = jmd(2)  # ~JMD$2,000 added to debt

# ===============================
# Types
# ===============================
@dataclass
class LoanDetails:
    principal: int
    interestRate: float
    monthlyPayment: int
    totalOwed: float
    monthsPaid: int
    totalMonths: int
    missedPayments: int
    creditScore: int

@dataclass
class RandomEvent:
    id: str
    title: str
    description: str
    icon: str
    type: Literal['opportunity','expense','penalty','bonus']
    impact: Dict[str, int] = field(default_factory=dict)
    choices: Optional[Dict[str,str]] = None

@dataclass
class GameLevel:
    level: int
    name: str
    loanAmount: int
    interestRate: float
    monthlyPayment: int
    totalMonths: int
    startingIncome: int
    description: str

# ===============================
# Data (shorter game: 3 levels)
# ===============================
GAME_LEVELS: List[GameLevel] = [
    GameLevel(1, "🎓 Student Loan", jmd(100), 0.15, jmd(25), 3, jmd(120), "Your first small loan as a student - let's learn together! 📚"),
    GameLevel(2, "🚗 Car Loan", jmd(250), 0.18, jmd(50), 3, jmd(140), "Buying your first car - bigger responsibility but you've got this! 🌟"),
    GameLevel(3, "💳 Credit Card Debt", jmd(400), 0.22, jmd(70), 3, jmd(160), "High-interest credit card debt - time to be extra careful! ⚠️"),
]

# Replaced 'Clothes' with 'Snacks' and added happiness boosts
EXPENSES = [
    {"id": "food", "name": "Food", "amount": jmd(0.9), "required": True, "healthImpact": -15, "emoji": "🍎"},       # ~JMD$900 per day
    {"id": "transport", "name": "Transport", "amount": jmd(0.5), "required": True, "healthImpact": 0, "emoji": "🚌"}, # ~JMD$500
    {"id": "utilities", "name": "Utilities", "amount": jmd(7), "required": True, "healthImpact": -5, "emoji": "💡"},  # ~JMD$7,000/mo
    {"id": "entertainment","name": "Entertainment","amount": jmd(1.5), "required": False, "healthImpact": 0, "happinessBoost": 5, "emoji": "🎮"},
    {"id": "snacks", "name": "Snacks", "amount": jmd(0.8), "required": False, "healthImpact": 0, "happinessBoost": 5, "emoji": "🍿"},
]

LEVEL_EVENT_POOL = {
    1: [  # Student Loan level
        RandomEvent("games_day", "🏟️ School Games Day", "Your school is holding Games Day. Small fee, but huge fun and morale!", "🏟️", "expense",
                    {"wallet": -jmd(2), "happiness": 5}, {"accept": f"Join ({fmt_money(jmd(2))}, +5% happy)", "decline": "Skip"}),
        RandomEvent("book_fair", "📚 Book Fair", "Discounted textbooks help your grades (and future pay!).", "📚", "opportunity",
                    {"wallet": -jmd(3), "income": jmd(1), "happiness": 3}, {"accept": "Buy books", "decline": "Pass"}),
        RandomEvent("tuition_deadline", "🎓 Tuition Deadline", "A small admin fee pops up unexpectedly.", "🎓", "expense",
                    {"wallet": -jmd(3.5)}, {"accept": "Pay fee", "decline": "Appeal"}),
    ],
    2: [  # Car Loan level
        RandomEvent("gas_hike", "⛽ Gas Price Hike", "Fuel costs rise this week.", "⛽", "expense",
                    {"wallet": -jmd(2.5)}, {"accept": "Buy gas", "decline": "Drive less"}),
        RandomEvent("oil_change", "🛠️ Discount Oil Change", "Maintenance now saves larger repair later.", "🛠️", "opportunity",
                    {"wallet": -jmd(3), "creditScore": 5}),
    ],
    3: [  # Credit Card level
        RandomEvent("flash_sale", "🛍️ Flash Sale Temptation", "Limited-time sale! Tempting but watch your debt.", "🛍️", "penalty",
                    {"debt": jmd(4), "happiness": 4}, {"accept": "Buy (+debt)", "decline": "Resist"}),
        RandomEvent("cashback", "💳 Cashback Bonus", "Your card offers a cashback promo.", "💳", "bonus",
                    {"wallet": jmd(3)}),
    ],
}

EVENT_POOL: List[RandomEvent] = [
    # Money-earning opportunities
    RandomEvent("yard_sale", "🧹 Yard Sale Fun!", "You sell old items and make some quick cash! Great job being resourceful! 🌟", "🧹", "opportunity", {"wallet": jmd(6)}),
    RandomEvent("tutoring", "📚 Tutoring Helper", "You help someone with homework and get paid! Sharing knowledge feels great! 😊", "📚", "opportunity", {"wallet": jmd(5)}),
    RandomEvent("odd_jobs", "🧰 Weekend Helper", "You mow lawns and wash a car over the weekend! Hard work pays off! 💪", "🧰", "opportunity", {"wallet": jmd(7)}),

    # Bonuses / grants
    RandomEvent("overtime_work", "💼 Extra Work Time", "Your boss offers you overtime this period. Extra money but you'll be tired! 😴", "💼", "opportunity",
                {"wallet": jmd(8)}, {"accept": f"Work overtime (+{fmt_money(jmd(8))}) 💪", "decline": "Rest instead 😴"}),
    RandomEvent("freelance_job", "💻 Weekend Project", "A friend asks you to help with their business for some quick cash! 🤝", "💻", "opportunity",
                {"wallet": jmd(6)}, {"accept": f"Take the job (+{fmt_money(jmd(6))}) 💼", "decline": "Enjoy your weekend 🌈"}),
    RandomEvent("bonus_payment", "⭐ Amazing Work!", "Your excellent work this period earned you a bonus! You're doing great! 🎉", "⭐", "bonus", {"wallet": jmd(5), "creditScore": 10}),
    RandomEvent("scholarship_opportunity", "🎓 Learning Reward", "You qualify for a small educational grant! Knowledge pays off! 📖", "🎓", "bonus", {"wallet": jmd(10), "income": jmd(2)}),

    # Health & happiness helpers
    RandomEvent("mental_health", "🧠 Feeling Better", "A free counseling session can help you feel better and happier! 🌈", "🧠", "opportunity",
                {"wallet": 0, "health": 10, "happiness": 10}, {"accept": "Feel better! 😊", "decline": "Maybe later 🤔"}),
    RandomEvent("health_checkup", "🏥 Health Check", "Local clinic does a free health checkup! Taking care of yourself is important! 💚", "🏥", "opportunity",
                {"wallet": 0, "health": 10, "happiness": 5}, {"accept": "Get healthy! 💪", "decline": "Skip it 🤷"}),

    # Expenses / penalties
    RandomEvent("landlord_eviction", "🏠 Moving Costs", "You need a small deposit for a new place soon. Moving can be expensive! 📦", "🏠", "expense",
                {"wallet": -jmd(9)}, {"accept": f"Pay deposit (-{fmt_money(jmd(9))}) 🏠", "decline": "Try to negotiate 🤝"}),
    RandomEvent("transport_breakdown", "🚫 Transport Trouble", "Your usual transport is down. You need an alternative way to get around! 🚶", "🚫", "expense",
                {"wallet": -jmd(3)}, {"accept": f"Pay for ride (-{fmt_money(jmd(3))}) 🚗", "decline": "Walk everywhere 🚶"}),
    RandomEvent("utilities_shutoff", "⚡ Utility Warning", "Utilities will be shut off if not paid soon! Don't let the lights go out! 💡", "⚡", "expense",
                {"wallet": -jmd(4)}, {"accept": f"Pay now (-{fmt_money(jmd(4))}) 💡", "decline": "Risk it 😬"}),
]

# ===============================
# Helpers
# ===============================
def get_level(level:int) -> GameLevel:
    return GAME_LEVELS[level-1]

def required_expenses_total() -> int:
    return sum(e["amount"] for e in EXPENSES if e["required"])

def progress_percent(total_owed: float, monthly_payment: int, total_months: int) -> float:
    pct = ((total_months - (total_owed / max(monthly_payment,1))) / total_months) * 100
    return max(0.0, min(100.0, pct))

def payoff_projection(balance: float, apr: float, monthly_payment: int):
    """
    Simulate payoff using the game's timing:
    - Player pays during the month (before interest).
    - At month end, interest accrues on the remaining balance and is added.
    Returns (months_needed, total_interest_paid). If payment <= interest, returns (None, None).
    """
    r = apr / 12.0
    if balance <= 0:
        return 0, 0
    if r <= 0:
        months = math.ceil(balance / max(1, monthly_payment))
        return months, 0
    if monthly_payment <= balance * r:
        return None, None
    months = 0
    total_interest = 0.0
    b = float(balance)
    for _ in range(10000):  # safety cap
        pay = min(monthly_payment, b)
        b -= pay
        months += 1
        if b <= 1e-6:
            break
        interest = b * r
        b += interest
        total_interest += interest
        if monthly_payment <= b * r - 1e-9:
            return None, None
    return months, int(round(total_interest))


def _award_level_completion_if_needed():
    """Give exactly +50 XP once per completed level, including the last level."""
    user = st.session_state.get("user")
    if not user:
        return
    lvl = int(st.session_state.currentLevel)
    key = f"_dd_xp_awarded_L{lvl}"
    if st.session_state.get(key):
        return  # already awarded for this level

    try:
        dbapi.record_debt_dilemma_round(
            user["user_id"],
            level=lvl,
            round_no=0,
            wallet=int(st.session_state.wallet),
            health=int(st.session_state.health),
            happiness=int(st.session_state.happiness),
            credit_score=int(st.session_state.loan.creditScore),
            event_json={"phase": st.session_state.gamePhase},
            outcome="level_complete" if st.session_state.gamePhase == "level-complete" else "game_complete",
            gained_xp=50
        )
        st.session_state[key] = True
        st.success("Saved +50 XP for completing this loan")
    except Exception as e:
        st.error(f"Could not save completion XP: {e}")


def check_loan_completion() -> bool:
    """Advance level or finish game when loan is cleared. Returns True if game phase changed."""
    loan = st.session_state.loan
    #  use integerized check; tiny float dust won't block completion
    if clamp_money(loan.totalOwed) == 0:
        if st.session_state.currentLevel < len(GAME_LEVELS):
            st.session_state.gamePhase = "level-complete"
            st.toast(f"Level {st.session_state.currentLevel} complete! Ready for next?")
        else:
            st.session_state.gamePhase = "completed"
            st.toast("All levels done! 🎉")
        return True
    return False

def init_state():
    if "gamePhase" not in st.session_state:
        st.session_state.update({
            "gamePhase": "setup",
            "currentMonth": 1,
            "currentDay": 1,
            "daysInMonth": 28,
            "roundsLeft": 6,
            "wallet": random.randint(START_WALLET_MIN, START_WALLET_MAX),
            "monthlyIncome": GAME_LEVELS[0].startingIncome,
            "health": 100,
            "happiness": 100,
            "monthsWithoutFood": 0,
            "currentEvent": None,
            "eventHistory": [],
            "difficultyMultiplier": 1.0,
            "currentLevel": 1,
            "paidExpenses": [],
            "hasWorkedThisMonth": False,
            "achievements": [],
            "lastWorkPeriod": 0,
            "amountPaidThisMonth": 0,
            "fullPaymentMadeThisMonth": False,
            "paidFoodToday": False,
        })
        lvl = get_level(1)
        st.session_state["loan"] = LoanDetails(
            principal=lvl.loanAmount,
            interestRate=lvl.interestRate,
            monthlyPayment=lvl.monthlyPayment,
            totalOwed=float(lvl.loanAmount),
            monthsPaid=0,
            totalMonths=lvl.totalMonths,
            missedPayments=0,
            creditScore=random.randint(200, 600),
        )

# Fortnight helper (every 2 weeks)
def current_fortnight() -> int:
    return 1 + (st.session_state.currentDay - 1) // 14

# ===== End checks =====
def check_end_conditions() -> bool:
    if st.session_state.health <= 0:
        st.session_state.health = 0
        st.session_state.gamePhase = "hospital"
        st.toast("You've been hospitalized! Health reached 0%. Game Over.")
        return True
    if st.session_state.happiness <= 0:
        st.session_state.happiness = 0
        st.session_state.gamePhase = "burnout"
        st.toast("Happiness reached 0%. You gave up. Game Over.")
        return True
    return False

# ===== Day advancement =====
def advance_day(no_event: bool = False):
    """Advance one day. If no_event=True, skip daily event roll (use when an action already consumed the day)."""
    if st.session_state.gamePhase == "repaying":
        if not st.session_state.paidFoodToday:
            st.session_state.health = max(0, st.session_state.health - 5)
            st.toast("You skipped food today. Health -5%")
        st.session_state.paidFoodToday = False

    if not no_event and st.session_state.gamePhase == "repaying" and st.session_state.currentEvent is None:
        new_evt = gen_random_event()
        if new_evt:
            st.session_state.currentEvent = new_evt
            st.toast(f"New event: {new_evt.title}")
            return

    if check_end_conditions():
        return

    st.session_state.currentDay += 1
    if st.session_state.currentDay > st.session_state.daysInMonth:
        st.session_state.currentDay = 1
        next_month()
    else:
        st.toast(f"Day {st.session_state.currentDay}/{st.session_state.daysInMonth}")

def fast_forward_to_month_end():
    st.toast("Skipping to month end…")
    st.session_state.currentDay = st.session_state.daysInMonth
    next_month()

# ===============================
# Random events
# ===============================
def set_event(evt: Optional[RandomEvent]):
    st.session_state["currentEvent"] = evt

def gen_random_event() -> Optional[RandomEvent]:
    currentMonth = st.session_state.currentMonth
    difficulty = st.session_state.difficultyMultiplier
    base = 0.08
    eventChance = min(base + (currentMonth * 0.03) + (difficulty * 0.02), 0.4)
    if random.random() < eventChance:
        seen = set(st.session_state.eventHistory)
        level_specific = LEVEL_EVENT_POOL.get(st.session_state.currentLevel, [])
        pool = EVENT_POOL + level_specific
        available = [e for e in pool if (e.id not in seen) or (e.type in ("opportunity","bonus"))]
        if available:
            return random.choice(available)
    return None

# ===============================
# Game actions
# ===============================
def start_loan():
    st.session_state.gamePhase = "repaying"
    if DISBURSE_LOAN_TO_WALLET:
        st.session_state.wallet += st.session_state.loan.principal
        st.toast(f"Loan approved! {fmt_money(st.session_state.loan.principal)} added to your wallet.")
    else:
        st.toast("Loan approved! Funds go directly to fees (not your wallet).")

def do_skip_payment():
    loan: LoanDetails = st.session_state.loan
    loan.missedPayments += 1
    loan.creditScore = max(300, loan.creditScore - 50)
    st.toast("Payment missed! Credit score -50.")
    advance_day(no_event=False)

def can_work_this_period() -> bool:
    return st.session_state.lastWorkPeriod != current_fortnight()

WORK_HAPPINESS_COST = 10
WORK_MIN = jmd(6)  # ~JMD$6,000
WORK_VAR = jmd(3)  # up to +JMD$3,000

def do_work_for_money():
    if not can_work_this_period():
        st.toast("You already worked this fortnight. Try later.")
        return
    earnings = WORK_MIN + random.randint(0, WORK_VAR)
    st.session_state.wallet += earnings
    st.session_state.happiness = max(0, st.session_state.happiness - WORK_HAPPINESS_COST)
    st.session_state.hasWorkedThisMonth = True
    st.session_state.lastWorkPeriod = current_fortnight()
    st.toast(f"Work done! +{fmt_money(earnings)}, Happiness -{WORK_HAPPINESS_COST} (uses 1 day)")
    if st.session_state.happiness <= 30 and "workaholic" not in st.session_state.achievements:
        st.session_state.achievements.append("workaholic")
        st.toast("Achievement: Workaholic - Worked while happiness was low!")
    if not check_end_conditions():
        advance_day(no_event=True)

def do_make_payment_full():
    make_payment(st.session_state.loan.monthlyPayment)

def do_make_payment_partial():
    #  use ceil so a tiny remainder (e.g., 0.4 JMD) can be fully cleared
    leftover = math.ceil(st.session_state.loan.totalOwed)
    pay_what = max(0, min(st.session_state.wallet - required_expenses_total(), leftover))
    make_payment(pay_what)

def make_payment(amount: int):
    loan: LoanDetails = st.session_state.loan
    required_total = required_expenses_total()
    if amount <= 0:
        st.toast("Enter a valid payment amount.")
        return
    if st.session_state.wallet >= amount and st.session_state.wallet - amount >= required_total:
        st.session_state.wallet -= amount
        #  clamp debt after payment to eliminate float dust
        loan.totalOwed = clamp_money(loan.totalOwed - amount)
        st.session_state.amountPaidThisMonth += amount
        if amount >= loan.monthlyPayment:
            loan.monthsPaid += 1
            st.session_state.fullPaymentMadeThisMonth = True
            st.toast(f"Payment successful! {fmt_money(amount)} paid.")
        else:
            still = max(0, loan.monthlyPayment - amount)
            st.toast(f"Partial payment {fmt_money(amount)}. Need {fmt_money(still)} more for full.")
        #  rely on integerized zero check
        if check_loan_completion():
            return
        if st.session_state.gamePhase == "repaying":
            advance_day(no_event=True)
    else:
        st.toast("Not enough money (remember mandatory expenses).")

# Paying expenses is free; Food heals
def pay_expense(expense: Dict):
    if st.session_state.wallet >= expense["amount"]:
        st.session_state.wallet -= expense["amount"]
        if expense["id"] not in st.session_state.paidExpenses:
            st.session_state.paidExpenses.append(expense["id"])
        st.toast(f"Paid {fmt_money(expense['amount'])} for {expense['name']}")
        boost = int(expense.get("happinessBoost", 0))
        if boost:
            before = st.session_state.happiness
            st.session_state.happiness = min(100, st.session_state.happiness + boost)
            st.toast(f"Happiness +{st.session_state.happiness - before}%")
        if expense["id"] == "food":
            st.session_state.paidFoodToday = True
            before_h = st.session_state.health
            st.session_state.health = min(100, st.session_state.health + 10)
            healed = st.session_state.health - before_h
            if healed > 0:
                st.toast(f"Health +{healed}% from eating well")
        if expense["id"] == "utilities":
            before = st.session_state.happiness
            st.session_state.happiness = max(0, st.session_state.happiness - 3)
            st.toast(f"Happiness -{before - st.session_state.happiness}% (paid utilities)")
        check_end_conditions()
    else:
        st.toast(f"Can't afford {expense['name']}! It will be auto-deducted at month end.")

# Resolving events: consumes 1 day
def handle_event_choice(accept: bool):
    evt: Optional[RandomEvent] = st.session_state.currentEvent
    if not evt:
        return
    loan: LoanDetails = st.session_state.loan

    if accept and evt.impact:
        if "wallet" in evt.impact:
            delta = evt.impact["wallet"]
            if delta < 0 and st.session_state.wallet < abs(delta):
                st.toast("You can't afford this! Emergency loan taken.")
                short = abs(delta) + SMALL_PROC_FEE
                st.session_state.wallet = 0
                #  clamp after adding emergency shortfall
                loan.totalOwed = clamp_money(loan.totalOwed + short)
                loan.creditScore = max(300,loan.creditScore - CS_EMERGENCY_EVENT_HIT)
                st.toast(f"Added to debt: {fmt_money(short)}")
            else:
                st.session_state.wallet += delta
                st.toast(f"{'+' if delta>0 else ''}{fmt_money(delta)} {'earned' if delta>0 else 'spent'}.")
        if "income" in evt.impact:
            st.session_state.monthlyIncome = max(jmd(0.05), st.session_state.monthlyIncome + evt.impact["income"])
        if "creditScore" in evt.impact:
            loan.creditScore = max(300, min(850, loan.creditScore + evt.impact["creditScore"]))
        if "debt" in evt.impact:
            #  clamp after debt increase from event
            loan.totalOwed = clamp_money(loan.totalOwed + evt.impact["debt"])
        if "health" in evt.impact:
            st.session_state.health = min(100, max(0, st.session_state.health + evt.impact["health"]))
        if "happiness" in evt.impact:
            st.session_state.happiness = min(100, max(0, st.session_state.happiness + evt.impact["happiness"]))
    elif not accept:
        if evt.type == "expense":
            st.toast("You avoided the expense but there might be consequences…")
            if random.random() < 0.5 and "wallet" in evt.impact:
                base_k = abs(evt.impact["wallet"]) / MONEY_SCALE  # convert JMD → 'thousands'
                penalty = int(round(base_k * CS_EVENT_DECLINE_PER_K))
                penalty = max(CS_EVENT_DECLINE_MIN, min(CS_EVENT_DECLINE_MAX, penalty))
                loan.creditScore = max(300, loan.creditScore - penalty)
                st.toast(f"Credit score penalty: -{penalty}")
        else:
            st.toast("You declined the opportunity.")

    st.session_state.eventHistory.append(evt.id)
    st.session_state.difficultyMultiplier += 0.1
    st.session_state.currentEvent = None
    if not check_end_conditions():
        advance_day(no_event=True)

# ===============================
# Month processing
# ===============================
def check_achievements():
    if st.session_state.health == 100 and "perfect-health" not in st.session_state.achievements:
        st.session_state.achievements.append("perfect-health")
        st.toast("Achievement: Perfect Health!")
    if st.session_state.health <= 20 and "survivor" not in st.session_state.achievements:
        st.session_state.achievements.append("survivor")
        st.toast("Achievement: Survivor!")
    if st.session_state.happiness >= 90 and "happy-camper" not in st.session_state.achievements:
        st.session_state.achievements.append("happy-camper")
        st.toast("Achievement: Happy Camper!")
    if st.session_state.wallet <= jmd(0.01) and st.session_state.happiness >= 50 and "broke-not-broken" not in st.session_state.achievements:
        st.session_state.achievements.append("broke-not-broken")
        st.toast("Achievement: Broke But Not Broken!")
    if st.session_state.loan.creditScore >= 800 and "credit-master" not in st.session_state.achievements:
        st.session_state.achievements.append("credit-master")
        st.toast("Achievement: Credit Master!")

def next_month():
    loan: LoanDetails = st.session_state.loan
    st.session_state.lastWorkPeriod = 0

    if st.session_state.gamePhase == "repaying":
        if not st.session_state.fullPaymentMadeThisMonth:
            loan.missedPayments += 1
            st.toast("You missed this month’s full payment.")
        st.session_state.amountPaidThisMonth = 0
        st.session_state.fullPaymentMadeThisMonth = False

        unpaid = [e for e in EXPENSES if e["required"] and e["id"] not in st.session_state.paidExpenses]
        total_forced = sum(e["amount"] for e in unpaid)
        total_health_loss = sum(abs(e.get("healthImpact", 0)) for e in unpaid)

        if total_forced > 0:
            if st.session_state.wallet >= total_forced:
                st.session_state.wallet -= total_forced
                st.session_state.health = max(0, st.session_state.health - total_health_loss)
                st.toast(f"Mandatory expenses auto-deducted: {fmt_money(total_forced)}, Health -{total_health_loss}")
            else:
                shortfall = total_forced - st.session_state.wallet
                st.session_state.wallet = 0
                st.session_state.health = max(0, st.session_state.health - total_health_loss - 10)
                #  clamp after emergency shortfall + fee
                loan.totalOwed = clamp_money(loan.totalOwed + shortfall + EMERGENCY_FEE)
                loan.creditScore = max(300, loan.creditScore - 35)
                st.toast(f"Couldn't afford mandatory expenses! Emergency loan: {fmt_money(shortfall + EMERGENCY_FEE)}, Health -{total_health_loss + 10}")

        if st.session_state.currentLevel >= 3 and st.session_state.wallet < st.session_state.monthlyIncome * 0.5:
            loss = int(((st.session_state.monthlyIncome * 0.5) - st.session_state.wallet) / jmd(1))
            if loss > 0:
                st.session_state.happiness = max(0, st.session_state.happiness - loss)
                st.toast(f"Low funds affecting mood! Happiness -{loss}")

        st.session_state.currentMonth += 1
        st.session_state.currentDay = 1
        st.session_state.roundsLeft -= 1
        st.session_state.wallet += st.session_state.monthlyIncome
        st.session_state.paidExpenses = []
        st.session_state.hasWorkedThisMonth = False

        if st.session_state.roundsLeft <= 0:
            st.toast("Time's up! You ran out of rounds!")
            st.session_state.gamePhase = "completed"
            return

        if loan.missedPayments > 0:
            late_fee = LATE_FEE_BASE + (loan.missedPayments * LATE_FEE_PER_MISS)
            #  clamp after applying late fees
            loan.totalOwed = clamp_money(loan.totalOwed + late_fee)
            st.toast(f"Late fee applied: {fmt_money(late_fee)}")
            loan.missedPayments = 0

        # Extra month-end consequences if Utilities weren't paid
        unpaid_ids = {e["id"] for e in unpaid}
        if "utilities" in unpaid_ids:
            # Credit score & happiness hit + reconnection fee
            loan.creditScore = max(300, loan.creditScore - UTILITY_NONPAY_CS_HIT)
            st.session_state.happiness = max(0, st.session_state.happiness - UTILITY_NONPAY_HAPPY_HIT)
            #  clamp after reconnect fee
            loan.totalOwed = clamp_money(loan.totalOwed + UTILITY_RECONNECT_FEE)
            st.toast(
                f"Utilities unpaid: Credit -{UTILITY_NONPAY_CS_HIT}, "
                f"Happiness -{UTILITY_NONPAY_HAPPY_HIT}, "
                f"Reconnect fee {fmt_money(UTILITY_RECONNECT_FEE)}"
            )

        check_achievements()

        if st.session_state.gamePhase == "repaying":
            #  integerize monthly interest and clamp new total
            monthly_interest = clamp_money((loan.totalOwed * loan.interestRate) / 12.0)
            loan.totalOwed = clamp_money(loan.totalOwed + monthly_interest)
            #  ensure completion triggers even after month-end math
            check_loan_completion()

        st.toast(f"Month {st.session_state.currentMonth}: +{fmt_money(st.session_state.monthlyIncome)} income. {st.session_state.roundsLeft} rounds left.")
        check_end_conditions()

# ===============================
# UI
# ===============================
def header():
    level = get_level(st.session_state.currentLevel)
    base_payday_hint = "Paid at month end"
    st.markdown(f"""
      <div class="game-header">
        <div class="game-title">🎮 Debt Dilemma 💳</div>
        <h3>Month {st.session_state.currentMonth} · Day {st.session_state.currentDay}/{st.session_state.daysInMonth}</h3>
        <p>Level {st.session_state.currentLevel}: {level.name}</p>
      </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
      <div class="metric-card">
        <h3>📊 Your Status</h3>
        <div style="display:flex;flex-wrap:wrap;gap:1rem;justify-content:space-between;margin-top:1rem;">
          <div><strong>💰 Wallet:</strong> {fmt_money(st.session_state.wallet)}</div>
          <div><strong>💼 Base Salary:</strong> {fmt_money(st.session_state.monthlyIncome)} <small>({base_payday_hint})</small></div>
          <div><strong>📊 Credit:</strong> {st.session_state.loan.creditScore}</div>
          <div><strong>❤️ Health:</strong> {st.session_state.health}%</div>
          <div><strong>😊 Happy:</strong> {st.session_state.happiness}%</div>
        </div>
        <div style="margin-top:.5rem;">
          <small>💡 “Work for Money” is extra: once per fortnight you can earn ~JMD$6k–9k for 1 day, and it lowers happiness by 10%.</small>
        </div>
      </div>
    """, unsafe_allow_html=True)

def setup_screen():
    level = get_level(st.session_state.currentLevel)

    # --- Header ---
    st.markdown(f"""
      <div class="game-header">
        <div class="game-title">🎯 Level {level.level}: {level.name}</div>
        <p>{level.description}</p>
      </div>
    """, unsafe_allow_html=True)

    # --- Loan Info ---
    months_est, interest_est = payoff_projection(
        balance=float(level.loanAmount),
        apr=level.interestRate,
        monthly_payment=level.monthlyPayment
    )
    if months_est is None:
        proj_html = "<small>🧮 Projection: Payment too low — balance will grow.</small>"
    else:
        years_est = months_est / 12.0
        proj_html = (f"<small>🧮 Projection: ~{months_est} payments (~{years_est:.1f} years), "
                     f"est. interest {fmt_money(interest_est)}</small>")

    st.markdown("### 📋 Loan Details")
    st.markdown(f"""
      <div class="metric-card">
        <h3>💳 Loan Information</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem;">
          <div><strong>💰 Amount:</strong> {fmt_money(level.loanAmount)}</div>
          <div><strong>📈 Interest:</strong> {int(level.interestRate*100)}% yearly</div>
          <div><strong>💳 Monthly Payment:</strong> {fmt_money(level.monthlyPayment)}</div>
          <div><strong>⏰ Time Limit (target):</strong> {level.totalMonths} months</div>
        </div>
        <div style="margin-top:.5rem;">{proj_html}</div>
      </div>
    """, unsafe_allow_html=True)

    # --- Player situation ---
    st.markdown("### 🌟 Your Current Situation")
    st.markdown(f"""
      <div class="metric-card">
        <h3>💼 Your Financial Status</h3>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-top:1rem;">
          <div><strong>💰 Wallet (random start):</strong> {fmt_money(st.session_state.wallet)}</div>
          <div><strong>💼 Base Salary (month end):</strong> {fmt_money(st.session_state.monthlyIncome)}</div>
          <div><strong>🏠 Required Expenses (per month):</strong> {fmt_money(required_expenses_total())}</div>
          <div><strong>📊 Credit Score:</strong> {st.session_state.loan.creditScore}</div>
        </div>
        <div style="margin-top:.5rem;">
          <small>💡 You get your <strong>base salary automatically at month end</strong>. The <em>Work for Money</em> button gives <strong>extra</strong> cash (~JMD$6k–9k) and can be used <strong>once per fortnight</strong> (costs 1 day, -10% happiness).</small>
        </div>
      </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    ### 🎮 Game Rules - Let's Learn Together!
    🎯 **Your Mission:** Pay off your loan while staying healthy and happy!

    📚 **Important Rules:**
    - 💰 Interest grows your debt each month - pay on time!
    - ❤️ Health 0% = hospital visit (game over!)
    - 😊 Happiness 0% = you give up (game over!)
    - 🍎 Food keeps you healthy (+10 health when paid!)
    - 🎮 Entertainment & 🍿 Snacks make you happy (+5% each!)
    - 🎲 Random events happen daily - some good, some challenging!

    ⏰ **Time Costs:**
    - 💼 Work (extra) = 1 day (**once per fortnight**)
    - 💳 Make loan payment = 1 day
    - 🎲 Handle events = 1 day
    - 🏠 Paying expenses = FREE (no time cost!)

    💡 **Payday:** Your **base salary** hits your wallet automatically at **month end**.
    """)

    #  use st.buttondd (scoped) instead of st.button
    st.buttondd(
        f"🚀 Accept Level {level.level} Loan & {'Receive ' + fmt_money(level.loanAmount) if DISBURSE_LOAN_TO_WALLET else 'Start the Level'}!",
        use_container_width=True,
        on_click=start_loan,
        key="btn_start_loan",
        variant="success"
    )

def main_screen():
    header()

    left, right = st.columns([2,1])

    with left:
        evt: Optional[RandomEvent] = st.session_state.currentEvent
        if evt:
            st.markdown(f"""
              <div class="event-card">
                <div class="event-title">{evt.icon} {evt.title}</div>
                <p>{evt.description}</p>
              </div>
            """, unsafe_allow_html=True)

            badge_colors = {
                "opportunity": "🌟 GREAT OPPORTUNITY!",
                "expense": "⚠️ EXPENSE ALERT",
                "penalty": "⛔ CHALLENGE",
                "bonus": "🎁 AWESOME BONUS!"
            }
            st.success(badge_colors[evt.type])

            c1, c2 = st.columns(2)
            if evt.choices:
                with c1:
                    st.buttondd(evt.choices["accept"], use_container_width=True, on_click=lambda: handle_event_choice(True), key="evt_accept", variant="success")
                with c2:
                    st.buttondd(evt.choices["decline"], use_container_width=True, on_click=lambda: handle_event_choice(False), key="evt_decline", variant="warning")
            else:
                st.buttondd("✨ Continue (uses 1 day)", use_container_width=True, on_click=lambda: handle_event_choice(True), key="evt_continue", variant="success")

            st.markdown("---")

        # --- Loan status + payoff projection ---
        progress = progress_percent(st.session_state.loan.totalOwed, st.session_state.loan.monthlyPayment, st.session_state.loan.totalMonths)/100
        months_est, interest_est = payoff_projection(
            st.session_state.loan.totalOwed,
            st.session_state.loan.interestRate,
            st.session_state.loan.monthlyPayment
        )
        if months_est is None:
            proj_html = "<div><strong>🧮 Projection:</strong> Payment too low — balance will grow.</div>"
        else:
            years_est = months_est / 12.0
            proj_html = (
                f"<div><strong>🧮 Projection:</strong> ~{months_est} payments "
                f"(~{years_est:.1f} years), est. interest {fmt_money(interest_est)}</div>"
            )

        st.markdown(f"""
          <div class="metric-card">
            <h3>💳 Loan Status</h3>
            <div style="margin-top: 1rem;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                <div><strong>💰 Still Owed:</strong> {fmt_money(st.session_state.loan.totalOwed)}</div>
                <div><strong>💳 Monthly Due:</strong> {fmt_money(st.session_state.loan.monthlyPayment)}</div>
              </div>
              {proj_html}
              <div style="margin: 1rem 0;">
                <div style="background: #e0e0e0; border-radius: 10px; height: 20px; overflow: hidden;">
                  <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); height: 100%; width: {progress*100}%; border-radius: 10px;"></div>
                </div>
                <div style="text-align: center; margin-top: 0.5rem;"><strong>🎯 Progress: {progress*100:.1f}% Complete!</strong></div>
              </div>
              <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: .5rem;">
                <div><strong>✅ Payments:</strong> {st.session_state.loan.monthsPaid}/{st.session_state.loan.totalMonths}</div>
                <div><strong>{"⚠️" if st.session_state.loan.missedPayments > 0 else "✅"} Missed:</strong> {st.session_state.loan.missedPayments}</div>
                <div><small>{(st.session_state.loan.interestRate*100/12):.1f}% monthly interest</small></div>
                <div><small>📅 Paid This Month: {fmt_money(st.session_state.amountPaidThisMonth)}{" — ✅ Full" if st.session_state.fullPaymentMadeThisMonth else ""}</small></div>
              </div>
            </div>
          </div>
        """, unsafe_allow_html=True)

        can_afford = st.session_state.wallet >= (st.session_state.loan.monthlyPayment + required_expenses_total())
        #  use ceil so you can actually clear small residuals
        pay_what = max(0, min(st.session_state.wallet - required_expenses_total(), math.ceil(st.session_state.loan.totalOwed)))

        b1, b2, b3 = st.columns([2,2,2])
        with b1:
            st.buttondd(
                f"💰 Full Payment (1 day) {fmt_money(st.session_state.loan.monthlyPayment)}",
                disabled=not can_afford,
                use_container_width=True,
                on_click=do_make_payment_full,
                key="btn_pay_full",
                variant="success" if can_afford else "warning"
            )
        with b2:
            st.buttondd(
                f"💸 Pay What I Can (1 day) {fmt_money(pay_what)}",
                disabled=pay_what<=0,
                use_container_width=True,
                on_click=do_make_payment_partial,
                key="btn_pay_partial",
                variant="success" if pay_what>0 else "warning"
            )
        with b3:
            st.buttondd("⏭️ Skip Payment (1 day)", use_container_width=True, on_click=do_skip_payment, key="btn_skip", variant="danger")

        st.markdown("### 🏠 Monthly Expenses (Free Actions - No Time Cost!)")
        cols = st.columns(2)
        for i, exp in enumerate(EXPENSES):
            with cols[i % 2]:
                required_text = "⚠️ Required" if exp["required"] else "🌟 Optional"
                happiness_text = f"<br><small>😊 (+{exp.get('happinessBoost', 0)}% happiness)</small>" if exp.get('happinessBoost', 0) > 0 else ""
                st.markdown(f"""
                  <div class="expense-card">
                    <h4>{exp['emoji']} {exp['name']} - {fmt_money(exp['amount'])}</h4>
                    <p>{required_text}{happiness_text}</p>
                  </div>
                """, unsafe_allow_html=True)
                disabled = st.session_state.wallet < exp["amount"]
                st.buttondd(
                    f"{exp['emoji']} Pay",
                    key=f"pay_{exp['id']}",
                    disabled=disabled,
                    on_click=lambda e=exp: pay_expense(e),
                    use_container_width=True,
                    variant="success" if not disabled else "warning"
                )

        st.markdown("---")
        label = "🌅 End Day & See What Happens!"
        if st.session_state.currentDay == st.session_state.daysInMonth:
            label = f"🗓️ End Month {st.session_state.currentMonth} → Payday: {fmt_money(st.session_state.monthlyIncome)}!"
        st.buttondd(label, disabled=st.session_state.currentEvent is not None, use_container_width=True, on_click=lambda: advance_day(no_event=False), key="btn_end_day", variant="success")
        st.buttondd("⏩ Skip to Month End (When Low on Money!)", use_container_width=True, on_click=fast_forward_to_month_end, key="btn_ff", variant="warning")

    with right:
        health_color = "🟢" if st.session_state.health > 70 else "🟡" if st.session_state.health > 30 else "🔴"
        happiness_color = "😊" if st.session_state.happiness > 70 else "😐" if st.session_state.happiness > 30 else "😢"

        net_monthly = st.session_state.monthlyIncome - required_expenses_total() - st.session_state.loan.monthlyPayment
        net_color = "🟢" if net_monthly > 0 else "🔴"

        st.markdown("### 🌟 Your Wellbeing")
        st.markdown(f"""
          <div class="metric-card">
            <h3>💪 Status Overview</h3>
            <div style="margin-top: 1rem;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 1rem;">
                <div><strong>❤️ Health:</strong> {health_color} {st.session_state.health}%</div>
                <div><strong>😊 Happiness:</strong> {happiness_color} {st.session_state.happiness}%</div>
              </div>
              <div style="text-align: center; padding: 1rem 0; border-top: 1px solid #eee;">
                <strong>💹 Monthly Budget:</strong> {net_color} {fmt_money(net_monthly)}<br>
                <small>After loan & required expenses</small>
              </div>
            </div>
          </div>
        """, unsafe_allow_html=True)

        # Work button
        work_available = can_work_this_period()
        st.buttondd("💼 Work for Money! (1 day, once/fortnight)\n~JMD$6k–9k, -10% Happiness",
                    disabled=not work_available,
                    on_click=do_work_for_money,
                    key="btn_work",
                    variant="success" if work_available else "warning")
        cur_fn = current_fortnight()
        st.caption(f"📅 Fortnight {cur_fn}/2 — you can work once each 2 weeks!")

def reset_game():
    # INTEGRATION: only reset the Debt Dilemma state; then rerun
    for k in list(st.session_state.keys()):
        # keep global app keys like 'user', 'current_page', 'current_game'
        if k not in {"user", "current_page", "xp", "streak", "current_game", "temp_user"}:
            del st.session_state[k]
    init_state()
    st.rerun()

def hospital_screen():
    st.error("🏥 You've been hospitalized. Health hit 0%. Game over.")
    #  use scoped button
    st.buttondd("🔁 Play again", on_click=reset_game, key="btn_again_hospital", variant="success")

def burnout_screen():
    st.warning("😵 You burned out. Happiness hit 0%. Game over.")
    #  use scoped button
    st.buttondd("🔁 Play again", on_click=reset_game, key="btn_again_burnout", variant="success")

def level_complete_screen():
    _award_level_completion_if_needed()
    st.success(f"🎉 Level {st.session_state.currentLevel} complete!")
    def _go_next():
        st.session_state.currentLevel += 1
        lvl = get_level(st.session_state.currentLevel)
        st.session_state.loan = LoanDetails(
            principal=lvl.loanAmount,
            interestRate=lvl.interestRate,
            monthlyPayment=lvl.monthlyPayment,
            totalOwed=float(lvl.loanAmount),
            monthsPaid=0,
            totalMonths=lvl.totalMonths,
            missedPayments=0,
            creditScore=st.session_state.loan.creditScore,
        )
        st.session_state.monthlyIncome = lvl.startingIncome
        st.session_state.gamePhase = "setup"
    #  use scoped button
    st.buttondd("➡️ Start next level", on_click=_go_next, key="btn_next_level", variant="success")

def completed_screen():
    _award_level_completion_if_needed()
    st.balloons()
    st.success("🏁 You’ve finished all levels or ran out of rounds!")
    #  use scoped button
    st.buttondd("🔁 Play again", on_click=reset_game, key="btn_again_completed", variant="success")

# ===============================
# Public entry point expected by game.py
# ===============================
def show_debt_dilemma():
    
    load_css(os.path.join("assets", "styles.css"))
    
    _ensure_dd_css()
    st.markdown(f'<div class="{DD_SCOPE_CLASS}">', unsafe_allow_html=True)  # OPEN SCOPE

    # Initialize game state 
    init_state()

    # Route within the game
    phase = st.session_state.gamePhase
    if phase == "setup":
        setup_screen()
    elif phase == "hospital":
        hospital_screen()
    elif phase == "burnout":
        burnout_screen()
    elif phase == "level-complete":
        level_complete_screen()
    elif phase == "completed":
        completed_screen()
    else:
        main_screen()

    st.markdown('</div>', unsafe_allow_html=True)  # CLOSE SCOPE
