import confetti from "canvas-confetti";
import { useCallback, useEffect, useState, type ReactNode } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import type { LevelSlug } from "../types";

/** Load data on mount; returns { data, error, loading, reload, setData }. */
export function useLoad<T>(fn: () => Promise<T>, deps: unknown[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const reload = useCallback(() => {
    setLoading(true);
    setError(null);
    return fn().then(setData).catch((e) => setError(e.message || String(e))).finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);
  useEffect(() => { reload(); }, [reload]);
  return { data, error, loading, reload, setData };
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-3 py-16 text-ink-mute">
      <span className="h-6 w-6 animate-spin rounded-full border-[3px] border-jam-green/20 border-t-jam-green" />
      {label && <span className="font-medium">{label}</span>}
    </div>
  );
}

export function ErrorBox({ error, onRetry }: { error: string; onRetry?: () => void }) {
  return (
    <div className="card card-pad flex flex-col items-start gap-3 border-rose-100 bg-rose-50/70">
      <div className="font-semibold text-rose-700">😕 {error}</div>
      {onRetry && <button className="btn-ghost btn-sm" onClick={onRetry}>Try again</button>}
    </div>
  );
}

export function Markdown({ children, className = "prose-kid" }: { children: string; className?: string }) {
  return <div className={className}><ReactMarkdown remarkPlugins={[remarkGfm]}>{children}</ReactMarkdown></div>;
}

export function Bar({ value, className = "", color = "bg-jam-green" }: { value: number; className?: string; color?: string }) {
  return (
    <div className={`h-2.5 w-full overflow-hidden rounded-full bg-black/5 ${className}`}>
      <div className={`h-full rounded-full transition-all duration-700 ${color}`} style={{ width: `${Math.max(0, Math.min(100, value))}%` }} />
    </div>
  );
}

export function Ring({ value, size = 64, stroke = 7, color = "#009b3a", children }:
  { value: number; size?: number; stroke?: number; color?: string; children?: ReactNode }) {
  const r = (size - stroke) / 2, c = 2 * Math.PI * r;
  return (
    <div className="relative inline-grid place-items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={r} stroke="#0000000d" strokeWidth={stroke} fill="none" />
        <circle cx={size / 2} cy={size / 2} r={r} stroke={color} strokeWidth={stroke} fill="none" strokeLinecap="round"
                strokeDasharray={c} strokeDashoffset={c * (1 - Math.max(0, Math.min(100, value)) / 100)}
                style={{ transition: "stroke-dashoffset .8s ease" }} />
      </svg>
      <div className="absolute text-sm font-bold">{children ?? `${Math.round(value)}%`}</div>
    </div>
  );
}

export const LEVEL_STYLE: Record<LevelSlug, { tile: string; text: string; ring: string; chip: string; label: string }> = {
  beginner: { tile: "bg-tile-mint", text: "text-emerald-700", ring: "#009b3a", chip: "bg-emerald-100 text-emerald-800", label: "Beginner" },
  intermediate: { tile: "bg-tile-sky", text: "text-sky-700", ring: "#0284c7", chip: "bg-sky-100 text-sky-800", label: "Intermediate" },
  advanced: { tile: "bg-tile-lilac", text: "text-violet-700", ring: "#7c3aed", chip: "bg-violet-100 text-violet-800", label: "Advanced" },
};

export function LevelChip({ level }: { level: LevelSlug | string }) {
  const s = LEVEL_STYLE[(level as LevelSlug)] ?? LEVEL_STYLE.beginner;
  return <span className={`chip ${s.chip}`}>{s.label}</span>;
}

export function Empty({ icon, title, children }: { icon: string; title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-4xl border-2 border-dashed border-black/10 px-6 py-12 text-center">
      <div className="text-4xl">{icon}</div>
      <div className="text-lg font-semibold">{title}</div>
      {children && <div className="max-w-md text-ink-mute">{children}</div>}
    </div>
  );
}

export function Modal({ open, onClose, title, children, wide }:
  { open: boolean; onClose: () => void; title: string; children: ReactNode; wide?: boolean }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 grid place-items-center bg-ink/30 p-4 backdrop-blur-sm" onClick={onClose}>
      <div className={`card card-pad w-full animate-pop ${wide ? "max-w-3xl" : "max-w-lg"} max-h-[90vh] overflow-y-auto scroll-thin`}
           onClick={(e) => e.stopPropagation()} role="dialog" aria-modal="true" aria-label={title}>
        <div className="mb-4 flex items-center justify-between gap-4">
          <h2 className="text-xl font-bold">{title}</h2>
          <button className="grid h-9 w-9 place-items-center rounded-full hover:bg-black/5" onClick={onClose} aria-label="Close">✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

export function celebrate() {
  const colors = ["#009b3a", "#fed100", "#111111", "#3fd17a"];
  confetti({ particleCount: 120, spread: 80, origin: { y: 0.6 }, colors });
  setTimeout(() => confetti({ particleCount: 60, angle: 60, spread: 60, origin: { x: 0 }, colors }), 200);
  setTimeout(() => confetti({ particleCount: 60, angle: 120, spread: 60, origin: { x: 1 }, colors }), 350);
}

export function timeAgo(iso?: string | null) {
  if (!iso) return "—";
  const s = (Date.now() - new Date(iso).getTime()) / 1000;
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)}m ago`;
  if (s < 86400) return `${Math.floor(s / 3600)}h ago`;
  if (s < 86400 * 7) return `${Math.floor(s / 86400)}d ago`;
  return new Date(iso).toLocaleDateString();
}

export function greeting() {
  const h = new Date().getHours();
  return h < 12 ? "Good morning" : h < 17 ? "Good afternoon" : "Good evening";
}
