import { Link } from "react-router-dom";
import { api } from "../../api";
import { ErrorBox, LEVEL_STYLE, Ring, Spinner, useLoad } from "../../components/ui";
import type { LearningPath, PathGame, PathLesson } from "../../types";

export default function LearnPath() {
  const { data, error, loading, reload } = useLoad(() => api.get<LearningPath>("/api/learn/path"));
  if (loading) return <Spinner label="Drawing your map…" />;
  if (error || !data) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;

  return (
    <div className="space-y-8">
      <div>
        <h1 className="h-page">Your learning path</h1>
        <p className="muted mt-1">Read a lesson → take the quiz → chat with FinBuddy → next lesson. Finish a level to unlock its game!</p>
      </div>

      {data.levels.map((lv) => {
        const s = LEVEL_STYLE[lv.slug];
        return (
          <section key={lv.slug} className={`rounded-5xl p-5 sm:p-7 ${s.tile} ${!lv.unlocked ? "opacity-70" : ""}`}>
            <div className="flex flex-wrap items-center gap-4">
              <div className="grid h-16 w-16 place-items-center rounded-3xl bg-white text-4xl shadow-card">{lv.emoji}</div>
              <div className="min-w-0 flex-1">
                <div className={`text-sm font-bold uppercase tracking-wider ${s.text}`}>{s.label} · {lv.ages}</div>
                <h2 className="text-2xl font-bold">{lv.name}</h2>
                <p className="text-sm text-ink-soft">{lv.blurb}</p>
              </div>
              <div className="rounded-full bg-white p-1"><Ring value={lv.progress} color={s.ring} /></div>
            </div>

            {!lv.unlocked && <div className="mt-4 rounded-3xl bg-white/60 px-4 py-3 text-sm font-medium">🔒 Finish the level before this one to unlock it.</div>}

            <ol className="relative mt-6 space-y-3">
              {lv.lessons.map((l, i) => <LessonRow key={l.lesson_id} l={l} n={i + 1} />)}
              {lv.games.map((g) => <GameRow key={g.slug} g={g} />)}
            </ol>
          </section>
        );
      })}
    </div>
  );
}

function LessonRow({ l, n }: { l: PathLesson; n: number }) {
  const locked = l.status === "locked";
  const badge = l.status === "completed" ? "✅" : l.status === "in_progress" ? "▶️" : locked ? "🔒" : "✨";
  const inner = (
    <div className={`flex items-center gap-4 rounded-3xl bg-white p-4 transition ${locked ? "cursor-not-allowed" : "hover:-translate-y-0.5 hover:shadow-card"}`}>
      <div className={`grid h-12 w-12 shrink-0 place-items-center rounded-2xl text-2xl ${locked ? "bg-black/5 grayscale" : "bg-tile-sun"}`}>{l.emoji}</div>
      <div className="min-w-0 flex-1">
        <div className="text-xs font-semibold text-ink-mute">Lesson {n} · {l.minutes} min</div>
        <div className="truncate font-bold">{l.title}</div>
        <div className="truncate text-sm text-ink-mute">{l.description}</div>
      </div>
      {l.best_pct != null && <span className={`chip ${l.best_pct >= l.pass_pct ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>{l.best_pct}%</span>}
      <span className="text-xl" aria-label={l.status}>{badge}</span>
    </div>
  );
  return <li>{locked ? inner : <Link to={`/lesson/${l.lesson_id}`}>{inner}</Link>}</li>;
}

function GameRow({ g }: { g: PathGame }) {
  const locked = g.status === "locked";
  const inner = (
    <div className={`flex items-center gap-4 rounded-3xl border-2 border-dashed p-4 transition ${locked ? "border-black/10 bg-white/40" : "border-jam-green bg-white hover:-translate-y-0.5 hover:shadow-card"}`}>
      <div className={`grid h-12 w-12 shrink-0 place-items-center rounded-2xl text-2xl ${locked ? "bg-black/5 grayscale" : "bg-jam-gold"}`}>{g.emoji}</div>
      <div className="min-w-0 flex-1">
        <div className="text-xs font-semibold uppercase tracking-wider text-jam-green">Level game</div>
        <div className="font-bold">{g.name}</div>
        <div className="truncate text-sm text-ink-mute">{locked ? "Pass every lesson above to unlock" : g.blurb}</div>
      </div>
      <span className="text-xl">{g.won ? "🏆" : locked ? "🔒" : "🎮"}</span>
    </div>
  );
  return <li>{locked ? inner : <Link to={`/games/${g.slug}`}>{inner}</Link>}</li>;
}
