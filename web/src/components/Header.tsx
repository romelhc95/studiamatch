"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/" && pathname === "/") return true;
    if (href !== "/" && pathname.startsWith(href)) return true;
    return false;
  };

  const handleMobileClose = () => handleMobileClose;

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-100 bg-white">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link href="/" className="flex items-center space-x-3" onClick={() => handleMobileClose}>
          <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-gradient-to-br from-brand-blue to-brand-teal text-sm font-black text-white shadow-premium">
            SM
          </div>
          <span className="hidden sm:block text-sm font-bold tracking-tight text-slate-800">
            StudIAMatch
          </span>
        </Link>

        <nav className="hidden md:flex items-center space-x-8">
          <Link
            href="/"
            className={cn(
              "text-sm font-semibold transition-colors",
              isActive("/") && "text-brand-blue border-b-2 border-brand-blue pb-0.5",
              !isActive("/") && "text-slate-500 hover:text-brand-blue"
            )}
          >
            Inicio
          </Link>
          <Link
            href="/#como-funciona"
            className="text-sm font-semibold text-slate-500 hover:text-brand-blue transition-colors"
          >
            Cómo Funciona
          </Link>
          <Link
            href="/compare"
            className={cn(
              "text-sm font-semibold transition-colors",
              isActive("/compare") && "text-brand-blue border-b-2 border-brand-blue pb-0.5",
              !isActive("/compare") && "text-slate-500 hover:text-brand-blue"
            )}
          >
            Comparar
          </Link>
          <Link
            href="/#programas"
            className="rounded-lg bg-gradient-to-r from-brand-blue to-brand-teal px-4 py-2 text-xs font-bold text-white shadow-premium hover:shadow-lg transition-all"
          >
            Explorar Carreras
          </Link>
        </nav>

        <button
          onClick={() => setMobileOpen(!mobileOpen)}
          className="md:hidden p-2 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer"
          aria-label={mobileOpen ? "Cerrar menú" : "Abrir menú"}
        >
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {mobileOpen ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            )}
          </svg>
        </button>
      </div>

      {mobileOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm" onClick={() => handleMobileClose} />
          <div className="relative z-50 md:hidden border-t border-slate-100 bg-white px-6 py-6 space-y-4 shadow-lg">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Navegación</span>
              <button
                onClick={() => handleMobileClose}
                className="p-1 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer"
                aria-label="Cerrar menú"
              >
                <svg className="h-4 w-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <Link
              href="/"
              className={cn(
                "block text-sm font-semibold transition-colors py-1",
                isActive("/") ? "text-brand-blue" : "text-slate-600"
              )}
              onClick={() => handleMobileClose}
            >
              Inicio
            </Link>
            <Link
              href="/#como-funciona"
              className="block text-sm font-semibold text-slate-600 transition-colors hover:text-brand-blue"
              onClick={() => handleMobileClose}
            >
              Cómo Funciona
            </Link>
            <Link
              href="/compare"
              className={cn(
                "block text-sm font-semibold transition-colors py-1",
                isActive("/compare") ? "text-brand-blue" : "text-slate-600"
              )}
              onClick={() => handleMobileClose}
            >
              Comparar
            </Link>
            <Link
              href="/#programas"
              className="block text-sm font-bold text-brand-blue pt-1"
              onClick={() => handleMobileClose}
            >
              Explorar Carreras
            </Link>
          </div>
        </>
      )}
    </header>
  );
}
