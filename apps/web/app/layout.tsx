import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: {
    default: "AlertaBOE — el BOE, en claro",
    template: "%s · AlertaBOE",
  },
  description:
    "Explora el Boletín Oficial del Estado en lenguaje claro: publicaciones del día, el hilo y los precedentes de cada norma, y un asistente que responde con citas.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es">
      <body>
        <header className="border-b border-gray-200 bg-white/80 backdrop-blur dark:border-gray-800 dark:bg-boe-ink/80">
          <nav className="mx-auto flex max-w-5xl items-center justify-between px-4 py-3">
            <Link href="/" className="flex items-center gap-2 font-bold">
              <span className="text-boe-primary">📰 AlertaBOE</span>
            </Link>
            <div className="flex gap-4 text-sm">
              <Link href="/" className="hover:text-boe-primary">
                El BOE de hoy
              </Link>
              <Link href="/buscar" className="hover:text-boe-primary">
                Buscar
              </Link>
            </div>
          </nav>
        </header>
        <main className="mx-auto max-w-5xl px-4 py-8">{children}</main>
        <footer className="mx-auto max-w-5xl px-4 py-8 text-xs text-gray-500">
          Datos de{" "}
          <a href="https://boe.es" className="underline">
            boe.es
          </a>{" "}
          (datos abiertos). AlertaBOE no es asesoramiento legal.
        </footer>
      </body>
    </html>
  );
}
