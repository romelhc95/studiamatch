import assert from 'node:assert/strict';
import { auditChanges } from '../web/src/lib/admin-audit-changes.mjs';

const publishWithoutAvailabilityChange = auditChanges({
  action: 'publish',
  old_values: {
    editorial_status: 'draft',
    availability_status: 'unknown',
    published_manual_overrides: {},
    published_manual_start_date: null,
  },
  new_values: {
    editorial_status: 'published',
    published_at: '2026-10-29T12:00:00Z',
    published_manual_overrides: {},
    published_manual_start_date: null,
    published_editorial_values: { mode: 'Remoto' },
  },
});
assert.equal(
  publishWithoutAvailabilityChange.some(({ field }) => field === 'availability_status'),
  false,
  'publish payload omission must not be rendered as an availability change',
);

const explicitNull = auditChanges({
  action: 'update',
  old_values: { editorial_fields: { mode: 'Híbrido' } },
  new_values: { editorial_fields: { mode: null } },
}).find(({ field }) => field === 'mode');
assert.ok(explicitNull, 'explicit null remains an auditable change');
assert.equal(explicitNull.after, null);

const editorialChange = auditChanges({
  action: 'update',
  old_values: { editorial_fields: { mode: 'Híbrido' } },
  new_values: { editorial_fields: { mode: 'Presencial' } },
}).find(({ field }) => field === 'mode');
assert.deepEqual(editorialChange, { field: 'mode', before: 'Híbrido', after: 'Presencial' });

const permittedOverrideDeletion = auditChanges({
  action: 'update',
  old_values: {
    manual_overrides: { benefits: 'Beneficio editorial' },
    editorial_fields: { benefits: 'Beneficio editorial' },
  },
  new_values: {
    manual_overrides: {},
    editorial_fields: { benefits: 'Beneficio base' },
  },
}).find(({ field }) => field === 'benefits');
assert.ok(permittedOverrideDeletion, 'a permitted override removal remains visible in the update event');
assert.equal(permittedOverrideDeletion.before, 'Beneficio editorial');
assert.equal(permittedOverrideDeletion.after, 'Beneficio base');

process.stdout.write('admin-audit-changes=PASS|publish-omission=ignored|explicit-null=preserved|editorial-change=preserved|override-removal=preserved\n');
