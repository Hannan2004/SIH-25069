/** @type {import('next').NextConfig} */
// NOTE: Removed `output: 'export'` because the app relies on dynamic route segments `/projects/[id]/*`.
// Static HTML export requires all params at build time (generateStaticParams). Project IDs are created at runtime in the browser (localStorage),
// so using static export breaks navigation. Use the default Node server output so dynamic routes work properly.
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: { unoptimized: true },
};

module.exports = nextConfig;
