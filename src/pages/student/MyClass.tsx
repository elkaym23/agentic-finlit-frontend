import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import { Empty, ErrorBox, LevelChip, Spinner, useLoad } from "../../components/ui";
import type { LeaderRow, MyClass as TClass } from "../../types";

export default function MyClass() {
  const { data, error, loading, reload } = useLoad(() => api.get<TClass[]>("/api/classes/mine"));
  const [code, setCode] = useState("");
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  const [sel, setSel] = useState<number | null>(null);

  const join = async (e: React.FormEvent) => {
    e.preventDefault();
    setMsg(null);
    try {
      const r = await api.post<{ class_id: number; name: string }>("/api/classes/join", { code });
      setMsg({ ok: true, text: `You joined ${r.name}! 🎉` });
      setCode("");
      setSel(r.class_id);
      reload();
    } catch (e: any) { setMsg({ ok: false, text: e.message }); }
  };

  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;
  const cls = data.find((c) => c.class_id === sel) ?? data[0];

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="h-page">My class</h1>
          <p className="muted mt-1">See what your teacher assigned and how you rank.</p>
        </div>
        <form onSubmit={join} className="flex gap-2">
          <input className="input w-40 uppercase tracking-widest" value={code} onChange={(e) => setCode(e.target.value)} placeholder="CLASS CODE" maxLength={10} required aria-label="Class code" />
          <button className="btn-dark">Join</button>
        </form>
      </div>
      {msg && <div className={`rounded-2xl px-4 py-3 text-sm font-medium ${msg.ok ? "bg-emerald-50 text-emerald-700" : "bg-rose-50 text-rose-700"}`}>{msg.text}</div>}

      {!cls ? (
        <Empty icon="🏫" title="You're not in a class yet">Ask your teacher for the class code and type it above.</Empty>
      ) : (
        <>
          {data.length > 1 && (
            <div className="flex flex-wrap gap-2">
              {data.map((c) => (
                <button key={c.class_id} onClick={() => setSel(c.class_id)} className={`chip py-2 ${c.class_id === cls.class_id ? "bg-ink text-white" : "bg-black/5"}`}>{c.name}</button>
              ))}
            </div>
          )}
          <div className="grid gap-6 lg:grid-cols-[1fr_380px]">
            <div className="min-w-0 space-y-4">
              <div className="rounded-4xl bg-tile-sky p-6">
                <div className="text-sm text-ink-mute">{cls.teacher_name}'s class</div>
                <div className="text-2xl font-bold">{cls.name}</div>
                <div className="mt-2 text-sm">You're <b>#{cls.my_position ?? "–"}</b> of {cls.size} students</div>
              </div>
              <h2 className="text-xl font-bold">Assignments</h2>
              {cls.assignments.length === 0 ? <Empty icon="📭" title="Nothing assigned yet">Keep going on your learning path!</Empty> : (
                <div className="space-y-2">
                  {cls.assignments.map((a) => {
                    const done = a.best_pct != null && a.best_pct >= 60;
                    return (
                      <Link key={a.assignment_id} to={a.lesson_id ? `/lesson/${a.lesson_id}` : `/quiz/${a.quiz_id}`}
                            className="flex items-center gap-4 rounded-3xl border border-black/5 bg-white p-4 transition hover:border-jam-green">
                        <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-tile-peach text-2xl">{a.lesson_id ? "📖" : "📝"}</div>
                        <div className="min-w-0 flex-1">
                          <div className="truncate font-semibold">{a.title}</div>
                          <div className="flex flex-wrap items-center gap-2 text-sm text-ink-mute">
                            <LevelChip level={a.level} />
                            {a.due_at && <span>Due {new Date(a.due_at).toLocaleDateString()}</span>}
                            {a.attempts > 0 && <span>{a.attempts} attempt{a.attempts > 1 ? "s" : ""}</span>}
                          </div>
                        </div>
                        {a.best_pct != null && <span className={`chip ${done ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>{a.best_pct}%</span>}
                        <span className="text-xl">{done ? "✅" : "→"}</span>
                      </Link>
                    );
                  })}
                </div>
              )}
              <button className="text-sm font-medium text-ink-mute hover:text-rose-600" onClick={async () => {
                if (!confirm(`Leave ${cls.name}?`)) return;
                await api.del(`/api/classes/${cls.class_id}/leave`); setSel(null); reload();
              }}>Leave this class</button>
            </div>
            <Leaderboard classId={cls.class_id} />
          </div>
        </>
      )}
    </div>
  );
}

export function Leaderboard({ classId, rows: given }: { classId?: number; rows?: LeaderRow[] }) {
  const { user } = useAuth();
  const { data } = useLoad(() => given ? Promise.resolve(given) : api.get<LeaderRow[]>(`/api/classes/${classId}/leaderboard`), [classId, given]);
  const rows = data ?? [];
  const medal = (p: number) => (p === 1 ? "🥇" : p === 2 ? "🥈" : p === 3 ? "🥉" : `#${p}`);
  return (
    <div className="rounded-4xl bg-ink p-5 text-white">
      <h2 className="mb-4 text-lg font-bold">🏆 Leaderboard</h2>
      {rows.length === 0 ? <div className="text-sm text-white/60">No students yet.</div> : (
        <ol className="space-y-2">
          {rows.map((r) => (
            <li key={r.user_id} className={`flex items-center gap-3 rounded-3xl px-3 py-2.5 ${r.user_id === user?.user_id ? "bg-jam-gold text-ink" : "bg-white/10"}`}>
              <span className="w-8 text-center font-bold">{medal(r.position)}</span>
              <span className="grid h-9 w-9 place-items-center rounded-full bg-white text-xl">{r.avatar}</span>
              <div className="min-w-0 flex-1">
                <div className="truncate font-semibold">{r.name}{r.user_id === user?.user_id ? " (you)" : ""}</div>
                <div className="text-xs opacity-70">{r.lessons_done} lessons · {r.games_won} games{r.streak ? ` · 🔥${r.streak}` : ""}</div>
              </div>
              <span className="font-bold">{r.xp} XP</span>
            </li>
          ))}
        </ol>
      )}
    </div>
  );
}
