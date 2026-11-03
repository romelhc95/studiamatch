// StudIAMatch-Docs: .context/componentes/presentacion_web_compartida.md#utilidad-de-clases
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
