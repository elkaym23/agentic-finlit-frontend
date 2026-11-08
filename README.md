# SmartKids — Frontend (React)

React + Vite + Tailwind web app for students and teachers. It talks to **SmartKids-backend** at `/api`
(FastAPI + Supabase + FinBuddy, the RAG tutor).

**Students:** pick a level → read a lesson → take the quiz → FinBuddy marks it and you can chat about every
answer → next lesson. Pass every lesson in a level to unlock its game (Money Match, Budget Builder,
Profit Puzzle, Debt Dilemma); win it to unlock the next level. Students earn XP and streaks, and can join a class.

**Teachers:** create classes (students join with a 6-letter code), upload a PDF / Word / text document or
type a topic and FinBuddy writes a lesson and quiz, edit any quiz, assign work with due dates, and track every
student's scores, quiz chats and the class leaderboard.

## Run it (development)

Set up Supabase and the backend first (see `../SmartKids-backend/README.md`), then start the backend on port 7860:

```bash
cd SmartKids-frontend
npm install
npm run dev
```

Open <http://localhost:5173>. Vite forwards `/api` to `http://localhost:7860`.

## Run it (school demo, one server)

```bash
npm run build
```

Now `uvicorn app.main:app --port 7860` in the backend also serves this app at <http://localhost:7860>.

## Layout

| Path | What |
|---|---|
| `src/pages/student` | Home, learning path, lesson, quiz, review + chat, games, tutor, my class |
| `src/pages/teacher` | Dashboard, class progress, student report, library (upload / generate), quiz + lesson editors |
| `src/games` | The four level games |
| `src/components` | Layout (sidebar), FinBuddy mascot, chat, shared UI |
| `public/money` | Jamaican coin and note images used by Money Match |
