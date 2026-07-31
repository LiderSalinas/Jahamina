export function ConnectionStatus({ status }: { status: string }) {
  const label = status === "connected" ? "Conectado" : status === "reconnecting" ? "Reconectando…" : "Desconectado";
  return <span className={`connection-status ${status}`} aria-live="polite"><i />{label}</span>;
}
