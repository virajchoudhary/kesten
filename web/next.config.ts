import type { NextConfig } from "next";

function djangoOrigin(): string {
  const configuredUrl = process.env.DJANGO_API_URL ?? "http://127.0.0.1:8000";
  const parsedUrl = new URL(configuredUrl);
  const isHttp = parsedUrl.protocol === "http:" || parsedUrl.protocol === "https:";
  const hasOnlyOrigin =
    parsedUrl.pathname === "/" &&
    parsedUrl.search.length === 0 &&
    parsedUrl.hash.length === 0 &&
    parsedUrl.username.length === 0 &&
    parsedUrl.password.length === 0;

  if (!isHttp || !hasOnlyOrigin) {
    throw new Error("DJANGO_API_URL must be an HTTP(S) origin without a path or credentials.");
  }

  return parsedUrl.origin;
}

const apiOrigin = djangoOrigin();

const nextConfig = {
  poweredByHeader: false,
  reactStrictMode: true,
  trailingSlash: true,
  skipTrailingSlashRedirect: true,
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*/",
        destination: `${apiOrigin}/api/v1/:path*/`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          {
            key: "Content-Security-Policy",
            value: "base-uri 'self'; frame-ancestors 'none'; object-src 'none'; form-action 'self'",
          },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
} satisfies NextConfig;

export default nextConfig;
