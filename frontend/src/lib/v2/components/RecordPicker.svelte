<script>
  /**
   * Picks records to link to. Chosen records are chips, each carrying a hidden
   * input named `name`; the search asks the pick proxy, which lists only what
   * the caller may open.
   */
  import { untrack } from 'svelte';
  import { resolve } from '$app/paths';
  import { asInternalPath } from '#lib/utils/paths.js';
  import { X } from '@lucide/svelte';

  /** @type {{ name: string, target: string, multiple?: boolean, selected?: { id: string, name: string }[], label: string, picked?: number }} */
  let { name, target, multiple = false, selected = [], label, picked = $bindable(0) } = $props();

  let chosen = $state(untrack(() => selected.map((r) => ({ id: r.id, name: r.name }))));
  let text = $state('');
  let matches = $state(/** @type {{ id: string, name: string }[]} */ ([]));
  let searched = $state(false);
  let failed = $state(false);
  let timer = /** @type {ReturnType<typeof setTimeout> | undefined} */ (undefined);
  let ticket = 0;
  const uid = $props.id();

  $effect(() => {
    picked = chosen.length;
  });

  let offered = $derived(matches.filter((m) => !chosen.some((c) => c.id === m.id)));

  /** @param {string} q */
  async function search(q) {
    const mine = ++ticket;
    try {
      const url = `${resolve(asInternalPath('/api/objects/pick'))}?target=${encodeURIComponent(target)}&q=${encodeURIComponent(q)}`;
      const res = await fetch(url);
      if (mine !== ticket) return;
      failed = !res.ok;
      matches = res.ok ? await res.json() : [];
    } catch {
      if (mine !== ticket) return;
      failed = true;
      matches = [];
    }
    searched = true;
  }

  /** @param {Event} event */
  function typed(event) {
    text = /** @type {HTMLInputElement} */ (event.currentTarget).value;
    clearTimeout(timer);
    if (text.trim() === '') {
      ticket++;
      matches = [];
      searched = false;
      failed = false;
      return;
    }
    timer = setTimeout(() => search(text.trim()), 250);
  }

  /** @param {{ id: string, name: string }} record */
  function add(record) {
    chosen = multiple ? [...chosen, record] : [record];
    text = '';
    matches = [];
    searched = false;
  }

  /** @param {string} id */
  function remove(id) {
    chosen = chosen.filter((c) => c.id !== id);
  }
</script>

<div class="rp">
  {#if chosen.length > 0}
    <ul class="rp-chips">
      {#each chosen as record (record.id)}
        <li class="v2-chip rp-chip">
          <b>{record.name}</b>
          <button type="button" aria-label="Remove {record.name}" onclick={() => remove(record.id)}>
            <X size={14} />
          </button>
          <input type="hidden" {name} value={record.id} />
        </li>
      {/each}
    </ul>
  {/if}

  {#if multiple || chosen.length === 0}
    <input
      id="{uid}-q"
      class="v2-input"
      type="search"
      autocomplete="off"
      placeholder="Search {label.toLowerCase()}"
      aria-label="Search {label}"
      value={text}
      oninput={typed}
      onkeydown={(e) => {
        if (e.key === 'Enter') e.preventDefault();
      }}
    />
  {:else}
    <p class="v2-hint">Remove it to pick a different one.</p>
  {/if}

  {#if failed}
    <p class="v2-error">Could not search.</p>
  {:else if searched && offered.length === 0}
    <p class="v2-hint">No matches.</p>
  {:else if offered.length > 0}
    <ul class="rp-results">
      {#each offered as m (m.id)}
        <li><button type="button" class="rp-pick" onclick={() => add(m)}>{m.name}</button></li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .rp .v2-input {
    min-height: 44px;
  }
  .rp-chips,
  .rp-results {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .rp-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    margin-bottom: 8px;
  }
  .rp-chip {
    min-height: 44px;
    padding-block: 0;
    max-width: 100%;
  }
  .rp-chip b {
    overflow-wrap: anywhere;
  }
  .rp-chip button {
    min-width: 44px;
    min-height: 44px;
    margin: 0 -9px 0 0;
  }
  .rp-results {
    margin-top: 6px;
    border: 1px solid var(--v2-line);
    border-radius: 8px;
    background: var(--v2-card);
    max-height: 264px;
    overflow-y: auto;
  }
  .rp-pick {
    display: block;
    width: 100%;
    min-height: 44px;
    padding: 8px 12px;
    border: 0;
    border-bottom: 1px solid var(--v2-line-soft);
    background: none;
    color: var(--v2-ink);
    font: inherit;
    font-size: 13.5px;
    text-align: left;
    cursor: pointer;
    overflow-wrap: anywhere;
  }
  .rp-results li:last-child .rp-pick {
    border-bottom: 0;
  }
  .rp-pick:hover,
  .rp-pick:focus-visible {
    background: var(--v2-line-soft);
  }
</style>
