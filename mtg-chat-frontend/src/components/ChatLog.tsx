import type { ChatMsg } from "../App";

type Props = { messages: ChatMsg[] };

export default function ChatLog({ messages }: Props) {
  if (!messages?.length) {
    return <div style={{ color: "#9aa3b2" }}>Ask about Magic: The Gathering…</div>;
    }
  return (
    <div>
      {messages.map((m, i) => (
        <div key={i} className={`message ${m.role}`}>
          <strong>{m.role === "user" ? "You" : "Agent"}: </strong>
          {m.content}
        </div>
      ))}
    </div>
  );
}
