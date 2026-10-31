function asRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
    ? value
    : null;
}

function hasOwn(record, key) {
  return Object.prototype.hasOwnProperty.call(record, key);
}

/**
 * @typedef {Object} AuditEventShape
 * @property {string} action
 * @property {Record<string, unknown> | null} [old_values]
 * @property {Record<string, unknown> | null} [new_values]
 */

/**
 * @param {AuditEventShape} event
 * @returns {Array<{ field: string, before: unknown, after: unknown }>}
 */
export function auditChanges(event) {
  const before = asRecord(event.old_values?.editorial_fields)
    || asRecord(event.old_values?.manual_overrides)
    || event.old_values
    || {};
  const after = asRecord(event.new_values?.editorial_fields)
    || asRecord(event.new_values?.manual_overrides)
    || event.new_values
    || {};

  return [...new Set([...Object.keys(before), ...Object.keys(after)])]
    .filter((key) => {
      // admin_publish_course records availability only in old_values: it does not mutate that field.
      // Keep this exception scoped to that action/field so update omissions still show removals.
      const publishOmission = event.action === 'publish'
        && key === 'availability_status'
        && hasOwn(before, key)
        && !hasOwn(after, key);
      return key !== 'version'
        && !publishOmission
        && JSON.stringify(before[key]) !== JSON.stringify(after[key]);
    })
    .map((field) => ({ field, before: before[field], after: after[field] }));
}
