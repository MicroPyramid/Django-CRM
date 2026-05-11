<script>
  import { cn } from '$lib/utils.js';

  /**
   * @type {{
   *   variant?: 'default' | 'success' | 'violet' | 'amber',
   *   time?: string,
   *   quote?: string,
   *   text: import('svelte').Snippet,
   *   icon?: import('svelte').Snippet,
   *   class?: string,
   * }}
   */
  let { variant = 'default', time = '', quote = '', text, icon, class: className } = $props();

  // Map variant → icon background classes. Default is the neutral chip.
  const iconBg = $derived(
    variant === 'success'
      ? 'bg-[color:var(--green)]/12 border-[color:var(--green)]/30 text-[color:var(--green)]'
      : variant === 'violet'
        ? 'bg-[color:var(--violet-soft)] border-[color:var(--violet)]/30 text-[color:var(--violet-soft-text)]'
        : variant === 'amber'
          ? 'bg-[color:var(--amber)]/12 border-[color:var(--amber)]/30 text-[color:var(--amber)]'
          : 'bg-[color:var(--bg-elevated)] border-[color:var(--border-faint)] text-[color:var(--text-muted)]'
  );
</script>

<li class={cn('flex items-start gap-3 py-3.5 first:pt-0 last:pb-0', className)}>
  <div
    aria-hidden="true"
    class={cn(
      'flex size-7 shrink-0 items-center justify-center rounded-full border',
      iconBg
    )}
  >
    {#if icon}
      {@render icon()}
    {/if}
  </div>
  <div class="min-w-0 flex-1">
    <div class="text-[13px] leading-[1.55] text-[color:var(--text-muted)] [&_strong]:font-medium [&_strong]:text-[color:var(--text)]">
      {@render text()}
    </div>
    {#if quote}
      <blockquote
        class="mt-2 rounded-[var(--r-md)] border border-[color:var(--border-faint)] bg-[color:var(--bg-elevated)] px-3 py-2 text-[12.5px] leading-[1.5] text-[color:var(--text)]"
      >
        {quote}
      </blockquote>
    {/if}
    {#if time}
      <p class="mt-1.5 text-[11px] leading-none text-[color:var(--text-subtle)]">{time}</p>
    {/if}
  </div>
</li>
