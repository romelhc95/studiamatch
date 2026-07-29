import { SUPABASE_PUBLISHABLE_KEY, SUPABASE_URL } from "./supabase";
import {
  isLeadCaptureEnabled,
  submitLeadToEndpoint,
  type LeadPayload,
  type LeadSubmitResult,
} from "./leadCaptureCore";

export {
  LEAD_CAPTURE_ALLOWED_COLUMNS,
  LEAD_CAPTURE_MAINTENANCE_COPY,
  LEAD_CAPTURE_MAINTENANCE_TITLE,
  sanitizeLeadPayload,
  type LeadPayload,
  type LeadSubmitResult,
} from "./leadCaptureCore";

export const LEAD_CAPTURE_ENABLED = isLeadCaptureEnabled(
  process.env.NEXT_PUBLIC_LEAD_CAPTURE_ENABLED,
);

export async function submitLead(input: LeadPayload): Promise<LeadSubmitResult> {
  return submitLeadToEndpoint(input, {
    enabled: LEAD_CAPTURE_ENABLED,
    supabaseUrl: SUPABASE_URL,
    publishableKey: SUPABASE_PUBLISHABLE_KEY,
    fetchImpl: (input, init) => fetch(input, init),
  });
}
