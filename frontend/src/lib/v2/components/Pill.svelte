<script>
  /**
   * A status pill. Tinted background, never a solid fill. Solid reads as a
   * button, and only actions get solid colour.
   *
   * Ember is deliberately not an available tone: it belongs to actions and
   * to "this needs you now", never to a status a record happens to be in.
   *
   * @type {{ tone?: 'ink'|'slate'|'clay'|'rust'|'moss', dot?: boolean, children: import('svelte').Snippet }}
   */
  let { tone = 'slate', dot = false, children } = $props();

  const VAR = {
    ink: 'var(--v2-ink)',
    slate: 'var(--v2-slate)',
    clay: 'var(--v2-clay)',
    rust: 'var(--v2-rust)',
    moss: 'var(--v2-moss)'
  };

  let color = $derived(VAR[tone] ?? VAR.slate);
</script>

<span class="v2-pill" style="color:{color};background:color-mix(in srgb, {color} 12%, transparent)">
  {#if dot}<i class="v2-pill-dot" style="background:{color}"></i>{/if}
  {@render children()}
</span>
