import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "export",
  turbopack: {
    root: path.resolve(__dirname),
  },
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
