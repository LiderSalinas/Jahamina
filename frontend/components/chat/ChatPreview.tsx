"use client";

import { useEffect, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api, ApiError } from "@/lib/api";
import type { ChatMessage, Conversation } from "@/lib/types";
import { ChatPanel } from "./ChatPanel";

export function ChatPreview({ reservationId, reservationState, tripState }: { reservationId: number; reservationState: string; tripState?: string }) {
  const { token, user } = useAuth();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [unavailable, setUnavailable] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!token) return;
    let active = true;
    api.conversationByReservation(reservationId, token)
      .then(async (current) => { const page = await api.chatMessages(current.id, token); if (active) { setConversation(current); setMessages(page.items.slice(-3)); } })
      .catch((caught) => { if (active && caught instanceof ApiError && [404, 409].includes(caught.status)) setUnavailable(true); });
    return () => { active = false; };
  }, [reservationId, token]);

  useEffect(() => {
    const show = () => setOpen(true);
    window.addEventListener("jahamina:open-chat", show);
    return () => window.removeEventListener("jahamina:open-chat", show);
  }, []);

  const accepted = ["aceptada", "finalizada"].includes(reservationState);
  return <>
    <div className="chat-preview-body">
      {conversation && <div className="chat-preview-person"><span aria-hidden>{conversation.participante.slice(0, 1).toUpperCase()}</span><div><b>{conversation.participante}</b><small>{["conductor_en_camino", "conductor_en_punto"].includes(tripState ?? "") ? "En camino" : tripState === "en_curso" ? "Viaje en curso" : "Conversación disponible"}</small></div></div>}
      {messages.length > 0 ? <ol className="chat-preview-messages">{messages.map((message) => <li key={message.id}><div><b>{message.tipo === "sistema" ? "Jahamina" : message.remitente_id === user?.id ? "Vos" : conversation?.participante}</b><time>{new Date(message.creado_en).toLocaleTimeString("es-PY", { hour: "2-digit", minute: "2-digit" })}</time></div><p>{message.contenido}</p></li>)}</ol> : <p className="chat-preview-empty">{unavailable && !accepted ? "El chat estará disponible cuando la reserva sea aceptada." : "No hay mensajes en esta conversación."}</p>}
      {(conversation || accepted) && <button className="button-secondary chat-preview-action" type="button" onClick={() => setOpen(true)}>Ver conversación</button>}
    </div>
    {open && <div className="chat-dialog-backdrop" role="presentation" onMouseDown={(event) => { if (event.currentTarget === event.target) setOpen(false); }}><section className="chat-dialog" role="dialog" aria-modal="true" aria-labelledby="full-chat-title"><header><div><p className="ui-eyebrow">Reserva #{reservationId}</p><h2 id="full-chat-title">Chat del viaje</h2></div><button type="button" aria-label="Cerrar conversación" onClick={() => setOpen(false)}>×</button></header><ChatPanel reservationId={reservationId} reservationState={reservationState}/></section></div>}
  </>;
}
