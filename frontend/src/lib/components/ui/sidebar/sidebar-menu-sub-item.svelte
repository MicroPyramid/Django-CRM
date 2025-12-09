<script>
  import { cn } from '$lib/utils.js';
  /**
   * @type {{
   *   ref?: HTMLElement | null,
   *   children?: import('svelte').Snippet,
   *   class?: string,
   *   [key: string]: any
   * }}
   */
  let { ref = $bindable(null), children, class: className, ...restProps } = $props();
</script>

<li
  bind:this={ref}
  data-slot="sidebar-menu-sub-item"
  data-sidebar="menu-sub-item"
  class={cn('group/menu-sub-item relative', className)}
  {...restProps}
>
  {@render children?.()}
</li>
