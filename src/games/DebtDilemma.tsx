import { useMemo, useState } from "react";
import { jmd, shuffle, type GameProps } from "./types";

type Choice = { text: string; good: boolean; effect: number; why: string };
type Scene = { e: string; story: string; choices: Choice[] };

const SCENES: Scene[] = [
  { e: "📱", story: "Your phone screen cracked. A fix costs JA$8,000. You have JA$3,000 saved.", choices: [
    { text: "Borrow from a 'quick cash' lender at 30% a month", good: false, effect: -4000, why: "30% a month is huge! In 3 months you'd owe about JA$9,500 interest on JA$5,000." },
    { text: "Use your JA$3,000 and save the rest over a few weeks", good: true, effect: 0, why: "Waiting and saving costs you no interest at all." },
    { text: "Buy a brand-new phone on a store credit plan", good: false, effect: -6000, why: "You'd take on a much bigger debt to fix a small problem." }] },
  { e: "💳", story: "Your credit card bill is JA$20,000. The minimum payment is JA$1,000.", choices: [
    { text: "Pay just the minimum every month", good: false, effect: -3000, why: "Interest keeps growing on the rest. It could take years to pay off!" },
    { text: "Pay as much as you can, at least JA$5,000", good: true, effect: 1000, why: "Paying more than the minimum cuts the interest you pay." },
    { text: "Skip this month, pay next month", good: false, effect: -2500, why: "Late fees plus interest, and a hit to your credit score." }] },
  { e: "🧑🏾‍🤝‍🧑🏽", story: "Your friend wants to borrow JA$5,000 and says they'll pay you back 'soon'.", choices: [
    { text: "Lend only what you can afford to lose, with a clear payback date", good: true, effect: 0, why: "Clear terms protect your money AND your friendship." },
    { text: "Lend it all, no questions asked", good: false, effect: -2500, why: "Without a plan, money lent to friends often doesn't come back." },
    { text: "Take out a loan so you can lend it to them", good: false, effect: -3500, why: "Never borrow money to lend it. You'd owe interest on someone else's debt." }] },
  { e: "🏦", story: "You need JA$50,000 to start a small baking business. Which loan is best?", choices: [
    { text: "Credit union loan at 12% a year", good: true, effect: 1500, why: "Credit unions often have lower rates. 12% a year is much cheaper than the others." },
    { text: "Payday lender at 15% a month", good: false, effect: -5000, why: "15% a month is about 180% a year. Super expensive!" },
    { text: "Put it all on a credit card at 45% a year", good: false, effect: -3000, why: "Card interest is high. It's better for short, small purchases." }] },
  { e: "🎁", story: "A store offers 'Buy now, pay later!' on a JA$30,000 gaming console.", choices: [
    { text: "Read the fine print: total cost, interest and fees", good: true, effect: 500, why: "'Pay later' plans can hide a much bigger total price." },
    { text: "Sign up right away, it's free money!", good: false, effect: -4000, why: "It's not free. It's debt, and missed payments add fees." },
    { text: "Sign up for two consoles to sell one", good: false, effect: -5000, why: "Double the debt, and there's no promise you'll sell it." }] },
  { e: "📊", story: "You got a JA$10,000 bonus. You owe JA$10,000 on a loan at 25% interest.", choices: [
    { text: "Pay off the loan", good: true, effect: 2500, why: "Paying off high-interest debt is like earning 25% on your money!" },
    { text: "Put it in a savings account at 2%", good: false, effect: -2000, why: "You'd earn 2% but keep paying 25%. You lose money." },
    { text: "Spend it on a party and keep the loan", good: false, effect: -3000, why: "The debt keeps growing while the bonus disappears." }] },
  { e: "📉", story: "A lender says your credit score is low. Why might that be?", choices: [
    { text: "Missed or late bill payments", good: true, effect: 500, why: "Paying on time is the biggest part of a good credit score." },
    { text: "You save money every month", good: false, effect: -1000, why: "Saving doesn't hurt your score. Late payments do." },
    { text: "You checked your own credit report", good: false, effect: -1000, why: "Checking your own report doesn't lower your score." }] },
];
const ROUNDS = 6, NEED = 5, START = 10000;

export default function DebtDilemma({ onFinish }: GameProps) {
  const scenes = useMemo(() => shuffle(SCENES).slice(0, ROUNDS).map((s) => ({ ...s, choices: shuffle(s.choices) })), []);
  const [i, setI] = useState(0);
  const [picked, setPicked] = useState<Choice | null>(null);
  const [good, setGood] = useState(0);
  const [money, setMoney] = useState(START);
  const s = scenes[i];

  const choose = (c: Choice) => {
    if (picked) return;
    setPicked(c);
    setMoney((m) => m + c.effect);
    if (c.good) setGood((g) => g + 1);
  };
  const next = () => {
    if (i + 1 >= ROUNDS) {
      onFinish({ won: good >= NEED, score: good, details: { correct: good, money },
        summary: good >= NEED ? `${good}/${ROUNDS} smart choices and you finished with ${jmd(money)}. You're a debt boss!` : `${good}/${ROUNDS} smart choices. You need ${NEED}. High interest is a trap. Read every choice carefully!` });
      return;
    }
    setI(i + 1); setPicked(null);
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-2 text-sm font-semibold">
        <span>Choice {i + 1} of {ROUNDS}</span>
        <div className="flex gap-2"><span className="chip bg-tile-mint">✅ {good} smart</span><span className={`chip ${money >= START ? "bg-tile-sun" : "bg-rose-100 text-rose-800"}`}>💰 {jmd(money)}</span></div>
      </div>
      <div key={i} className="animate-pop rounded-4xl bg-tile-lilac p-6 sm:p-8">
        <div className="text-5xl">{s.e}</div>
        <p className="mt-3 text-xl font-bold leading-snug">{s.story}</p>
        <div className="mt-5 grid gap-3">
          {s.choices.map((c) => {
            const show = picked && (c === picked || c.good);
            return (
              <button key={c.text} onClick={() => choose(c)} disabled={!!picked}
                      className={`rounded-3xl border-2 bg-white p-4 text-left font-medium transition ${!picked ? "border-transparent hover:border-black/15" : show ? (c.good ? "border-jam-green bg-emerald-50" : "border-rose-300 bg-rose-50") : "border-transparent opacity-50"}`}>
                {c.text}
                {show && <div className="mt-1 text-sm font-normal text-ink-soft">{c.good ? "✅ " : "❌ "}{c.why}</div>}
              </button>
            );
          })}
        </div>
      </div>
      {picked && <button className="btn-dark w-full py-3" onClick={next}>{i + 1 >= ROUNDS ? "See result" : "Next →"}</button>}
    </div>
  );
}
