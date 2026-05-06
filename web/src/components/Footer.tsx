import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-slate-100 bg-white">
      <div className="mx-auto max-w-6xl px-6 py-12">
        <div className="flex flex-col md:flex-row justify-between items-start gap-10 mb-8">
          <div className="space-y-3 max-w-xs">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-md bg-brand-slate text-white text-[9px] font-bold">SM</div>
              <span className="text-sm font-semibold tracking-tight text-brand-slate">StudIAMatch</span>
            </div>
            <p className="text-[13px] text-slate-400 leading-relaxed">
              Auditoría educativa imparcial basada en datos reales para profesionales del futuro.
            </p>
            <p className="text-[12px] text-slate-300 flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
              Datos actualizados periódicamente
            </p>
          </div>
          <div className="flex gap-12">
            <div className="space-y-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Plataforma</p>
              <ul className="space-y-2.5">
                <li><Link href="/#programas" className="text-[13px] text-slate-500 hover:text-brand-slate transition-colors">Explorar</Link></li>
                <li><Link href="/#como-funciona" className="text-[13px] text-slate-500 hover:text-brand-slate transition-colors">Metodología</Link></li>
                <li><Link href="/compare" className="text-[13px] text-slate-500 hover:text-brand-slate transition-colors">Comparar</Link></li>
              </ul>
            </div>
            <div className="space-y-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Legal</p>
              <ul className="space-y-2.5">
                <li><Link href="/privacidad" className="text-[13px] text-slate-500 hover:text-brand-slate transition-colors">Privacidad</Link></li>
                <li><Link href="/terminos" className="text-[13px] text-slate-500 hover:text-brand-slate transition-colors">Términos</Link></li>
              </ul>
            </div>
            <div className="space-y-3">
              <p className="text-[11px] font-semibold uppercase tracking-wider text-slate-400">Contacto</p>
              <ul className="space-y-2.5">
                <li><a href="mailto:hola@studiamatch.com" className="text-[13px] text-slate-500 hover:text-brand-slate transition-colors">hola@studiamatch.com</a></li>
                <li><a href="#" className="text-[13px] text-slate-500 hover:text-brand-slate transition-colors">LinkedIn</a></li>
              </ul>
            </div>
          </div>
        </div>
        <div className="pt-6 border-t border-slate-50 flex flex-col md:flex-row justify-between items-center gap-3">
          <p className="text-[12px] text-slate-300">
            &copy; {new Date().getFullYear()} StudIAMatch
          </p>
          <p className="text-[12px] text-slate-300">
            Transparencia educativa para el futuro del Perú
          </p>
        </div>
      </div>
    </footer>
  );
}
