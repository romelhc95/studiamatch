import { getLeadCaptureBuildState } from "@/lib/leadCaptureCore";
import CoursesFallbackPage from "./CoursesFallbackPage";

export const metadata = {
  title: "Detalle de programa | StudIAMatch",
  description: "Información detallada de programas educativos verificados en StudIAMatch.",
};

export default function CoursesPage() {
  const leadCaptureBuildState = getLeadCaptureBuildState(process.env.NEXT_PUBLIC_LEAD_CAPTURE_ENABLED);

  return (
    <>
      <div hidden aria-hidden="true" data-lead-capture-server-marker="course-detail" data-lead-capture-state={leadCaptureBuildState} />
      <CoursesFallbackPage />
    </>
  );
}
