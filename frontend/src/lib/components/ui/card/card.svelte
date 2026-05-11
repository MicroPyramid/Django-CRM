<script>
  import { cn } from '$lib/utils.js';

  /**
   * @type {{
   *   ref?: HTMLElement | null,
   *   class?: string,
   *   children?: import('svelte').Snippet,
   *   [key: string]: any
   * }}
   */
  let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<div
  bind:this={ref}
  data-slot="card"
  class={cn(
    'flex flex-col overflow-hidden',
    'rounded-[var(--r-lg)] border border-[color:var(--border-faint)]',
    'bg-[color:var(--bg-card)] text-[color:var(--text)]',
    className
  )}
  {...restProps}
>
  {@render children?.()}
</div>
