import { useState } from "react";
import ChatLog from "./components/ChatLog";
import InputBar from "./components/InputBar";

export type ChatMsg = { role: "user" | "assistant"; content: string };

const API = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8008").replace(/\/$/, "");

export default function App() {
  const [sessionId, setSessionId] = useState<string>("alex-1");
  const [messages, setMessages] = useState<ChatMsg[]>([]);
  const [busy, setBusy] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (text: string) => {
    const msg = text.trim();
    if (!msg || busy) return;

    setMessages((m) => [...m, { role: "user", content: msg }]);
    setBusy(true);
    setError(null);

    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: msg })
      });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data: { reply: string } = await res.json();
      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Request failed";
      setError(msg);
      setMessages((m) => [...m, { role: "assistant", content: "Request failed." }]);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h2>MTG Chat (Strands + MCP)</h2>
        <div className="session">
          <label>
            Session:&nbsp;
            <input
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              placeholder="session id"
            />
          </label>
        </div>
      </header>

      <main>
        <ChatLog messages={messages} />
      </main>

      <footer>
        <InputBar onSend={sendMessage} disabled={busy} />
        {busy && <div className="status">Thinking…</div>}
        {error && <div className="error">Error: {error}</div>}
      </footer>
    </div>
  );
}
