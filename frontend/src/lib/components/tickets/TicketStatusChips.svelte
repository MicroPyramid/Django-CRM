<script>
  /** @type {{
   *   value: 'ALL' | 'open' | 'closed',
   *   total: number,
   *   openCount: number,
   *   closedCount: number,
   *   onChange: (v: 'ALL' | 'open' | 'closed') => void
   * }} */
  let { value, total, openCount, closedCount, onChange } = $props();
</script>

<div class="flex gap-1">
  <button
    type="button"
    onclick={() => onChange('ALL')}
    class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {value ===
    'ALL'
      ? 'bg-[var(--color-primary-default)] text-white'
      : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]'}"
  >
    All
    <span
      class="rounded-full px-1.5 py-0.5 text-xs {value === 'ALL'
        ? 'bg-[var(--color-primary-dark)] text-white/90'
        : 'bg-[var(--border-default)] text-[var(--text-tertiary)]'}"
    >
      {total}
    </span>
  </button>
  <button
    type="button"
    onclick={() => onChange('open')}
    class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {value ===
    'open'
      ? 'bg-[var(--stage-qualified)] text-white'
      : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]'}"
  >
    Open
    <span
      class="rounded-full px-1.5 py-0.5 text-xs {value === 'open'
        ? 'bg-black/20 text-white/90'
        : 'bg-[var(--border-default)] text-[var(--text-tertiary)]'}"
    >
      {openCount}
    </span>
  </button>
  <button
    type="button"
    onclick={() => onChange('closed')}
    class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {value ===
    'closed'
      ? 'bg-[var(--text-secondary)] text-white'
      : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]'}"
  >
    Closed
    <span
      class="rounded-full px-1.5 py-0.5 text-xs {value === 'closed'
        ? 'bg-[var(--text-tertiary)] text-white/90'
        : 'bg-[var(--border-default)] text-[var(--text-tertiary)]'}"
    >
      {closedCount}
    </span>
  </button>
</div>
