<script>
  /**
   * Render a comment body with `@username` tokens upgraded to styled chips.
   *
   * - Tokens with no leading alphanumeric (so emails are skipped).
   * - Resolved usernames link to /users/<id>; unresolved ones render as
   *   plain text so we never break out of the comment thread.
   *
   * @type {{
   *   body: string,
   *   candidates?: Array<{ username: string, id?: string, email?: string }>
   * }}
   */
  let { body = '', candidates = [] } = $props();

  // Mirror the backend regex (cases/notifications.py).
  const MENTION_RE = /(?<![A-Za-z0-9])@([A-Za-z0-9._-]+)/g;

  const lookup = $derived(() => {
    /** @type {Map<string, { id?: string, email?: string }>} */
    const m = new Map();
    for (const c of candidates) {
      if (!c?.username) continue;
      m.set(c.username.toLowerCase(), { id: c.id, email: c.email });
    }
    return m;
  });

  /** @returns {Array<any>} */
  function tokenize(/** @type {string} */ s) {
    const out = [];
    let last = 0;
    let match;
    const re = new RegExp(MENTION_RE.source, MENTION_RE.flags);
    while ((match = re.exec(s)) !== null) {
      if (match.index > last) {
        out.push({ type: 'text', value: s.slice(last, match.index) });
      }
      const username = match[1];
      const resolved = lookup().get(username.toLowerCase()) || null;
      out.push({ type: 'mention', username, resolved });
      last = match.index + match[0].length;
    }
    if (last < s.length) out.push({ type: 'text', value: s.slice(last) });
    return out;
  }

  const tokens = $derived(tokenize(body || ''));
</script>

<span class="whitespace-pre-wrap">{#each tokens as t}{#if t.type === 'text'}{t.value}{:else if t.resolved && t.resolved.id}<a
        href={`/users/${t.resolved.id}`}
        class="rounded bg-[var(--color-primary-default)]/10 px-1 font-medium text-[var(--color-primary-default)] hover:underline"
        >@{t.username}</a
      >{:else}@{t.username}{/if}{/each}</span>
