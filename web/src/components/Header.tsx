"use client";

import Link from "next/link";

export function Header() {
  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    } else {
      // Si no estamos en home, redirigir a home con el hash
      window.location.href = `/#${id}`;
    }
  };

  return (
    <header className="sticky top-0 z-50 bg-white/70 backdrop-blur-xl border-b border-slate-100">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 h-14">
        <Link href="/" className="flex items-center gap-2.5 group" onClick={() => window.location.href = '/'}>
          <div className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-slate text-white">
            <span className="text-[10px] font-bold tracking-tight">SM</span>
          </div>
          <span className="text-[13px] font-semibold tracking-tight text-brand-slate">StudIAMatch</span>
        </Link>
        <nav className="hidden md:flex gap-1 items-center">
          <button onClick={() => scrollToSection('programas')} className="px-3 py-1.5 text-[13px] font-medium text-slate-500 hover:text-brand-slate hover:bg-slate-50 rounded-md transition-all">Programas</button>
          <button onClick={() => scrollToSection('como-funciona')} className="px-3 py-1.5 text-[13px] font-medium text-slate-500 hover:text-brand-slate hover:bg-slate-50 rounded-md transition-all">Metodología</button>
          <button onClick={() => scrollToSection('nosotros')} className="px-3 py-1.5 text-[13px] font-medium text-slate-500 hover:text-brand-slate hover:bg-slate-50 rounded-md transition-all">Nosotros</button>
        </nav>
      </div>
    </header>
  );
}
