import type { NextConfig } from "next";

import { copyFileSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const maplibrePackagePath = require.resolve("maplibre-gl/package.json");
const { version: maplibreVersion } = require(maplibrePackagePath) as { version: string };
const workerDirectory = `/maplibre/${maplibreVersion}`;
const workerDestination = join(process.cwd(), "public", workerDirectory);

// Turbopack rewrites import.meta.url to file:///ROOT/..., so MapLibre 6's
// HTTP-only worker auto-detection returns an empty URL. Its emitted worker also
// imports a shared sibling by name, which hashed assets don't preserve. Publish
// the pair unchanged on dev/build, including direct `next build` on Vercel.
mkdirSync(workerDestination, { recursive: true });
for (const file of ["maplibre-gl-worker.mjs", "maplibre-gl-shared.mjs"]) {
  copyFileSync(join(dirname(maplibrePackagePath), "dist", file), join(workerDestination, file));
}

const allowedDevOrigins = process.env.NODE_ENV === "development"
  ? (process.env.JAHAMINA_ALLOWED_DEV_ORIGINS ?? "")
      .split(",")
      .map((origin) => origin.trim())
      .filter((origin) => origin.length > 0 && origin !== "*")
  : [];

const nextConfig: NextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_MAPLIBRE_WORKER_URL: `${workerDirectory}/maplibre-gl-worker.mjs`,
  },

  ...(allowedDevOrigins.length > 0 ? { allowedDevOrigins } : {}),

  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
