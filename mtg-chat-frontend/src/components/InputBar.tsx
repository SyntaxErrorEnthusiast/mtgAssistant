import { useRef, useState } from "react";

type Props = {
  onSend?: (text: string) => void;
  disabled?: boolean;
};

export default function InputBar({ onSend, disabled }: Props) {
  const [text, setText] = useState<string>("");
  const ref = useRef<HTMLTextAreaElement | null>(null);

  const submit = () => {
    const t = text.trim();
    if (!t) return;
    onSend?.(t);
    setText("");
    ref.current?.focus();
  };

  const onKeyDown: React.KeyboardEventHandler<HTMLTextAreaElement> = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      submit();
    }
  };

  return (
    <div className="inputbar">
      <textarea
        ref={ref}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={onKeyDown}
        placeholder={`e.g., What does "Wilhelt, the Rotcleaver" do?`}
        disabled={disabled}
      />
      <button onClick={submit} disabled={disabled || !text.trim()}>
        Send
      </button>
    </div>
  );
}
