<script>
  import { cn } from '$lib/utils.js';
  /** @type {{ ref?: HTMLElement | null, class?: string, children?: import('svelte').Snippet, [key: string]: any }} */
  let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<div
  bind:this={ref}
  data-slot="card-content"
  class={cn(
    'px-4 py-3.5 text-[13px] leading-[1.55] text-[color:var(--text-muted)]',
    className
  )}
  {...restProps}
>
  {@render children?.()}
</div>
