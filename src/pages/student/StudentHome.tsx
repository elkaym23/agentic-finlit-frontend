import { Link } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import Mascot from "../../components/Mascot";
import { Bar, ErrorBox, LEVEL_STYLE, Spinner, greeting, useLoad } from "../../components/ui";
import type { LearningPath, MyClass, NextStep } from "../../types";

export function nextLink(n: NextStep | null | undefined): { to: string; label: string } | null {
  if (!n) return null;
  if (n.type === "lesson") return { to: `/lesson/${n.lesson_id}`, label: n.title };
  if (n.type === "game") return { to: `/games/${n.slug}`, label: n.title };
  if (n.type === "retry" && n.lesson_id) return { to: `/lesson/${n.lesson_id}`, label: "Try the lesson again" };
  if (n.type === "retry" && n.quiz_id) return { to: `/quiz/${n.quiz_id}`, label: "Try the quiz again" };
  if (n.type === "class") return { to: "/class", label: "Back to my class" };
  return { to: "/learn", label: "My learning path" };
}

const TIPS = [
  "Put some of every JA$1000 you get into savings before you spend. Pay yourself first!",
  "Before you buy something, ask: is it a need or a want?",
  "Compare prices at two shops before you buy. That's being a smart spender.",
  "Never share your bank PIN, not even with a friend.",
  "Small savings add up: JA$100 a week is JA$5,200 in a year!",
];

