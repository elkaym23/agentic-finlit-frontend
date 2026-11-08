import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../api";
import { Empty, ErrorBox, LEVEL_STYLE, LevelChip, Modal, Spinner, timeAgo, useLoad } from "../../components/ui";
import type { LeaderRow, LevelSlug } from "../../types";
import { Leaderboard } from "../student/MyClass";

type Cell = { best: number | null; attempts: number; passed: boolean; submission_id: number };
interface ClassDetail {
  class: { class_id: number; name: string; code: string };
  students: { user_id: number; name: string; email: string; avatar: string; level_slug: LevelSlug; xp: number; rank: number;
    streak: number; last_active: string | null; cells: Record<string, Cell>; core_done: number; avg_score: number | null }[];
  core: { lesson_id: number; quiz_id: number; title: string; emoji: string; level: LevelSlug; pass_pct: number }[];
  assignments: { assignment_id: number; lesson_id: number | null; quiz_id: number | null; title: string; level: LevelSlug;
    kind: "lesson" | "quiz"; due_at: string | null; completed: number; avg_score: number | null }[];
  leaderboard: LeaderRow[];
}

export default function ClassPage() {
  const { id } = useParams();
  const nav = useNavigate();
  const { data, error, loading, reload } = useLoad(() => api.get<ClassDetail>(`/api/teacher/classes/${id}`), [id]);
  const [tab, setTab] = useState<"progress" | "assignments" | "leaderboard">("progress");
  const [view, setView] = useState<"assigned" | LevelSlug>("beginner");
  const [rename, setRename] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  if (loading) return <Spinner />;
  if (error || !data) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;
  const c = data.class;

  const cols = view === "assigned"
    ? data.assignments.map((a) => ({ key: `a${a.assignment_id}`, title: a.title, emoji: a.kind === "lesson" ? "📖" : "📝" }))
    : data.core.filter((x) => x.level === view).map((x) => ({ key: String(x.quiz_id), title: x.title, emoji: x.emoji }));

  const copy = () => { navigator.clipboard?.writeText(c.code); setCopied(true); setTimeout(() => setCopied(false), 1500); };
  const removeStudent = async (sid: number, name: string) => {
    if (!confirm(`Remove ${name} from ${c.name}? Their progress is kept.`)) return;
    await api.del(`/api/teacher/classes/${c.class_id}/students/${sid}`); reload();
  };
  const unassign = async (aid: number) => {
    if (!confirm("Remove this assignment from the class?")) return;
    await api.del(`/api/teacher/assignments/${aid}`); reload();
  };

  return (
    <div className="space-y-6">
      <Link to="/" className="text-sm font-semibold text-ink-mute hover:text-ink">← Dashboard</Link>
      <div className="flex flex-wrap items-center justify-between gap-4 rounded-4xl bg-tile-mint p-6">
        <div>
          <div className="text-sm text-ink-mute">Class</div>
          <h1 className="h-page">{c.name}</h1>
          <div className="mt-1 text-sm">{data.students.length} students · {data.assignments.length} assignments</div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button onClick={copy} className="rounded-3xl bg-white px-5 py-3 text-left shadow-card" title="Copy code">
            <div className="text-xs text-ink-mute">Join code {copied ? "· copied!" : "· tap to copy"}</div>
            <div className="font-mono text-2xl font-extrabold tracking-[0.3em]">{c.code}</div>
          </button>
          <Link to="/library" className="btn-green">＋ Assign work</Link>
          <button className="btn-ghost btn-sm" onClick={() => setRename(c.name)}>Rename</button>
          <button className="btn-ghost btn-sm text-rose-600" onClick={async () => {
            if (!confirm(`Delete ${c.name}? Students stay registered but leave this class.`)) return;
            await api.del(`/api/teacher/classes/${c.class_id}`); nav("/");
          }}>Delete</button>
        </div>
      </div>

      <div className="flex gap-1 rounded-full bg-black/5 p-1 sm:w-fit">
        {(["progress", "assignments", "leaderboard"] as const).map((t) => (
          <button key={t} onClick={() => setTab(t)} className={`flex-1 rounded-full px-5 py-2 text-sm font-semibold capitalize transition ${tab === t ? "bg-white shadow-sm" : "text-ink-mute"}`}>{t}</button>
        ))}
      </div>

      {tab === "progress" && (data.students.length === 0 ? (
        <Empty icon="🎒" title="No students yet">Give your students the code <b className="font-mono">{c.code}</b>. They enter it when they sign up or on their "My Class" page.</Empty>
      ) : (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {(["beginner", "intermediate", "advanced"] as const).map((l) => (
              <button key={l} onClick={() => setView(l)} className={`chip py-2 ${view === l ? "bg-ink text-white" : LEVEL_STYLE[l].chip}`}>{LEVEL_STYLE[l].label} lessons</button>
            ))}
            <button onClick={() => setView("assigned")} className={`chip py-2 ${view === "assigned" ? "bg-ink text-white" : "bg-tile-peach"}`}>Assigned work</button>
          </div>
          <div className="overflow-x-auto rounded-3xl border border-black/5 scroll-thin">
            <table className="w-full min-w-[640px] text-sm">
              <thead className="bg-[#f7f6fb] text-left text-xs uppercase tracking-wider text-ink-mute">
                <tr>
                  <th className="sticky left-0 bg-[#f7f6fb] p-3">Student</th>
                  <th className="p-3">XP</th>
                  <th className="p-3">Avg</th>
                  {cols.map((col) => <th key={col.key} className="max-w-[120px] p-3 font-semibold normal-case" title={col.title}><div className="truncate">{col.emoji} {col.title}</div></th>)}
                  <th className="p-3" />
                </tr>
              </thead>
              <tbody>
                {data.students.map((s) => (
                  <tr key={s.user_id} className="border-t border-black/5 hover:bg-black/[0.015]">
                    <td className="sticky left-0 bg-white p-3">
                      <Link to={`/students/${s.user_id}`} className="flex items-center gap-2 font-semibold hover:text-jam-green">
                        <span className="grid h-8 w-8 place-items-center rounded-full bg-tile-sun">{s.avatar}</span>
                        <span><span className="block">{s.name}</span><span className="block text-xs font-normal text-ink-mute">{timeAgo(s.last_active)}{s.streak ? ` · 🔥${s.streak}` : ""}</span></span>
                      </Link>
                    </td>
                    <td className="p-3 font-semibold">{s.xp}</td>
                    <td className="p-3">{s.avg_score != null ? `${s.avg_score}%` : "–"}</td>
                    {cols.map((col) => {
                      const cell = s.cells[col.key];
                      return (
                        <td key={col.key} className="p-3">
                          {cell ? (
                            <Link to={`/review/${cell.submission_id}`} title={`${cell.attempts} attempt(s)`}
                                  className={`chip ${cell.passed ? "bg-emerald-100 text-emerald-800" : "bg-amber-100 text-amber-800"}`}>
                              {cell.passed ? "✓" : "↻"} {cell.best}%
                            </Link>
                          ) : <span className="text-ink-mute">–</span>}
                        </td>
                      );
                    })}
                    <td className="p-3 text-right"><button className="text-xs text-ink-mute hover:text-rose-600" onClick={() => removeStudent(s.user_id, s.name)}>Remove</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {cols.length === 0 && <div className="text-sm text-ink-mute">Nothing assigned yet. Go to Lessons & Quizzes to assign work.</div>}
          <div className="text-xs text-ink-mute">✓ passed · ↻ tried, not passed yet · tap a score to see their answers and FinBuddy chat</div>
        </div>
      ))}

      {tab === "assignments" && (data.assignments.length === 0 ? (
        <Empty icon="📭" title="No assignments yet"><Link className="font-semibold text-jam-green" to="/library">Upload a document or pick a quiz</Link> to assign it.</Empty>
      ) : (
        <div className="space-y-2">
          {data.assignments.map((a) => (
            <div key={a.assignment_id} className="flex flex-wrap items-center gap-4 rounded-3xl border border-black/5 bg-white p-4">
              <div className="grid h-12 w-12 place-items-center rounded-2xl bg-tile-peach text-2xl">{a.kind === "lesson" ? "📖" : "📝"}</div>
              <div className="min-w-0 flex-1">
                <div className="font-semibold">{a.title}</div>
                <div className="flex flex-wrap items-center gap-2 text-sm text-ink-mute"><LevelChip level={a.level} />{a.due_at && <span>Due {new Date(a.due_at).toLocaleDateString()}</span>}</div>
              </div>
              <div className="text-sm"><b>{a.completed}</b>/{data.students.length} done{a.avg_score != null && <> · avg <b>{a.avg_score}%</b></>}</div>
              {a.quiz_id && <Link className="btn-ghost btn-sm" to={a.kind === "lesson" ? `/lesson/${a.lesson_id}` : `/quizzes/${a.quiz_id}/edit`}>View</Link>}
              <button className="btn-ghost btn-sm text-rose-600" onClick={() => unassign(a.assignment_id)}>Remove</button>
            </div>
          ))}
        </div>
      ))}

      {tab === "leaderboard" && <div className="max-w-xl"><Leaderboard rows={data.leaderboard} /></div>}

      <Modal open={rename !== null} onClose={() => setRename(null)} title="Rename class">
        <form className="space-y-4" onSubmit={async (e) => {
          e.preventDefault(); await api.patch(`/api/teacher/classes/${c.class_id}`, { name: rename }); setRename(null); reload();
        }}>
          <input className="input" autoFocus required maxLength={80} value={rename ?? ""} onChange={(e) => setRename(e.target.value)} />
          <button className="btn-green w-full">Save</button>
        </form>
      </Modal>
    </div>
  );
}
