<script>
  import { mentionAt, insertMention, matchPeople } from '#lib/v2/mentions.js';

  /**
   * A textarea that offers people from `people` while an `@` handle is being
   * typed. Arrow keys move, Enter or Tab inserts, Escape closes. Every other
   * attribute goes to the textarea, and `ref` is the textarea element.
   *
   * @type {{
   *   value: string,
   *   people?: import('#lib/v2/mentions.js').MentionPerson[],
   *   ref?: HTMLTextAreaElement,
   *   [key: string]: any
   * }}
   */
  // No fallback on `ref`: Svelte refuses `bind:ref={undefined}` against one.
  let { value = $bindable(''), people = [], ref = $bindable(), ...rest } = $props();

  const listId = $props.id();
  /** @type {{ start: number, query: string } | null} */
  let typing = $state(null);
  let active = $state(0);
  const matches = $derived(typing ? matchPeople(people, typing.query) : []);
  const open = $derived(matches.length > 0);

  function detect() {
    typing = ref ? mentionAt(value, ref.selectionStart) : null;
    active = 0;
  }

  /** @param {import('#lib/v2/mentions.js').MentionPerson} person */
  function pick(person) {
    if (!typing || !ref) return;
    const next = insertMention(value, typing.start, ref.selectionStart, person.username);
    value = next.text;
    typing = null;
    requestAnimationFrame(() => {
      ref?.focus();
      ref?.setSelectionRange(next.caret, next.caret);
    });
  }

  /** @param {KeyboardEvent} event */
  function onkeydown(event) {
    if (!open) return;
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      const step = event.key === 'ArrowDown' ? 1 : -1;
      active = (active + step + matches.length) % matches.length;
    } else if (event.key === 'Enter' || event.key === 'Tab') {
      event.preventDefault();
      pick(matches[active]);
    } else if (event.key === 'Escape') {
      event.preventDefault();
      typing = null;
    }
  }

  /** @param {KeyboardEvent} event */
  function onkeyup(event) {
    if (['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) detect();
  }
</script>

<div class="mention">
  <textarea
    bind:this={ref}
    bind:value
    {...rest}
    aria-autocomplete="list"
    aria-controls={open ? listId : undefined}
    aria-activedescendant={open ? `${listId}-${active}` : undefined}
    oninput={detect}
    onclick={detect}
    onblur={() => (typing = null)}
    {onkeydown}
    {onkeyup}></textarea>
  {#if open}
    <ul id={listId} class="mention-list" role="listbox" aria-label="People to mention">
      {#each matches as person, i (person.username)}
        <li
          id={`${listId}-${i}`}
          role="option"
          tabindex="-1"
          aria-selected={i === active}
          class:active={i === active}
          onpointerdown={(event) => {
            // Before the textarea blurs, so the pick still knows where the handle is.
            event.preventDefault();
            pick(person);
          }}
        >
          <span class="mention-name">{person.name}</span>
          <span class="mention-handle">@{person.username}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .mention {
    position: relative;
  }
  .mention-list {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    /* Above .v2-fab (30), below the scrims and drawers (60). */
    z-index: 40;
    margin: 4px 0 0;
    padding: 4px;
    list-style: none;
    max-height: 240px;
    overflow-y: auto;
    background: var(--v2-card);
    border: 1px solid var(--v2-line);
    border-radius: 8px;
  }
  .mention-list li {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    min-height: 44px;
    padding: 0 10px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 13px;
  }
  .mention-list li.active,
  .mention-list li:hover {
    background: var(--v2-line-soft);
  }
  .mention-name,
  .mention-handle {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .mention-name {
    color: var(--v2-ink);
    font-weight: 550;
  }
  .mention-handle {
    color: var(--v2-slate);
    font-size: 12px;
  }
</style>
