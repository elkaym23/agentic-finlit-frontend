import { Link } from "react-router-dom";
import { api } from "../../api";
import { ErrorBox, LEVEL_STYLE, Spinner, useLoad } from "../../components/ui";
import type { LearningPath } from "../../types";

export default function Games() {
  const { data, error, loading, reload } = useLoad(() => api.get<LearningPath>("/api/learn/path"));
  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;
  return (
    <div>
      <h1 className="h-page">Games</h1>
      <p className="muted mt-1">Each level has its own game. Pass all the lessons in a level to unlock it, then win it to move on!</p>
      <div className="mt-6 grid gap-5 md:grid-cols-2">
        {data.levels.flatMap((lv) => lv.games.map((g) => {
          const locked = g.status === "locked";
          const s = LEVEL_STYLE[lv.slug];
          const card = (
            <div className={`flex h-full flex-col rounded-4xl p-6 transition ${s.tile} ${locked ? "opacity-60" : "hover:-translate-y-1 hover:shadow-card"}`}>
              <div className="flex items-start justify-between">
                <div className={`grid h-20 w-20 place-items-center rounded-4xl bg-white text-5xl shadow-card ${locked ? "grayscale" : ""}`}>{g.emoji}</div>
                <span className="chip bg-white/80">{g.won ? "🏆 Won" : locked ? "🔒 Locked" : "Ready to play"}</span>
              </div>
              <div className={`mt-5 text-xs font-bold uppercase tracking-wider ${s.text}`}>{lv.emoji} {lv.name}</div>
              <div className="text-2xl font-bold">{g.name}</div>
              <p className="mt-1 flex-1 text-sm text-ink-soft">{g.blurb}</p>
              <div className="mt-4">{locked ? <span className="text-sm font-medium">Finish the {lv.name} lessons first</span>
                : <span className="btn-dark">{g.won ? "Play again" : "Play"} →</span>}</div>
            </div>
          );
          return locked ? <div key={g.slug}>{card}</div> : <Link key={g.slug} to={`/games/${g.slug}`}>{card}</Link>;
        }))}
      </div>
    </div>
  );
}
