import { useMemo, useState } from "react";
import { jmd, shuffle, type GameProps } from "./types";

const DAYS = 5, TARGET = 3000, COST = 60, START_CASH = 3000;
const WEATHER = [
  { name: "Hot and sunny", e: "☀️", demand: 1.4 }, { name: "Warm", e: "🌤️", demand: 1.0 },
  { name: "Cloudy", e: "☁️", demand: 0.75 }, { name: "Rainy", e: "🌧️", demand: 0.45 }, { name: "Sports day crowd!", e: "🏃🏾", demand: 1.7 },
];
type Day = { weather: typeof WEATHER[number]; cups: number; price: number; sold: number; profit: number };

/** Cups people want: base ~40, scaled by weather, lower when the price is high. */
function demand(price: number, w: number) { return Math.max(0, Math.round((60 - price * 0.25) * w + (Math.random() * 6 - 3))); }

export default function ProfitPuzzle({ onFinish }: GameProps) {
  const forecast = useMemo(() => shuffle(WEATHER).slice(0, DAYS), []);
  const [days, setDays] = useState<Day[]>([]);
  const [cups, setCups] = useState(30);
  const [price, setPrice] = useState(120);
  const d = days.length;
  const cash = START_CASH + days.reduce((a, x) => a + x.profit, 0);
  const profit = cash - START_CASH;
  const w = forecast[Math.min(d, DAYS - 1)];
  const last = days[d - 1];
  const cost = cups * COST;

  const sell = () => {
    if (cost > cash) return;
    const sold = Math.min(cups, demand(price, w.demand));
    const p = sold * price - cost;
    const nd = [...days, { weather: w, cups, price, sold, profit: p }];
    setDays(nd);
    if (nd.length === DAYS) {
      const total = nd.reduce((a, x) => a + x.profit, 0);
      setTimeout(() => onFinish({ won: total >= TARGET, score: total, details: { days: nd.map(({ weather, ...x }) => ({ ...x, weather: weather.name })) },
        summary: total >= TARGET ? `You made ${jmd(total)} profit in 5 days! Smart pricing, boss.` : `You made ${jmd(total)} profit. The goal was ${jmd(TARGET)}. Watch the weather and don't make too many cups!` }), 1400);
    }
  };

  return (
    <div className="space-y-5">
      <div className="grid grid-cols-3 gap-3 text-center">
        <div className="rounded-3xl bg-tile-sun p-4"><div className="text-xs text-ink-mute">Day</div><div className="text-2xl font-extrabold">{Math.min(d + 1, DAYS)}/{DAYS}</div></div>
        <div className="rounded-3xl bg-tile-mint p-4"><div className="text-xs text-ink-mute">Cash</div><div className="text-2xl font-extrabold">{jmd(cash)}</div></div>
        <div className={`rounded-3xl p-4 ${profit >= TARGET ? "bg-jam-green text-white" : "bg-tile-lilac"}`}><div className="text-xs opacity-70">Profit / goal</div><div className="text-2xl font-extrabold">{jmd(profit)}</div><div className="text-xs">of {jmd(TARGET)}</div></div>
      </div>

      {last && (
        <div className="animate-pop rounded-3xl bg-[#f7f6fb] p-4 text-sm">
          <b>Day {d} report {last.weather.e}:</b> made {last.cups} cups, sold <b>{last.sold}</b> at {jmd(last.price)}.
          Earned {jmd(last.sold * last.price)}, cost {jmd(last.cups * COST)} → <b className={last.profit >= 0 ? "text-emerald-700" : "text-rose-700"}>{last.profit >= 0 ? "profit" : "loss"} {jmd(Math.abs(last.profit))}</b>
          {last.sold === last.cups && " · You sold out! Maybe make more?"}
          {last.sold < last.cups * 0.6 && " · Lots of leftover cups. Wasted money!"}
        </div>
      )}

      {d < DAYS && (
        <div className="rounded-4xl border border-black/5 bg-white p-6">
          <div className="flex items-center gap-3">
            <span className="text-5xl">{w.e}</span>
            <div><div className="text-sm text-ink-mute">Today's weather</div><div className="text-xl font-bold">{w.name}</div></div>
          </div>
          <div className="mt-6 grid gap-6 sm:grid-cols-2">
            <label className="block">
              <span className="label">Cups to make: <b>{cups}</b> <span className="font-normal text-ink-mute">({jmd(COST)} each = {jmd(cost)})</span></span>
              <input type="range" min={5} max={90} step={5} value={cups} onChange={(e) => setCups(+e.target.value)} className="w-full accent-[#009b3a]" />
            </label>
            <label className="block">
              <span className="label">Price per cup: <b>{jmd(price)}</b></span>
              <input type="range" min={60} max={220} step={10} value={price} onChange={(e) => setPrice(+e.target.value)} className="w-full accent-[#009b3a]" />
            </label>
          </div>
          <p className="mt-3 text-xs text-ink-mute">Tip: higher prices mean fewer buyers. Hot days bring more customers. Profit = money in − cost of cups.</p>
          {cost > cash && <p className="mt-2 text-sm font-medium text-rose-700">You can't afford that many cups.</p>}
          <button className="btn-green mt-4 w-full py-3 text-lg" disabled={cost > cash} onClick={sell}>Open the stand 🍹</button>
        </div>
      )}
      {d === DAYS && <div className="text-center font-semibold text-ink-mute">Counting your money…</div>}
    </div>
  );
}
