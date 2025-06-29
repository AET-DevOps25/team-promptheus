/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
  },
  output: "standalone",
  async rewrites() {
    return [
      {
        destination: `${process.env.NEXT_PUBLIC_SERVER_API_URL || "http://localhost:8080"}/api/repositories/:path*`,
        source: "/api/repositories/:path*",
      },
      {
        destination: `${process.env.NEXT_PUBLIC_GENAI_API_URL || "http://localhost:3003"}/api/genai/:path*`,
        source: "/api/genai/:path*",
      },
      {
        destination: `${process.env.NEXT_PUBLIC_SEARCH_API_URL || "http://localhost:8070"}/api/search/:path*`,
        source: "/api/search/:path*",
      },
      {
        destination: `${process.env.NEXT_PUBLIC_SEARCH_API_URL || "http://localhost:8070"}/api/search`,
        source: "/api/search",
      },
      {
        destination: `${process.env.NEXT_PUBLIC_CONTRIBUTIONS_API_URL || "http://localhost:8082"}/api/contributions/:path*`,
        source: "/api/contributions/:path*",
      },
      {
        destination: `${process.env.NEXT_PUBLIC_CONTRIBUTIONS_API_URL || "http://localhost:8082"}/api/contributions`,
        source: "/api/contributions",
      },
    ];
  },
  typescript: {
    ignoreBuildErrors: true,
  },
};

export default nextConfig;
