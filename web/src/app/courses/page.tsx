import type { Metadata } from "next";
import Home from "../page";

export const metadata: Metadata = {
  title: "Catálogo de programas | StudIAMatch",
  description: "Explora y compara programas educativos verificados en StudIAMatch.",
  alternates: {
    canonical: "https://studiamatch.com/courses/",
  },
};

export default async function CoursesPage() {
  return Home();
}
