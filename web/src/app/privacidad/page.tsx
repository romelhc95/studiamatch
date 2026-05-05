import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Política de Privacidad — StudIAMatch",
  description: "Política de privacidad de StudIAMatch.",
};

export default function PrivacidadPage() {
  return (
    <div className="section-spacing max-w-3xl mx-auto px-6">
      <h1 className="text-3xl font-bold text-slate-800 mb-6">Política de Privacidad</h1>
      <p className="text-slate-600 mb-4">Última actualización: mayo 2026</p>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-700 mb-3">1. Información que recopilamos</h2>
        <p className="text-slate-600 leading-relaxed">
          StudIAMatch recopila información pública de programas educativos de instituciones peruanas
          para ofrecer comparativas objetivas. No recopilamos información personal identificable
          de los usuarios de forma automática.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-700 mb-3">2. Uso de la información</h2>
        <p className="text-slate-600 leading-relaxed">
          Los datos recopilados se utilizan exclusivamente para mantener y mejorar la plataforma,
          generar comparativas educativas y ofrecer información relevante a los usuarios.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-700 mb-3">3. Datos de terceros</h2>
        <p className="text-slate-600 leading-relaxed">
          La información de programas, precios y contenido educativo proviene de fuentes públicas
          y de las propias instituciones. No garantizamos la exactitud de datos de terceros.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-700 mb-3">4. Cookies y analítica</h2>
        <p className="text-slate-600 leading-relaxed">
          Utilizamos cookies esenciales para el funcionamiento de la plataforma y analítica anónima
          para mejorar la experiencia del usuario. No utilizamos cookies publicitarias.
        </p>
      </section>

      <section className="mb-8">
        <h2 className="text-xl font-semibold text-slate-700 mb-3">5. Contacto</h2>
        <p className="text-slate-600 leading-relaxed">
          Para consultas sobre privacidad, escríbenos a{" "}
          <a href="mailto:hola@studiamatch.com" className="text-brand-blue hover:underline">
            hola@studiamatch.com
          </a>.
        </p>
      </section>
    </div>
  );
}