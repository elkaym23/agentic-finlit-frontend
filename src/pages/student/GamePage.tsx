import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api";
import { useAuth } from "../../auth";
import Mascot from "../../components/Mascot";
import { ErrorBox, celebrate } from "../../components/ui";
import BudgetBuilder from "../../games/BudgetBuilder";
import DebtDilemma from "../../games/DebtDilemma";
import MoneyMatch from "../../games/MoneyMatch";
import ProfitPuzzle from "../../games/ProfitPuzzle";
import type { GameProps, GameResult } from "../../games/types";
import type { NextStep } from "../../types";
import { nextLink } from "./StudentHome";

const GAMES: Record<string, { name: string; emoji: string; how: string; C: (p: GameProps) => JSX.Element }> = {
  money_match: { name: "Money Match", emoji: "💵", C: MoneyMatch,
    how: "Tap Jamaican coins and notes to make the exact amount. Get 4 out of 5 rounds right to win!" },
  budget_builder: { name: "Budget Builder", emoji: "🧾", C: BudgetBuilder,
    how: "You have JA$5,000 for the week. Cover every need, save at least 20%, and don't overspend!" },
  profit_puzzle: { name: "Profit Puzzle", emoji: "🍹", C: ProfitPuzzle,
    how: "Run a sorrel and juice stand for 5 days. Pick how many cups to make and your price. Earn JA$3,000 profit to win!" },
  debt_dilemma: { name: "Debt Dilemma", emoji: "💳", C: DebtDilemma,
    how: "Make 6 borrowing and credit choices. Pick wisely and keep your money healthy. Get 5 right to win!" },
};

interface ResultOut { xp: number; first_win: boolean; level_completed: boolean; continue: NextStep | null; graduated: boolean }

export default function GamePage() {
  const { slug = "" } = useParams();
  const { refresh } = useAuth();
  const g = GAMES[slug];
  const [round, setRound] = useState(0);
  const [started, setStarted] = useState(false);
  const [res, setRes] = useState<(GameResult & { out?: ResultOut; err?: string }) | null>(null);

  if (!g) return <ErrorBox error="That game doesn't exist." />;

  const finish = async (r: GameResult) => {
    setRes(r);
    try {
      const out = await api.post<ResultOut>(`/api/games/${slug}/result`, r);
      setRes({ ...r, out });
      if (r.won) celebrate();
      refresh();
    } catch (e: any) { setRes({ ...r, err: e.message }); }
  };
  const again = () => { setRes(null); setRound(round + 1); setStarted(true); };
  const next = nextLink(res?.out?.continue);

  return (
    <div className="mx-auto max-w-4xl">
      <Link to="/games" className="text-sm font-semibold text-ink-mute hover:text-ink">← All games</Link>
      <div className="mt-3 flex items-center gap-3">
        <div className="grid h-14 w-14 place-items-center rounded-3xl bg-jam-gold text-3xl">{g.emoji}</div>
        <h1 className="h-page">{g.name}</h1>
      </div>

      {!started ? (
        <div className="mt-6 flex flex-col items-center gap-5 rounded-5xl bg-tile-mint p-8 text-center sm:p-12">
          <div className="animate-bob"><Mascot size={120} mood="cheer" /></div>
          <p className="max-w-md text-lg">{g.how}</p>
          <button className="btn-green px-8 py-3 text-lg" onClick={() => setStarted(true)}>Start game 🎮</button>
        </div>
      ) : res ? (
        <div className={`mt-6 flex animate-pop flex-col items-center gap-4 rounded-5xl p-8 text-center sm:p-12 ${res.won ? "bg-tile-mint" : "bg-tile-peach"}`}>
          <Mascot size={110} mood={res.won ? "cheer" : "think"} />
          <h2 className="text-3xl font-extrabold">{res.won ? "You won! 🏆" : "Not this time!"}</h2>
          <p className="max-w-md text-lg">{res.summary}</p>
          {res.out && (
            <div className="flex flex-wrap justify-center gap-2">
              {res.out.xp > 0 && <span className="chip bg-jam-gold py-2">+{res.out.xp} XP</span>}
              {res.out.level_completed && res.won && <span className="chip bg-white py-2">✅ Level complete!</span>}
              {res.out.graduated && <span className="chip bg-ink py-2 text-white">🎓 You graduated SmartKids!</span>}
            </div>
          )}
          {res.err && <div className="text-sm font-medium text-rose-700">{res.err}</div>}
          <div className="mt-2 flex flex-wrap justify-center gap-3">
            <button className="btn-ghost" onClick={again}>Play again</button>
            {res.won && next && next.to !== `/games/${slug}` && <Link className="btn-green" to={next.to}>{next.label} →</Link>}
            {!res.won && <Link className="btn-dark" to="/tutor">Ask FinBuddy for tips</Link>}
          </div>
        </div>
      ) : (
        <div className="mt-6"><g.C key={round} onFinish={finish} /></div>
      )}
    </div>
  );
}
