/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy same-origin hacia la API: el navegador llama a /api/boe/* y Next lo
  // reenvía al backend (API_BASE). Evita CORS en producción y no expone la
  // URL/clave de la API al cliente.
  async rewrites() {
    const base = process.env.API_BASE ?? "http://127.0.0.1:8000";
    return [{ source: "/api/boe/:path*", destination: `${base}/:path*` }];
  },
};

module.exports = nextConfig;
