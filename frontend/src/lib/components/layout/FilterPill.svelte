<script>
  import { X } from '@lucide/svelte';
  /**
   * @type {{
   *   label: string,
   *   active?: boolean,
   *   value?: string,
   *   icon?: import('svelte').Snippet,
   *   onclick?: (e: MouseEvent) => void,
   *   onclear?: (e: MouseEvent) => void,
   *   dashed?: boolean,
   *   class?: string,
   * }}
   */
  let { label, active = false, value = '', icon, onclick, onclear, dashed = false, class: className = '' } = $props();

  const base =
    'inline-flex h-7 items-center gap-1.5 rounded-[var(--r-sm)] px-[9px] text-[13px] font-medium leading-none transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-[color:var(--ring)]';
  const neutral =
    'border border-[color:var(--border-faint)] bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)] hover:bg-[color:var(--bg-hover)]';
  const activeCls =
    'border border-[color:var(--violet)]/40 bg-[color:var(--violet-soft)] text-[color:var(--violet-soft-text)]';
  const dashedCls =
    'border border-dashed border-[color:var(--border-faint)] bg-transparent text-[color:var(--text-subtle)] hover:text-[color:var(--text-muted)] hover:border-[color:var(--border)]';
</script>

<button
  type="button"
  {onclick}
  class="{base} {dashed ? dashedCls : active ? activeCls : neutral} {className}"
>
  {#if icon}<span class="flex shrink-0 items-center">{@render icon()}</span>{/if}
  <span class="truncate">{label}{#if value}<span class="ml-1 opacity-80">: {value}</span>{/if}</span>
  {#if active && onclear}
    <span
      role="button"
      tabindex="-1"
      class="-mr-1 ml-0.5 flex size-3.5 shrink-0 items-center justify-center rounded-sm hover:bg-[color:var(--violet)]/15"
      onclick={(e) => { e.stopPropagation(); onclear(e); }}
      onkeydown={(e) => { if (e.key === 'Enter') { e.stopPropagation(); onclear(/** @type {any} */ (e)); } }}
      aria-label="Clear filter"
    >
      <X class="size-3 stroke-[2]" />
    </span>
  {/if}
</button>
