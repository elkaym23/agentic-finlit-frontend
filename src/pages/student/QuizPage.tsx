import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import Mascot from "../../components/Mascot";
import { Bar, ErrorBox, LevelChip, Spinner, useLoad } from "../../components/ui";
import type { Quiz, Submission } from "../../types";

export default function QuizPage() {
  const { id } = useParams();
  const nav = useNavigate();
  const { refresh } = useAuth();
  const { data: Q, error, loading, reload } = useLoad(() => api.get<Quiz>(`/api/quizzes/${id}`), [id]);
  const [i, setI] = useState(0);
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  if (loading) return <Spinner label="Getting the questions…" />;
  if (error || !Q) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;
  if (!Q.items.length) return <ErrorBox error="This quiz has no questions yet." />;
  if (busy) return (
    <div className="flex flex-col items-center gap-4 py-20 text-center">
      <div className="animate-bob"><Mascot size={120} mood="think" /></div>
      <div className="text-xl font-bold">FinBuddy is checking your answers…</div>
      <div className="muted">This only takes a few seconds.</div>
    </div>
  );

  const it = Q.items[i];
  const last = i === Q.items.length - 1;
  const val = answers[it.item_id] ?? "";
  const answered = Q.items.filter((x) => (answers[x.item_id] ?? "").trim()).length;
  const set = (v: string) => setAnswers({ ...answers, [it.item_id]: v });

  const submit = async () => {
    setErr(null);
    const missing = Q.items.findIndex((x) => !(answers[x.item_id] ?? "").trim());
    if (missing >= 0 && !confirm(`Question ${missing + 1} has no answer yet. Submit anyway?`)) { setI(missing); return; }
    setBusy(true);
    try {
      const s = await api.post<Submission>(`/api/quizzes/${Q.quiz_id}/submit`, { answers });
      await refresh();
      nav(`/review/${s.submission_id}`, { replace: true });
    } catch (e: any) {
      setErr(e.message);
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl">
      <div className="mb-5 flex flex-wrap items-center gap-2 text-sm">
        <Link to={Q.lesson_id ? `/lesson/${Q.lesson_id}` : "/class"} className="font-semibold text-ink-mute hover:text-ink">← Back to {Q.lesson_id ? "lesson" : "class"}</Link>
        <LevelChip level={Q.level} />
        <span className="chip bg-black/5">Pass mark {Q.pass_pct}%</span>
      </div>
      <h1 className="h-page">{Q.title}</h1>
      {Q.last_attempt && <p className="muted mt-1">Last try: {Q.last_attempt.percent}% {Q.last_attempt.passed ? "✅" : ""}</p>}

      <div className="mt-6 flex items-center gap-3">
        <Bar value={(answered / Q.items.length) * 100} color="bg-jam-gold" />
        <span className="shrink-0 text-sm font-semibold text-ink-mute">{answered}/{Q.items.length} answered</span>
      </div>
      <div className="mt-3 flex flex-wrap gap-1.5">
        {Q.items.map((x, k) => (
          <button key={x.item_id} onClick={() => setI(k)} aria-label={`Question ${k + 1}`}
                  className={`h-9 w-9 rounded-full text-sm font-bold transition ${k === i ? "bg-ink text-white" : (answers[x.item_id] ?? "").trim() ? "bg-jam-green/15 text-jam-green" : "bg-black/5 text-ink-mute"}`}>{k + 1}</button>
        ))}
      </div>

      <div key={it.item_id} className="mt-6 animate-pop rounded-4xl bg-[#fbfaf6] p-6 sm:p-8">
        <div className="text-sm font-semibold text-ink-mute">Question {i + 1} · {it.kind === "short" ? "Write your answer" : "Pick one"} · {it.points} pt{it.points > 1 ? "s" : ""}</div>
        <div className="mt-2 text-xl font-bold leading-snug">{it.question}</div>

        {it.kind === "mcq" ? (
          <div className="mt-5 grid gap-3">
            {it.options.map((o, k) => {
              const letter = String.fromCharCode(65 + k);
              const on = val === letter;
              return (
                <button key={k} onClick={() => set(letter)}
                        className={`flex items-center gap-3 rounded-3xl border-2 bg-white p-4 text-left transition ${on ? "border-jam-green bg-tile-mint" : "border-transparent hover:border-black/10"}`}>
                  <span className={`grid h-9 w-9 shrink-0 place-items-center rounded-full font-bold ${on ? "bg-jam-green text-white" : "bg-black/5"}`}>{letter}</span>
                  <span className="font-medium">{o}</span>
                </button>
              );
            })}
          </div>
        ) : (
          <textarea className="input mt-5 min-h-[140px] resize-y" value={val} onChange={(e) => set(e.target.value)}
                    placeholder="Explain in your own words. Full sentences help FinBuddy understand you!" maxLength={1500} />
        )}
      </div>

      {err && <div className="mt-4 rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{err}</div>}
      <div className="mt-6 flex items-center justify-between">
        <button className="btn-ghost" disabled={i === 0} onClick={() => setI(i - 1)}>← Back</button>
        {last ? <button className="btn-green px-6 text-lg" onClick={submit}>Submit quiz ✓</button>
              : <button className="btn-dark" onClick={() => setI(i + 1)}>Next →</button>}
      </div>
    </div>
  );
}
