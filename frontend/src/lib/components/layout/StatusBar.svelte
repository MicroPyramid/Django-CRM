<script>
  /**
   * @type {{
   *   status?: string,
   *   online?: boolean,
   *   hints?: { keys: string[], label: string }[],
   *   class?: string,
   * }}
   */
  let {
    status = 'Ready',
    online = true,
    hints = [
      { keys: ['↑', '↓'], label: 'navigate' },
      { keys: ['⏎'], label: 'open' },
      { keys: ['⌘K'], label: 'command' },
    ],
    class: className = '',
  } = $props();
</script>

<div
  class="sticky bottom-0 z-10 flex h-8 items-center justify-between gap-4 border-t border-[color:var(--border-faint)] bg-[color:var(--bg)] px-7 md:px-8 text-[11px] text-[color:var(--text-subtle)] {className}"
>
  <div class="flex items-center gap-2">
    {#if online}
      <span class="size-1.5 rounded-full bg-[color:var(--green)]" aria-hidden="true"></span>
    {/if}
    <span>{status}</span>
  </div>
  <div class="hidden items-center gap-3 sm:flex">
    {#each hints as h, i (i)}
      <span class="flex items-center gap-1">
        {#each h.keys as k (k)}<span class="kbd">{k}</span>{/each}
        <span class="ml-1">{h.label}</span>
      </span>
      {#if i < hints.length - 1}<span aria-hidden="true">·</span>{/if}
    {/each}
  </div>
</div>
