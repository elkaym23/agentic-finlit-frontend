import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import Mascot from "../../components/Mascot";
import { Bar, ErrorBox, LevelChip, Markdown, Spinner, useLoad } from "../../components/ui";
import type { Lesson } from "../../types";

export default function LessonPage() {
  const { id } = useParams();
  const { user } = useAuth();
  const nav = useNavigate();
  const isStudent = user?.role === "Student";
  const { data: L, error, loading, reload } = useLoad(() => api.get<Lesson>(`/api/lessons/${id}`), [id]);
  const [page, setPage] = useState(0);

  useEffect(() => {
    if (L?.progress && L.progress.status !== "completed") setPage(Math.max(0, Math.min(L.sections.length - 1, (L.progress.current_pos || 1) - 1)));
    else setPage(0);
  }, [L]);

  useEffect(() => {
    if (L && isStudent && L.sections.length) api.post(`/api/lessons/${L.lesson_id}/progress`, { position: page + 1 }).catch(() => {});
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [page, L, isStudent]);

  if (loading) return <Spinner label="Opening the lesson…" />;
  if (error || !L) return <ErrorBox error={error || "Couldn't load"} onRetry={reload} />;

  const secs = L.sections;
  const last = page >= secs.length - 1;
  const sec = secs[page];
  const passed = L.best_pct != null && L.best_pct >= 60;

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-5 flex flex-wrap items-center gap-2 text-sm">
        <Link to={isStudent ? "/learn" : "/library"} className="font-semibold text-ink-mute hover:text-ink">← {isStudent ? "Learning path" : "Library"}</Link>
        <span className="text-ink-mute">/</span>
        <LevelChip level={L.level} />
        {L.is_core && L.position && <span className="chip bg-black/5">Lesson {L.position} of {L.lesson_count}</span>}
        {L.doc_name && <span className="chip bg-black/5">📄 {L.doc_name}</span>}
      </div>

      <div className="flex items-start gap-4">
        <div className="grid h-16 w-16 shrink-0 place-items-center rounded-3xl bg-tile-sun text-4xl">{L.emoji || "📖"}</div>
        <div>
          <h1 className="h-page">{L.title}</h1>
          {L.description && <p className="muted mt-1">{L.description}</p>}
        </div>
      </div>

      {secs.length > 1 && (
        <div className="mt-6 flex items-center gap-3">
          <Bar value={((page + 1) / secs.length) * 100} />
          <span className="shrink-0 text-sm font-semibold text-ink-mute">{page + 1} / {secs.length}</span>
        </div>
      )}

      {sec ? (
        <article key={page} className="mt-6 animate-pop rounded-4xl bg-[#fbfaf6] p-6 sm:p-8">
          {sec.title && <h2 className="mb-3 text-2xl font-bold text-jam-green">{sec.title}</h2>}
          <Markdown>{sec.content}</Markdown>
        </article>
      ) : <div className="mt-6 muted">This lesson has no content yet.</div>}

      <div className="mt-6 flex items-center justify-between gap-3">
        <button className="btn-ghost" disabled={page === 0} onClick={() => setPage(page - 1)}>← Back</button>
        {!last ? (
          <button className="btn-dark" onClick={() => setPage(page + 1)}>Next →</button>
        ) : L.quiz_id && isStudent ? (
          <button className="btn-green px-6 text-lg" onClick={() => nav(`/quiz/${L.quiz_id}`)}>{passed ? "Retake the quiz" : "Take the quiz 📝"}</button>
        ) : L.quiz_id && !L.is_core ? (
          <Link className="btn-green" to={`/quizzes/${L.quiz_id}/edit`}>Edit the quiz</Link>
        ) : <span />}
      </div>

      {last && isStudent && L.quiz_id && (
        <div className="mt-6 flex items-center gap-4 rounded-4xl bg-tile-mint p-5">
          <Mascot size={64} mood="cheer" />
          <div className="text-sm leading-relaxed">
            <b>Nice reading!</b> Now show what you learned. After the quiz I'll go through your answers with you and you can ask me
            anything. {passed && <>You already passed with <b>{L.best_pct}%</b>, but you can try to beat it!</>}
          </div>
        </div>
      )}
    </div>
  );
}
