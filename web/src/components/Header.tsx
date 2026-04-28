import Link from "next/link";

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-100 bg-white/95 backdrop-blur-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        <Link href="/" className="flex items-center space-x-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-blue to-brand-teal text-[11px] font-black text-white shadow-premium">
            SM
          </div>
          <span className="hidden sm:block text-sm font-bold tracking-tight text-slate-800">
            StudIAMatch
          </span>
        </Link>

        <nav className="hidden md:flex items-center space-x-8">
          <Link href="/" className="text-xs font-semibold text-slate-500 hover:text-brand-blue transition-colors">
            Inicio
          </Link>
          <Link href="/#como-funciona" className="text-xs font-semibold text-slate-500 hover:text-brand-blue transition-colors">
            Cómo Funciona
          </Link>
          <Link href="/compare" className="text-xs font-semibold text-slate-500 hover:text-brand-blue transition-colors">
            Comparar
          </Link>
          <Link href="/" className="rounded-lg bg-gradient-to-r from-brand-blue to-brand-teal px-4 py-2 text-[11px] font-bold text-white shadow-premium hover:shadow-lg transition-all">
            Explorar Carreras
          </Link>
        </nav>

        <label htmlFor="mobile-menu-toggle" className="md:hidden p-2 rounded-lg hover:bg-slate-50 transition-colors cursor-pointer" aria-label="Menú">
          <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
          </svg>
        </label>
      </div>

      <input type="checkbox" id="mobile-menu-toggle" className="hidden peer" />
      <div className="md:hidden border-t border-slate-100 bg-white px-6 py-4 space-y-3 hidden peer-checked:block">
        <Link href="/" className="block text-sm font-semibold text-slate-600">
          Inicio
        </Link>
        <Link href="/#como-funciona" className="block text-sm font-semibold text-slate-600">
          Cómo Funciona
        </Link>
        <Link href="/compare" className="block text-sm font-semibold text-slate-600">
          Comparar
        </Link>
        <Link href="/" className="block text-sm font-bold text-brand-blue">
          Explorar Carreras
        </Link>
      </div>
    </header>
  );
}
