export type CompareStorageItem = {
  id: string;
  name: string;
};

const COMPARE_STORAGE_KEY = "StudIAMatch_compare_list";
const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const MAX_COMPARE_ITEMS = 3;
const MAX_COMPARE_NAME_LENGTH = 140;

export function isValidCompareId(value: unknown): value is string {
  return typeof value === "string" && UUID_RE.test(value.trim());
}

export function canonicalizeCompareId(value: unknown): string | null {
  if (!isValidCompareId(value)) return null;
  return value.trim().toLowerCase();
}

export function sanitizeCompareItems(value: unknown): CompareStorageItem[] {
  if (!Array.isArray(value)) return [];

  const seen = new Set<string>();
  const result: CompareStorageItem[] = [];

  for (const item of value) {
    if (!item || typeof item !== "object") continue;
    const candidate = item as Record<string, unknown>;
    const id = canonicalizeCompareId(candidate.id);
    const rawName = candidate.name;
    if (!id || typeof rawName !== "string") continue;
    const name = rawName.trim().slice(0, MAX_COMPARE_NAME_LENGTH);
    if (!name || seen.has(id)) continue;
    seen.add(id);
    result.push({ id, name });
    if (result.length >= MAX_COMPARE_ITEMS) break;
  }

  return result;
}

export function sanitizeCompareIds(values: Iterable<unknown>): string[] {
  const seen = new Set<string>();
  const result: string[] = [];

  for (const value of values) {
    const id = canonicalizeCompareId(value);
    if (!id || seen.has(id)) continue;
    seen.add(id);
    result.push(id);
    if (result.length >= MAX_COMPARE_ITEMS) break;
  }

  return result;
}

export function readCompareItems(): CompareStorageItem[] {
  try {
    const raw = window.localStorage.getItem(COMPARE_STORAGE_KEY);
    if (!raw) return [];
    return sanitizeCompareItems(JSON.parse(raw));
  } catch {
    return [];
  }
}

export function writeCompareItems(items: CompareStorageItem[]): void {
  try {
    window.localStorage.setItem(
      COMPARE_STORAGE_KEY,
      JSON.stringify(sanitizeCompareItems(items)),
    );
  } catch {
    return;
  }
}
