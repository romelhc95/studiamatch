export const LEAD_CAPTURE_MAINTENANCE_TITLE = "Captura temporalmente en pausa";
export const LEAD_CAPTURE_MAINTENANCE_COPY =
  "Estamos verificando la seguridad del canal de contacto. Puedes seguir explorando y comparando programas mientras reabrimos la captura.";

export const LEAD_CAPTURE_ALLOWED_COLUMNS = [
  "first_name",
  "last_name",
  "email",
  "whatsapp",
  "source_page",
  "type",
  "course_id",
  "area_interest",
  "budget",
  "modality",
  "description",
  "is_late_enrollment_request",
] as const;

type LeadColumn = (typeof LEAD_CAPTURE_ALLOWED_COLUMNS)[number];
export type LeadPayload = Partial<Record<LeadColumn, string | number | boolean | null>>;

export type LeadSubmitResult =
  | { status: "disabled" }
  | { status: "submitted" }
  | { status: "failed"; statusCode: number };

export type LeadCaptureBuildState = "enabled" | "disabled" | "unset";

export type LeadSubmitConfig = {
  enabled: boolean;
  supabaseUrl: string;
  publishableKey: string;
  fetchImpl: typeof fetch;
};

export function isLeadCaptureEnabled(value: string | undefined): boolean {
  return value === "true";
}

export function getLeadCaptureBuildState(value: string | undefined): LeadCaptureBuildState {
  if (value === "true") return "enabled";
  if (value === "false") return "disabled";
  return "unset";
}

export function sanitizeLeadPayload(input: LeadPayload): LeadPayload {
  return LEAD_CAPTURE_ALLOWED_COLUMNS.reduce<LeadPayload>((payload, column) => {
    if (input[column] !== undefined) {
      payload[column] = input[column];
    }
    return payload;
  }, {});
}

export async function submitLeadToEndpoint(
  input: LeadPayload,
  config: LeadSubmitConfig,
): Promise<LeadSubmitResult> {
  if (!config.enabled) {
    return { status: "disabled" };
  }

  const response = await config.fetchImpl(`${config.supabaseUrl}/rest/v1/leads`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "apikey": config.publishableKey,
      "Prefer": "return=minimal",
    },
    body: JSON.stringify(sanitizeLeadPayload(input)),
  });

  if (!response.ok) {
    return { status: "failed", statusCode: response.status };
  }

  return { status: "submitted" };
}
