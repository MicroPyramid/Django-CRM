<script>
  /**
   * Which field of a post fills which lead field. Rows live in the browser
   * and travel as one JSON string in a hidden input, so adding or removing a
   * row never renumbers form names. The server validates every target.
   *
   * @type {{
   *   rows: { from: string, to: string }[],
   *   targets: { value: string, label: string }[],
   *   disabled?: boolean
   * }}
   */
  import { untrack } from 'svelte';
  import { Plus, Trash2 } from '@lucide/svelte';
  import { cleanMapping } from '#lib/v2/lead-intakes.js';

  let { rows, targets, disabled = false } = $props();

  let next = 0;
  // Seeded once: a revalidation must not throw away rows being typed.
  let list = $state(untrack(() => rows.map((r) => ({ id: next++, from: r.from, to: r.to }))));
  let payload = $derived(JSON.stringify(cleanMapping(list)));
  let incomplete = $derived(list.filter((r) => Boolean(r.from.trim()) !== Boolean(r.to)).length);

  function add() {
    list.push({ id: next++, from: '', to: '' });
  }

  /** @param {number} id */
  function remove(id) {
    list = list.filter((r) => r.id !== id);
  }
</script>

<input type="hidden" name="mapping" value={payload} />

{#if list.length}
  <div class="me-list">
    {#each list as row, n (row.id)}
      <div class="me-row">
        <div class="me-cell">
          <label class="v2-label" for="me-from-{row.id}">Field in the post</label>
          <input
            id="me-from-{row.id}"
            class="v2-input v2-num"
            bind:value={row.from}
            {disabled}
            autocapitalize="off"
            autocomplete="off"
            spellcheck="false"
            maxlength="255"
            placeholder="data.email"
          />
        </div>
        <div class="me-cell">
          <label class="v2-label" for="me-to-{row.id}">Fills</label>
          <select id="me-to-{row.id}" class="v2-input" bind:value={row.to} {disabled}>
            <option value="">Choose a lead field</option>
            {#each targets as t (t.value)}
              <option value={t.value}>{t.label}</option>
            {/each}
          </select>
        </div>
        <button
          type="button"
          class="v2-btn v2-btn-sm me-remove"
          aria-label="Remove row {n + 1}"
          {disabled}
          onclick={() => remove(row.id)}
        >
          <Trash2 size={14} />
        </button>
      </div>
    {/each}
  </div>
{:else}
  <p class="v2-sub" style="font-size:12.5px;margin:0 0 10px">
    No fields mapped yet. A field no row uses goes into the lead's enquiry text.
  </p>
{/if}

{#if incomplete}
  <p class="v2-hint" style="color:var(--v2-clay)">
    {incomplete === 1 ? 'One row is' : `${incomplete} rows are`} half filled in and will not be saved.
  </p>
{/if}

<button type="button" class="v2-btn v2-btn-sm me-add" {disabled} onclick={add}>
  <Plus size={13} />Add a field
</button>

<style>
  .me-list {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-bottom: 10px;
  }
  .me-row {
    display: grid;
    grid-template-columns: 1fr 1fr auto;
    gap: 8px;
    align-items: end;
  }
  .me-cell {
    display: flex;
    flex-direction: column;
    gap: 4px;
    min-width: 0;
  }
  .me-remove,
  .me-add {
    min-height: 44px;
  }
  .me-remove {
    min-width: 44px;
    justify-content: center;
  }
  @media (max-width: 768px) {
    .me-row {
      grid-template-columns: 1fr auto;
      padding-bottom: 10px;
      border-bottom: 1px solid var(--v2-line-soft);
    }
    .me-row .me-cell:first-child {
      grid-column: 1 / -1;
    }
  }
</style>
