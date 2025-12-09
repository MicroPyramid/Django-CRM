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

<ul
  bind:this={ref}
  data-slot="sidebar-menu"
  data-sidebar="menu"
  class={cn('flex w-full min-w-0 flex-col gap-1', className)}
  {...restProps}
>
  {@render children?.()}
</ul>
