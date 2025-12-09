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
  data-slot="sidebar-content"
  data-sidebar="content"
  class={cn(
    'flex min-h-0 flex-1 flex-col gap-2 overflow-auto group-data-[collapsible=icon]:overflow-hidden',
    className
  )}
  {...restProps}
>
  {@render children?.()}
</div>
