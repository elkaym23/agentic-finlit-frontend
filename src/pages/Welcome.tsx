import { useState } from "react";
import { useAuth } from "../auth";
import Mascot from "../components/Mascot";

const AVATARS = ["🦜", "🐢", "🦁", "🐬", "🦊", "🐼", "🐝", "🦄", "🐸", "🐙"];
const LEVELS = [
  { slug: "beginner", label: "Money Explorers", ages: "Ages 7–8", emoji: "🌱" },
  { slug: "intermediate", label: "Smart Spenders", ages: "Ages 9–10", emoji: "🚀" },
  { slug: "advanced", label: "Money Masters", ages: "Ages 11–12", emoji: "🎓" },
];

export default function Welcome() {
  const { login, signup } = useAuth();
  const [mode, setMode] = useState<"login" | "signup">("login");
  const [role, setRole] = useState<"Student" | "Teacher">("Student");
  const [f, setF] = useState({ name: "", email: "", password: "", title: "Ms", level_slug: "beginner", avatar: "🦜", class_code: "" });
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const set = (k: keyof typeof f) => (e: { target: { value: string } }) => setF({ ...f, [k]: e.target.value });

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      if (mode === "login") await login(f.email, f.password);
      else await signup({ ...f, role, class_code: f.class_code || undefined });
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto grid min-h-screen max-w-6xl items-center gap-8 p-4 py-10 lg:grid-cols-[1.1fr_1fr]">
      {/* hero */}
      <div className="relative">
        <div className="chip mb-5 bg-white py-2 text-sm shadow-card">
          <span className="flex h-3 w-5 overflow-hidden rounded-sm">
            <span className="w-1/3 bg-jam-green" /><span className="w-1/3 bg-jam-gold" /><span className="w-1/3 bg-jam-black" />
          </span>
          Made for Jamaican classrooms
        </div>
        <h1 className="text-5xl font-extrabold leading-[1.05] tracking-tight sm:text-6xl">
          Money smarts,<br /><span className="text-jam-green">one lesson</span> at a time.
        </h1>
        <p className="mt-5 max-w-lg text-lg text-ink-soft">
          Learn about JA$ coins and notes, saving, budgeting and running a business, with fun quizzes, games and
          <b> FinBuddy</b>, your AI doctor-bird tutor.
        </p>
        <div className="mt-8 grid max-w-lg grid-cols-3 gap-3">
          {LEVELS.map((l, i) => (
            <div key={l.slug} className={`rounded-3xl p-4 ${["bg-tile-mint", "bg-tile-sky", "bg-tile-lilac"][i]}`}>
              <div className="text-2xl">{l.emoji}</div>
              <div className="mt-2 text-sm font-bold leading-tight">{l.label}</div>
              <div className="text-xs text-ink-mute">{l.ages}</div>
            </div>
          ))}
        </div>
        <div className="pointer-events-none absolute -right-2 -top-28 hidden animate-bob lg:block"><Mascot size={170} mood="cheer" /></div>
      </div>

      {/* form */}
      <div className="card card-pad shadow-float sm:p-8">
        <div className="mb-6 flex rounded-full bg-black/5 p-1">
          {(["login", "signup"] as const).map((m) => (
            <button key={m} onClick={() => { setMode(m); setErr(null); }}
                    className={`flex-1 rounded-full py-2.5 font-semibold transition ${mode === m ? "bg-white shadow-sm" : "text-ink-mute"}`}>
              {m === "login" ? "Log in" : "Create account"}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="space-y-4">
          {mode === "signup" && (
            <>
              <div className="grid grid-cols-2 gap-2">
                {(["Student", "Teacher"] as const).map((r) => (
                  <button type="button" key={r} onClick={() => setRole(r)}
                          className={`rounded-3xl border-2 p-3 text-left transition ${role === r ? "border-jam-green bg-tile-mint" : "border-black/5 hover:border-black/15"}`}>
                    <div className="text-2xl">{r === "Student" ? "🎒" : "👩🏾‍🏫"}</div>
                    <div className="font-bold">I'm a {r.toLowerCase()}</div>
                  </button>
                ))}
              </div>
              <div className={role === "Teacher" ? "grid grid-cols-[90px_1fr] gap-2" : ""}>
                {role === "Teacher" && (
                  <div><label className="label">Title</label>
                    <select className="input" value={f.title} onChange={set("title")}>
                      {["Ms", "Mrs", "Miss", "Mr", "Dr"].map((t) => <option key={t}>{t}</option>)}
                    </select></div>
                )}
                <div><label className="label">{role === "Teacher" ? "Name" : "First name"}</label>
                  <input className="input" required value={f.name} onChange={set("name")} placeholder={role === "Teacher" ? "Campbell" : "Kemar"} /></div>
              </div>
            </>
          )}
          <div><label className="label">Email</label>
            <input className="input" type="email" required value={f.email} onChange={set("email")} placeholder="you@school.edu.jm" autoComplete="email" /></div>
          <div><label className="label">Password</label>
            <input className="input" type="password" required minLength={mode === "signup" ? 6 : 1} value={f.password} onChange={set("password")}
                   autoComplete={mode === "login" ? "current-password" : "new-password"} placeholder={mode === "signup" ? "At least 6 characters" : ""} /></div>

          {mode === "signup" && role === "Student" && (
            <>
              <div><label className="label">Pick your buddy</label>
                <div className="flex flex-wrap gap-2">
                  {AVATARS.map((a) => (
                    <button type="button" key={a} onClick={() => setF({ ...f, avatar: a })} aria-label={`Avatar ${a}`}
                            className={`grid h-11 w-11 place-items-center rounded-2xl text-2xl transition ${f.avatar === a ? "bg-jam-gold scale-110" : "bg-black/5 hover:bg-black/10"}`}>{a}</button>
                  ))}
                </div></div>
              <div><label className="label">Where do you want to start?</label>
                <div className="grid gap-2 sm:grid-cols-3">
                  {LEVELS.map((l) => (
                    <button type="button" key={l.slug} onClick={() => setF({ ...f, level_slug: l.slug })}
                            className={`rounded-2xl border-2 px-3 py-2 text-left text-sm transition ${f.level_slug === l.slug ? "border-jam-green bg-tile-mint" : "border-black/5"}`}>
                      <b>{l.emoji} {l.label}</b><div className="text-xs text-ink-mute">{l.ages}</div>
                    </button>
                  ))}
                </div></div>
              <div><label className="label">Class code <span className="font-normal text-ink-mute">(optional, from your teacher)</span></label>
                <input className="input uppercase tracking-widest" value={f.class_code} onChange={set("class_code")} placeholder="ABC123" maxLength={10} /></div>
            </>
          )}

          {err && <div className="rounded-2xl bg-rose-50 px-4 py-3 text-sm font-medium text-rose-700">{err}</div>}
          <button className="btn-green w-full py-3 text-lg" disabled={busy}>
            {busy ? "Just a sec…" : mode === "login" ? "Let's go! 🚀" : "Create my account"}
          </button>
        </form>
      </div>
    </div>
  );
}
