/**
 * @mentions in ticket comments, held to the backend's rules: `cases/notifications.py`
 * reads `@<handle>` with MENTION_RE and resolves it against the email local part
 * of an active member. Mirroring both means the composer only offers handles that
 * resolve, and a chip appears only where a notification went out.
 */

// MENTION_RE in cases/notifications.py.
const MENTION = /(?<![A-Za-z0-9])@([A-Za-z0-9._-]+)/g;
const TYPING = /(?<![A-Za-z0-9])@([A-Za-z0-9._-]*)$/;
const LIMIT = 6;

/** @typedef {{ username: string, name: string }} MentionPerson */

/**
 * @param {{ id: string, name: string, email: string }[]} people from `getOrgPeopleAndTeams`
 * @returns {MentionPerson[]}
 */
export function mentionPeople(people) {
  const seen = new Set();
  /** @type {MentionPerson[]} */
  const out = [];
  for (const person of people) {
    const username = (person.email ?? '').split('@')[0].toLowerCase();
    if (!username || seen.has(username)) continue;
    seen.add(username);
    out.push({ username, name: person.name });
  }
  return out;
}

/**
 * The handle being typed just before the caret, or null when there is none.
 *
 * @param {string} text
 * @param {number | null} caret
 * @returns {{ start: number, query: string } | null}
 */
export function mentionAt(text, caret) {
  const end = caret ?? text.length;
  const match = text.slice(0, end).match(TYPING);
  return match ? { start: end - match[0].length, query: match[1] } : null;
}

/**
 * @param {string} text
 * @param {number} start where the `@` sits
 * @param {number} caret where the typed handle ends
 * @param {string} username
 * @returns {{ text: string, caret: number }}
 */
export function insertMention(text, start, caret, username) {
  const after = text.slice(caret);
  const insert = `@${username}${/^\s/.test(after) ? '' : ' '}`;
  return { text: text.slice(0, start) + insert + after, caret: start + insert.length };
}

/**
 * @param {MentionPerson[]} people
 * @param {string} query
 * @returns {MentionPerson[]}
 */
export function matchPeople(people, query) {
  const q = query.toLowerCase();
  const hits = q
    ? people.filter(
        (p) =>
          p.username.startsWith(q) ||
          p.name
            .toLowerCase()
            .split(/\s+/)
            .some((word) => word.startsWith(q))
      )
    : people;
  return hits.slice(0, LIMIT);
}

/**
 * @param {string} body
 * @param {MentionPerson[]} people
 * @returns {({ type: 'text', value: string } | { type: 'mention', value: string, person: MentionPerson })[]}
 */
export function mentionTokens(body, people) {
  const byName = new Map(people.map((p) => [p.username, p]));
  /** @type {any[]} */
  const out = [];
  let last = 0;
  for (const match of body.matchAll(MENTION)) {
    const at = match.index ?? 0;
    if (at > last) out.push({ type: 'text', value: body.slice(last, at) });
    const person = byName.get(match[1].toLowerCase());
    out.push(
      person ? { type: 'mention', value: match[0], person } : { type: 'text', value: match[0] }
    );
    last = at + match[0].length;
  }
  if (last < body.length) out.push({ type: 'text', value: body.slice(last) });
  return out;
}
