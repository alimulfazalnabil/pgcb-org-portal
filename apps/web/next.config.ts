import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  poweredByHeader: false,
  async rewrites() {
    return [
      {
        source: '/backend/:path*',
        destination: `${process.env.INTERNAL_API_URL || 'http://localhost:8000'}/:path*`,
      },
    ];
  },
};

export default nextConfig;
