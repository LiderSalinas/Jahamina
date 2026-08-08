import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "Jahamina",
    short_name: "Jahamina",
    description: "Compartí el camino con Jahamina.",
    start_url: "/",
    scope: "/",
    display: "standalone",
    background_color: "#f7faf8",
    theme_color: "#075b49",
    categories: ["travel", "transportation"],
    icons: [
      { src: "/icons/icon-192.png", sizes: "192x192", type: "image/png" },
      { src: "/icons/icon-512.png", sizes: "512x512", type: "image/png" },
      { src: "/icons/icon-maskable-512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
      { src: "/icons/jahamina.svg", sizes: "any", type: "image/svg+xml" },
    ],
  };
}
