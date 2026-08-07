"use client";

import { useState } from "react";
import { safeRemoteImageUrl } from "@/lib/media";

type VehicleImageProps = {
  brand: string;
  model: string;
  color?: string | null;
  registration?: string | null;
  imageUrl?: string | null;
};

export function VehicleImage({ brand, model, color, registration, imageUrl }: VehicleImageProps) {
  const label = `${brand} ${model}`.trim();
  const resolvedImageUrl = safeRemoteImageUrl(imageUrl);
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const showPhoto = Boolean(resolvedImageUrl && failedUrl !== resolvedImageUrl);

  return <figure className={`vehicle-image ${showPhoto ? "has-image" : "is-fallback"}`} aria-label={label || "Vehículo del viaje"}>
    {showPhoto ? <>
      {/* Arbitrary vehicle URLs cannot use a global Next/Image host allowlist safely. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img className="vehicle-image-photo" src={resolvedImageUrl!} alt={label} loading="lazy" decoding="async" referrerPolicy="no-referrer" onError={() => setFailedUrl(resolvedImageUrl)}/>
    </> : <svg viewBox="0 0 460 220" role="img" aria-label={`Ilustración de ${label}`}>
      <defs><linearGradient id="vehicle-paint" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor="#ffffff"/><stop offset="0.48" stopColor="#e8eee9"/><stop offset="1" stopColor="#a8bdb3"/></linearGradient><linearGradient id="vehicle-glass" x1="0" x2="1" y1="0" y2="1"><stop offset="0" stopColor="#d9eee7"/><stop offset="0.55" stopColor="#78a89a"/><stop offset="1" stopColor="#315e53"/></linearGradient></defs>
      <ellipse className="vehicle-shadow" cx="228" cy="174" rx="158" ry="16"/>
      <path className="vehicle-body" d="M45 139c6-28 29-43 68-49l54-9 35-43h103l55 47 34 13c14 6 22 18 20 35l-3 24-352 5-17-9 3-14Z"/>
      <path className="vehicle-volume" d="M62 128c59-15 176-25 327-14l20 14-2 29-348 5-17-9 3-14c3-4 8-8 17-11Z"/>
      <path className="vehicle-highlight" d="M69 126c63-13 195-20 322-9M95 103l75-15 37-41h91l44 39"/>
      <path className="vehicle-window" d="m181 80 31-35h38v38l-69-3Zm76 3V45h38l40 39-78-1Z"/>
      <path className="vehicle-door" d="M176 91 166 148m91-60-2 61m-72-46h24"/>
      <path className="vehicle-mirror" d="m169 82-23 5 4 10 22-4Z"/>
      <path className="vehicle-grille" d="m364 126 45 1-2 19-49 1"/>
      <path className="vehicle-light" d="m356 96 34 11-37 8Z"/>
      <g className="vehicle-wheel-set"><circle className="vehicle-wheel" cx="119" cy="157" r="29"/><circle className="vehicle-rim" cx="119" cy="157" r="17"/><path d="m119 142v30m-15-15h30m-26-11 22 22m0-22-22 22"/><circle className="vehicle-hub" cx="119" cy="157" r="6"/></g>
      <g className="vehicle-wheel-set"><circle className="vehicle-wheel" cx="339" cy="157" r="29"/><circle className="vehicle-rim" cx="339" cy="157" r="17"/><path d="m339 142v30m-15-15h30m-26-11 22 22m0-22-22 22"/><circle className="vehicle-hub" cx="339" cy="157" r="6"/></g>
    </svg>}
    <figcaption><small>Vehículo asignado</small><b>{label}</b>{(color || registration) && <span className="vehicle-image-meta">{color && <span>{color}</span>}{registration && <em>{registration}</em>}</span>}</figcaption>
  </figure>;
}
