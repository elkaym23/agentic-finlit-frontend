import { useState, type ReactNode } from "react";
import { Link, NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";

const I = {
  home: <path d="M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z" />,
  map: <path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2zm0 0v14m6-12v14" />,
  game: <path d="M6 9h4M8 7v4m7-1h.01M18 12h.01M7 5h10a5 5 0 0 1 5 5v1a5 5 0 0 1-8.6 3.4L12 13l-1.4 1.4A5 5 0 0 1 2 11v-1a5 5 0 0 1 5-5z" />,
  chat: <path d="M21 12a8 8 0 0 1-11.6 7.1L4 20l1-4.6A8 8 0 1 1 21 12z" />,
  class: <path d="M17 20v-1a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v1m18 0v-1a4 4 0 0 0-3-3.9M14 4.1a4 4 0 0 1 0 7.8M10 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0z" />,
  book: <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20V3H6.5A2.5 2.5 0 0 0 4 5.5v14zM4 19.5A2.5 2.5 0 0 0 6.5 22H20v-5" />,
  out: <path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4M10 17l-5-5 5-5M5 12h12" />,
};
function Icon({ d }: { d: ReactNode }) {
  return <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth="1.9"
              strokeLinecap="round" strokeLinejoin="round">{d}</svg>;
}

export default function Layout() {
  const { user, logout } = useAuth();
  const nav = useNavigate();
  const [menu, setMenu] = useState(false);
  if (!user) return null;
  const items = user.role === "Student"
    ? [{ to: "/", icon: I.home, label: "Home" }, { to: "/learn", icon: I.map, label: "Learn" },
       { to: "/games", icon: I.game, label: "Games" }, { to: "/tutor", icon: I.chat, label: "Ask FinBuddy" },
       { to: "/class", icon: I.class, label: "My Class" }]
    : [{ to: "/", icon: I.home, label: "Dashboard" }, { to: "/library", icon: I.book, label: "Lessons & Quizzes" }];

  const out = () => { logout(); nav("/"); };
  const link = ({ isActive }: { isActive: boolean }) =>
    `group relative grid h-11 w-11 place-items-center rounded-full transition ${isActive ? "bg-jam-gold text-ink" : "text-white/60 hover:bg-white/10 hover:text-white"}`;

  return (
    <div className="mx-auto flex min-h-screen max-w-[1440px] gap-5 p-3 sm:p-5">
      {/* desktop pill sidebar */}
      <aside className="sticky top-5 hidden h-[calc(100vh-2.5rem)] w-[72px] shrink-0 flex-col items-center md:flex">
        <Link to="/" className="mb-5 grid h-14 w-14 place-items-center rounded-full bg-white text-3xl shadow-card" title="SmartKids">🐦</Link>
        <nav className="flex flex-col items-center gap-2 rounded-full bg-ink px-2.5 py-4 shadow-float">
          {items.map((it) => (
            <NavLink key={it.to} to={it.to} end={it.to === "/"} className={link} aria-label={it.label}>
              <Icon d={it.icon} />
              <span className="pointer-events-none absolute left-14 z-20 whitespace-nowrap rounded-full bg-ink px-3 py-1 text-xs font-semibold text-white opacity-0 shadow transition group-hover:opacity-100">
                {it.label}
              </span>
            </NavLink>
          ))}
        </nav>
        <button onClick={out} className="mt-auto grid h-12 w-12 place-items-center rounded-full bg-white text-ink-soft shadow-card hover:text-rose-600" title="Log out" aria-label="Log out">
          <Icon d={I.out} />
        </button>
      </aside>

      <div className="min-w-0 flex-1 pb-24 md:pb-0">
        <div className="card min-h-[calc(100vh-2.5rem)] px-4 py-5 sm:px-8 sm:py-7">
          <header className="mb-6 flex items-center justify-between gap-3">
            <Link to="/" className="flex items-center gap-3">
              <div className="grid h-11 w-11 place-items-center rounded-2xl bg-jam-green text-xl text-white md:hidden">🐦</div>
              <div>
                <div className="text-xs font-semibold uppercase tracking-wider text-jam-green">SmartKids</div>
                <div className="hidden text-sm text-ink-mute sm:block">{new Date().toLocaleDateString(undefined, { weekday: "long", day: "numeric", month: "long" })}</div>
              </div>
            </Link>
            <div className="flex items-center gap-2">
              {user.role === "Student" && <>
                <span className="chip hidden bg-tile-sun py-2 text-sm text-amber-800 sm:inline-flex" title="Days in a row">🔥 {user.streak}</span>
                <span className="chip whitespace-nowrap bg-tile-mint py-2 text-sm text-emerald-800" title="Experience points">⭐ {user.xp} XP</span>
              </>}
              <div className="relative">
                <button onClick={() => setMenu(!menu)} className="flex items-center gap-2 rounded-full border border-black/10 bg-white py-1 pl-1 pr-3 hover:bg-black/5">
                  <span className="grid h-9 w-9 place-items-center rounded-full bg-tile-sun text-xl">{user.role === "Teacher" ? "👩🏾‍🏫" : user.avatar}</span>
                  <span className="hidden max-w-[10rem] truncate text-sm font-semibold sm:block">{user.title ? `${user.title} ` : ""}{user.name}</span>
                </button>
                {menu && (
                  <div className="absolute right-0 z-30 mt-2 w-48 animate-pop rounded-3xl border border-black/5 bg-white p-2 shadow-float" onMouseLeave={() => setMenu(false)}>
                    <div className="px-3 py-2 text-xs text-ink-mute">{user.email}</div>
                    <button onClick={out} className="w-full rounded-2xl px-3 py-2 text-left font-medium hover:bg-black/5">Log out</button>
                  </div>
                )}
              </div>
            </div>
          </header>
          <Outlet />
        </div>
      </div>

      {/* mobile bottom bar */}
      <nav className="fixed inset-x-3 bottom-3 z-40 flex justify-around rounded-full bg-ink px-2 py-2 shadow-float md:hidden">
        {items.map((it) => (
          <NavLink key={it.to} to={it.to} end={it.to === "/"} className={link} aria-label={it.label}><Icon d={it.icon} /></NavLink>
        ))}
      </nav>
    </div>
  );
}
