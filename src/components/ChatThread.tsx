import { useEffect, useRef, useState } from "react";
import type { ChatMsg } from "../types";
import Mascot from "./Mascot";
import { Markdown } from "./ui";

/** Chat UI shared by the quiz review and the free tutor. `send` returns the assistant reply. */
export default function ChatThread({ messages, send, suggestions = [], placeholder = "Ask Casheous anything…", height = "h-[460px]" }:
  { messages: ChatMsg[]; send: (text: string) => Promise<string>; suggestions?: string[]; placeholder?: string; height?: string }) {
  const [msgs, setMsgs] = useState<ChatMsg[]>(messages);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const end = useRef<HTMLDivElement>(null);

  useEffect(() => setMsgs(messages), [messages]);
  useEffect(() => { end.current?.scrollIntoView({ behavior: "smooth", block: "nearest" }); }, [msgs, busy]);

  const submit = async (t: string) => {
    const q = t.trim();
    if (!q || busy) return;
    setErr(null);
    setText("");
    setMsgs((m) => [...m, { role: "user", content: q }]);
    setBusy(true);
    try {
      const reply = await send(q);
      setMsgs((m) => [...m, { role: "assistant", content: reply }]);
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="flex flex-col">
      <div className={`${height} space-y-4 overflow-y-auto rounded-3xl bg-[#f7f6fb] p-4 scroll-thin`}>
        {msgs.map((m, i) => (
          <div key={i} className={`flex items-end gap-2 ${m.role === "user" ? "justify-end" : ""}`}>
            {m.role === "assistant" && <div className="mb-1 shrink-0 rounded-full bg-white p-0.5 shadow-sm"><Mascot size={34} face /></div>}
            <div className={`max-w-[82%] animate-pop rounded-3xl px-4 py-2.5 text-[15px] leading-relaxed ${
              m.role === "user" ? "rounded-br-lg bg-jam-green text-white" : "rounded-bl-lg bg-white text-ink shadow-sm"}`}>
              {m.role === "assistant" ? <Markdown className="prose-chat">{m.content}</Markdown> : m.content}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex items-end gap-2">
            <div className="rounded-full bg-white p-0.5 shadow-sm"><Mascot size={34} mood="think" face /></div>
            <div className="flex gap-1 rounded-3xl rounded-bl-lg bg-white px-4 py-3 shadow-sm">
              {[0, 1, 2].map((d) => <span key={d} className="h-2 w-2 animate-bounce rounded-full bg-jam-green/60" style={{ animationDelay: `${d * 120}ms` }} />)}
            </div>
          </div>
        )}
        <div ref={end} />
      </div>
      {err && <div className="mt-2 text-sm font-medium text-rose-600">😕 {err}</div>}
      {suggestions.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {suggestions.map((s) => (
            <button key={s} disabled={busy} onClick={() => submit(s)} className="chip border border-black/10 bg-white py-1.5 text-sm text-ink-soft hover:border-jam-green hover:text-jam-green">{s}</button>
          ))}
        </div>
      )}
      <form className="mt-3 flex gap-2" onSubmit={(e) => { e.preventDefault(); submit(text); }}>
        <input className="input" value={text} onChange={(e) => setText(e.target.value)} placeholder={placeholder} maxLength={2000} aria-label="Message" />
        <button className="btn-green shrink-0" disabled={busy || !text.trim()}>Send</button>
      </form>
    </div>
  );
}
