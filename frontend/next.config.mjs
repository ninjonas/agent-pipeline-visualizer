/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Explicitly set the server port to 3000
  server: {
    port: 3000,
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:4000/api/:path*',  // Backend on port 4000
      },
    ];
  },
}

export default nextConfig;
