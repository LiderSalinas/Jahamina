import type { Metadata, Viewport } from "next";

import { AuthProvider } from "@/components/AuthProvider";
import { Navbar } from "@/components/Navbar";
import { InstallPrompt } from "@/components/pwa/InstallPrompt";

import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";

export const metadata: Metadata = {
  title: "Jahamina | Compartimos el camino",
  description: "Viajes compartidos para conectar comunidades en Paraguay.",
  manifest: "/manifest.webmanifest",
};

export const viewport: Viewport = { themeColor: "#075b49" };

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <AuthProvider>
          <Navbar />
          <InstallPrompt />
          <main className="app-main">{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
