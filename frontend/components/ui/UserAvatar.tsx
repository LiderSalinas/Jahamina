"use client";

import { useState } from "react";
import { safeRemoteImageUrl } from "@/lib/media";

type UserAvatarProps = {
  name: string;
  imageUrl?: string | null;
  size?: "sm" | "md" | "lg";
  className?: string;
};

function initialsFor(name: string) {
  return name.trim().split(/\s+/).filter(Boolean).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "J";
}

export function UserAvatar({ name, imageUrl, size = "md", className = "" }: UserAvatarProps) {
  const safeUrl = safeRemoteImageUrl(imageUrl);
  const [failedUrl, setFailedUrl] = useState<string | null>(null);
  const showPhoto = Boolean(safeUrl && failedUrl !== safeUrl);

  return <span className={`user-avatar is-${size} ${showPhoto ? "has-photo" : "is-fallback"} ${className}`.trim()} aria-label={name}>
    {showPhoto ? <>
      {/* Arbitrary user URLs cannot use a global Next/Image host allowlist safely. */}
      {/* eslint-disable-next-line @next/next/no-img-element */}
      <img src={safeUrl!} alt={name} loading="lazy" decoding="async" referrerPolicy="no-referrer" onError={() => setFailedUrl(safeUrl)}/>
    </> : <span aria-hidden>{initialsFor(name)}</span>}
  </span>;
}
