import type { NextConfig } from "next";
import path from "path";

const nextConfig: NextConfig = {
  output: "export",
  // Roden er repoets rod, ikke webapp/: shared.ts importerer
  // data/indikatorer.json, som Python-pipelinen også læser. Med webapp/ som
  // rod nægter Turbopack at resolve filer uden for mappen.
  turbopack: {
    root: path.resolve(__dirname, ".."),
  },
  allowedDevOrigins: ["127.0.0.1"],
};

export default nextConfig;
