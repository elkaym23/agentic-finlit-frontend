---
title: Agentic Finlit Frontend
emoji: 🚀
colorFrom: red
colorTo: red
sdk: streamlit
app_port: 8501
app_file: streamlit_app.py
pinned: false
short_description: agentic-finlit-frontend
license: unknown
---

# SmartKids FinEdu — Frontend (Streamlit)

Student + teacher app. All data lives in **Supabase**; the AI tutor (RAG chat, lesson summaries,
mini-quizzes, auto-generated teacher quizzes) is served by **SmartKids-backend**.

## Setup

1. Set up Supabase and the backend first — see `SmartKids-backend/README.md`.
2. Then:

```bash
cd SmartKids-frontend
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # DATABASE_URL (same as backend) + BACKEND_URL
streamlit run streamlit_app.py
```

The sidebar's **🔌 AI tutor status** panel shows whether the backend, database and LLM are reachable.

On Hugging Face add `DATABASE_URL` and `BACKEND_URL` (and `BACKEND_API_KEY` if used) as Space secrets.
