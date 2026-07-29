import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Términos de Uso — StudIAMatch",
  description: "Términos y condiciones de uso de StudIAMatch.",
};

export default function TerminosPage() {
  return (
    <div className="section-spacing max-w-3xl mx-auto px-4 sm:px-6 break-words">
      <h1 className="text-2xl sm:text-3xl font-bold text-slate-800 mb-6 break-words">Términos de Uso</h1>
      <p className="text-slate-600 mb-4">Última actualización: mayo 2026</p>

      <section className="mb-8">
        <h2 className="text-lg sm:text-xl font-semibold text-slate-700 mb-3 break-words">1. Aceptación de los términos</h2>
        <p className="text-slate-600 leading-relaxed">
          Al acceder y utilizar StudIAMatch, aceptas los presentes términos de uso.
          Si no estás de acuerdo, por favor no utilices la plataforma.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-lg sm:text-xl font-semibold text-slate-700 mb-3 break-words">2. Naturaleza del servicio</h2>
        <p className="text-slate-600 leading-relaxed">
          StudIAMatch es una plataforma de comparación educativa que presenta información pública
          sobre programas de instituciones peruanas. No somos una institución educativa ni
          certificamos programas.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-lg sm:text-xl font-semibold text-slate-700 mb-3 break-words">3. Precisión de la información</h2>
        <p className="text-slate-600 leading-relaxed">
          Nos esforzamos por mantener la información actualizada, pero los precios, fechas de inicio,
          contenido y disponibilidad de programas pueden cambiar sin previo aviso. Recomendamos
          verificar siempre con la institución antes de tomar decisiones.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-lg sm:text-xl font-semibold text-slate-700 mb-3 break-words">4. Uso permitido</h2>
        <p className="text-slate-600 leading-relaxed">
          La plataforma es de uso personal y no comercial. No está permitido extraer datos
          de forma automatizada sin autorización expresa.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-lg sm:text-xl font-semibold text-slate-700 mb-3 break-words">5. Limitación de responsabilidad</h2>
        <p className="text-slate-600 leading-relaxed">
          StudIAMatch no se responsabiliza por decisiones tomadas en base a la información
          presentada en la plataforma. Los datos se proporcionan &quot;tal cual&quot; sin garantías
          de ningún tipo.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-lg sm:text-xl font-semibold text-slate-700 mb-3 break-words">6. Contacto</h2>
        <p className="text-slate-600 leading-relaxed">
          Para consultas sobre estos términos, escríbenos a{" "}
          <a href="mailto:hola@studiamatch.com" className="break-all text-brand-blue hover:underline">
            hola@studiamatch.com
          </a>.
        </p>
      </section>
    </div>
  );
}
