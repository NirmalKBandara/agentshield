import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  experimental: {
    // Node 26 currently drops captured output from Next's detached TypeScript
    // CLI process. The compiler API performs the same strict check reliably.
    useTypeScriptCli: false,
  },
  turbopack: {
    root: process.cwd(),
  },
};

export default nextConfig;
