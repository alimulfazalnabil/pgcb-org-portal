import type { MetadataRoute } from 'next';

export default function sitemap(): MetadataRoute.Sitemap {
  const base = (process.env.NEXT_PUBLIC_SITE_URL || 'https://pgcb.org.bd').replace(/\/$/, '');
  const paths = [
    '',
    '/about',
    '/membership',
    '/news',
    '/notices',
    '/circulars',
    '/events',
    '/documents',
    '/contact',
    '/search',
    '/committee',
    '/circles',
    '/members',
    '/apply',
    '/eligibility',
    '/benefits',
    '/fees',
    '/structure',
    '/constitution',
    '/journal',
    '/media',
    '/verify',
    '/verify-certificate',
    '/certificates/verify',
    '/register',
    '/login',
    '/privacy',
    '/terms',
    '/accessibility',
  ];
  return paths.map((path) => ({
    url: `${base}${path}`,
    lastModified: new Date(),
    changeFrequency: path === '' || path === '/news' || path === '/notices' ? 'daily' : 'weekly',
    priority: path === '' ? 1.0 : ['/about', '/membership', '/news', '/notices', '/circulars', '/events', '/contact'].includes(path) ? 0.85 : 0.65,
  }));
}
