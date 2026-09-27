import path from 'path';
import type { NextConfig } from 'next';

function resolveBackendTarget(): string {
  const internalUrl = (process.env.INTERNAL_API_URL || '').trim();
  const publicUrl = (process.env.NEXT_PUBLIC_API_URL || '').trim();
  const candidate =
    internalUrl ||
    (publicUrl && !publicUrl.startsWith('/') ? publicUrl : '') ||
    'http://127.0.0.1:8000';

  let normalized = candidate.replace(/\/+$/, '').replace(/\/api\/v1$/, '');
  if (!/^https?:\/\//i.test(normalized)) {
    // Render fromService property: hostport (e.g. pgcb-portal-api:10000) uses internal HTTP
    if (normalized.includes(':') || normalized.startsWith('127.0.0.1') || normalized.startsWith('localhost')) {
      normalized = `http://${normalized}`;
    } else if (normalized.includes('.')) {
      normalized = `https://${normalized}`;
    } else {
      normalized = `http://${normalized}:10000`;
    }
  }
  return normalized;
}

const nextConfig: NextConfig = {
  poweredByHeader: false,
  outputFileTracingRoot: path.join(__dirname, '../../'),
  async rewrites() {
    const baseUrl = resolveBackendTarget();
    return [
      {
        source: '/backend/:path*',
        destination: `${baseUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
