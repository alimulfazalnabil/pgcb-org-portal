import type { MetadataRoute } from 'next';
export default function sitemap(): MetadataRoute.Sitemap {
  const base = process.env.NEXT_PUBLIC_SITE_URL || 'https://example.org';
  const paths = ['', '/search', '/committee', '/circles', '/circulars', '/journal', '/events', '/media', '/contact', '/verify', '/certificates/verify', '/register', '/login', '/privacy', '/terms', '/accessibility'];
  return paths.map(path => ({ url: `${base}${path}`, changeFrequency: path === '' ? 'daily' : 'weekly', priority: path === '' ? 1 : 0.6 }));
}
