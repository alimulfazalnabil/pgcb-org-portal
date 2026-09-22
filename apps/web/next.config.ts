import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  poweredByHeader: false,
  async rewrites() {
    const rawUrl = process.env.INTERNAL_API_URL || 'http://localhost:8000';
    const baseUrl = rawUrl.replace(/\/+$/, '');
    return [
      {
        source: '/backend/:path*',
        destination: `${baseUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
