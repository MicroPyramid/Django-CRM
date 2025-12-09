<script>
  import { cn } from '$lib/utils.js';
  /**
   * @type {{
   *   ref?: HTMLElement | null,
   *   class?: string,
   *   inset?: boolean,
   *   children?: import('svelte').Snippet,
   *   [key: string]: any
   * }}
   */
  let { ref = $bindable(null), class: className, inset = false, children, ...restProps } = $props();
</script>

<div
  bind:this={ref}
  data-slot="dropdown-menu-label"
  data-inset={inset}
  class={cn('px-2 py-1.5 text-sm font-semibold data-[inset]:ps-8', className)}
  {...restProps}
>
  {@render children?.()}
</div>
