#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"
cd "$ROOT_DIR/web"

mock_file="/tmp/h2_web_mock.js"
build_log="/tmp/h2_web_smoke_build.log"

cat > "$mock_file" <<'JS'
const http = require("http");

const course = {
  id: "course-1",
  institution_id: "inst-1",
  category_id: "cat-1",
  name: "Curso Legacy Visible",
  slug: "curso-legacy-visible",
  url: "https://inst-a.example/curso-legacy-visible",
  price_pen: 1200,
  price_status: "publicado",
  mode: "Remoto",
  duration: "6 meses",
  description_long: "Programa legacy visible preservado por H2",
  syllabus: "Modulo 1",
  target_audience: "Estudiantes",
  requirements: "DNI",
  certification: "Certificado",
  benefits: "Beneficio",
  objectives: "Objetivo",
  start_date: null,
  start_date_text: "Sin confirmar",
  course_type: "Curso",
  brochure_url: null,
  expected_monthly_salary: 2500,
  seniority_level: "Junior",
  roi_months: 6,
  view_count: 0,
  comparison_count: 0,
  created_at: "2026-08-26T00:00:00Z",
  updated_at: "2026-08-26T00:00:00Z"
};

http.createServer((req, res) => {
  res.setHeader("content-type", "application/json");
  if (req.url.startsWith("/rest/v1/ratings") || req.url.startsWith("/rest/v1/reviews")) {
    res.statusCode = 500;
    res.end(JSON.stringify({ error: "social proof endpoints are outside H2 public contract" }));
    return;
  }
  if (req.url.startsWith("/rest/v1/courses_public_effective")) {
    res.end(JSON.stringify([course]));
    return;
  }
  if (req.url.startsWith("/rest/v1/institutions")) {
    res.end(JSON.stringify([{ id: "inst-1", name: "Instituto A", slug: "inst-a" }]));
    return;
  }
  if (req.url.startsWith("/rest/v1/categories")) {
    res.end(JSON.stringify([{ id: "cat-1", name: "Data" }]));
    return;
  }
  res.statusCode = 500;
  res.end(JSON.stringify({ error: `unexpected endpoint ${req.url}` }));
}).listen(3210, "127.0.0.1");
JS

cleanup() {
  kill "$mock_pid" 2>/dev/null || true
  rm -f "$mock_file"
}

node "$mock_file" &
mock_pid=$!
trap cleanup EXIT

NEXT_PUBLIC_SUPABASE_URL="http://127.0.0.1:3210" \
NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY="sb_publishable_test" \
npm run build > "$build_log"

test -f out/index.html
test -f out/courses/inst-a/curso-legacy-visible/index.html
grep -q "Curso Legacy Visible" out/index.html
grep -q "Curso Legacy Visible" out/courses/inst-a/curso-legacy-visible/index.html
if grep -q "Ruta de programa no válida" out/courses/inst-a/curso-legacy-visible/index.html; then
  echo "Detail route served fallback HTML" >&2
  exit 1
fi

echo "h2_web_mock_smoke_ok"
