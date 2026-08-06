import { KeyboardEvent, useState } from "react";

export function MessageComposer({ disabled, onSend, onTyping }: { disabled: boolean; onSend: (content: string) => Promise<void>; onTyping: (active: boolean) => void }) {
  const [content, setContent] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");

  async function submit() {
    const clean = content.trim();
    if (!clean || disabled || sending) return;
    setSending(true);
    setError("");
    try {
      await onSend(clean);
      setContent("");
      onTyping(false);
    } catch {
      setContent((current) => current || clean);
      setError("No pudimos enviar el mensaje. Podés intentarlo nuevamente.");
    } finally {
      setSending(false);
    }
  }

  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      void submit();
    }
  }

  return <div className="message-composer"><textarea aria-label="Escribe un mensaje" value={content} maxLength={1000} disabled={disabled || sending} placeholder={disabled ? "El chat está cerrado" : "Escribe un mensaje…"} onChange={(event) => { setContent(event.target.value); setError(""); onTyping(Boolean(event.target.value)); }} onKeyDown={keyDown} />{error && <p className="error-message" role="alert">{error}</p>}<div><span>{content.length}/1000</span><button className="button-primary" type="button" disabled={disabled || sending || !content.trim()} onClick={() => void submit()}>{sending ? "Enviando…" : "Enviar"}</button></div></div>;
}
