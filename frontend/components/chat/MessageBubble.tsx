import type { ChatMessage } from "@/lib/types";

export type DisplayMessage = ChatMessage & { delivery?: "sending" | "sent" | "error" };

export function MessageBubble({ message, own, retry }: { message: DisplayMessage; own: boolean; retry?: () => void }) {
  const time = new Date(message.creado_en).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  if (message.tipo === "sistema") return <div className="system-message"><span>{message.contenido}</span><time>{time}</time></div>;
  return <article className={`message-bubble ${own ? "own" : "other"}`}><p>{message.contenido}</p><footer><time>{time}</time>{own && <span>{message.delivery === "sending" ? "Enviando…" : message.delivery === "error" ? "Error" : message.leido_en ? "Leído" : "Enviado"}</span>}{message.delivery === "error" && retry && <button type="button" onClick={retry}>Reintentar</button>}</footer></article>;
}
