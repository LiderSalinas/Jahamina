export function ChatEmptyState({ unavailable = false }: { unavailable?: boolean }) {
  return <div className="chat-empty"><span aria-hidden="true">✦</span><p>{unavailable ? "El chat estará disponible cuando la reserva sea aceptada." : "La coordinación empieza aquí. Envía el primer mensaje."}</p></div>;
}
