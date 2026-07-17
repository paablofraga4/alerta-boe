/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Proxy same-origin hacia la API: el navegador llama a /api/boe/* y Next lo
  // reenvía al backend (API_BASE). Evita CORS en producción y no expone la
  // URL/clave de la API al cliente.
  async rewrites() {
    // En producción, por defecto la API de Render; en local, el backend local.
    // API_BASE sobreescribe ambos.
    const fallback =
      process.env.NODE_ENV === "production"
        ? "https://alertaboe-api.onrender.com"
        : "http://127.0.0.1:8000";
    const base = process.env.API_BASE ?? fallback;
    return [{ source: "/api/boe/:path*", destination: `${base}/:path*` }];
  },
};

module.exports = nextConfig;
