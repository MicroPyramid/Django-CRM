<script>
  import { cn } from '$lib/utils.js';

  /**
   * @typedef {Object} Stage
   * @property {string} value
   * @property {string} label
   * @property {string} [meta] - date or dwell text shown under the name (e.g. "Mar 12 · 3d")
   */

  /**
   * @type {{
   *   stages: Stage[],
   *   current: string,
   *   class?: string,
   * }}
   */
  let { stages = [], current = '', class: className } = $props();

  // Index of the current stage; -1 means "no current" → all rendered as future.
  const currentIndex = $derived(stages.findIndex((s) => s.value === current));

  /**
   * @param {number} i
   * @returns {'done' | 'current' | 'future'}
   */
  function stateAt(i) {
    if (currentIndex === -1) return 'future';
    if (i < currentIndex) return 'done';
    if (i === currentIndex) return 'current';
    return 'future';
  }
</script>

<div
  role="list"
  aria-label="Stage progress"
  class={cn(
    'grid w-full gap-1.5',
    className
  )}
  style="grid-template-columns: repeat({stages.length}, minmax(0, 1fr));"
>
  {#each stages as stage, i (stage.value)}
    {@const state = stateAt(i)}
    <div
      role="listitem"
      aria-current={state === 'current' ? 'step' : undefined}
      class={cn(
        'flex h-10 flex-col justify-center gap-0.5 rounded-[var(--r-md)] border px-2.5 py-1.5',
        state === 'current' && 'border-[color:var(--text)] bg-[color:var(--text)] text-[color:var(--bg)]',
        state === 'done' && 'border-[color:var(--border-faint)] bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)]',
        state === 'future' && 'border-[color:var(--border-faint)] bg-[color:var(--bg-elevated)] text-[color:var(--text-subtle)]'
      )}
    >
      <span
        class={cn(
          'truncate text-[10px] font-semibold uppercase tracking-[0.04em] leading-none',
          state === 'current' ? '' : state === 'done' ? 'text-[color:var(--text-muted)]' : 'text-[color:var(--text-subtle)]'
        )}
      >
        {stage.label}
      </span>
      <span
        class={cn(
          'truncate text-[10px] leading-none',
          state === 'current' ? 'text-[color:var(--bg)] opacity-80' : 'text-[color:var(--text-subtle)]'
        )}
      >
        {state === 'future' ? '—' : (stage.meta || '—')}
      </span>
    </div>
  {/each}
</div>
