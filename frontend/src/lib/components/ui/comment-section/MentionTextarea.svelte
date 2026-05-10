<script>
  import { Textarea } from '$lib/components/ui/textarea/index.js';

  /**
   * Textarea with `@username` typeahead. Accepts the same props as the
   * underlying `Textarea` plus a `candidates` list. When the cursor sits
   * just after a typed `@`, a small popup surfaces matching usernames;
   * Enter / Tab inserts the selected candidate.
   *
   * @type {{
   *   value: string,
   *   candidates?: Array<{ username: string, email?: string }>,
   *   placeholder?: string,
   *   name?: string,
   *   class?: string,
   *   disabled?: boolean
   * }}
   */
  let {
    value = $bindable(''),
    candidates = [],
    placeholder = '',
    name = undefined,
    class: cls = '',
    disabled = false
  } = $props();

  const MENTION_TYPING_RE = /(?:^|[^A-Za-z0-9])@([A-Za-z0-9._-]*)$/;

  /** @type {HTMLTextAreaElement | undefined} */
  let textareaEl = $state(undefined);
  let open = $state(false);
  let query = $state('');
  let startPos = $state(-1);
  let cursorIdx = $state(0);

  const matches = $derived(() => {
    if (!open) return [];
    const q = query.toLowerCase();
    const list = candidates || [];
    if (!q) return list.slice(0, 6);
    return list.filter((c) => c.username.toLowerCase().startsWith(q)).slice(0, 6);
  });

  function _detect() {
    if (!textareaEl) return;
    const caret = textareaEl.selectionStart ?? value.length;
    const before = value.slice(0, caret);
    const m = before.match(MENTION_TYPING_RE);
    if (!m) {
      open = false;
      startPos = -1;
      query = '';
      return;
    }
    startPos = m.index + (m[0].length - m[1].length - 1);
    query = m[1];
    open = true;
    cursorIdx = 0;
  }

  /** @param {{ username: string }} cand */
  function apply(cand) {
    if (!textareaEl || startPos < 0) {
      open = false;
      return;
    }
    const caret = textareaEl.selectionStart ?? value.length;
    const before = value.slice(0, startPos);
    const after = value.slice(caret);
    const insert = `@${cand.username} `;
    value = before + insert + after;
    open = false;
    startPos = -1;
    query = '';
    queueMicrotask(() => {
      if (!textareaEl) return;
      const pos = before.length + insert.length;
      textareaEl.selectionStart = textareaEl.selectionEnd = pos;
      textareaEl.focus();
    });
  }

  function onkeydown(/** @type {KeyboardEvent} */ ev) {
    if (!open || matches().length === 0) return;
    if (ev.key === 'ArrowDown') {
      ev.preventDefault();
      cursorIdx = (cursorIdx + 1) % matches().length;
    } else if (ev.key === 'ArrowUp') {
      ev.preventDefault();
      cursorIdx = (cursorIdx - 1 + matches().length) % matches().length;
    } else if (ev.key === 'Enter' || ev.key === 'Tab') {
      ev.preventDefault();
      apply(matches()[cursorIdx]);
    } else if (ev.key === 'Escape') {
      ev.preventDefault();
      open = false;
    }
  }
</script>

<div class="relative">
  <Textarea
    bind:ref={textareaEl}
    bind:value
    {name}
    {placeholder}
    class={cls}
    {disabled}
    oninput={_detect}
    {onkeydown}
  />
  {#if open && matches().length > 0}
    <ul
      class="absolute left-2 right-2 top-full z-30 mt-1 max-h-56 overflow-y-auto rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] shadow-md"
    >
      {#each matches() as cand, i (cand.username)}
        <li>
          <button
            type="button"
            onmousedown={(ev) => {
              ev.preventDefault();
              apply(cand);
            }}
            class="flex w-full items-center justify-between gap-2 px-3 py-1.5 text-left text-sm hover:bg-[var(--surface-muted)] {i === cursorIdx
              ? 'bg-[var(--surface-muted)]'
              : ''}"
          >
            <span class="font-medium">@{cand.username}</span>
            {#if cand.email && cand.email !== cand.username}
              <span class="truncate text-xs text-[var(--text-secondary)]">{cand.email}</span>
            {/if}
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</div>
