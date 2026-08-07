type VehicleImageProps = {
  brand: string;
  model: string;
  color?: string | null;
  registration?: string | null;
  imageUrl?: string | null;
  catalogImageUrl?: string | null;
};

function safeVisualUrl(value?: string | null) {
  return value && (/^https?:\/\//i.test(value) || value.startsWith("/")) ? value : null;
}

export function VehicleImage({ brand, model, color, registration, imageUrl, catalogImageUrl }: VehicleImageProps) {
  const label = `${brand} ${model}`.trim();
  const resolvedImageUrl = safeVisualUrl(imageUrl) ?? safeVisualUrl(catalogImageUrl);

  return <figure className={`vehicle-image ${resolvedImageUrl ? "has-image" : "is-fallback"}`} aria-label={label || "Vehículo del viaje"}>
    {resolvedImageUrl ? <span className="vehicle-image-photo" role="img" aria-label={label} style={{ backgroundImage: `url(${JSON.stringify(resolvedImageUrl).slice(1, -1)})` }}/> : <svg viewBox="0 0 440 210" role="img" aria-label={`Ilustración de ${label}`}>
      <ellipse className="vehicle-shadow" cx="228" cy="174" rx="158" ry="16"/>
      <path className="vehicle-body" d="M45 139c6-28 29-43 68-49l54-9 35-43h103l55 47 34 13c14 6 22 18 20 35l-3 24-352 5-17-9 3-14Z"/>
      <path className="vehicle-highlight" d="M69 126c63-13 195-20 322-9M95 103l75-15 37-41h91l44 39"/>
      <path className="vehicle-window" d="m181 80 31-35h38v38l-69-3Zm76 3V45h38l40 39-78-1Z"/>
      <path className="vehicle-grille" d="m364 126 45 1-2 19-49 1"/>
      <path className="vehicle-light" d="m356 96 34 11-37 8Z"/>
      <circle className="vehicle-wheel" cx="119" cy="157" r="29"/><circle className="vehicle-rim" cx="119" cy="157" r="17"/><circle className="vehicle-hub" cx="119" cy="157" r="6"/>
      <circle className="vehicle-wheel" cx="339" cy="157" r="29"/><circle className="vehicle-rim" cx="339" cy="157" r="17"/><circle className="vehicle-hub" cx="339" cy="157" r="6"/>
    </svg>}
    <figcaption><small>Vehículo asignado</small><b>{label}</b>{(color || registration) && <span>{[color, registration].filter(Boolean).join(" · ")}</span>}</figcaption>
  </figure>;
}
