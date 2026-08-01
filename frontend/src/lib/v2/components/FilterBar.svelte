<script>
  import { X, Plus, ChevronDown } from '@lucide/svelte';

  /**
   * One filter system. A saved view, then one removable chip per active
   * filter, then Add. Nothing hidden in a dropdown that the row of chips
   * does not already show.
   *
   * Replaces the three overlapping systems in v1 (segment pills + view tabs
   * + inline dropdowns), where you could not tell what was actually applied.
   *
   * @type {{
   *   view?: string,
   *   filters?: Array<{ key: string, label: string, value: string }>,
   *   meta?: string,
   *   onremove?: (key: string) => void
   * }}
   */
  let { view = 'All', filters = [], meta = null, onremove = () => {} } = $props();
</script>

<div class="v2-filters">
  <button class="v2-view" type="button">
    {view}
    <ChevronDown size={13} style="color:var(--v2-slate)" />
  </button>

  {#each filters as f (f.key)}
    <span class="v2-chip">
      <b>{f.label}</b>
      {f.value}
      <button
        type="button"
        aria-label="Remove the {f.label} filter"
        onclick={() => onremove(f.key)}
      >
        <X size={12} />
      </button>
    </span>
  {/each}

  <button class="v2-chip v2-chip-add" type="button">
    <Plus size={12} />
    Filter
  </button>

  {#if meta}
    <span class="v2-sub" style="margin-left:auto">{meta}</span>
  {/if}
</div>
