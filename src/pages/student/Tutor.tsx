import { useRef } from "react";
import { api } from "../../api";
import { useAuth } from "../../auth";
import ChatThread from "../../components/ChatThread";
import Mascot from "../../components/Mascot";
import type { ChatMsg } from "../../types";

export default function Tutor() {
  const { user } = useAuth();
  const history = useRef<ChatMsg[]>([]);
  const welcome: ChatMsg[] = [{ role: "assistant", content: `Hi ${user?.name ?? "there"}! 🐦 I'm **FinBuddy**. Ask me anything about money: saving, budgeting, banks, or running a business. Wha yuh waan know?` }];

  const send = async (message: string) => {
    const r = await api.post<{ reply: string }>("/api/chat", { message, history: history.current.slice(-10) });
    history.current.push({ role: "user", content: message }, { role: "assistant", content: r.reply });
    return r.reply;
  };

  return (
    <div className="mx-auto max-w-3xl">
      <div className="mb-5 flex items-center gap-4">
        <div className="animate-bob"><Mascot size={76} mood="happy" /></div>
        <div>
          <h1 className="h-page">Ask FinBuddy</h1>
          <p className="muted">Your doctor-bird money tutor. It uses your lessons to answer.</p>
        </div>
      </div>
      <ChatThread messages={welcome} send={send} height="h-[min(60vh,560px)]"
                  suggestions={["What's the difference between a need and a want?", "How do I make a budget with JA$2000?",
                                "What is interest?", "How can I start a small business at school?"]} />
    </div>
  );
}
