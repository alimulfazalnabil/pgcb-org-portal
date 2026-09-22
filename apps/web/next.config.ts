import path from 'path';
import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  poweredByHeader: false,
  outputFileTracingRoot: path.join(__dirname, '../../'),
  async rewrites() {
    const rawUrl =
      process.env.INTERNAL_API_URL ||
      process.env.NEXT_PUBLIC_API_URL ||
      'https://pgcb-org-portal.onrender.com';
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
