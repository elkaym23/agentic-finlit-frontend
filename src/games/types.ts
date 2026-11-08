export interface GameResult { won: boolean; score: number; summary: string; details: Record<string, unknown> }
export interface GameProps { onFinish: (r: GameResult) => void }

export const jmd = (n: number) => `JA$${Math.round(n).toLocaleString("en-JM")}`;
export const shuffle = <T,>(a: T[]) => { const b = [...a]; for (let i = b.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [b[i], b[j]] = [b[j], b[i]]; } return b; };
export const pick = <T,>(a: T[]) => a[Math.floor(Math.random() * a.length)];
