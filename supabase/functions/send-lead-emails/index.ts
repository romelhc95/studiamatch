import "jsr:@supabase/functions-js/edge-runtime.d.ts";

const RESEND_API_KEY = Deno.env.get("RESEND_API_KEY") || "";
const ADMIN_EMAIL = Deno.env.get("ADMIN_EMAIL") || "romelhc95@gmail.com";
const SUPABASE_URL = Deno.env.get("SUPABASE_URL") || "";
const SUPABASE_PUBLISHABLE_KEY = Deno.env.get("SUPABASE_PUBLISHABLE_KEY") || "";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  whatsapp: string | null;
  course_id: string;
}

interface Course {
  name: string;
  slug: string;
  institution_id: string;
  price_pen: number | null;
  mode: string | null;
  duration: string | null;
}

interface Institution {
  name: string;
  slug: string;
  contact_email: string | null;
  website_url: string | null;
}

async function fetchRecord(table: string, id: string, columns: string) {
  const url = `${SUPABASE_URL}/rest/v1/${table}?select=${columns}&id=eq.${id}&limit=1`;
  const res = await fetch(url, {
    headers: {
      "apikey": SUPABASE_PUBLISHABLE_KEY,
      "Authorization": `Bearer ${SUPABASE_PUBLISHABLE_KEY}`,
    },
  });
  if (!res.ok) return null;
  const data = await res.json();
  return data?.[0] || null;
}

async function sendEmail(to: string[], subject: string, html: string) {
  if (!RESEND_API_KEY) {
    console.log("[EMAIL] Resend not configured — would send to:", to.join(", "), subject);
    return { id: "mock-" + Date.now(), to, subject };
  }
  const res = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${RESEND_API_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      from: "StudIAMatch <no-reply@studiamatch.com>",
      to: to,
      subject: subject,
      html: html,
    }),
  });
  return res.json();
}

function userTemplate(lead: Lead, course: Course, institution: Institution): string {
  const price = course.price_pen ? `S/ ${course.price_pen.toLocaleString()}` : "Consultar";
  const mode = course.mode || "No especificado";
  const duration = course.duration || "Consultar";
  const courseUrl = `https://www.studiamatch.com/courses/${institution.slug}/${course.slug}/`;

  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#1e293b">
<table width="100%" style="background:#1B3A5C;padding:30px;border-radius:12px 12px 0 0">
  <tr><td style="color:#fff;font-size:24px;font-weight:800">StudIAMatch</td></tr>
</table>
<div style="padding:30px;border:1px solid #e2e8f0;border-top:0;border-radius:0 0 12px 12px">
  <h2 style="color:#1B3A5C">${lead.first_name}, recibimos tu solicitud</h2>
  <p>Gracias por tu interés en <strong>${course.name}</strong> de <strong>${institution.name}</strong>.</p>
  <table style="width:100%;border-collapse:collapse;margin:20px 0;background:#f8fafc;border-radius:8px">
    <tr><td style="padding:12px;font-weight:600;color:#1B3A5C">Institución</td><td style="padding:12px">${institution.name}</td></tr>
    <tr><td style="padding:12px;font-weight:600;color:#1B3A5C">Programa</td><td style="padding:12px">${course.name}</td></tr>
    <tr><td style="padding:12px;font-weight:600;color:#1B3A5C">Inversión</td><td style="padding:12px">${price}</td></tr>
    <tr><td style="padding:12px;font-weight:600;color:#1B3A5C">Modalidad</td><td style="padding:12px">${mode}</td></tr>
    <tr><td style="padding:12px;font-weight:600;color:#1B3A5C">Duración</td><td style="padding:12px">${duration}</td></tr>
  </table>
  <div style="text-align:center;margin:30px 0">
    <a href="${courseUrl}" style="background:#FF6B35;color:#fff;padding:14px 32px;text-decoration:none;border-radius:8px;font-weight:600;display:inline-block">Ver programa completo</a>
  </div>
  <hr style="border-top:1px solid #e2e8f0;margin:20px 0">
  <p style="font-size:12px;color:#94a3b8">© ${new Date().getFullYear()} StudIAMatch — Transparencia educativa</p>
</div>
</body></html>`;
}

function adminTemplate(lead: Lead, course: Course, institution: Institution): string {
  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#1e293b">
<table width="100%" style="background:#1B3A5C;padding:20px;border-radius:12px 12px 0 0">
  <tr><td style="color:#fff;font-size:18px;font-weight:800">Nuevo lead · StudIAMatch</td></tr>
</table>
<div style="padding:30px;border:1px solid #e2e8f0;border-top:0;border-radius:0 0 12px 12px">
  <h2 style="color:#1B3A5C">${lead.first_name} ${lead.last_name || ""} se interesó en ${course.name}</h2>
  <table style="width:100%;border-collapse:collapse;margin:20px 0;background:#f8fafc;border-radius:8px">
    <tr><td style="padding:12px;font-weight:600">Email</td><td style="padding:12px"><a href="mailto:${lead.email}">${lead.email}</a></td></tr>
    ${lead.whatsapp ? `<tr><td style="padding:12px;font-weight:600">WhatsApp</td><td style="padding:12px">${lead.whatsapp}</td></tr>` : ""}
    <tr><td style="padding:12px;font-weight:600">Curso</td><td style="padding:12px">${course.name}</td></tr>
    <tr><td style="padding:12px;font-weight:600">Institución</td><td style="padding:12px">${institution.name}</td></tr>
  </table>
  <p style="font-size:12px;color:#94a3b8">Lead ID: ${lead.id}</p>
</div>
</body></html>`;
}

