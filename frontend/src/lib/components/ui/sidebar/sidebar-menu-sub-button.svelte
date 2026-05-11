<script>
  import { cn } from '$lib/utils.js';
  /**
   * @type {{
   *   ref?: HTMLElement | null,
   *   children?: import('svelte').Snippet,
   *   child?: import('svelte').Snippet<[{ props: Record<string, any> }]>,
   *   class?: string,
   *   size?: 'sm' | 'md',
   *   isActive?: boolean,
   *   [key: string]: any
   * }}
   */
  let {
    ref = $bindable(null),
    children,
    child,
    class: className,
    size = 'md',
    isActive = false,
    ...restProps
  } = $props();

  const mergedProps = $derived({
    class: cn(
      'ring-sidebar-ring outline-hidden flex min-w-0 items-center gap-2.5 overflow-hidden rounded-md font-medium transition-colors duration-150 focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 [&>span:last-child]:truncate',
      'group-data-[collapsible=icon]:hidden',
      className
    ),
    'data-slot': 'sidebar-menu-sub-button',
    'data-sidebar': 'menu-sub-button',
    'data-size': size,
    'data-active': isActive,
    ...restProps
  });
</script>

{#if child}
  {@render child({ props: mergedProps })}
{:else}
  <a bind:this={ref} {...mergedProps}>
    {@render children?.()}
  </a>
{/if}
