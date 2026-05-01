"use client";
import dynamic from "next/dynamic";

const CourseDetailClient = dynamic(
  () => import("./CourseDetailClient"),
  { ssr: false }
);

export default function CourseDetailClientWrapper({
  institutionSlug,
  courseSlug
}: {
  institutionSlug: string;
  courseSlug: string;
}) {
  return <CourseDetailClient institutionSlug={institutionSlug} courseSlug={courseSlug} />;
}
