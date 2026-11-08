import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../api";
import { Bar, Empty, ErrorBox, LEVEL_STYLE, Spinner, timeAgo, useLoad } from "../../components/ui";
import type { LearningPath, User } from "../../types";

interface Report {
  student: User; path: LearningPath;
  submissions: { submission_id: number; quiz_title: string; percent: number; passed: boolean; submitted_at: string; questions_asked: number }[];
  games: { game_slug: string; won: boolean; score: number | null; gained_xp: number; created_at: string }[];
}

export default function StudentReport() {
  const { id } = useParams();
  const nav = useNavigate();
  const { data, error, loading, reload } = useLoad(() => api.get<Report>(`/api/teacher/students/${id}`), [id]);
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;
  const s = data.student;

  return (
    <div className="space-y-6">
      <button onClick={() => nav(-1)} className="text-sm font-semibold text-ink-mute hover:text-ink">← Back</button>
      <div className="flex flex-wrap items-center gap-4 rounded-4xl bg-tile-sun p-6">
        <div className="grid h-16 w-16 place-items-center rounded-full bg-white text-4xl">{s.avatar}</div>
        <div className="min-w-0 flex-1">
          <h1 className="h-page">{s.name}</h1>
          <div className="text-sm text-ink-soft">{s.email}</div>
        </div>
        <div className="flex gap-2">
          <span className="chip bg-white py-2">⭐ {s.xp} XP</span><span className="chip bg-white py-2">🏅 Rank {s.rank}</span><span className="chip bg-white py-2">🔥 {s.streak} days</span>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        {data.path.levels.map((lv) => (
          <div key={lv.slug} className={`rounded-4xl p-5 ${LEVEL_STYLE[lv.slug].tile}`}>
            <div className="flex items-center justify-between"><b>{lv.emoji} {lv.name}</b><span className="text-sm">{lv.completed ? "✅" : lv.unlocked ? "" : "🔒"}</span></div>
            <Bar value={lv.progress} color="bg-ink" className="mt-3 bg-white/60" />
            <ul className="mt-3 space-y-1 text-sm">
              {lv.lessons.map((l) => (
                <li key={l.lesson_id} className="flex justify-between gap-2"><span className="truncate">{l.emoji} {l.title}</span>
                  <span className="shrink-0 font-semibold">{l.best_pct != null ? `${l.best_pct}%` : l.status === "locked" ? "🔒" : "–"}</span></li>
              ))}
              {lv.games.map((g) => <li key={g.slug} className="flex justify-between"><span>{g.emoji} {g.name}</span><span>{g.won ? "🏆" : "–"}</span></li>)}
            </ul>
          </div>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-[1fr_320px]">
        <div>
          <h2 className="mb-3 text-xl font-bold">Quiz attempts</h2>
          {data.submissions.length === 0 ? <Empty icon="📝" title="No quizzes yet" /> : (
            <div className="space-y-2">
              {data.submissions.map((x) => (
                <Link key={x.submission_id} to={`/review/${x.submission_id}`} className="flex items-center gap-3 rounded-3xl border border-black/5 bg-white p-4 hover:border-jam-green">
                  <span className={`chip ${x.passed ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>{x.percent}%</span>
                  <div className="min-w-0 flex-1"><div className="truncate font-semibold">{x.quiz_title}</div><div className="text-xs text-ink-mute">{timeAgo(x.submitted_at)}</div></div>
                  {x.questions_asked > 0 && <span className="chip bg-tile-lilac text-xs">💬 {x.questions_asked} question{x.questions_asked > 1 ? "s" : ""}</span>}
                  <span className="text-ink-mute">→</span>
                </Link>
              ))}
            </div>
          )}
        </div>
        <div>
          <h2 className="mb-3 text-xl font-bold">Games</h2>
          {data.games.length === 0 ? <div className="text-sm text-ink-mute">No games played yet.</div> : (
            <ul className="space-y-2">
              {data.games.map((g, i) => (
                <li key={i} className="flex items-center justify-between rounded-3xl bg-[#f7f6fb] px-4 py-3 text-sm">
                  <span>{g.won ? "🏆" : "🎮"} {g.game_slug.replace(/_/g, " ")}</span><span className="text-ink-mute">{timeAgo(g.created_at)}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </div>
  );
}
