import Link from "next/link";

type JahaminaBrandProps = {
  className?: string;
  compact?: boolean;
  onClick?: () => void;
};

export function JahaminaBrand({ className = "", compact = false, onClick }: JahaminaBrandProps) {
  return (
    <Link className={`brand ${className}`.trim()} href="/" aria-label="Jahamina, Vamos juntos" onClick={onClick}>
      <svg className="brand-symbol" viewBox="0 0 48 48" aria-hidden="true">
        <path d="M8 25C8 14.5 16.5 6 27 6h12v9H27c-5.5 0-10 4.5-10 10s4.5 10 10 10h4v-7h9v16H27C16.5 44 8 35.5 8 25Z" fill="currentColor" />
        <circle cx="39" cy="11" r="6" />
      </svg>
      <span>
        <b><span>Jaha</span><em>mina</em></b>
        {!compact && <small>Vamos juntos</small>}
      </span>
    </Link>
  );
}
