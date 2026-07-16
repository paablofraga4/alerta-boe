import type { Metadata } from "next";
import Link from "next/link";
import { Fraunces, Inter } from "next/font/google";
import "./globals.css";

const serif = Fraunces({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "900"],
  variable: "--font-serif",
  display: "swap",
});
const sans = Inter({
  subsets: ["latin"],
  variable: "--font-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "AlertaBOE — el Boletín Oficial del Estado, en claro",
    template: "%s · AlertaBOE",
  },
  description:
    "El BOE de cada día contado como un periódico: titulares, resúmenes claros, el hilo de cada norma y el documento oficial al lado.",
};

function Masthead() {
  const hoy = new Intl.DateTimeFormat("es-ES", {
    weekday: "long",
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(new Date());

  return (
    <header className="border-b-2 border-ink">
      <div className="mx-auto max-w-6xl px-5">
        <div className="flex items-center justify-between py-2 text-[0.7rem] uppercase tracking-wider text-muted">
          <span className="first-letter:uppercase">{hoy}</span>
          <span>Datos abiertos · boe.es</span>
        </div>
        <div className="flex items-end justify-between border-t border-hair pt-3 pb-4">
          <Link href="/" className="font-serif text-4xl font-black leading-none tracking-tight sm:text-5xl">
            Alerta<span className="text-crimson">BOE</span>
          </Link>
          <nav className="hidden gap-6 pb-1 text-sm font-medium sm:flex">
            <Link href="/" className="hover:text-crimson">Portada</Link>
            <Link href="/radar" className="hover:text-crimson">Radar de plazos</Link>
            <Link href="/buscar" className="hover:text-crimson">Buscar</Link>
            <Link href="/contenido" className="hover:text-crimson">Redacción</Link>
          </nav>
        </div>
      </div>
    </header>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="es" className={`${serif.variable} ${sans.variable}`}>
      <body className="font-sans">
        <Masthead />
        <main className="mx-auto max-w-6xl px-5 py-8">{children}</main>
        <footer className="mx-auto max-w-6xl border-t border-hair px-5 py-10 text-xs text-muted">
          <p className="font-serif text-base text-ink">AlertaBOE</p>
          <p className="mt-1">
            Información divulgativa elaborada a partir de los datos abiertos del{" "}
            <a href="https://boe.es" className="underline">Boletín Oficial del Estado</a>. No es
            asesoramiento legal.
          </p>
        </footer>
      </body>
    </html>
  );
}
