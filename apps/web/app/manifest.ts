import type { MetadataRoute } from 'next';

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: 'PGCB Member Portal — পাওয়ার গ্রিড প্রকৌশলী সমিতি',
    short_name: 'PGCB Portal',
    description:
      'Official Institutional Portal, Digital Membership ID Card, Certificate Wallet & Services for Power Grid Engineers',
    start_url: '/portal',
    scope: '/',
    display: 'standalone',
    orientation: 'portrait',
    background_color: '#0f172a',
    theme_color: '#0f172a',
    categories: ['government', 'productivity', 'utilities'],
    icons: [
      {
        src: '/favicon.ico',
        sizes: '48x48 32x32 16x16',
        type: 'image/x-icon',
      },
    ],
  };
}
