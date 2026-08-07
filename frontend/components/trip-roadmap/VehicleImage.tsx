type VehicleImageProps = {
  brand: string;
  model: string;
  color?: string | null;
  registration?: string | null;
  imageUrl?: string | null;
};

export function VehicleImage({ brand, model, color, registration, imageUrl }: VehicleImageProps) {
  const label = `${brand} ${model}`.trim();
  const safeImageUrl = imageUrl && (/^https?:\/\//i.test(imageUrl) || imageUrl.startsWith("/")) ? imageUrl : null;

  return <figure className={`vehicle-image ${safeImageUrl ? "has-image" : "is-fallback"}`} aria-label={label || "Vehículo del viaje"}>
    {safeImageUrl ? <span className="vehicle-image-photo" role="img" aria-label={label} style={{ backgroundImage: `url(${JSON.stringify(safeImageUrl).slice(1, -1)})` }}/> : <svg viewBox="0 0 360 170" role="img" aria-label={`Vista ilustrada de ${label}`}>
      <path className="vehicle-shadow" d="M55 132h254"/>
      <path className="vehicle-body" d="M51 108c5-18 19-29 42-33l38-7 28-34h83l38 37 30 8c14 4 23 14 23 29v18H45v-8c0-4 2-8 6-10Z"/>
      <path className="vehicle-window" d="m151 68 23-27h60l29 30-112-3Z"/>
      <path className="vehicle-detail" d="M54 101h55m178 0h38"/>
      <circle className="vehicle-wheel" cx="104" cy="126" r="22"/><circle className="vehicle-hub" cx="104" cy="126" r="9"/>
      <circle className="vehicle-wheel" cx="274" cy="126" r="22"/><circle className="vehicle-hub" cx="274" cy="126" r="9"/>
    </svg>}
    <figcaption><small>Vehículo asignado</small><b>{label}</b>{(color || registration) && <span>{[color, registration].filter(Boolean).join(" · ")}</span>}</figcaption>
  </figure>;
}
