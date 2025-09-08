# phase\Student_view\games\budgetbuilder.py

import streamlit as st
from utils import db as dbapi
import matplotlib.pyplot as plt

def show_budget_builder():
    # Add custom CSS for improved styling
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }
    
    /* Card-like styling for sections */
    .budget-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1.5rem;
        border: 1px solid #e5e7eb;
    }
    
    /* Header styling */
    .main h1 {
        color: #1f2937;
        font-weight: 700;
        margin-bottom: 0.5rem;
    }
    
    .main h2 {
        color: #374151;
        font-weight: 600;
        margin-bottom: 1rem;
        font-size: 1.5rem;
    }
    
    .main h3 {
        color: #4b5563;
        font-weight: 600;
        margin-bottom: 0.75rem;
        font-size: 1.25rem;
    }
    
    /* Slider styling improvements */
    .stSlider > div > div > div > div {
        background-color: #f3f4f6;
        border-radius: 8px;
    }
    
    /* Updated button styling with specific colors for Check Budget (green) and Reset (gray) */
    .stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: 600;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Green button for Check Budget */
    .stButton > button[kind="primary"] {
        background-color: #10b981;
        color: white;
    }
    
    .stButton > button[kind="primary"]:hover {
        background-color: #059669;
    }
    
    /* Gray button for Reset */
    .stButton > button[kind="secondary"] {
        background-color: white;
        color: black;
    }
    
    .stButton > button[kind="secondary"]:hover {
        background-color: #f3f4f6;
    }
    
    /* Success/Error message styling */
    .stSuccess {
        border-radius: 8px;
        border-left: 4px solid #10b981;
    }
    
    .stError {
        border-radius: 8px;
        border-left: 4px solid #ef4444;
    }
    
    /* Metric styling */
    .metric-container {
        background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
        border-radius: 12px;
        padding: 1rem;
        border: 1px solid #e2e8f0;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Table styling */
    .stTable {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid #e5e7eb;
    }
    
    /* Progress bar styling */
    .stProgress > div > div > div {
        background-color: #10b981;
        border-radius: 4px;
    }
    
    /* Info box styling */
    .stInfo {
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        background-color: #eff6ff;
    }
    </style>
    """, unsafe_allow_html=True)

    # -----------------------------
    # Define Levels and Categories
    # -----------------------------
    levels = [
        {
            "id": 1,
            "title": "First Budget",
            "description": "Learn basic budget allocation",
            "scenario": "You're 14 and just started getting a weekly allowance. Your parents want to see you can manage money responsibly before increasing it.",
            "income": 300,
            "objectives": [
                "Save at least 20% of your income",
                "Don't spend more than 30% on entertainment",
                "Allocate money for food and transport"
            ],
            "constraints": {
                "savings": {"min": 60},
                "fun": {"max": 90},
                "food": {"min": 40, "required": True},
                "transport": {"min": 30, "required": True},
            },
            "success": [
                ("Save at least JA$60 (20%)", lambda cats, inc: cats["savings"] >= 60),
                ("Keep entertainment under JA$90 (30%)", lambda cats, inc: cats["fun"] <= 90),
                ("Balance your budget completely", lambda cats, inc: sum(cats.values()) == inc),
            ],
            "xp": 20,
        },
        {
            "id": 2,
            "title": "Emergency Fund",
            "description": "Build an emergency fund while managing expenses",
            "scenario": "Your phone broke last month and you had no savings to fix it. This time, build an emergency fund while still enjoying life.",
            "income": 400,
            "objectives": [
                "Build an emergency fund (JA$100+)",
                "Still save for long-term goals",
                "Cover all essential expenses",
            ],
            "constraints": {
                "savings": {"min": 150},  # Emergency + regular savings
                "food": {"min": 60, "required": True},
                "transport": {"min": 40, "required": True},
                "school": {"min": 20, "required": True},
            },
            "success": [
                ("Save at least JA$150 total", lambda cats, inc: cats["savings"] >= 150),
                (
                    "Cover all essential expenses",
                    lambda cats, inc: cats["food"] >= 60
                    and cats["transport"] >= 40
                    and cats["school"] >= 20,
                ),
            ],
            "xp": 30,
        },
        {
            "id": 3,
            "title": "Reduced Income",
            "description": "Manage when money is tight",
            "scenario": "Your allowance got cut because of family finances. You need to make tough choices while still maintaining your savings habit.",
            "income": 250,
            "objectives": [
                "Still save something (minimum JA$25)",
                "Cut non-essential spending",
                "Maintain essential expenses",
            ],
            "constraints": {
                "savings": {"min": 25},
                "fun": {"max": 40},
                "food": {"min": 50, "required": True},
                "transport": {"min": 35, "required": True},
            },
            "success": [
                ("Save at least JA$25 (10%)", lambda cats, inc: cats["savings"] >= 25),
                ("Keep entertainment under JA$40", lambda cats, inc: cats["fun"] <= 40),
                ("Balance your budget", lambda cats, inc: sum(cats.values()) == inc),
            ],
            "xp": 35,
        },
        {
            "id": 4,
            "title": "Debt & Goals",
            "description": "Pay off debt while saving for something special",
            "scenario": "You borrowed JA$100 from your parents for a school trip. Now you need to pay it back (JA$25/week) while saving for a new game console.",
            "income": 450,
            "objectives": [
                "Pay debt installment (JA$25)",
                "Save for console (JA$50+ per week)",
                "Don't compromise on essentials",
            ],
            "constraints": {
                "savings": {"min": 75},  # 50 for console + 25 debt payment
                "food": {"min": 70, "required": True},
                "transport": {"min": 45, "required": True},
                "school": {"min": 30, "required": True},
            },
            "success": [
                ("Allocate JA$75+ for savings & debt", lambda cats, inc: cats["savings"] >= 75),
                (
                    "Cover all essentials adequately",
                    lambda cats, inc: cats["food"] >= 70
                    and cats["transport"] >= 45
                    and cats["school"] >= 30,
                ),
            ],
            "xp": 40,
        },
        {
            "id": 5,
            "title": "Master Budgeter",
            "description": "Handle multiple financial goals like an adult",
            "scenario": "You're 16 now with part-time job income. Manage multiple goals: emergency fund, college savings, social life, and family contribution.",
            "income": 600,
            "objectives": [
                "Build emergency fund (JA$50)",
                "Save for college (JA$100)",
                "Contribute to family (JA$40)",
                "Maintain social life and hobbies",
            ],
            "constraints": {
                "savings": {"min": 150},  # Emergency + college
                "charity": {"min": 40},   # Family contribution
                "food": {"min": 80, "required": True},
                "transport": {"min": 60, "required": True},
                "school": {"min": 50, "required": True},
            },
            "success": [
                ("Save JA$150+ for future goals", lambda cats, inc: cats["savings"] >= 150),
                ("Contribute JA$40+ to family", lambda cats, inc: cats["charity"] >= 40),
                (
                    "Balance entertainment & responsibilities",
                    lambda cats, inc: cats["fun"] >= 30 and cats["fun"] <= 150,
                ),
                ("Perfect budget balance", lambda cats, inc: sum(cats.values()) == inc),
            ],
            "xp": 50,
        },
    ]

    # -----------------------------
    # Initialize Session State
    # -----------------------------
    if "current_level" not in st.session_state:
        st.session_state.current_level = 1
    if "completed_levels" not in st.session_state:
        st.session_state.completed_levels = []
    if "categories" not in st.session_state:
        st.session_state.categories = {}
    if "level_completed" not in st.session_state:
        st.session_state.level_completed = False

    # -----------------------------
    # Categories Master
    # -----------------------------
    categories_master = {
        "food": {"name": "Food & Snacks", "color": "#16a34a", "icon": "🍎", "min": 0, "max": 300},
        "savings": {"name": "Savings", "color": "#2563eb", "icon": "💰", "min": 0, "max": 400},
        "fun": {"name": "Entertainment", "color": "#dc2626", "icon": "🎮", "min": 0, "max": 300},
        "charity": {"name": "Charity/Family", "color": "#e11d48", "icon": "❤️", "min": 0, "max": 200},
        "transport": {"name": "Transport", "color": "#ea580c", "icon": "🚌", "min": 0, "max": 200},
        "school": {"name": "School Supplies", "color": "#0891b2", "icon": "📚", "min": 0, "max": 150},
    }
    if not st.session_state.categories:
        st.session_state.categories = {cid: 0 for cid in categories_master.keys()}

    # -----------------------------
    # Current Level Setup
    # -----------------------------
    level = [l for l in levels if l["id"] == st.session_state.current_level][0]

    # Header section with improved styling
    st.markdown(f"""
    <div style="text-align: center; padding: 2rem 0; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 12px; margin-bottom: 2rem; color: white;">
        <h1 style="color: white; margin-bottom: 0.5rem;">💵 Budget Builder</h1>
    </div>
    """, unsafe_allow_html=True)

    # Level progress indicator
    st.markdown(f"""
    <div style="background: #f8fafc; border-radius: 8px; padding: 1rem; margin-bottom: 2rem; border: 1px solid #e2e8f0;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
            <span style="font-weight: 600; color: #374151;">Level Progress</span>
            <span style="color: #6b7280;">{len(st.session_state.completed_levels)}/5 Complete</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Scenario description with better styling
    st.markdown(f"""
    <div style="background: #eff6ff; border-radius: 8px; padding: 1.5rem; margin-bottom: 2rem; 
                border-left: 4px solid #3b82f6;">
        <h4 style="color: #1e40af; margin-bottom: 0.5rem;">📖 Scenario</h4>
        <p style="color: #1f2937; margin-bottom: 1rem;">{level["scenario"]}</p>
        <div style="background: white; border-radius: 6px; padding: 1rem; border: 1px solid #dbeafe;">
            <strong style="color: #059669;">Weekly Income: JA${level['income']}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # -----------------------------
    # Two-column layout
    # -----------------------------
    left_col, right_col = st.columns([2, 1], gap="large")

    with left_col:
        st.markdown(f"""
        <div class="budget-card" style="background: #f8fafc; border-left: 4px solid #10b981;">
            <h3 style="color: #059669; margin-bottom: 1rem;">🎯 Objectives</h3>
            {''.join([f'<div style="margin-bottom: 0.5rem; color: #374151;">• {obj}</div>' for obj in level["objectives"]])}
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <h2 style="color: #374151; margin-bottom: 1.5rem;">💰 Budget Allocation</h3>
        <p style="color: #6b7280; margin-bottom: 1.5rem;">Use the sliders below to allocate your weekly income across different categories. Make sure to meet the objectives!</p>
        """, unsafe_allow_html=True)

        st.markdown("### 📊 Allocate Your Budget")
        # Render sliders without dynamic inter-dependencies
        for cid, cat in categories_master.items():
            constraints = level["constraints"].get(cid, {})
            min_val = 0
            #max is set to the level income for more flexibility
            max_val = level["income"]
            st.session_state.categories[cid] = st.slider(
                f"{cat['icon']} {cat['name']}",
                min_value=min_val,
                max_value=max_val,
                value=st.session_state.categories[cid],
                step=5,
                help=f"Min: JA${min_val}, Max: JA${max_val}"
            )

        # Calculate totals after sliders have been selected
        total_allocated = sum(st.session_state.categories.values())
        remaining = level["income"] - total_allocated
        st.metric("Remaining", f"JA${remaining}", delta_color="inverse" if remaining < 0 else "normal")

        
        # Remaining budget display with better styling
        color = "#ef4444" if remaining < 0 else "#059669" if remaining == 0 else "#f59e0b"
        st.markdown(f"""
        <div class="metric-container" style="border-left: 4px solid {color};">
            <h4 style="color: #6b7280; margin-bottom: 0.5rem;">Remaining Budget</h4>
            <h2 style="color: {color}; margin: 0;">JA${remaining}</h2>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Check Budget", use_container_width=True, type="primary"):
                results = [(desc, fn(st.session_state.categories, level["income"])) for desc, fn in level["success"]]
                all_passed = all(r[1] for r in results)

                if all_passed and remaining == 0:
                    st.success(f"🎉 Level {level['id']} Complete! +{level['xp']} XP")
                    st.session_state.level_completed = True
                    if level["id"] not in st.session_state.completed_levels:
                        st.session_state.completed_levels.append(level["id"])
                else:
                    st.error("❌ Not complete yet. Check the requirements!")
                    for desc, passed in results:
                        icon = "✅" if passed else "⚠️"
                        st.markdown(f"{icon} {desc}")

        with col2:
            # Reset button
            if st.button("🔄 Reset Budget", use_container_width=True, type="secondary"):
                # Reset all category amounts
                for cid in categories_master.keys():
                    st.session_state[cid] = 0
                # Reset the dictionary in session_state too
                st.session_state.categories = {cid: 0 for cid in categories_master.keys()}
                st.session_state.level_completed = False
                st.experimental_rerun()


        # Next Level button
        if st.session_state.level_completed and st.session_state.current_level < len(levels):
            if st.button("➡️ Next Level", use_container_width=True, type="primary"):
                st.session_state.current_level += 1
                st.session_state.categories = {cid: 0 for cid in categories_master.keys()}
                st.session_state.level_completed = False
                st.experimental_rerun()

    with right_col:
        criteria_html = ""
        for desc, fn in level["success"]:
            passed = fn(st.session_state.categories, level["income"])
            icon = "✅" if passed else "⚠️"
            color = "#059669" if passed else "#f59e0b"
            criteria_html += f"<div style='margin-bottom: 0.5rem; color: {color};'>{icon} {desc}</div>"
        
        st.markdown(f"""
        <div class="budget-card">
            <h3 style="color: #374151; margin-bottom: 1rem;">✅ Success Criteria</h3>
            {criteria_html}
        </div>
        """, unsafe_allow_html=True)

        breakdown_html = ""
        for cid, amount in st.session_state.categories.items():
            if amount > 0:
                cat = categories_master[cid]
                percentage = (amount / level["income"]) * 100
                breakdown_html += f"""
        <div style="display:flex; justify-content:space-between; align-items:center; 
                    padding:0.5rem; margin-bottom:0.5rem; background:#f8fafc; border-radius:6px;">
            <span style="color:#374151;">{cat['icon']} {cat['name']}</span>
            <div style="text-align:right;">
                <div style="font-weight:600; color:#1f2937;">JA${amount}</div>
                <div style="font-size:0.8rem; color:#6b7280;">{percentage:.1f}%</div>
            </div>
        </div>
        """

        st.markdown(f"""
        <div class="budget-card">
            <h3 style="color:#374151; margin-bottom:1rem;">📊 Budget Breakdown</h3>
            {breakdown_html}
        </div>
        """, unsafe_allow_html=True)


        st.markdown("""
        <div class="budget-card" style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                    border-left: 4px solid #f59e0b;">
            <h3 style="color: #92400e; margin-bottom: 1rem;">💡 Level Tips</h3>
            <div style="color: #451a03;">
                <div style="margin-bottom: 0.5rem;">💰 Start with essentials like food and transport</div>
                <div style="margin-bottom: 0.5rem;">🎯 The 50/30/20 rule: needs, wants, savings</div>
                <div>📊 Review and adjust your budget regularly</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    if len(st.session_state.completed_levels) == len(levels):
        st.balloons()
        st.markdown("""
        <div style="text-align: center; padding: 2rem; background: linear-gradient(135deg, #10b981 0%, #059669 100%); 
                    border-radius: 12px; color: white; margin-top: 2rem;">
            <h2 style="color: white; margin-bottom: 1rem;">🎉 Congratulations!</h2>
            <h3 style="color: #d1fae5; margin: 0;">You are now a Master Budgeter!</h3>
        </div>
        <br>
        """, unsafe_allow_html=True)

        # Show a restart button
        if st.button("🔄 Restart Game"):
            st.session_state.current_level = 1
            st.session_state.completed_levels = []
            st.session_state.categories = {cid: 0 for cid in categories_master.keys()}
            st.session_state.level_completed = False
            st.experimental_rerun()
