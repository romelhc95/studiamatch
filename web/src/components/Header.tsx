"use client";

import Link from "next/link";
import { Button } from "@/components/ui/button";

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
    <header className="sticky top-0 z-50 border-b border-brand-gray/50 bg-white/80 backdrop-blur-xl">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-8 py-3">
        <Link href="/" className="flex items-center gap-3 group transition-opacity hover:opacity-90" onClick={() => window.location.href = '/'}>
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-slate text-white shadow-sm ring-1 ring-white/20">
            <span className="text-sm font-black tracking-tighter">SM</span>
          </div>
          <span className="text-lg font-bold tracking-tight text-brand-slate uppercase">StudIAMatch</span>
        </Link>
        <nav className="hidden md:flex gap-8 items-center">
          <button onClick={() => scrollToSection('programas')} className="text-[11px] font-black uppercase tracking-widest text-slate-500 hover:text-brand-blue transition-colors">Programas</button>
          <button onClick={() => scrollToSection('como-funciona')} className="text-[11px] font-black uppercase tracking-widest text-slate-500 hover:text-brand-blue transition-colors">Cómo Funciona</button>
          <button onClick={() => scrollToSection('nosotros')} className="text-[11px] font-black uppercase tracking-widest text-slate-500 hover:text-brand-blue transition-colors">Nosotros</button>
        </nav>
      </div>
    </header>
  );
}
