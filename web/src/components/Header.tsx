"use client";

import { useState } from "react";
import Link from "next/link";
import { Menu, X } from "lucide-react";

export function Header() {
  const [mobileOpen, setMobileOpen] = useState(false);

  const scrollToSection = (id: string) => {
    setMobileOpen(false);
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    } else {
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
          <span className="text-[13px] font-semibold tracking-tight text-brand-slate">
            Stud<span className="text-brand-blue font-bold">IA</span>Match
          </span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden md:flex gap-1 items-center">
          <button onClick={() => scrollToSection('programas')} className="px-3 py-1.5 text-[13px] font-medium text-slate-500 hover:text-brand-slate hover:bg-slate-50 rounded-md transition-all">Programas</button>
          <button onClick={() => scrollToSection('como-funciona')} className="px-3 py-1.5 text-[13px] font-medium text-slate-500 hover:text-brand-slate hover:bg-slate-50 rounded-md transition-all">Metodología</button>
          <button onClick={() => scrollToSection('nosotros')} className="px-3 py-1.5 text-[13px] font-medium text-slate-500 hover:text-brand-slate hover:bg-slate-50 rounded-md transition-all">Nosotros</button>
        </nav>

        {/* Mobile hamburger */}
        <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-1.5 rounded-md hover:bg-slate-50 transition-colors">
          {mobileOpen ? <X className="h-5 w-5 text-slate-600" /> : <Menu className="h-5 w-5 text-slate-600" />}
        </button>
      </div>

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-slate-100 bg-white/95 backdrop-blur-xl animate-in slide-in-from-top-2 duration-200">
          <div className="px-6 py-3 space-y-1">
            <button onClick={() => scrollToSection('programas')} className="w-full text-left px-3 py-2.5 text-[14px] font-medium text-slate-600 hover:text-brand-slate hover:bg-slate-50 rounded-lg transition-all">Programas</button>
            <button onClick={() => scrollToSection('como-funciona')} className="w-full text-left px-3 py-2.5 text-[14px] font-medium text-slate-600 hover:text-brand-slate hover:bg-slate-50 rounded-lg transition-all">Metodología</button>
            <button onClick={() => scrollToSection('nosotros')} className="w-full text-left px-3 py-2.5 text-[14px] font-medium text-slate-600 hover:text-brand-slate hover:bg-slate-50 rounded-lg transition-all">Nosotros</button>
          </div>
        </div>
      )}
    </header>
  );
}
