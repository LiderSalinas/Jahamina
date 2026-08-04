import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,

  allowedDevOrigins: [
    "192.168.1.20",
  ],

  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;