export default function StudentHome() {
  const { user } = useAuth();
  const path = useLoad(() => api.get<LearningPath>("/api/learn/path"));
  const classes = useLoad(() => api.get<MyClass[]>("/api/classes/mine"));
  if (!user) return null;
  if (path.loading) return <Spinner label="Getting your lessons…" />;
  if (path.error || !path.data) return <ErrorBox error={path.error || "Couldn't load"} onRetry={path.reload} />;

  const p = path.data;
  const allLessons = p.levels.flatMap((l) => l.lessons);
  const done = allLessons.filter((l) => l.status === "completed").length;
  const cont = nextLink(p.continue);
  const current = p.levels.find((l) => l.slug === p.current_level) ?? p.levels[0];
  const tip = TIPS[new Date().getDate() % TIPS.length];
  const pending = (classes.data ?? []).flatMap((c) => c.assignments.map((a) => ({ ...a, cls: c.name })))
    .filter((a) => a.lesson_status !== "completed" && !(a.best_pct != null && a.best_pct >= 60)).slice(0, 3);

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_320px]">
      <div className="min-w-0 space-y-6">
        <div>
          <h1 className="h-page">{greeting()}, {user.name} {user.avatar}</h1>
          <p className="muted mt-1">Wah gwaan! Ready to grow your money smarts today?</p>
        </div>

        {/* continue card */}
        <div className="relative overflow-hidden rounded-4xl bg-jam-green p-6 text-white sm:p-8">
          <div className="absolute -right-10 -top-10 h-48 w-48 rounded-full bg-jam-gold/30" />
          <div className="absolute -bottom-16 right-24 h-40 w-40 rounded-full bg-white/10" />
          <div className="relative flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">
            <div>
              <div className="text-sm font-semibold uppercase tracking-wider text-jam-gold">
                {p.graduated ? "You did it!" : "Continue learning"}
              </div>
              <div className="mt-1 text-2xl font-bold sm:text-3xl">
                {p.graduated ? "Money Master graduate 🎓" : cont?.label}
              </div>
              <div className="mt-4 flex items-center gap-3">
                <Bar value={(done / Math.max(1, allLessons.length)) * 100} color="bg-jam-gold" className="w-48 bg-white/20" />
                <span className="text-sm text-white/80">{done}/{allLessons.length} lessons</span>
              </div>
            </div>
            {cont && !p.graduated && <Link to={cont.to} className="btn-gold shrink-0 px-6 py-3 text-lg">Let's go →</Link>}
            {p.graduated && <Link to="/games" className="btn-gold shrink-0">Play games</Link>}
          </div>
        </div>

        {/* levels */}
        <div>
          <div className="mb-3 flex items-end justify-between">
            <h2 className="text-xl font-bold">Your levels</h2>
            <Link to="/learn" className="text-sm font-semibold text-jam-green hover:underline">See path →</Link>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {p.levels.map((lv) => {
              const s = LEVEL_STYLE[lv.slug];
              return (
                <Link key={lv.slug} to="/learn" className={`group relative rounded-4xl p-5 transition hover:-translate-y-1 ${s.tile} ${!lv.unlocked ? "opacity-60" : ""}`}>
                  <div className="flex items-start justify-between">
                    <div className="grid h-14 w-14 place-items-center rounded-3xl bg-white/70 text-3xl">{lv.emoji}</div>
                    <span className="chip bg-white/70 text-xs">{lv.completed ? "✅ Done" : lv.unlocked ? lv.ages : "🔒 Locked"}</span>
                  </div>
                  <div className="mt-4 text-lg font-bold">{lv.name}</div>
                  <div className="mt-1 line-clamp-2 text-sm text-ink-soft">{lv.blurb}</div>
                  <div className="mt-4 flex items-center gap-2">
                    <Bar value={lv.progress} color="bg-ink" className="bg-white/60" />
                    <span className="text-xs font-bold">{lv.progress}%</span>
                  </div>
                </Link>
              );
            })}
          </div>
        </div>

        {/* class to-dos */}
        {pending.length > 0 && (
          <div>
            <h2 className="mb-3 text-xl font-bold">From your teacher</h2>
            <div className="space-y-2">
              {pending.map((a) => (
                <Link key={a.assignment_id} to={a.lesson_id ? `/lesson/${a.lesson_id}` : `/quiz/${a.quiz_id}`}
                      className="flex items-center gap-4 rounded-3xl border border-black/5 bg-white p-4 transition hover:border-jam-green">
                  <div className="grid h-12 w-12 place-items-center rounded-2xl bg-tile-peach text-2xl">{a.lesson_id ? "📖" : "📝"}</div>
                  <div className="min-w-0 flex-1">
                    <div className="truncate font-semibold">{a.title}</div>
                    <div className="text-sm text-ink-mute">{a.cls}{a.due_at ? ` · due ${new Date(a.due_at).toLocaleDateString()}` : ""}</div>
                  </div>
                  <span className="btn-dark btn-sm">Start</span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* right rail: mascot + stats */}
      <aside className="space-y-4">
        <div className="relative overflow-hidden rounded-4xl bg-ink p-6 text-white">
          <div className="absolute -right-6 -top-6 h-28 w-28 rounded-full bg-jam-green/40" />
          <div className="relative flex items-center gap-3">
            <div className="animate-bob"><Mascot size={84} mood="happy" /></div>
            <div>
              <div className="text-lg font-bold">FinBuddy</div>
              <div className="text-sm text-white/70">Your doctor-bird tutor</div>
            </div>
          </div>
          <div className="relative mt-4 rounded-3xl bg-white/10 p-4 text-sm leading-relaxed">💡 {tip}</div>
          <Link to="/tutor" className="btn-gold relative mt-4 w-full">Ask FinBuddy a question</Link>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <Stat bg="bg-tile-sun" icon="⭐" value={user.xp} label="Total XP" />
          <Stat bg="bg-tile-peach" icon="🔥" value={user.streak} label="Day streak" />
          <Stat bg="bg-tile-mint" icon="📚" value={done} label="Lessons done" />
          <Stat bg="bg-tile-lilac" icon="🏅" value={user.rank} label="Rank" />
        </div>

        <div className="rounded-4xl border border-black/5 p-5">
          <div className="flex items-center justify-between text-sm font-semibold">
            <span>Rank {user.rank}</span><span className="text-ink-mute">{user.xp_into_rank}/{user.xp_per_rank} XP</span>
          </div>
          <Bar value={(user.xp_into_rank / user.xp_per_rank) * 100} color="bg-jam-gold" className="mt-2" />
          <div className="mt-2 text-xs text-ink-mute">Now on {current.emoji} {current.name}</div>
        </div>

        {(classes.data ?? []).slice(0, 1).map((c) => (
          <Link key={c.class_id} to="/class" className="block rounded-4xl bg-tile-sky p-5 transition hover:-translate-y-0.5">
            <div className="text-sm text-ink-mute">{c.name}</div>
            <div className="mt-1 text-2xl font-bold">#{c.my_position ?? "–"} <span className="text-base font-medium text-ink-mute">of {c.size}</span></div>
            <div className="text-sm font-semibold text-sky-800">View leaderboard →</div>
          </Link>
        ))}
        {classes.data && classes.data.length === 0 && (
          <Link to="/class" className="block rounded-4xl border-2 border-dashed border-black/10 p-5 text-center text-sm text-ink-mute hover:border-jam-green">
            🏫 Got a class code from your teacher? <b className="text-jam-green">Join your class</b>
          </Link>
        )}
      </aside>
    </div>
  );
}

function Stat({ bg, icon, value, label }: { bg: string; icon: string; value: number | string; label: string }) {
  return (
    <div className={`rounded-3xl p-4 ${bg}`}>
      <div className="text-xl">{icon}</div>
      <div className="mt-1 text-2xl font-extrabold">{value}</div>
      <div className="text-xs font-medium text-ink-soft">{label}</div>
    </div>
  );
}
