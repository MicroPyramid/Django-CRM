<script>
  /**
   * @type {{
   *   views: { id: string, label: string, count?: number }[],
   *   active?: string,
   *   onSelect?: (id: string) => void,
   * }}
   */
  let { views, active = views[0]?.id, onSelect } = $props();
</script>

<div class="flex items-center gap-1 overflow-x-auto" role="tablist" aria-label="Views">
  {#each views as v (v.id)}
    {@const isActive = v.id === active}
    <button
      type="button"
      role="tab"
      aria-selected={isActive}
      onclick={() => onSelect?.(v.id)}
      class="-mb-px inline-flex items-center gap-1.5 px-3 pt-2 pb-[11px] text-[14px] leading-none transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--ring)] {isActive
        ? 'font-medium text-[color:var(--text)] border-b-2 border-[color:var(--text)]'
        : 'text-[color:var(--text-muted)] border-b-2 border-transparent hover:text-[color:var(--text)]'}"
    >
      <span>{v.label}</span>
      {#if v.count != null}
        <span class="inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-[var(--r-sm)] border border-[color:var(--border-faint)] bg-[color:var(--bg-elevated)] px-1.5 text-[11.2px] tabular-nums text-[color:var(--text-muted)]">
          {v.count}
        </span>
      {/if}
    </button>
  {/each}
</div>
