import { KeyboardEvent, useState } from "react";

export function MessageComposer({ disabled, onSend, onTyping }: { disabled: boolean; onSend: (content: string) => void; onTyping: (active: boolean) => void }) {
  const [content, setContent] = useState("");
  function submit() { const clean = content.trim(); if (!clean || disabled) return; onSend(clean); setContent(""); onTyping(false); }
  function keyDown(event: KeyboardEvent<HTMLTextAreaElement>) { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submit(); } }
  return <div className="message-composer"><textarea aria-label="Escribe un mensaje" value={content} maxLength={1000} disabled={disabled} placeholder={disabled ? "El chat está cerrado" : "Escribe un mensaje…"} onChange={(event) => { setContent(event.target.value); onTyping(Boolean(event.target.value)); }} onKeyDown={keyDown} /><div><span>{content.length}/1000</span><button className="button-primary" type="button" disabled={disabled || !content.trim()} onClick={submit}>Enviar</button></div></div>;
}
