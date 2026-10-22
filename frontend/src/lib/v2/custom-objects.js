/**
 * Browser-safe helpers for custom object pages. Imports nothing from `$app`
 * or `#lib/server`, so Svelte pages and vitest can both use it.
 */

export const PHOTO_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp', 'gif'];

/**
 * @param {{ file_name?: string, is_image?: boolean }} attachment
 * @returns {boolean}
 */
export function isPhoto(attachment) {
  if (attachment.is_image !== true) return false;
  const ext = (attachment.file_name ?? '').split('.').pop()?.toLowerCase() ?? '';
  return PHOTO_EXTENSIONS.includes(ext);
}

/** The server limit is 6 MiB for the whole body; the multipart envelope takes a little. */
export const WEB_UPLOAD_MAX_BYTES = 6 * 1024 * 1024 - 64 * 1024;

/**
 * @param {{ name: string, size: number }} file
 * @returns {string | null}
 */
export function uploadTooLarge(file) {
  if (file.size <= WEB_UPLOAD_MAX_BYTES) return null;
  return `${file.name} is ${(file.size / 1_000_000).toFixed(1)} MB. Files must be 6 MB or smaller here.`;
}

const BUILT_IN_PATHS = {
  lead: '/leads',
  contact: '/contacts',
  account: '/accounts',
  deal: '/pipeline',
  ticket: '/tickets',
  task: '/tasks'
};

export const OBJECT_KEY = /^[a-z][a-z0-9_]{1,27}$/;
export const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

/**
 * @param {string} target Registry key: `lead`, `deal`, `obj:<key>`, ...
 * @param {string} id
 * @returns {string | null}
 */
export function recordHref(target, id) {
  if (typeof target !== 'string' || typeof id !== 'string' || !UUID.test(id)) return null;
  if (target.startsWith('obj:')) {
    const key = target.slice(4);
    return OBJECT_KEY.test(key) ? `/objects/${key}/${id}` : null;
  }
  return Object.hasOwn(BUILT_IN_PATHS, target)
    ? `${/** @type {Record<string, string>} */ (BUILT_IN_PATHS)[target]}/${id}`
    : null;
}

/**
 * @param {{ objects: any[] } | null} answer The `/objects/` answer, or null.
 * @returns {{ href: string, label: string }[]}
 */
export function objectNavItems(answer) {
  if (!answer) return [];
  return answer.objects
    .filter((o) => typeof o.key === 'string' && OBJECT_KEY.test(o.key))
    .map((o) => ({ href: `/objects/${o.key}`, label: o.label_plural }));
}

/**
 * @param {{ objects: any[] } | null} answer
 * @param {boolean} isAdmin
 * @returns {boolean}
 */
export function showObjectsSetting(answer, isAdmin) {
  return answer !== null && (isAdmin || answer.objects.length > 0);
}

/**
 * Shape a Related answer for the section on a built-in record's page.
 *
 * @param {{ groups: any[], can_edit: boolean, link_fields: any[] } | null} related
 * @returns {{ groups: any[], addTargets: any[] } | null}
 */
export function relatedView(related) {
  if (!related) return null;
  const addTargets = related.link_fields ?? [];
  const groups = (related.groups ?? []).map((g) => ({
    object: g.object,
    field: g.field,
    records: g.records,
    removable: addTargets.some((t) => t.object.key === g.object.key && t.field.key === g.field.key)
  }));
  if (groups.length === 0 && addTargets.length === 0) return null;
  return { groups, addTargets: addTargets.map((t) => ({ object: t.object, field: t.field })) };
}

/**
 * @param {string} label
 * @param {number} max
 * @returns {string}
 */
export function suggestKey(label, max) {
  return label
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^[^a-z]+/, '')
    .slice(0, max)
    .replace(/_+$/, '');
}
