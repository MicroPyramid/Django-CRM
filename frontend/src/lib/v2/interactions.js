/**
 * Interactions: calls, meetings, emails, WhatsApp and texts logged on a
 * record, plus the enquiries lead intake writes. Labels and formatting only,
 * safe in a component; the API calls are `#lib/server/v2/interactions.js`.
 */

/** What a person may log. `enquiry` is written by lead intake, never a form. */
export const LOGGABLE_KINDS = ['call', 'meeting', 'email', 'whatsapp', 'sms'];

/** @type {Record<string, string>} */
export const KIND_LABEL = {
  call: 'Call',
  meeting: 'Meeting',
  email: 'Email',
  whatsapp: 'WhatsApp',
  sms: 'Text',
  enquiry: 'Enquiry'
};

export const CALL_OUTCOMES = ['connected', 'no_answer', 'voicemail', 'busy', 'wrong_number'];

/** @type {Record<string, string>} */
export const OUTCOME_LABEL = {
  connected: 'Connected',
  no_answer: 'No answer',
  voicemail: 'Voicemail',
  busy: 'Busy',
  wrong_number: 'Wrong number'
};

/** @type {Record<string, string>} */
const ENQUIRY_VIA = {
  webform: 'web form',
  intake: 'lead webhook',
  email: 'email'
};

/**
 * The line a timeline shows for one interaction: "Outgoing call", "Email
 * received", "Enquiry via web form".
 *
 * @param {{ kind: string, direction?: string, origin?: string }} interaction
 */
export function interactionTitle({ kind, direction, origin }) {
  const inbound = direction === 'inbound';
  if (kind === 'call') return inbound ? 'Incoming call' : 'Outgoing call';
  if (kind === 'meeting') return 'Meeting';
  if (kind === 'email') return inbound ? 'Email received' : 'Email sent';
  if (kind === 'whatsapp') return inbound ? 'WhatsApp received' : 'WhatsApp sent';
  if (kind === 'sms') return inbound ? 'Text received' : 'Text sent';
  if (kind === 'enquiry') {
    const via = origin && origin !== 'manual' ? (ENQUIRY_VIA[origin] ?? origin) : '';
    return via ? `Enquiry via ${via}` : 'Enquiry';
  }
  return 'Activity';
}

/**
 * A span of time for a person: "under a minute", "14 min", "2 h 14 min",
 * "3 d 4 h". Empty for a value that is not a number; negative reads as zero.
 *
 * @param {number | null | undefined} seconds
 */
export function spanText(seconds) {
  if (seconds === null || seconds === undefined) return '';
  const s = Number(seconds);
  if (!Number.isFinite(s)) return '';
  const mins = Math.floor(Math.max(0, s) / 60);
  if (mins < 1) return 'under a minute';
  if (mins < 60) return `${mins} min`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return mins % 60 ? `${hours} h ${mins % 60} min` : `${hours} h`;
  const days = Math.floor(hours / 24);
  return hours % 24 ? `${days} d ${hours % 24} h` : `${days} d`;
}

/**
 * Seconds from `iso` to `now`, or null when `iso` is not a date.
 *
 * @param {string | null | undefined} iso
 * @param {Date} [now]
 */
export function secondsSince(iso, now = new Date()) {
  if (!iso) return null;
  const at = new Date(iso).getTime();
  return Number.isNaN(at) ? null : (now.getTime() - at) / 1000;
}

/**
 * A call's length, "about 4 min" when the phone estimated it.
 *
 * @param {number | null | undefined} seconds
 * @param {boolean} [estimated]
 */
export function durationText(seconds, estimated = false) {
  const text = spanText(seconds);
  return text && estimated ? `about ${text}` : text;
}

/**
 * A lead's response time, which the API defines as its first response minus
 * its creation, wall clock. Empty until it has one.
 *
 * @param {{ first_response_at?: string | null, created_at?: string | null }} lead
 */
export function responseTimeText(lead) {
  if (!lead.first_response_at || !lead.created_at) return '';
  const first = new Date(lead.first_response_at).getTime();
  const created = new Date(lead.created_at).getTime();
  if (Number.isNaN(first) || Number.isNaN(created)) return '';
  return spanText((first - created) / 1000);
}

/**
 * `https://wa.me/<digits>` for an E.164 number, or null when there is none.
 * The API fills `phone_e164` only for a number it could parse, so a raw
 * `phone` is never used here.
 *
 * @param {string | null | undefined} e164
 */
export function whatsappHref(e164) {
  const raw = String(e164 ?? '').trim();
  return /^\+[1-9]\d{6,14}$/.test(raw) ? `https://wa.me/${raw.slice(1)}` : null;
}
