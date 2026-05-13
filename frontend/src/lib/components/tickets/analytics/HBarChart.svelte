<script>
  /**
   * Horizontal bar chart for small categorical breakdowns (e.g. MTTR by priority).
   *
   * @type {{
   *   bars: Array<{ label: string, value: number | null, color?: string }>,
   *   format?: (n: number) => string,
   * }}
   */
  let { bars, format = (n) => String(Math.round(n)) } = $props();

  const numericBars = $derived(
    bars.filter((b) => b.value !== null && Number.isFinite(b.value))
  );
  const maxValue = $derived(
    Math.max(1, ...numericBars.map((b) => /** @type {number} */ (b.value)))
  );
</script>

<ul class="space-y-2">
  {#each bars as bar (bar.label)}
    {@const v = bar.value}
    {@const pct = v !== null && Number.isFinite(v) ? Math.max(2, (v / maxValue) * 100) : 0}
    <li>
      <div class="flex items-center justify-between text-xs">
        <span class="font-medium text-[var(--text-secondary)]">{bar.label}</span>
        <span class="tabular-nums text-[var(--text-primary)]">
          {v === null ? '—' : format(v)}
        </span>
      </div>
      <div class="mt-1 h-2 w-full rounded-full bg-[var(--surface-muted)]">
        {#if v !== null && Number.isFinite(v)}
          <div
            class="h-2 rounded-full"
            style:width="{pct}%"
            style:background-color={bar.color || 'var(--color-primary-default)'}
          ></div>
        {/if}
      </div>
    </li>
  {/each}
</ul>