function institutionTemplate(lead: Lead, course: Course, institution: Institution): string {
  return `<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:Arial,Helvetica,sans-serif;max-width:600px;margin:0 auto;padding:20px;color:#1e293b">
<table width="100%" style="background:#FF6B35;padding:20px;border-radius:12px 12px 0 0">
  <tr><td style="color:#fff;font-size:18px;font-weight:800">Nuevo interesado via StudIAMatch</td></tr>
</table>
<div style="padding:30px;border:1px solid #e2e8f0;border-top:0;border-radius:0 0 12px 12px">
  <h2 style="color:#1B3A5C">${lead.first_name} ${lead.last_name || ""} está interesado en ${course.name}</h2>
  <table style="width:100%;border-collapse:collapse;margin:20px 0;background:#f8fafc;border-radius:8px">
    <tr><td style="padding:12px;font-weight:600">Interesado</td><td style="padding:12px">${lead.first_name} ${lead.last_name || ""}</td></tr>
    <tr><td style="padding:12px;font-weight:600">Email</td><td style="padding:12px"><a href="mailto:${lead.email}">${lead.email}</a></td></tr>
    ${lead.whatsapp ? `<tr><td style="padding:12px;font-weight:600">WhatsApp</td><td style="padding:12px">${lead.whatsapp}</td></tr>` : ""}
    <tr><td style="padding:12px;font-weight:600">Programa</td><td style="padding:12px">${course.name}</td></tr>
  </table>
  <div style="text-align:center;margin:25px 0">
    ${lead.whatsapp ? `<a href="https://wa.me/${lead.whatsapp.replace(/\D/g,'')}" style="background:#25D366;color:#fff;padding:12px 24px;text-decoration:none;border-radius:8px;font-weight:600;display:inline-block;margin-right:10px">Contactar WhatsApp</a>` : ""}
    <a href="mailto:${lead.email}" style="background:#1B3A5C;color:#fff;padding:12px 24px;text-decoration:none;border-radius:8px;font-weight:600;display:inline-block">Contactar Email</a>
  </div>
  <hr style="border-top:1px solid #e2e8f0;margin:20px 0">
  <p style="font-size:12px;color:#94a3b8">Este interesado fue referido via StudIAMatch.com</p>
</div>
</body></html>`;
}

Deno.serve(async (req: Request) => {
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    const payload = await req.json();
    const leadId = payload.record?.id || payload.lead_id;

    if (!leadId) {
      return new Response(JSON.stringify({ error: "lead_id required" }), {
        status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const lead = await fetchRecord("leads", leadId, "id,first_name,last_name,email,whatsapp,course_id") as Lead | null;
    if (!lead) {
      return new Response(JSON.stringify({ error: "lead not found" }), {
        status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const course = await fetchRecord("courses", lead.course_id, "name,slug,institution_id,price_pen,mode,duration") as Course | null;
    if (!course) {
      return new Response(JSON.stringify({ error: "course not found" }), {
        status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" },
      });
    }

    const institution = await fetchRecord("institutions", course.institution_id, "name,slug,contact_email,website_url") as Institution | null;
    const instName = institution?.name || "Institución";
    const instSlug = institution?.slug || "";

    const inst: Institution = {
      name: instName,
      slug: instSlug,
      contact_email: institution?.contact_email || null,
      website_url: institution?.website_url || null,
    };

    const results: Record<string, unknown>[] = [];

    // 1. User confirmation
    const userResult = await sendEmail(
      [lead.email],
      `Gracias por tu interés en ${course.name} — ${inst.name}`,
      userTemplate(lead, course, inst),
    );
    results.push({ recipient_type: "user", ...userResult });

    // 2. Admin notification
    const adminResult = await sendEmail(
      [ADMIN_EMAIL],
      `Nuevo lead: ${lead.first_name} ${lead.last_name || ""} — ${course.name}`,
      adminTemplate(lead, course, inst),
    );
    results.push({ recipient_type: "admin", ...adminResult });

    // 3. Institution notification (only if contact_email exists)
    if (inst.contact_email) {
      const instResult = await sendEmail(
        [inst.contact_email],
        `Nuevo interesado en ${course.name} — via StudIAMatch`,
        institutionTemplate(lead, course, inst),
      );
      results.push({ recipient_type: "institution", ...instResult });
    }

    return new Response(JSON.stringify({ success: true, results }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (error) {
    return new Response(JSON.stringify({ error: String(error) }), {
      status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }
});
