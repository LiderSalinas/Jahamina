import type { ReactNode } from "react";

export function PageHeader({ eyebrow, title, description, action }: { eyebrow?: string; title: string; description?: string; action?: ReactNode }) {
  return <header className="page-header"><div>{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1>{title}</h1>{description && <p>{description}</p>}</div>{action && <div className="page-header-action">{action}</div>}</header>;
}

export function SurfaceCard({ children, className = "", as = "section" }: { children: ReactNode; className?: string; as?: "section" | "article" | "div" }) {
  const Tag = as;
  return <Tag className={`surface-card ${className}`.trim()}>{children}</Tag>;
}

export function AsyncState({ kind = "empty", title, description, action, icon }: { kind?: "loading" | "empty" | "error" | "success"; title: string; description?: string; action?: ReactNode; icon?: string }) {
  return <div className={`async-state async-state-${kind}`} role={kind === "error" ? "alert" : "status"}><span aria-hidden>{icon ?? (kind === "loading" ? "…" : kind === "error" ? "!" : kind === "success" ? "✓" : "J")}</span><div><h2>{title}</h2>{description && <p>{description}</p>}{action && <div className="async-state-action">{action}</div>}</div></div>;
}
