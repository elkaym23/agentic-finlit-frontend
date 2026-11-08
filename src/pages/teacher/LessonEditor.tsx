import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api";
import { ErrorBox, Spinner, useLoad } from "../../components/ui";
import type { Lesson, LevelSlug } from "../../types";

export default function LessonEditor() {
  const { id } = useParams();
  const { data: L, error, loading, reload } = useLoad(() => api.get<Lesson>(`/api/lessons/${id}`), [id]);
  const [title, setTitle] = useState(""), [desc, setDesc] = useState(""), [level, setLevel] = useState<LevelSlug>("beginner");
  const [secs, setSecs] = useState<{ title: string; content: string }[]>([]);
  const [msg, setMsg] = useState<{ ok: boolean; t: string } | null>(null), [saving, setSaving] = useState(false);

  useEffect(() => {
    if (!L) return;
    setTitle(L.title); setDesc(L.description ?? ""); setLevel(L.level);
    setSecs(L.sections.map((s) => ({ title: s.title ?? "", content: s.content })));
  }, [L]);

  if (loading) return <Spinner />;
  if (error || !L) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;
  if (L.is_core) return <ErrorBox error="Built-in lessons can't be edited." />;

  const upd = (k: number, p: Partial<{ title: string; content: string }>) => setSecs(secs.map((s, i) => (i === k ? { ...s, ...p } : s)));
  const save = async () => {
    setSaving(true); setMsg(null);
    try { await api.put(`/api/teacher/lessons/${L.lesson_id}`, { title, description: desc || null, level, sections: secs }); setMsg({ ok: true, t: "Saved ✓ Casheous will use the new text." }); }
    catch (e: any) { setMsg({ ok: false, t: e.message }); } finally { setSaving(false); }
  };

  return (
    <div className="mx-auto max-w-3xl space-y-5">
      <Link to="/library" className="text-sm font-semibold text-ink-mute hover:text-ink">← Lessons & Quizzes</Link>
      <div className="rounded-4xl bg-[#f7f6fb] p-5">
        <label className="label">Lesson title</label>
        <input className="input text-lg font-bold" value={title} onChange={(e) => setTitle(e.target.value)} maxLength={150} />
        <label className="label mt-3">Description</label>
        <input className="input" value={desc} onChange={(e) => setDesc(e.target.value)} />
        <label className="label mt-3">Level</label>
        <select className="input" value={level} onChange={(e) => setLevel(e.target.value as LevelSlug)}>
          <option value="beginner">Beginner</option><option value="intermediate">Intermediate</option><option value="advanced">Advanced</option>
        </select>
      </div>
      {secs.map((s, k) => (
        <div key={k} className="rounded-4xl border border-black/5 bg-white p-5">
          <div className="mb-2 flex items-center gap-2">
            <span className="grid h-8 w-8 place-items-center rounded-full bg-ink text-sm font-bold text-white">{k + 1}</span>
            <input className="input" placeholder="Part title" value={s.title} onChange={(e) => upd(k, { title: e.target.value })} />
            <button className="btn-ghost btn-sm text-rose-600" onClick={() => setSecs(secs.filter((_, i) => i !== k))}>Delete</button>
          </div>
          <textarea className="input min-h-[180px] font-mono text-sm" value={s.content} onChange={(e) => upd(k, { content: e.target.value })} placeholder="Text (Markdown works: **bold**, - lists)" />
        </div>
      ))}
      <button className="btn-ghost w-full" onClick={() => setSecs([...secs, { title: "", content: "" }])}>＋ Add a part</button>
      <div className="flex items-center gap-3">
        <button className="btn-green" disabled={saving} onClick={save}>{saving ? "Saving…" : "Save lesson"}</button>
        <Link className="btn-ghost" to={`/lesson/${L.lesson_id}`}>Preview</Link>
        {msg && <span className={`text-sm ${msg.ok ? "text-emerald-700" : "text-rose-700"}`}>{msg.t}</span>}
      </div>
    </div>
  );
}
