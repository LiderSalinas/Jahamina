export function TypingIndicator({ visible }: { visible: boolean }) {
  return <div className="typing-indicator" aria-live="polite">{visible ? "La otra persona está escribiendo…" : "\u00a0"}</div>;
}
