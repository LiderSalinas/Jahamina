export function ChatEmptyState({ unavailable = false, accepted = false }: { unavailable?: boolean; accepted?: boolean }) {
  const message = unavailable
    ? accepted ? "No hay mensajes en esta conversación." : "El chat estará disponible cuando la reserva sea aceptada."
    : "No hay mensajes en esta conversación. Podés enviar el primero.";
  return <div className="chat-empty"><span aria-hidden="true">✦</span><p>{message}</p></div>;
}
