<script>
  /**
   * A stat tile. The value is tabular mono so a changing figure never
   * reflows the tile it sits in.
   *
   * @type {{ label: string, value: string, tone?: 'ink'|'slate'|'clay'|'rust'|'moss', detail?: string }}
   */
  let { label, value, tone = 'ink', detail = null } = $props();

  const VAR = {
    ink: 'var(--v2-ink)',
    slate: 'var(--v2-slate)',
    clay: 'var(--v2-clay)',
    rust: 'var(--v2-rust)',
    moss: 'var(--v2-moss)'
  };
</script>

<div class="v2-stat">
  <div class="v2-label">{label}</div>
  <div class="v2-stat-value" style="color:{VAR[tone] ?? VAR.ink}">{value}</div>
  {#if detail}<div class="v2-sub" style="font-size:11.5px;margin-top:2px">{detail}</div>{/if}
</div>
