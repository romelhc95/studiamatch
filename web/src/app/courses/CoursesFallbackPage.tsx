"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import CourseDetailClientWrapper from "./[institution]/[slug]/CourseDetailClientWrapper";

function parseCoursePath(pathname: string) {
  const parts = pathname.split("/").filter(Boolean);
  if (parts.length >= 3 && parts[0] === "courses") {
    try {
      return {
        institution: decodeURIComponent(parts[1]),
        slug: decodeURIComponent(parts[2]),
      };
    } catch {
      return null;
    }
  }
  return null;
}

export default function CoursesFallbackPage() {
  const pathname = usePathname();
  const params = parseCoursePath(pathname);

  if (!params) {
    return (
      <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-6 text-center">
        <p className="text-xs font-black uppercase tracking-[0.3em] text-brand-blue">StudIAMatch</p>
        <h1 className="mt-4 text-3xl font-black text-slate-950">Ruta de programa no válida</h1>
        <p className="mt-3 text-sm text-slate-600">
          Vuelve al catálogo para elegir un programa disponible.
        </p>
        <Link
          href="/"
          className="mt-8 rounded-full bg-brand-blue px-6 py-3 text-sm font-bold text-white transition hover:bg-blue-700"
        >
          Volver al catálogo
        </Link>
      </main>
    );
  }

  return <CourseDetailClientWrapper institutionSlug={params.institution} courseSlug={params.slug} />;
}
