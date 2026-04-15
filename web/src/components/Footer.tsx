"use client";

import Link from "next/link";

export function Footer() {
  const scrollToSection = (id: string) => {
    const element = document.getElementById(id);
    if (element) {
      element.scrollIntoView({ behavior: "smooth" });
    } else {
      window.location.href = `/#${id}`;
    }
  };

  return (
    <footer className="border-t border-brand-gray/50 py-12 bg-slate-50/30">
      <div className="mx-auto max-w-7xl px-8">
        <div className="flex flex-col md:flex-row justify-between items-start gap-12 border-b border-brand-gray/50 pb-12 mb-8">
          <div className="max-w-xs space-y-4">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 items-center justify-center rounded bg-brand-slate text-white text-[10px] font-black tracking-tighter">SM</div>
              <span className="text-sm font-black tracking-widest text-brand-slate uppercase">StudIAMatch</span>
            </div>
            <p className="text-[11px] text-slate-500 leading-relaxed font-medium uppercase tracking-wider">
              Auditoría educativa imparcial basada en datos reales para los profesionales del futuro.
            </p>
          </div>
          <div className="flex gap-16">
            <div className="space-y-4">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Plataforma</p>
              <ul className="space-y-2.5">
                <li><button onClick={() => scrollToSection('programas')} className="text-[11px] font-bold text-slate-500 hover:text-brand-blue transition-colors">Explorar</button></li>
                <li><button onClick={() => scrollToSection('como-funciona')} className="text-[11px] font-bold text-slate-500 hover:text-brand-blue transition-colors">Metodología</button></li>
                <li><button onClick={() => scrollToSection('nosotros')} className="text-[11px] font-bold text-slate-500 hover:text-brand-blue transition-colors">Nosotros</button></li>
              </ul>
            </div>
            <div className="space-y-4">
              <p className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-400">Legal</p>
              <ul className="space-y-2.5">
                <li><Link href="#" className="text-[11px] font-bold text-slate-500 hover:text-brand-blue transition-colors">Privacidad</Link></li>
                <li><Link href="#" className="text-[11px] font-bold text-slate-500 hover:text-brand-blue transition-colors">Términos</Link></li>
              </ul>
            </div>
          </div>
        </div>
        <div className="flex flex-col md:flex-row justify-between items-center gap-4">
          <p className="text-[10px] font-black uppercase tracking-widest text-slate-400">
            &copy; {new Date().getFullYear()} StudIAMatch · Data-driven decisions
          </p>
          <div className="flex gap-6">
            <Link href="#" className="text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-brand-blue transition-colors">LinkedIn</Link>
            <Link href="#" className="text-[10px] font-black uppercase tracking-widest text-slate-400 hover:text-brand-blue transition-colors">Twitter</Link>
          </div>
        </div>
      </div>
    </footer>
  );
}
