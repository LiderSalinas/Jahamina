"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { api, ApiError } from "@/lib/api";
import type { Conversation } from "@/lib/types";
import { ChatEmptyState } from "./ChatEmptyState";
import { ConnectionStatus } from "./ConnectionStatus";
import { MessageComposer } from "./MessageComposer";
import type { DisplayMessage } from "./MessageBubble";
import { MessageList } from "./MessageList";
import { TypingIndicator } from "./TypingIndicator";

type ConnectionState = "connected" | "reconnecting" | "disconnected";

export function ChatPanel({ reservationId }: { reservationId: number }) {
  const { token, user } = useAuth();
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<DisplayMessage[]>([]);
  const [cursor, setCursor] = useState<number | null>(null);
  const [connection, setConnection] = useState<ConnectionState>("disconnected");
  const [typing, setTyping] = useState(false);
  const [unavailable, setUnavailable] = useState(false);
  const [error, setError] = useState("");
  const socketRef = useRef<WebSocket | null>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const reconnectCount = useRef(0);
  const connectRef = useRef<(current: Conversation) => Promise<void>>(async () => undefined);
  const reconnectTimer = useRef<number | null>(null);
  const typingTimer = useRef<number | null>(null);
  const mounted = useRef(true);

  const mergeMessage = useCallback((message: DisplayMessage) => {
    setMessages((current) => {
      const index = current.findIndex((item) => item.id === message.id || Boolean(message.client_message_id && item.client_message_id === message.client_message_id));
      if (index < 0) return [...current, { ...message, delivery: "sent" }];
      const next = [...current]; next[index] = { ...message, delivery: "sent" }; return next;
    });
  }, []);

  const connect = useCallback(async (current: Conversation) => {
    if (!token || !mounted.current) return;
    if (
      socketRef.current?.readyState === WebSocket.OPEN
      || socketRef.current?.readyState === WebSocket.CONNECTING
    ) return;
    setConnection(reconnectCount.current ? "reconnecting" : "disconnected");
    try {
      const socket = new WebSocket(await api.chatWebSocketUrl(current.id, token));
      socketRef.current = socket;
      socket.onopen = async () => {
        if (!mounted.current) return;
        const wasReconnecting = reconnectCount.current > 0;
        reconnectCount.current = 0;
        if (wasReconnecting) {
          const page = await api.chatMessages(current.id, token);
          if (mounted.current) {
            setMessages(page.items);
            setCursor(page.next_cursor);
            await api.markChatRead(current.id, token);
            window.dispatchEvent(new Event("jahamina:unread-changed"));
          }
        }
      };
      socket.onmessage = (raw) => {
        const event = JSON.parse(raw.data) as { type: string; data: Record<string, unknown> };
        if (event.type === "connected") setConnection("connected");
        if (event.type === "message.created") {
          const message = event.data as unknown as DisplayMessage;
          mergeMessage(message);
          if (message.remitente_id !== user?.id) {
            void api.markChatRead(current.id, token).then(() => {
              window.dispatchEvent(new Event("jahamina:unread-changed"));
            });
          }
        }
        if (event.type === "message.read") setMessages((items) => items.map((item) => item.remitente_id === user?.id ? { ...item, leido_en: String(event.data.leido_en) } : item));
        if (event.type === "typing.started" && event.data.usuario_id !== user?.id) { setTyping(true); if (typingTimer.current) window.clearTimeout(typingTimer.current); typingTimer.current = window.setTimeout(() => setTyping(false), 2500); }
        if (event.type === "typing.stopped") setTyping(false);
      };
      socket.onclose = () => { if (socketRef.current === socket) socketRef.current = null; if (!mounted.current) return; setConnection("reconnecting"); reconnectCount.current += 1; reconnectTimer.current = window.setTimeout(() => connectRef.current(current), Math.min(15000, 1000 * 2 ** reconnectCount.current)); };
      socket.onerror = () => socket.close();
    } catch { if (mounted.current) { setConnection("reconnecting"); reconnectCount.current += 1; reconnectTimer.current = window.setTimeout(() => connectRef.current(current), Math.min(15000, 1000 * 2 ** reconnectCount.current)); } }
  }, [mergeMessage, token, user?.id]);

  useEffect(() => {
    mounted.current = true;
    connectRef.current = connect;
    if (!token) return;
    api.conversationByReservation(reservationId, token).then(async (current) => {
      if (!mounted.current) return; setConversation(current);
      const page = await api.chatMessages(current.id, token); if (!mounted.current) return;
      setMessages(page.items); setCursor(page.next_cursor); await api.markChatRead(current.id, token); window.dispatchEvent(new Event("jahamina:unread-changed")); await connect(current);
    }).catch((caught) => { if (caught instanceof ApiError && (caught.status === 409 || caught.status === 404)) setUnavailable(true); else setError(caught instanceof Error ? caught.message : "No se pudo cargar el chat."); });
    return () => { mounted.current = false; socketRef.current?.close(); if (reconnectTimer.current) window.clearTimeout(reconnectTimer.current); if (typingTimer.current) window.clearTimeout(typingTimer.current); };
  }, [connect, reservationId, token]);

  useEffect(() => { const element = listRef.current; if (element && element.scrollHeight - element.scrollTop - element.clientHeight < 180) element.scrollTo({ top: element.scrollHeight, behavior: "smooth" }); }, [messages]);

  const send = useCallback(async (content: string, previousId?: string | null) => {
    if (!conversation || !token || !user) return;
    const clientId = previousId || crypto.randomUUID();
    mergeMessage({ id: -Date.now(), conversacion_id: conversation.id, remitente_id: user.id, contenido: content, tipo: "texto", creado_en: new Date().toISOString(), editado_en: null, leido_en: null, eliminado: false, client_message_id: clientId, delivery: "sending" });
    if (socketRef.current?.readyState === WebSocket.OPEN) socketRef.current.send(JSON.stringify({ type: "message.send", data: { contenido: content, client_message_id: clientId } }));
    else try { mergeMessage(await api.sendChatMessage(conversation.id, { contenido: content, client_message_id: clientId }, token)); } catch { setMessages((items) => items.map((item) => item.client_message_id === clientId ? { ...item, delivery: "error" } : item)); }
  }, [conversation, mergeMessage, token, user]);

  async function loadOlder() { if (!conversation || !token || !cursor) return; const page = await api.chatMessages(conversation.id, token, cursor); setMessages((items) => [...page.items, ...items]); setCursor(page.next_cursor); }
  function signalTyping(active: boolean) { if (socketRef.current?.readyState === WebSocket.OPEN) socketRef.current.send(JSON.stringify({ type: active ? "typing.start" : "typing.stop", data: {} })); }

  if (unavailable) return <section className="chat-panel"><ChatEmptyState unavailable /></section>;
  if (!conversation || !user) return <section className="chat-panel chat-skeleton" aria-busy="true">{error || "Cargando conversación…"}</section>;
  return <section className="chat-panel"><header><div><p className="eyebrow">Chat del viaje</p><h2>{conversation.participante}</h2><span>{conversation.origen} → {conversation.destino}</span></div><ConnectionStatus status={connection} /></header><MessageList ref={listRef} messages={messages} user={user} loadOlder={loadOlder} hasOlder={Boolean(cursor)} retry={(message) => send(message.contenido, message.client_message_id)} /><TypingIndicator visible={typing} /><MessageComposer disabled={!conversation.puede_escribir} onSend={send} onTyping={signalTyping} /></section>;
}
