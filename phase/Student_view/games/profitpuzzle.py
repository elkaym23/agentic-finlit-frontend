from utils import db as dbapi
import streamlit as st

def _refresh_global_xp():
    user = st.session_state.get("user")
    if not user:
        return
    try:
        stats = dbapi.user_xp_and_level(user["user_id"])
        st.session_state.xp = stats.get("xp", st.session_state.get("xp", 0))
        st.session_state.streak = stats.get("streak", st.session_state.get("streak", 0))
    except Exception as e:
        st.warning(f"XP refresh failed: {e}")

# --- CSS Styling ---
def load_css():
    st.markdown("""
    <style>
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        font-family: "Comic Sans MS", "Segoe UI", Arial, sans-serif;
    }
    
    /* Game header styling */
    .game-header {
        background: linear-gradient(135deg, #d946ef, #ec4899);
        padding: 2rem;
        border-radius: 15px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 2rem;
    }
    
    /* Scenario card styling */
    .scenario-card {
        background: #ffffff;
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        border: 2px solid #e5e7eb;
        margin-bottom: 1.5rem;
    }
    
    /* Variables display */
    .variables-card {
        background: linear-gradient(to right, #4ade80, #22d3ee);
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        margin: 1rem 0;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
    }
    
    /* Progress card */
    .progress-card {
        background: #3b82f6;
        padding: 1.5rem;
        border-radius: 12px;
        color: white;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* XP display */
    .xp-display {
        background: #10b981;
        padding: 1rem;
        border-radius: 12px;
        color: white;
        text-align: center;
        font-weight: bold;
        margin-bottom: 1rem;
    }
    
    /* Solution card */
    .solution-card {
        background: #f0f9ff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 2px solid #0ea5e9;
        margin: 1rem 0;
    }
    
    /* Custom button styling */
    /* Default button styling (white buttons) */
    .stButton > button {
        background: #ffffff !important;
        color: #111827 !important; /* dark gray text */
        border: 2px solid #d1d5db !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        font-weight: bold !important;
        font-size: 1.1rem !important;
        transition: all 0.3s ease !important;
        font-family: "Comic Sans MS", "Segoe UI", Arial, sans-serif !important;
    }

    .stButton > button:hover {
        background: #f9fafb !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1) !important;
    }

    /* Next button styling */
    .next-btn button {
        background: #3b82f6 !important;
        color: white !important;
        border: none !important;
    }
    .next-btn button:hover {
        background: #2563eb !important;
    }

    /* Restart button styling */
    .restart-btn button {
        background: #ec4899 !important;
        color: white !important;
        border: none !important;
    }
    .restart-btn button:hover {
        background: #db2777 !important;
    }

    
    
    /* Text input styling */
    .stTextInput > div > div > input {
        border-radius: 12px !important;
        border: 2px solid #d1d5db !important;
        padding: 12px 16px !important;
        font-size: 1.1rem !important;
        font-family: "Comic Sans MS", "Segoe UI", Arial, sans-serif !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #10b981 !important;
        box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2) !important;
    }
    
    /* Slider styling */
    .stSlider > div > div > div {
        background: linear-gradient(to right, #4ade80, #22d3ee) !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: #f8fafc;
        border-radius: 12px;
        padding: 1rem;
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background: #dcfce7 !important;
        border: 2px solid #16a34a !important;
        border-radius: 12px !important;
        color: #15803d !important;
    }
    
    .stError {
        background: #fef2f2 !important;
        border: 2px solid #dc2626 !important;
        border-radius: 12px !important;
        color: #dc2626 !important;
    }
    
    .stInfo {
        background: #eff6ff !important;
        border: 2px solid #2563eb !important;
        border-radius: 12px !important;
        color: #1d4ed8 !important;
    }
    
    .stWarning {
        background: #fffbeb !important;
        border: 2px solid #d97706 !important;
        border-radius: 12px !important;
        color: #92400e !important;
    }
    
    /* Difficulty badge styling */
    .difficulty-easy {
        background: #dcfce7;
        color: #16a34a;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    .difficulty-medium {
        background: #fef3c7;
        color: #d97706;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    
    .difficulty-hard {
        background: #fecaca;
        color: #dc2626;
        padding: 0.25rem 0.75rem;
        border-radius: 12px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
#--- Show progress in sidebar ---
# --- Sidebar Progress ---
def show_profit_progress_sidebar():
    scenarios = st.session_state.get("profit_scenarios", [])
    total_scenarios = len(scenarios)
    current_s = st.session_state.get("current_scenario", 0)
    completed_count = len(st.session_state.get("completed_scenarios", []))

    with st.sidebar:        
        #add sidebar details for eg
        st.sidebar.markdown(f"""
        <div class="xp-display">
            <h2>🏆 Your Progress</h2>
            <p style="font-size: 1.5rem;">Total XP: {st.session_state.get("score", 0)}</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.sidebar.markdown("### 🎯 Challenge List")
        for i, s in enumerate(scenarios):
            if i in st.session_state.completed_scenarios:
                st.sidebar.success(f"✅ {s['title']}")
            elif i == st.session_state.current_scenario:
                st.sidebar.info(f"🎯 {s['title']} (Current)")
            else:
                st.sidebar.write(f"⭕ {s['title']}")

        st.sidebar.markdown("""
        <div style="background: #f0f9ff; padding: 1rem; border-radius: 12px; border: 2px solid #0ea5e9; margin-top: 1rem;">
            <h3>🧮 Profit Formula</h3>
            <p><strong>Profit = Revenue - Cost</strong></p>
            <hr style="border-color: #0ea5e9;">
            <p><strong>Revenue</strong> = Units × Selling Price</p>
            <p><strong>Cost</strong> = Units × Cost per Unit</p>
        </div>
        """, unsafe_allow_html=True)
        
        #space and back button
        st.sidebar.markdown("<br>", unsafe_allow_html=True)

        if st.button("← Back to Games Hub", use_container_width=True):
            st.session_state.current_game = None
            st.rerun()

def _current_scenario():
    ps = st.session_state.get("profit_scenarios", [])
    idx = st.session_state.get("current_scenario", 0)
    return (ps[idx] if ps and 0 <= idx < len(ps) else None)


def next_scenario():
    total = len(st.session_state.get("profit_scenarios", []))
    if st.session_state.get("current_scenario", 0) < total - 1:
        st.session_state.current_scenario += 1
        st.session_state.user_answer = ""
        st.session_state.show_solution = False
    st.rerun()

def reset_game():
    st.session_state.current_scenario = 0
    st.session_state.user_answer = ""
    st.session_state.show_solution = False
    st.session_state.score = 0
    st.session_state.completed_scenarios = []
    st.rerun()



# --- Profit Puzzle Game ---
def show_profit_puzzle():
    # Load CSS styling
    load_css()
    
    st.markdown("""
    <div class="game-header">
        <h1>🎯 Profit Puzzle Challenge!</h1>
        <p>Learn to calculate profits while having fun! 🚀</p>
    </div>
    """, unsafe_allow_html=True)

    # -------------------------
    # Game State Management
    # -------------------------
    if "current_scenario" not in st.session_state:
        st.session_state.current_scenario = 0
    if "user_answer" not in st.session_state:
        st.session_state.user_answer = ""
    if "show_solution" not in st.session_state:
        st.session_state.show_solution = False
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "completed_scenarios" not in st.session_state:
        st.session_state.completed_scenarios = []
    if "slider_units" not in st.session_state:
        st.session_state.slider_units = 10
    if "slider_price" not in st.session_state:
        st.session_state.slider_price = 50
    if "slider_cost" not in st.session_state:
        st.session_state.slider_cost = 30

    # -------------------------
    # Scenario Setup
    # -------------------------
    scenarios = [
        {
            "id": "juice-stand",
            "title": "🧃 Juice Stand Profit",
            "description": "You sold juice at your school event. Calculate your profit!",
            "variables": {"units": 10, "sellingPrice": 50, "costPerUnit": 30},
            "difficulty": "easy",
            "xpReward": 20
        },
        {
            "id": "craft-business",
            "title": "🎨 Craft Business",
            "description": "Your handmade crafts are selling well. What's your profit?",
            "variables": {"units": 15, "sellingPrice": 80, "costPerUnit": 45},
            "difficulty": "medium",
            "xpReward": 20
        },
        {
            "id": "bake-sale",
            "title": "🧁 School Bake Sale",
            "description": "You organized a bake sale fundraiser. Calculate the profit!",
            "variables": {"units": 25, "sellingPrice": 60, "costPerUnit": 35},
            "difficulty": "medium",
            "xpReward": 20
        },
        {
            "id": "tutoring-service",
            "title": "📚 Tutoring Service",
            "description": "You've been tutoring younger students. What's your profit after expenses?",
            "variables": {"units": 8, "sellingPrice": 200, "costPerUnit": 50},
            "difficulty": "hard",
            "xpReward": 40
        },
        {
            "id": "dynamic-scenario",
            "title": "🎮 Custom Business Scenario",
            "description": "Use the sliders to create your own business scenario and calculate profit!",
            "variables": {"units": st.session_state.slider_units,
                           "sellingPrice": st.session_state.slider_price,
                           "costPerUnit": st.session_state.slider_cost},
            "difficulty": "medium",
            "xpReward": 50
        }
    ]

    # after scenarios = [...]
    st.session_state.profit_scenarios = scenarios  # Store scenarios in session state for sidebar access
    scenario = scenarios[st.session_state.current_scenario]
    is_dynamic = scenario["id"] == "dynamic-scenario"

    # -------------------------
    # Helper Functions
    # -------------------------
    def calculate_profit(units, price, cost):
        return units * (price - cost)

    def check_answer():
        try:
            user_val = float(st.session_state.user_answer)
        except ValueError:
            st.warning("Please enter a number.")
            return

        units = int(scenario["variables"]["units"])
        price = int(scenario["variables"]["sellingPrice"])
        cost  = int(scenario["variables"]["costPerUnit"])
        actual_profit = units * (price - cost)

        correct = abs(user_val - actual_profit) < 0.01
        reward = int(scenario.get("xpReward", 20)) if correct else 0

        # UI feedback
        if correct:
            st.success(f"✅ Awesome! You got it right! +{reward} XP 🎉")
            st.session_state.score += reward
            if st.session_state.current_scenario not in st.session_state.completed_scenarios:
                st.session_state.completed_scenarios.append(st.session_state.current_scenario)
        else:
            st.error(f"❌ Oops. Correct profit is JA${actual_profit:.2f}")

        # Persist to TiDB if logged in
        user = st.session_state.get("user")
        if user:
            try:
                dbapi.record_profit_puzzle_result(
                    user_id=user["user_id"],
                    scenario_id=scenario.get("id") or f"scenario_{st.session_state.current_scenario}",
                    title=scenario.get("title", f"Scenario {st.session_state.current_scenario+1}"),
                    units=units, price=price, cost=cost,
                    user_answer=user_val, actual_profit=float(actual_profit),
                    is_correct=bool(correct), gained_xp=int(reward)
                )
                _refresh_global_xp()
            except Exception as e:
                st.warning(f"Could not save result: {e}")
        else:
            st.info("Login to earn and save XP.")

        st.session_state.show_solution = True

    def next_scenario():
        if st.session_state.current_scenario < len(scenarios) - 1:
            st.session_state.current_scenario += 1
            st.session_state.user_answer = ""
            st.session_state.show_solution = False

    def reset_game():
        st.session_state.current_scenario = 0
        st.session_state.user_answer = ""
        st.session_state.show_solution = False
        st.session_state.score = 0
        st.session_state.completed_scenarios = []

    # -------------------------
    # UI Layout
    # -------------------------
    
    difficulty_class = f"difficulty-{scenario['difficulty']}"
    st.markdown(f"""
    <div class="scenario-card">
        <h2>{scenario['title']}</h2>
        <span class="{difficulty_class}">{scenario['difficulty'].upper()}</span>
        <p style="margin-top: 1rem; font-size: 1.1rem;">{scenario["description"]}</p>
        <h3>📊 Business Details</h3>
        <p><strong>Units Sold:</strong> {scenario['variables']['units']}</p>
        <p><strong>Selling Price per Unit:</strong> JA${scenario['variables']['sellingPrice']}</p>
        <p><strong>Cost per Unit:</strong> JA${scenario['variables']['costPerUnit']}</p>
    </div>
    """, unsafe_allow_html=True)

    if is_dynamic:
        st.markdown("### 🎛️ Customize Your Business")
        st.session_state.slider_units = st.slider("Units Sold", 1, 50, st.session_state.slider_units)
        st.session_state.slider_price = st.slider("Selling Price per Unit (JA$)", 10, 200, st.session_state.slider_price, 5)
        st.session_state.slider_cost = st.slider("Cost per Unit (JA$)", 5, st.session_state.slider_price - 1, st.session_state.slider_cost, 5)

        scenario["variables"] = {
            "units": st.session_state.slider_units,
            "sellingPrice": st.session_state.slider_price,
            "costPerUnit": st.session_state.slider_cost
        }


    st.markdown("### 💰 What's the profit?")
    st.text_input("Enter Profit (JA$):", key="user_answer", disabled=st.session_state.show_solution, placeholder="Type your answer here...")

    if not st.session_state.show_solution:
        st.button("🎯 Check My Answer!", on_click=check_answer)
    else:
        actual_profit = calculate_profit(
            scenario["variables"]["units"],
            scenario["variables"]["sellingPrice"],
            scenario["variables"]["costPerUnit"]
        )

        st.markdown(f"""
        <div class="solution-card">
            <h3>🧮 Solution Breakdown</h3>
            <p><strong>Revenue:</strong> {scenario['variables']['units']} × JA${scenario['variables']['sellingPrice']} = JA${scenario['variables']['units'] * scenario['variables']['sellingPrice']}</p>
            <p><strong>Total Cost:</strong> {scenario['variables']['units']} × JA${scenario['variables']['costPerUnit']} = JA${scenario['variables']['units'] * scenario['variables']['costPerUnit']}</p>
            <p><strong>Profit:</strong> JA${scenario['variables']['units'] * scenario['variables']['sellingPrice']} - JA${scenario['variables']['units'] * scenario['variables']['costPerUnit']} = <span style="color: #10b981; font-weight: bold; font-size: 1.2rem;">JA${actual_profit}</span></p>
        </div>
        """, unsafe_allow_html=True)

        next_col, restart_col = st.columns(2)
        with next_col:
            if st.session_state.current_scenario < len(scenarios) - 1:
                st.markdown('<div class="next-btn">', unsafe_allow_html=True)
                st.button("➡️ Next Challenge", on_click=next_scenario)
                st.markdown('</div>', unsafe_allow_html=True)
        with restart_col:
            st.markdown('<div class="restart-btn">', unsafe_allow_html=True)
            st.button("🔄 Start Over", on_click=reset_game)
            st.markdown('</div>', unsafe_allow_html=True)

