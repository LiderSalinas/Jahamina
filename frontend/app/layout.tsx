import type { Metadata } from "next";

import { AuthProvider } from "@/components/AuthProvider";
import { Navbar } from "@/components/Navbar";

import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";

export const metadata: Metadata = {
  title: "Jahamina | Compartimos el camino",
  description: "Viajes compartidos para conectar comunidades en Paraguay.",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <AuthProvider>
          <Navbar />
          <main>{children}</main>
        </AuthProvider>
      </body>
    </html>
  );
}
