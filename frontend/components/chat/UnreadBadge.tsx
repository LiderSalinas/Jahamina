export function UnreadBadge({ count }: { count: number }) {
  if (!count) return null;
  return <span className="unread-badge" aria-label={`${count} mensajes no leídos`}>{count > 99 ? "99+" : count}</span>;
}
