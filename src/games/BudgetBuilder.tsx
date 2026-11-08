import { useState } from "react";
import { Bar } from "../components/ui";
import { jmd, type GameProps } from "./types";

const BUDGET = 5000;
const SAVE_GOAL = 0.2;
type Item = { id: string; name: string; e: string; cost: number; need: boolean; group: string };
const CHOICES: Item[] = [
  { id: "lunch", name: "School lunch (5 days)", e: "🍛", cost: 1500, need: true, group: "Lunch" },
  { id: "lunch_cook", name: "Lunch from home + snacks", e: "🥪", cost: 900, need: true, group: "Lunch" },
  { id: "bus", name: "Bus fare (5 days)", e: "🚌", cost: 800, need: true, group: "Getting to school" },
  { id: "taxi", name: "Route taxi (5 days)", e: "🚕", cost: 1400, need: true, group: "Getting to school" },
  { id: "book", name: "Exercise books & pens", e: "📓", cost: 450, need: true, group: "School supplies" },
  { id: "book_fancy", name: "Fancy gel pens & sparkly books", e: "✨", cost: 1100, need: true, group: "School supplies" },
  { id: "phone", name: "Phone credit", e: "📱", cost: 500, need: false, group: "Extras" },
  { id: "game", name: "New video game", e: "🎮", cost: 2500, need: false, group: "Extras" },
  { id: "icecream", name: "Devon House ice cream", e: "🍦", cost: 600, need: false, group: "Extras" },
  { id: "sneakers", name: "Brand-name sneakers deposit", e: "👟", cost: 2000, need: false, group: "Extras" },
  { id: "movie", name: "Movie with friends", e: "🎬", cost: 900, need: false, group: "Extras" },
];
const NEED_GROUPS = ["Lunch", "Getting to school", "School supplies"];

export default function BudgetBuilder({ onFinish }: GameProps) {
  const [picked, setPicked] = useState<Set<string>>(new Set());
  const chosen = CHOICES.filter((c) => picked.has(c.id));
  const spent = chosen.reduce((a, c) => a + c.cost, 0);
  const left = BUDGET - spent;
  const covered = NEED_GROUPS.filter((g) => chosen.some((c) => c.group === g));

  const toggle = (it: Item) => setPicked((prev) => {
    const s = new Set(prev);
    if (s.has(it.id)) s.delete(it.id);
    else {
      if (it.need) CHOICES.filter((c) => c.group === it.group).forEach((c) => s.delete(c.id)); // one option per need
      s.add(it.id);
    }
    return s;
  });

  const done = () => {
    const allNeeds = covered.length === NEED_GROUPS.length;
    const saved = left;
    const okSave = saved >= BUDGET * SAVE_GOAL;
    const won = allNeeds && saved >= 0 && okSave;
    const wants = chosen.filter((c) => !c.need).length;
    const why = !allNeeds ? `You forgot a need: ${NEED_GROUPS.filter((g) => !covered.includes(g)).join(", ")}.`
      : saved < 0 ? `You overspent by ${jmd(-saved)}!` : !okSave ? `You only saved ${jmd(saved)}. The goal was ${jmd(BUDGET * SAVE_GOAL)}.` : "";
    onFinish({ won, score: Math.max(0, saved), details: { spent, saved, wants, picked: [...picked] },
      summary: won ? `Every need covered, ${wants} treat${wants === 1 ? "" : "s"}, and ${jmd(saved)} saved. That's a real budget!` : `${why} Try again!` });
  };

  const groups = [...NEED_GROUPS, "Extras"];
  return (
    <div className="grid gap-5 lg:grid-cols-[1fr_300px]">
      <div className="space-y-5">
        {groups.map((g) => (
          <div key={g}>
            <div className="mb-2 flex items-center gap-2 font-bold">{g} {g !== "Extras" ? <span className="chip bg-emerald-100 text-xs text-emerald-800">Need: pick one</span> : <span className="chip bg-amber-100 text-xs text-amber-800">Wants: optional</span>}</div>
            <div className="grid gap-2 sm:grid-cols-2">
              {CHOICES.filter((c) => c.group === g).map((c) => {
                const on = picked.has(c.id);
                return (
                  <button key={c.id} onClick={() => toggle(c)} className={`flex items-center gap-3 rounded-3xl border-2 bg-white p-3 text-left transition ${on ? "border-jam-green bg-tile-mint" : "border-black/5 hover:border-black/15"}`}>
                    <span className="text-3xl">{c.e}</span>
                    <span className="min-w-0 flex-1"><span className="block font-semibold leading-tight">{c.name}</span><span className="text-sm text-ink-mute">{jmd(c.cost)}</span></span>
                    <span className="text-lg">{on ? "✅" : "＋"}</span>
                  </button>
                );
              })}
            </div>
          </div>
        ))}
      </div>
      <aside className="space-y-3 lg:sticky lg:top-5 lg:self-start">
        <div className="rounded-4xl bg-ink p-5 text-white">
          <div className="text-sm text-white/70">Weekly money</div>
          <div className="text-3xl font-extrabold">{jmd(BUDGET)}</div>
          <div className="mt-4 space-y-1 text-sm">
            <div className="flex justify-between"><span>Spent</span><b>{jmd(spent)}</b></div>
            <div className="flex justify-between"><span>Left to save</span><b className={left < 0 ? "text-rose-300" : "text-jam-gold"}>{jmd(left)}</b></div>
          </div>
          <Bar value={(spent / BUDGET) * 100} color={left < 0 ? "bg-rose-400" : "bg-jam-gold"} className="mt-3 bg-white/15" />
          <div className="mt-4 rounded-3xl bg-white/10 p-3 text-sm">
            🎯 Save at least <b>{jmd(BUDGET * SAVE_GOAL)}</b> (20%)<br />
            ✅ Needs covered: {covered.length}/{NEED_GROUPS.length}
          </div>
        </div>
        <button className="btn-green w-full py-3 text-lg" onClick={done}>Lock in my budget</button>
      </aside>
    </div>
  );
}
