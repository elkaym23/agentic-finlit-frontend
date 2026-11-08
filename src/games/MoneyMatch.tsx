import { useMemo, useState } from "react";
import { jmd, pick, type GameProps } from "./types";

const DENOMS = [1, 5, 10, 20, 50, 100, 500, 1000, 2000, 5000];
const ITEMS = [
  { name: "a bag of plantain chips", e: "🍌" }, { name: "a beef patty", e: "🥟" }, { name: "a box juice", e: "🧃" },
  { name: "a bulla and cheese", e: "🧀" }, { name: "a taxi fare", e: "🚕" }, { name: "an exercise book", e: "📓" },
  { name: "a coconut water", e: "🥥" }, { name: "a cricket ball", e: "🏏" }, { name: "a pack of crayons", e: "🖍️" },
  { name: "a bag of ackee", e: "🌿" }, { name: "a slice of toto", e: "🍰" }, { name: "a ticket to the match", e: "⚽" },
];
const ROUNDS = 5, NEED = 4;

function makeRound(r: number) {
  const pools = [[15, 35, 60, 75, 120], [160, 230, 350, 480, 650], [750, 1250, 1600, 2300, 3700]];
  const pool = pools[Math.min(2, Math.floor(r / 2))];
  return { target: pick(pool), item: pick(ITEMS) };
}

export default function MoneyMatch({ onFinish }: GameProps) {
  const [round, setRound] = useState(0);
  const [wins, setWins] = useState(0);
  const [tray, setTray] = useState<number[]>([]);
  const [feedback, setFeedback] = useState<null | { ok: boolean; text: string }>(null);
  const R = useMemo(() => makeRound(round), [round]);
  const total = tray.reduce((a, b) => a + b, 0);

  const check = () => {
    const ok = total === R.target;
    setFeedback({ ok, text: ok ? `Exactly ${jmd(R.target)}! Wicked! 🎉` : total > R.target ? `That's ${jmd(total)}, too much by ${jmd(total - R.target)}.` : `That's ${jmd(total)}, you need ${jmd(R.target - total)} more.` });
    if (ok) setWins((w) => w + 1);
  };
  const next = () => {
    const w = wins;
    if (round + 1 >= ROUNDS) {
      onFinish({ won: w >= NEED, score: w, details: { rounds: ROUNDS, correct: w },
        summary: w >= NEED ? `You made the right amount ${w} out of ${ROUNDS} times. You know your Jamaican money!` : `You got ${w} out of ${ROUNDS}. You need ${NEED} to win. Try again!` });
      return;
    }
    setRound(round + 1); setTray([]); setFeedback(null);
  };

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between text-sm font-semibold">
        <span>Round {round + 1} of {ROUNDS}</span><span className="chip bg-tile-mint">✅ {wins} correct</span>
      </div>
      <div className="rounded-4xl bg-tile-sun p-6 text-center">
        <div className="text-5xl">{R.item.e}</div>
        <div className="mt-2 text-lg">You want to buy {R.item.name}. It costs</div>
        <div className="text-4xl font-extrabold">{jmd(R.target)}</div>
      </div>

      <div className="min-h-[96px] rounded-4xl border-2 border-dashed border-black/10 p-3">
        <div className="mb-2 flex items-center justify-between text-sm"><b>Your money: {jmd(total)}</b>
          {tray.length > 0 && !feedback && <button className="text-ink-mute hover:text-ink" onClick={() => setTray([])}>Clear</button>}</div>
        <div className="flex flex-wrap gap-2">
          {tray.map((d, i) => (
            <button key={i} disabled={!!feedback} onClick={() => setTray(tray.filter((_, k) => k !== i))} title="Tap to remove"
                    className="animate-pop"><Money d={d} small /></button>
          ))}
          {!tray.length && <span className="p-2 text-sm text-ink-mute">Tap money below to add it here</span>}
        </div>
      </div>

      <div className="grid grid-cols-3 gap-3 sm:grid-cols-5">
        {DENOMS.map((d) => (
          <button key={d} disabled={!!feedback} onClick={() => setTray((t) => [...t, d])} className="transition hover:-translate-y-1 disabled:opacity-50">
            <Money d={d} />
          </button>
        ))}
      </div>

      {feedback ? (
        <div className={`flex flex-wrap items-center justify-between gap-3 rounded-3xl p-4 font-semibold ${feedback.ok ? "bg-emerald-50 text-emerald-800" : "bg-rose-50 text-rose-800"}`}>
          {feedback.text}<button className="btn-dark" onClick={next}>{round + 1 >= ROUNDS ? "See result" : "Next round →"}</button>
        </div>
      ) : (
        <button className="btn-green w-full py-3 text-lg" disabled={!tray.length} onClick={check}>Pay {jmd(total)}</button>
      )}
    </div>
  );
}

function Money({ d, small }: { d: number; small?: boolean }) {
  const coin = d < 50;
  return (
    <div className={`flex flex-col items-center gap-1 ${small ? "w-20" : "w-full"}`}>
      <img src={`/money/jmd_${d}.jpeg`} alt={`JA$${d} ${coin ? "coin" : "note"}`}
           className="aspect-[2/1] w-full rounded-xl bg-white object-contain p-1 shadow-sm" />
      {!small && <span className="text-xs font-bold">{jmd(d)}</span>}
    </div>
  );
}
