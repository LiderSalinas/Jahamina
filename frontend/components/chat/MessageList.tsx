import { forwardRef } from "react";
import type { User } from "@/lib/types";
import { ChatEmptyState } from "./ChatEmptyState";
import { DisplayMessage, MessageBubble } from "./MessageBubble";

export const MessageList = forwardRef<HTMLDivElement, { messages: DisplayMessage[]; user: User; loadOlder: () => void; hasOlder: boolean; retry: (message: DisplayMessage) => void }>(function MessageList({ messages, user, loadOlder, hasOlder, retry }, ref) {
  return <div className="message-list" ref={ref} role="log" aria-label="Mensajes de la conversación">{hasOlder && <button className="load-older" type="button" onClick={loadOlder}>Cargar mensajes anteriores</button>}{!messages.length ? <ChatEmptyState /> : messages.map((message) => <MessageBubble key={`${message.id}-${message.client_message_id}`} message={message} own={message.remitente_id === user.id} retry={() => retry(message)} />)}</div>;
});
