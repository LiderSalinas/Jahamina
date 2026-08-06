import type { NextConfig } from "next";

const allowedDevOrigins = process.env.NODE_ENV === "development"
  ? (process.env.JAHAMINA_ALLOWED_DEV_ORIGINS ?? "")
      .split(",")
      .map((origin) => origin.trim())
      .filter((origin) => origin.length > 0 && origin !== "*")
  : [];

const nextConfig: NextConfig = {
  reactStrictMode: true,

  ...(allowedDevOrigins.length > 0 ? { allowedDevOrigins } : {}),

  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
