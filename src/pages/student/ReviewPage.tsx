import { useEffect, useRef } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import ChatThread from "../../components/ChatThread";
import Mascot from "../../components/Mascot";
import { ErrorBox, Markdown, Ring, Spinner, celebrate, timeAgo, useLoad } from "../../components/ui";
import type { Submission } from "../../types";
import { nextLink } from "./StudentHome";

export default function ReviewPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const isStudent = user?.role === "Student";
  const { data: S, error, loading, reload } = useLoad(() => api.get<Submission>(`/api/submissions/${id}`), [id]);
  const fired = useRef(false);

  useEffect(() => {
    if (S?.passed && isStudent && !fired.current && Date.now() - new Date(S.submitted_at).getTime() < 60_000) {
      fired.current = true;
      celebrate();
    }
  }, [S, isStudent]);

  if (loading) return <Spinner label="Loading your results…" />;
  if (error || !S) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;

  const next = nextLink(S.next);
  const wrong = S.results.filter((r) => r.correct === false || (r.kind === "short" && r.earned < r.points));
  const suggestions = isStudent ? [
    ...(wrong[0] ? [`Why was my answer to "${wrong[0].question.slice(0, 50)}${wrong[0].question.length > 50 ? "…" : ""}" wrong?`] : []),
    "Explain the main idea again, simply",
    "Give me a real Jamaican example",
    "Can you give me a practice question?",
  ] : [];

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_420px]">
      <div className="min-w-0 space-y-5">
        <Link to={isStudent ? "/learn" : `/students/${(S as any).student_id}`} className="text-sm font-semibold text-ink-mute hover:text-ink">← Back</Link>

        <div className={`flex flex-col gap-5 rounded-4xl p-6 sm:flex-row sm:items-center ${S.passed ? "bg-tile-mint" : "bg-tile-peach"}`}>
          <div className="rounded-full bg-white p-2 shadow-card">
            <Ring value={S.percent} size={110} stroke={10} color={S.passed ? "#009b3a" : "#f59e0b"}>
              <span className="text-2xl font-extrabold">{S.percent}%</span>
            </Ring>
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-sm font-semibold uppercase tracking-wider text-ink-mute">{S.quiz_title}</div>
            <h1 className="mt-1 text-3xl font-extrabold">{S.passed ? "You passed! 🎉" : "Almost there! 💪"}</h1>
            <div className="mt-2 flex flex-wrap gap-2 text-sm">
              <span className="chip bg-white">{S.score} / {S.total} points</span>
              {S.xp > 0 && <span className="chip bg-jam-gold">+{S.xp} XP</span>}
              <span className="chip bg-white/70">{timeAgo(S.submitted_at)}</span>
            </div>
            {!S.passed && isStudent && <p className="mt-3 text-sm">Chat with FinBuddy about what tripped you up, then have another go.</p>}
          </div>
          {next && isStudent && (
            <Link to={next.to} className={`${S.passed ? "btn-green" : "btn-dark"} shrink-0 px-5 py-3`}>
              {S.next?.type === "game" ? "🎮 " : ""}{S.passed && S.next?.type === "lesson" ? "Next lesson →" : next.label}
            </Link>
          )}
        </div>

        <h2 className="text-xl font-bold">Your answers</h2>
        <div className="space-y-3">
          {S.results.map((r, k) => {
            const full = r.kind === "mcq" ? r.correct : r.earned >= r.points;
            const part = r.kind === "short" && r.earned > 0 && r.earned < r.points;
            return (
              <div key={r.item_id ?? k} className="rounded-3xl border border-black/5 bg-white p-5">
                <div className="flex items-start gap-3">
                  <span className={`grid h-8 w-8 shrink-0 place-items-center rounded-full text-sm font-bold ${full ? "bg-emerald-100 text-emerald-700" : part ? "bg-amber-100 text-amber-700" : "bg-rose-100 text-rose-700"}`}>
                    {full ? "✓" : part ? "½" : "✗"}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="font-semibold">{k + 1}. {r.question}</div>
                    <div className="mt-2 text-sm">
                      <span className="text-ink-mute">Your answer: </span>
                      <span className={full ? "font-medium text-emerald-700" : "font-medium"}>
                        {r.kind === "mcq" ? (r.answer_text || r.answer || "—") : (r.answer || "—")}
                      </span>
                    </div>
                    {r.kind === "mcq" && !r.correct && r.correct_text && (
                      <div className="text-sm"><span className="text-ink-mute">Correct answer: </span><span className="font-medium text-emerald-700">{r.correct_text}</span></div>
                    )}
                    {(r.explanation || r.feedback) && (
                      <div className="mt-2 rounded-2xl bg-[#f7f6fb] px-3 py-2 text-sm text-ink-soft">💡 {r.feedback || r.explanation}</div>
                    )}
                  </div>
                  <span className="shrink-0 text-sm font-bold text-ink-mute">{r.earned}/{r.points}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <aside className="xl:sticky xl:top-5 xl:self-start">
        <div className="rounded-4xl bg-ink p-5 text-white">
          <div className="mb-4 flex items-center gap-3">
            <Mascot size={52} mood={S.passed ? "cheer" : "think"} />
            <div>
              <div className="font-bold">Talk it through with FinBuddy</div>
              <div className="text-sm text-white/70">{isStudent ? "Ask about any question on this quiz" : "The student's chat about this quiz"}</div>
            </div>
          </div>
          <div className="rounded-4xl bg-white p-3 text-ink">
            {isStudent ? (
              <ChatThread messages={S.chat} suggestions={suggestions} height="h-[min(46vh,440px)]" placeholder="Ask about this quiz…"
                          send={async (message) => (await api.post<{ reply: string }>(`/api/submissions/${S.submission_id}/chat`, { message })).reply} />
            ) : (
              <ReadOnlyChat msgs={S.chat} />
            )}
          </div>
          {next && isStudent && <Link to={next.to} className="btn-gold mt-4 w-full">{S.passed ? "I'm ready, keep going →" : next.label}</Link>}
        </div>
      </aside>
    </div>
  );
}

function ReadOnlyChat({ msgs }: { msgs: Submission["chat"] }) {
  return (
    <div className="max-h-[520px] space-y-3 overflow-y-auto p-2 scroll-thin">
      {msgs.map((m, i) => (
        <div key={i} className={`rounded-2xl px-3 py-2 text-sm ${m.role === "user" ? "ml-8 bg-jam-green text-white" : "mr-8 bg-[#f7f6fb]"}`}>
          <div className="mb-0.5 text-[11px] font-bold uppercase opacity-60">{m.role === "user" ? "Student" : "FinBuddy"}</div>
          {m.role === "assistant" ? <Markdown className="prose-chat">{m.content}</Markdown> : <div className="whitespace-pre-wrap">{m.content}</div>}
        </div>
      ))}
    </div>
  );
}
