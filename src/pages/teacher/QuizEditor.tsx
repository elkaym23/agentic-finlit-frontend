import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { api } from "../../api";
import { ErrorBox, Spinner, useLoad } from "../../components/ui";
import type { LevelSlug, Quiz } from "../../types";
import { AssignModal } from "./Library";

type Item = { kind: "mcq" | "short"; question: string; options: string[]; answer_key: string; explanation: string; rubric: string };
const blankMcq = (): Item => ({ kind: "mcq", question: "", options: ["", "", "", ""], answer_key: "A", explanation: "", rubric: "" });
const blankShort = (): Item => ({ kind: "short", question: "", options: [], answer_key: "", explanation: "", rubric: "" });

export default function QuizEditor() {
  const { id } = useParams();
  const [sp] = useSearchParams();
  const nav = useNavigate();
  const { data: Q, error, loading, reload } = useLoad(() => api.get<Quiz>(`/api/quizzes/${id}`), [id]);
  const [title, setTitle] = useState(""), [desc, setDesc] = useState("");
  const [level, setLevel] = useState<LevelSlug>("beginner"), [pass, setPass] = useState(60);
  const [items, setItems] = useState<Item[]>([]);
  const [saving, setSaving] = useState(false), [msg, setMsg] = useState<{ ok: boolean; t: string } | null>(null);
  const [dirty, setDirty] = useState(false), [assign, setAssign] = useState(false);

  useEffect(() => {
    if (!Q) return;
    setTitle(Q.title); setDesc(Q.description ?? ""); setLevel(Q.level); setPass(Q.pass_pct);
    setItems(Q.items.map((i) => ({ kind: i.kind, question: i.question, options: i.kind === "mcq" ? [...i.options, "", "", "", ""].slice(0, 4) : [],
      answer_key: i.answer_key ?? "A", explanation: i.explanation ?? "", rubric: i.rubric ?? "" })));
    setDirty(false);
  }, [Q]);

  if (loading) return <Spinner />;
  if (error || !Q) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;
  if (Q.is_core) return <ErrorBox error="Built-in quizzes can't be edited. Make your own from a topic or document instead." />;

  const upd = (k: number, patch: Partial<Item>) => { setItems(items.map((it, i) => (i === k ? { ...it, ...patch } : it))); setDirty(true); };
  const move = (k: number, d: number) => { const j = k + d; if (j < 0 || j >= items.length) return; const n = [...items]; [n[k], n[j]] = [n[j], n[k]]; setItems(n); setDirty(true); };

  const save = async () => {
    setMsg(null); setSaving(true);
    try {
      await api.put(`/api/teacher/quizzes/${Q.quiz_id}`, { title, description: desc || null, level, pass_pct: pass,
        items: items.map((it) => it.kind === "mcq"
          ? { kind: "mcq", question: it.question, options: it.options.filter((o) => o.trim()), answer_key: it.answer_key, explanation: it.explanation || null }
          : { kind: "short", question: it.question, rubric: it.rubric || null, explanation: it.explanation || null }) });
      setMsg({ ok: true, t: "Saved ✓" }); setDirty(false);
    } catch (e: any) { setMsg({ ok: false, t: e.message }); } finally { setSaving(false); }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-5 pb-24">
      <Link to="/library" className="text-sm font-semibold text-ink-mute hover:text-ink">← Lessons & Quizzes</Link>
      {sp.get("new") && <div className="rounded-3xl bg-tile-mint p-4 text-sm">✨ <b>FinBuddy wrote {items.length} questions.</b> Check each one, fix anything that's off, then save and assign it.</div>}

      <div className="rounded-4xl bg-[#f7f6fb] p-5">
        <label className="label">Quiz title</label>
        <input className="input text-lg font-bold" value={title} maxLength={150} onChange={(e) => { setTitle(e.target.value); setDirty(true); }} />
        <label className="label mt-3">Description <span className="font-normal text-ink-mute">(optional)</span></label>
        <input className="input" value={desc} onChange={(e) => { setDesc(e.target.value); setDirty(true); }} />
        <div className="mt-3 grid grid-cols-2 gap-3">
          <div><label className="label">Level</label>
            <select className="input" value={level} onChange={(e) => { setLevel(e.target.value as LevelSlug); setDirty(true); }}>
              <option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option>
            </select></div>
          <div><label className="label">Pass mark: {pass}%</label>
            <input type="range" min={0} max={100} step={5} value={pass} onChange={(e) => { setPass(+e.target.value); setDirty(true); }} className="mt-3 w-full accent-[#009b3a]" /></div>
        </div>
        {Q.lesson_id && <div className="mt-3 text-sm text-ink-mute">📖 Students read <Link className="font-semibold text-jam-green" to={`/lesson/${Q.lesson_id}`}>{Q.lesson_title || "the lesson"}</Link> before this quiz. <Link className="underline" to={`/lessons/${Q.lesson_id}/edit`}>Edit lesson</Link></div>}
      </div>

      {items.map((it, k) => (
        <div key={k} className="rounded-4xl border border-black/5 bg-white p-5">
          <div className="mb-3 flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-ink text-sm font-bold text-white">{k + 1}</span>
            <span className="chip bg-black/5 text-xs">{it.kind === "mcq" ? "Multiple choice" : "Written answer · marked by AI"}</span>
            <div className="ml-auto flex gap-1">
              <button className="btn-ghost btn-sm" onClick={() => move(k, -1)} aria-label="Move up">↑</button>
              <button className="btn-ghost btn-sm" onClick={() => move(k, 1)} aria-label="Move down">↓</button>
              <button className="btn-ghost btn-sm text-rose-600" onClick={() => { setItems(items.filter((_, i) => i !== k)); setDirty(true); }}>Delete</button>
            </div>
          </div>
          <textarea className="input min-h-[70px]" placeholder="Question" value={it.question} onChange={(e) => upd(k, { question: e.target.value })} />
          {it.kind === "mcq" ? (
            <div className="mt-3 space-y-2">
              {it.options.map((o, j) => {
                const L = String.fromCharCode(65 + j);
                return (
                  <div key={j} className="flex items-center gap-2">
                    <button onClick={() => upd(k, { answer_key: L })} title="Mark as correct"
                            className={`grid h-9 w-9 shrink-0 place-items-center rounded-full font-bold ${it.answer_key === L ? "bg-jam-green text-white" : "bg-black/5"}`}>{L}</button>
                    <input className="input" placeholder={`Option ${L}${j >= 2 ? " (optional)" : ""}`} value={o}
                           onChange={(e) => upd(k, { options: it.options.map((x, i) => (i === j ? e.target.value : x)) })} />
                  </div>
                );
              })}
              <div className="text-xs text-ink-mute">Tap a letter to mark the correct answer (now: <b>{it.answer_key}</b>).</div>
            </div>
          ) : (
            <div className="mt-3"><label className="label">What a good answer includes (the AI marks using this)</label>
              <textarea className="input min-h-[60px]" value={it.rubric} onChange={(e) => upd(k, { rubric: e.target.value })} placeholder="e.g. Mentions saving part of the money and gives a reason" /></div>
          )}
          <div className="mt-3"><label className="label">Explanation shown after the quiz <span className="font-normal text-ink-mute">(optional)</span></label>
            <input className="input" value={it.explanation} onChange={(e) => upd(k, { explanation: e.target.value })} /></div>
        </div>
      ))}

      <div className="flex gap-2">
        <button className="btn-ghost flex-1" onClick={() => { setItems([...items, blankMcq()]); setDirty(true); }}>＋ Multiple choice</button>
        <button className="btn-ghost flex-1" onClick={() => { setItems([...items, blankShort()]); setDirty(true); }}>＋ Written answer</button>
      </div>

      <div className="fixed inset-x-3 bottom-20 z-30 mx-auto flex max-w-3xl items-center gap-3 rounded-full bg-ink p-2 pl-5 text-white shadow-float md:bottom-5">
        <span className={`flex-1 text-sm ${msg && !msg.ok ? "text-rose-300" : "text-white/70"}`}>{msg?.t ?? (dirty ? "Unsaved changes" : `${items.length} questions`)}</span>
        <button className="btn-ghost btn-sm border-white/20 bg-transparent text-white hover:bg-white/10" onClick={() => setAssign(true)}>Assign</button>
        <button className="btn-ghost btn-sm border-white/20 bg-transparent text-white hover:bg-white/10" onClick={() => nav("/library")}>Done</button>
        <button className="btn-gold btn-sm" disabled={saving || !dirty} onClick={save}>{saving ? "Saving…" : "Save"}</button>
      </div>
      <AssignModal target={assign ? { quiz_id: Q.quiz_id, title } : null} onClose={() => setAssign(false)} onDone={() => { setAssign(false); setMsg({ ok: true, t: "Assigned ✓" }); }} />
    </div>
  );
}
