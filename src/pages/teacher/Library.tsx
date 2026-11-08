import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { api } from "../../api";
import Mascot from "../../components/Mascot";
import { Empty, ErrorBox, LevelChip, Modal, Spinner, timeAgo, useLoad } from "../../components/ui";
import type { LevelSlug } from "../../types";

interface Lib {
  lessons: { lesson_id: number; title: string; description: string | null; level: LevelSlug; doc_name: string | null; created_at: string; sections: number; quiz_id: number | null }[];
  quizzes: { quiz_id: number; title: string; level: LevelSlug; lesson_id: number | null; lesson_title: string | null; items: number; assigned: number; updated_at: string }[];
  core: { level: LevelSlug; level_name: string; lessons: { lesson_id: number; title: string; emoji: string; quiz_id: number }[] }[];
}
type Target = { lesson_id?: number; quiz_id?: number; title: string };
const LEVELS: { v: LevelSlug; l: string }[] = [{ v: "beginner", l: "Beginner (7–8)" }, { v: "intermediate", l: "Intermediate (9–10)" }, { v: "advanced", l: "Advanced (11–12)" }];

export default function Library() {
  const nav = useNavigate();
  const lib = useLoad(() => api.get<Lib>("/api/teacher/library"));
  const [mode, setMode] = useState<"upload" | "topic">("upload");
  const [assign, setAssign] = useState<Target | null>(null);

  if (lib.loading) return <Spinner />;
  if (lib.error || !lib.data) return <ErrorBox error={lib.error || "Couldn't load"} onRetry={lib.reload} />;
  const L = lib.data;

  const blank = async () => {
    const r = await api.post<{ quiz_id: number }>("/api/teacher/quizzes", { title: "New quiz", level: "beginner",
      items: [{ kind: "mcq", question: "Type your question here", options: ["Option A", "Option B", "Option C", "Option D"], answer_key: "A" }] });
    nav(`/quizzes/${r.quiz_id}/edit`);
  };
  const del = async (kind: "quizzes" | "lessons", id: number, title: string) => {
    if (!confirm(`Delete "${title}"? Students lose access to it.`)) return;
    await api.del(`/api/teacher/${kind}/${id}`); lib.reload();
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="h-page">Lessons & Quizzes</h1>
        <p className="muted mt-1">Turn any document or topic into a quiz, edit it, then assign it to your classes.</p>
      </div>

      {/* creator */}
      <div className="rounded-5xl bg-ink p-5 text-white sm:p-7">
        <div className="flex flex-wrap items-center gap-4">
          <Mascot size={64} mood="think" />
          <div className="min-w-0 flex-1">
            <div className="text-xl font-bold">Create with Casheous</div>
            <div className="text-sm text-white/70">Any subject works, not just money.</div>
          </div>
          <div className="flex rounded-full bg-white/10 p-1">
            {(["upload", "topic"] as const).map((m) => (
              <button key={m} onClick={() => setMode(m)} className={`rounded-full px-4 py-2 text-sm font-semibold ${mode === m ? "bg-jam-gold text-ink" : "text-white/70"}`}>
                {m === "upload" ? "📄 From a document" : "💡 From a topic"}
              </button>
            ))}
          </div>
        </div>
        <div className="mt-5 rounded-4xl bg-white p-5 text-ink">
          {mode === "upload" ? <UploadForm onDone={(r) => { lib.reload(); nav(`/quizzes/${r.quiz_id}/edit?new=1`); }} />
                             : <TopicForm onDone={(r) => { lib.reload(); nav(`/quizzes/${r.quiz_id}/edit?new=1`); }} />}
        </div>
        <button onClick={blank} className="mt-3 text-sm font-semibold text-white/70 hover:text-white">or start a blank quiz and write it yourself →</button>
      </div>

      {/* my quizzes */}
      <section>
        <h2 className="mb-3 text-xl font-bold">My quizzes</h2>
        {L.quizzes.length === 0 ? <Empty icon="📝" title="No quizzes yet">Upload a document or type a topic above.</Empty> : (
          <div className="grid gap-3 md:grid-cols-2">
            {L.quizzes.map((q) => (
              <div key={q.quiz_id} className="flex flex-col rounded-4xl border border-black/5 bg-white p-5">
                <div className="flex items-start gap-3">
                  <div className="grid h-12 w-12 shrink-0 place-items-center rounded-2xl bg-tile-lilac text-2xl">📝</div>
                  <div className="min-w-0 flex-1">
                    <div className="font-bold leading-tight">{q.title}</div>
                    <div className="mt-1 flex flex-wrap items-center gap-2 text-xs text-ink-mute"><LevelChip level={q.level} />{q.items} questions · edited {timeAgo(q.updated_at)}</div>
                    {q.lesson_title && <div className="mt-1 text-xs text-ink-mute">📖 With lesson: {q.lesson_title}</div>}
                  </div>
                </div>
                <div className="mt-4 flex flex-wrap gap-2">
                  <Link to={`/quizzes/${q.quiz_id}/edit`} className="btn-dark btn-sm">Edit</Link>
                  <button className="btn-green btn-sm" onClick={() => setAssign({ quiz_id: q.quiz_id, title: q.title })}>Assign</button>
                  {q.assigned > 0 && <span className="chip bg-emerald-50 text-xs text-emerald-700">Assigned ×{q.assigned}</span>}
                  <button className="ml-auto text-xs text-ink-mute hover:text-rose-600" onClick={() => del("quizzes", q.quiz_id, q.title)}>Delete</button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* my lessons */}
      {L.lessons.length > 0 && (
        <section>
          <h2 className="mb-3 text-xl font-bold">My lessons <span className="text-sm font-normal text-ink-mute">(from uploaded documents)</span></h2>
          <div className="space-y-2">
            {L.lessons.map((l) => (
              <div key={l.lesson_id} className="flex flex-wrap items-center gap-3 rounded-3xl border border-black/5 bg-white p-4">
                <div className="grid h-11 w-11 place-items-center rounded-2xl bg-tile-sun text-xl">📖</div>
                <div className="min-w-0 flex-1">
                  <div className="truncate font-semibold">{l.title}</div>
                  <div className="text-xs text-ink-mute">{l.sections} parts{l.doc_name ? ` · ${l.doc_name}` : ""} · {timeAgo(l.created_at)}</div>
                </div>
                <Link to={`/lesson/${l.lesson_id}`} className="btn-ghost btn-sm">Preview</Link>
                <Link to={`/lessons/${l.lesson_id}/edit`} className="btn-ghost btn-sm">Edit</Link>
                <button className="btn-green btn-sm" onClick={() => setAssign({ lesson_id: l.lesson_id, title: l.title })}>Assign</button>
                <button className="text-xs text-ink-mute hover:text-rose-600" onClick={() => del("lessons", l.lesson_id, l.title)}>Delete</button>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* built-in */}
      <section>
        <h2 className="mb-1 text-xl font-bold">Built-in SmartKids lessons</h2>
        <p className="muted mb-3 text-sm">Every student works through these on their path. You can also assign one to give it a due date.</p>
        <div className="grid gap-4 md:grid-cols-3">
          {L.core.map((lv) => (
            <div key={lv.level} className="rounded-4xl bg-[#f7f6fb] p-4">
              <div className="mb-2 flex items-center gap-2 font-bold"><LevelChip level={lv.level} /> {lv.level_name}</div>
              <ul className="space-y-1">
                {lv.lessons.map((l) => (
                  <li key={l.lesson_id} className="flex items-center gap-2 rounded-2xl px-2 py-1.5 hover:bg-white">
                    <span>{l.emoji}</span>
                    <Link to={`/lesson/${l.lesson_id}`} className="min-w-0 flex-1 truncate text-sm font-medium hover:text-jam-green">{l.title}</Link>
                    <button className="text-xs font-semibold text-jam-green hover:underline" onClick={() => setAssign({ lesson_id: l.lesson_id, title: l.title })}>Assign</button>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>

      <AssignModal target={assign} onClose={() => setAssign(null)} onDone={() => { setAssign(null); lib.reload(); }} />
    </div>
  );
}

function Counts({ nq, ns, setNq, setNs, level, setLevel }: { nq: number; ns: number; setNq: (n: number) => void; setNs: (n: number) => void; level: LevelSlug; setLevel: (l: LevelSlug) => void }) {
  return (
    <div className="grid gap-3 sm:grid-cols-3">
      <div><label className="label">Level</label>
        <select className="input" value={level} onChange={(e) => setLevel(e.target.value as LevelSlug)}>{LEVELS.map((l) => <option key={l.v} value={l.v}>{l.l}</option>)}</select></div>
      <div><label className="label">Multiple choice</label><input className="input" type="number" min={1} max={15} value={nq} onChange={(e) => setNq(+e.target.value)} /></div>
      <div><label className="label">Written answers</label><input className="input" type="number" min={0} max={5} value={ns} onChange={(e) => setNs(+e.target.value)} /></div>
    </div>
  );
}

function UploadForm({ onDone }: { onDone: (r: { quiz_id: number }) => void }) {
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [level, setLevel] = useState<LevelSlug>("beginner");
  const [nq, setNq] = useState(5), [ns, setNs] = useState(1);
  const [busy, setBusy] = useState(false), [err, setErr] = useState<string | null>(null);
  const [drag, setDrag] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  const go = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return setErr("Pick a file first.");
    setErr(null); setBusy(true);
    const fd = new FormData();
    fd.append("file", file); fd.append("level", level); fd.append("n_questions", String(nq)); fd.append("n_short", String(ns));
    if (title.trim()) fd.append("title", title.trim());
    try { onDone(await api.post<{ quiz_id: number }>("/api/teacher/documents", fd)); }
    catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };

  return (
    <form onSubmit={go} className="space-y-4">
      <div onClick={() => input.current?.click()} onDragOver={(e) => { e.preventDefault(); setDrag(true); }} onDragLeave={() => setDrag(false)}
           onDrop={(e) => { e.preventDefault(); setDrag(false); const f = e.dataTransfer.files[0]; if (f) setFile(f); }}
           className={`cursor-pointer rounded-4xl border-2 border-dashed p-8 text-center transition ${drag ? "border-jam-green bg-tile-mint" : "border-black/10 hover:border-jam-green"}`}>
        <div className="text-4xl">{file ? "📄" : "⬆️"}</div>
        <div className="mt-2 font-semibold">{file ? file.name : "Drop a PDF, Word (.docx) or text file here"}</div>
        <div className="text-sm text-ink-mute">{file ? `${(file.size / 1024).toFixed(0)} KB · click to change` : "or click to choose · max 10 MB"}</div>
        <input ref={input} type="file" hidden accept=".pdf,.docx,.txt,.md" onChange={(e) => setFile(e.target.files?.[0] ?? null)} />
      </div>
      <div><label className="label">Lesson title <span className="font-normal text-ink-mute">(optional, Casheous can name it)</span></label>
        <input className="input" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={150} placeholder="e.g. The Story of the Jamaican Dollar" /></div>
      <Counts {...{ nq, ns, setNq, setNs, level, setLevel }} />
      {err && <div className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{err}</div>}
      <button className="btn-green w-full py-3" disabled={busy || !file}>{busy ? "Casheous is reading and writing questions… (up to a minute)" : "✨ Make the lesson + quiz"}</button>
    </form>
  );
}

function TopicForm({ onDone }: { onDone: (r: { quiz_id: number }) => void }) {
  const [topic, setTopic] = useState("");
  const [level, setLevel] = useState<LevelSlug>("beginner");
  const [nq, setNq] = useState(5), [ns, setNs] = useState(1);
  const [busy, setBusy] = useState(false), [err, setErr] = useState<string | null>(null);
  const go = async (e: React.FormEvent) => {
    e.preventDefault(); setErr(null); setBusy(true);
    try { onDone(await api.post<{ quiz_id: number }>("/api/teacher/quizzes/generate", { topic, level, n_questions: nq, n_short: ns })); }
    catch (e: any) { setErr(e.message); } finally { setBusy(false); }
  };
  return (
    <form onSubmit={go} className="space-y-4">
      <div><label className="label">Topic</label>
        <input className="input" required minLength={2} maxLength={300} value={topic} onChange={(e) => setTopic(e.target.value)} placeholder="e.g. Saving for Christmas, Fractions with money, The water cycle" /></div>
      <Counts {...{ nq, ns, setNq, setNs, level, setLevel }} />
      {err && <div className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{err}</div>}
      <button className="btn-green w-full py-3" disabled={busy}>{busy ? "Writing questions…" : "✨ Generate quiz"}</button>
    </form>
  );
}

export function AssignModal({ target, onClose, onDone }: { target: Target | null; onClose: () => void; onDone: () => void }) {
  const classes = useLoad(() => target ? api.get<{ classes: { class_id: number; name: string }[] }>("/api/teacher/overview").then((o) => o.classes) : Promise.resolve([]), [target]);
  const [picked, setPicked] = useState<number[]>([]);
  const [due, setDue] = useState("");
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const go = async () => {
    if (!target) return;
    setBusy(true); setMsg(null);
    const errs: string[] = [];
    for (const cid of picked) {
      try { await api.post("/api/teacher/assignments", { class_id: cid, lesson_id: target.lesson_id, quiz_id: target.quiz_id, due_at: due ? new Date(due + "T23:59:00").toISOString() : null }); }
      catch (e: any) { errs.push(`${classes.data?.find((c) => c.class_id === cid)?.name}: ${e.message}`); }
    }
    setBusy(false);
    if (errs.length) setMsg(errs.join(" ")); else { setPicked([]); setDue(""); onDone(); }
  };

  return (
    <Modal open={!!target} onClose={onClose} title={`Assign "${target?.title ?? ""}"`}>
      {classes.loading ? <Spinner /> : !classes.data?.length ? (
        <Empty icon="🏫" title="No classes yet"><Link className="font-semibold text-jam-green" to="/">Create a class</Link> first.</Empty>
      ) : (
        <div className="space-y-4">
          <div className="space-y-2">
            {classes.data.map((c) => (
              <label key={c.class_id} className={`flex cursor-pointer items-center gap-3 rounded-2xl border-2 p-3 ${picked.includes(c.class_id) ? "border-jam-green bg-tile-mint" : "border-black/5"}`}>
                <input type="checkbox" className="h-4 w-4 accent-[#009b3a]" checked={picked.includes(c.class_id)}
                       onChange={(e) => setPicked(e.target.checked ? [...picked, c.class_id] : picked.filter((x) => x !== c.class_id))} />
                <span className="font-semibold">{c.name}</span>
              </label>
            ))}
          </div>
          <div><label className="label">Due date <span className="font-normal text-ink-mute">(optional)</span></label>
            <input type="date" className="input" value={due} onChange={(e) => setDue(e.target.value)} /></div>
          {msg && <div className="rounded-2xl bg-rose-50 px-4 py-3 text-sm text-rose-700">{msg}</div>}
          <button className="btn-green w-full" disabled={!picked.length || busy} onClick={go}>{busy ? "Assigning…" : `Assign to ${picked.length || ""} class${picked.length === 1 ? "" : "es"}`}</button>
        </div>
      )}
    </Modal>
  );
}
