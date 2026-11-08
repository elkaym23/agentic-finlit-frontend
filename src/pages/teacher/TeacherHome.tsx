import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import Mascot from "../../components/Mascot";
import { Empty, ErrorBox, Modal, Spinner, greeting, timeAgo, useLoad } from "../../components/ui";

interface Overview {
  tiles: { students: number; active_week: number; avg_score: number | null; quizzes: number; lessons: number };
  classes: { class_id: number; name: string; code: string; students: number; assignments: number }[];
  recent: { kind: string; item_title: string | null; extra: string | number | null; created_at: string; student_name: string; avatar: string; class_name: string }[];
}
const TILE_BG = ["bg-tile-mint", "bg-tile-sky", "bg-tile-sun", "bg-tile-lilac", "bg-tile-peach", "bg-tile-rose"];

export default function TeacherHome() {
  const { user } = useAuth();
  const nav = useNavigate();
  const { data, error, loading, reload } = useLoad(() => api.get<Overview>("/api/teacher/overview"));
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [err, setErr] = useState<string | null>(null);

  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;

  const create = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const c = await api.post<{ class_id: number }>("/api/teacher/classes", { name });
      setOpen(false); setName(""); nav(`/classes/${c.class_id}`);
    } catch (e: any) { setErr(e.message); }
  };
  const t = data.tiles;

  return (
    <div className="grid gap-6 xl:grid-cols-[1fr_340px]">
      <div className="min-w-0 space-y-6">
        <div className="flex flex-wrap items-end justify-between gap-3">
          <div>
            <h1 className="h-page">{greeting()}, {user?.title} {user?.name}</h1>
            <p className="muted mt-1">Here's how your classes are doing.</p>
          </div>
          <div className="flex gap-2">
            <Link to="/library" className="btn-ghost">📄 Upload a document</Link>
            <button className="btn-green" onClick={() => setOpen(true)}>＋ New class</button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Tile bg="bg-tile-mint" icon="🎒" v={t.students} l="Students" />
          <Tile bg="bg-tile-sun" icon="⚡" v={t.active_week} l="Active this week" />
          <Tile bg="bg-tile-sky" icon="📊" v={t.avg_score != null ? `${t.avg_score}%` : "–"} l="Average score" />
          <Tile bg="bg-tile-lilac" icon="📝" v={t.quizzes} l="Your quizzes" />
        </div>

        <div>
          <h2 className="mb-3 text-xl font-bold">Your classes</h2>
          {data.classes.length === 0 ? (
            <Empty icon="🏫" title="Create your first class">Students join with a 6-letter code. You'll see their lessons, quiz scores and a class leaderboard.</Empty>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2">
              {data.classes.map((c, i) => (
                <Link key={c.class_id} to={`/classes/${c.class_id}`} className={`rounded-4xl p-5 transition hover:-translate-y-1 ${TILE_BG[i % TILE_BG.length]}`}>
                  <div className="flex items-start justify-between">
                    <div className="grid h-12 w-12 place-items-center rounded-2xl bg-white/70 text-2xl">🏫</div>
                    <span className="chip bg-white/80 font-mono tracking-widest">{c.code}</span>
                  </div>
                  <div className="mt-4 text-xl font-bold">{c.name}</div>
                  <div className="text-sm text-ink-soft">{c.students} student{c.students === 1 ? "" : "s"} · {c.assignments} assignment{c.assignments === 1 ? "" : "s"}</div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      <aside className="space-y-4">
        <div className="rounded-4xl bg-ink p-5 text-white">
          <div className="flex items-center gap-3"><Mascot size={60} /><div><div className="font-bold">Quiz from any document</div><div className="text-sm text-white/70">PDF, Word or text</div></div></div>
          <p className="mt-3 text-sm text-white/80">Upload a reading and Casheous turns it into a lesson and a quiz you can edit, then assign it to a class.</p>
          <Link to="/library" className="btn-gold mt-4 w-full">Go to Lessons & Quizzes</Link>
        </div>
        <div className="rounded-4xl border border-black/5 p-5">
          <h2 className="mb-3 font-bold">Recent activity</h2>
          {data.recent.length === 0 ? <div className="text-sm text-ink-mute">Nothing yet. Activity shows up when students do lessons, quizzes and games.</div> : (
            <ul className="space-y-3">
              {data.recent.map((r, i) => (
                <li key={i} className="flex gap-3 text-sm">
                  <span className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-tile-sun text-lg">{r.avatar}</span>
                  <div className="min-w-0">
                    <div><b>{r.student_name}</b> {verb(r.kind, r.extra)} <b>{r.item_title ?? ""}</b>{r.kind !== "lesson" && r.extra != null ? ` (${r.extra})` : ""}</div>
                    <div className="text-xs text-ink-mute">{r.class_name} · {timeAgo(r.created_at)}</div>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </div>
      </aside>

      <Modal open={open} onClose={() => setOpen(false)} title="New class">
        <form onSubmit={create} className="space-y-4">
          <div><label className="label">Class name</label>
            <input className="input" autoFocus required value={name} onChange={(e) => setName(e.target.value)} placeholder="Grade 5 Blue" maxLength={80} /></div>
          {err && <div className="text-sm text-rose-700">{err}</div>}
          <button className="btn-green w-full">Create class</button>
        </form>
      </Modal>
    </div>
  );
}

export function verb(kind: string, extra?: unknown) {
  if (kind === "lesson") return extra === "completed" ? "finished" : "started";
  return ({ quiz: "took", game: "played" } as Record<string, string>)[kind] ?? kind;
}

function Tile({ bg, icon, v, l }: { bg: string; icon: string; v: number | string; l: string }) {
  return <div className={`rounded-3xl p-4 ${bg}`}><div className="text-xl">{icon}</div><div className="mt-1 text-2xl font-extrabold">{v}</div><div className="text-xs font-medium text-ink-soft">{l}</div></div>;
}
