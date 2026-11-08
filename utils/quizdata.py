"""Built-in practice quizzes (ids 1-5). Teacher quizzes in Supabase start at id 1000.

Each question: {"question", "options", "answer" (option text, or list for multi-select), "explanation"}
"""

quizzes_data = {
    1: {
        "title": "Introduction to Money",
        "level": "beginner",
        "duration": "5 min",
        "description": "Coins, notes, digital money and counting Jamaican dollars.",
        "questions": [
            {
                "question": "What do we use money for?",
                "options": ["To buy things we need and want", "Only to play games", "To plant in the garden", "Nothing at all"],
                "answer": "To buy things we need and want",
                "explanation": "Money helps us pay for food, clothes, bus fare and more.",
            },
            {
                "question": "Which of these is a Jamaican coin?",
                "options": ["$5", "$500", "$1000", "$5000"],
                "answer": "$5",
                "explanation": "$1, $5, $10 and $20 are coins; $50 and up are notes.",
            },
            {
                "question": "When a parent taps a card to pay at the supermarket, what kind of money is that?",
                "options": ["Digital money", "Coins", "Bartering", "Play money"],
                "answer": "Digital money",
                "explanation": "Digital money lives in a bank account and is used with cards or phones.",
            },
            {
                "question": "One $100 note and two $20 coins make how much?",
                "options": ["$140", "$120", "$102", "$200"],
                "answer": "$140",
                "explanation": "$100 + $20 + $20 = $140.",
            },
            {
                "question": "Trading fish for yams without using money is called...",
                "options": ["Bartering", "Saving", "Budgeting", "Borrowing"],
                "answer": "Bartering",
                "explanation": "Before money, people swapped goods directly — that's bartering.",
            },
        ],
    },
    2: {
        "title": "Earning and Spending",
        "level": "beginner",
        "duration": "5 min",
        "description": "Jobs, pocket money, needs vs wants and simple budgets.",
        "questions": [
            {
                "question": "Which of these is a NEED?",
                "options": ["Food", "A video game", "Extra candy", "A toy car"],
                "answer": "Food",
                "explanation": "Needs keep us alive and safe: food, water, shelter, clothes.",
            },
            {
                "question": "Which of these are WANTS? (choose all)",
                "options": ["New sneakers when yours still fit", "Medicine", "A video game", "Clean water"],
                "answer": ["New sneakers when yours still fit", "A video game"],
                "explanation": "Wants are nice to have, but we can live without them.",
            },
            {
                "question": "Money you get for doing work is called...",
                "options": ["Income", "Debt", "A scam", "Change"],
                "answer": "Income",
                "explanation": "Income is the money people earn from their jobs.",
            },
            {
                "question": "You have JA$1000. You plan to save $300 and spend $500 on snacks. How much is left for fun?",
                "options": ["$200", "$300", "$500", "$800"],
                "answer": "$200",
                "explanation": "1000 − 300 − 500 = 200.",
            },
            {
                "question": "A plan for how you will use your money is a...",
                "options": ["Budget", "Bank", "Coin", "Receipt"],
                "answer": "Budget",
                "explanation": "A budget helps you decide what to spend and what to save.",
            },
        ],
    },
    3: {
        "title": "Saving Money",
        "level": "beginner",
        "duration": "5 min",
        "description": "Why we save, where to save and setting goals.",
        "questions": [
            {
                "question": "Saving means...",
                "options": ["Keeping some money to use later", "Spending everything today", "Borrowing from a friend", "Losing money"],
                "answer": "Keeping some money to use later",
                "explanation": "When you save, you put money aside for the future.",
            },
            {
                "question": "Which is the SAFEST place to keep a lot of savings?",
                "options": ["A bank or credit union", "Under your bed", "In your school bag", "In your pocket"],
                "answer": "A bank or credit union",
                "explanation": "Banks and credit unions keep money safe and may pay interest.",
            },
            {
                "question": "A football costs $3000. You save $500 a week. How many weeks will it take?",
                "options": ["6 weeks", "3 weeks", "5 weeks", "10 weeks"],
                "answer": "6 weeks",
                "explanation": "3000 ÷ 500 = 6.",
            },
            {
                "question": "'Pay yourself first' means...",
                "options": ["Save before you spend", "Buy a treat first", "Ask for more pocket money", "Spend on others first"],
                "answer": "Save before you spend",
                "explanation": "Put your savings aside as soon as you get money.",
            },
            {
                "question": "Extra money a bank pays you for saving is called...",
                "options": ["Interest", "A fine", "Tax", "A loan"],
                "answer": "Interest",
                "explanation": "Interest rewards you for keeping money in the bank.",
            },
        ],
    },
    4: {
        "title": "Financial Responsibility",
        "level": "beginner",
        "duration": "5 min",
        "description": "Smart choices, giving, staying safe from scams.",
        "questions": [
            {
                "question": "A message says you won a prize but must send your parent's card number first. You should...",
                "options": ["Tell a parent or teacher and not reply", "Send the number quickly", "Share it with friends", "Reply asking for more prizes"],
                "answer": "Tell a parent or teacher and not reply",
                "explanation": "That's a scam. Never share card numbers, PINs or passwords.",
            },
            {
                "question": "A money diary helps you...",
                "options": ["See where your money goes", "Get free money", "Hide money from your family", "Win prizes"],
                "answer": "See where your money goes",
                "explanation": "Writing down what you get and spend shows your habits.",
            },
            {
                "question": "Which is a smart shopping choice?",
                "options": ["Compare prices before you buy", "Buy whatever your friend has", "Buy the first thing you see", "Spend all your money at once"],
                "answer": "Compare prices before you buy",
                "explanation": "Comparing helps you get good value for your money.",
            },
            {
                "question": "Which is a way of giving?",
                "options": ["Donating to a charity", "Hiding your lunch money", "Borrowing a toy", "Buying more candy"],
                "answer": "Donating to a charity",
                "explanation": "Giving and sharing helps others in your community.",
            },
            {
                "question": "Which should you NEVER share with strangers?",
                "options": ["Your PIN or password", "Your favourite colour", "Your favourite fruit", "Your favourite song"],
                "answer": "Your PIN or password",
                "explanation": "PINs and passwords protect your money and accounts.",
            },
        ],
    },
    5: {
        "title": "Interest & Emergency Funds",
        "level": "intermediate",
        "duration": "7 min",
        "description": "Simple vs compound interest and saving for surprises.",
        "questions": [
            {
                "question": "JA$10,000 earns 5% simple interest per year. How much interest after 1 year?",
                "options": ["$500", "$50", "$5,000", "$1,000"],
                "answer": "$500",
                "explanation": "5% of 10,000 = 500.",
            },
            {
                "question": "Compound interest is interest on...",
                "options": ["Your money plus interest already earned", "Only the first money you saved", "Money you spent", "Your friend's money"],
                "answer": "Your money plus interest already earned",
                "explanation": "That's why compound interest grows faster over time.",
            },
            {
                "question": "An emergency fund is for...",
                "options": ["Unexpected costs like a doctor visit", "A new video game", "Weekend treats", "Birthday parties"],
                "answer": "Unexpected costs like a doctor visit",
                "explanation": "Keep it for real surprises only.",
            },
            {
                "question": "Why is starting to save early helpful?",
                "options": ["Compound interest has more time to grow", "Banks close later", "Money gets heavier", "It isn't helpful"],
                "answer": "Compound interest has more time to grow",
                "explanation": "More time means more interest on interest.",
            },
            {
                "question": "Spreading money across different investments is called...",
                "options": ["Diversification", "Bartering", "Budgeting", "Borrowing"],
                "answer": "Diversification",
                "explanation": "It lowers risk because not everything goes down at once.",
            },
        ],
    },
}
