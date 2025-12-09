<script>
  import { cn } from '$lib/utils.js';
  /**
   * @type {{
   *   ref?: HTMLElement | null,
   *   children?: import('svelte').Snippet,
   *   child?: import('svelte').Snippet<[{ props: Record<string, any> }]>,
   *   class?: string,
   *   [key: string]: any
   * }}
   */
  let { ref = $bindable(null), children, child, class: className, ...restProps } = $props();

  const mergedProps = $derived({
    class: cn(
      'text-sidebar-foreground/70 ring-sidebar-ring outline-hidden flex h-8 shrink-0 items-center rounded-md px-2 text-xs font-medium transition-[margin,opacity] duration-200 ease-linear focus-visible:ring-2 [&>svg]:size-4 [&>svg]:shrink-0',
      'group-data-[collapsible=icon]:-mt-8 group-data-[collapsible=icon]:opacity-0',
      className
    ),
    'data-slot': 'sidebar-group-label',
    'data-sidebar': 'group-label',
    ...restProps
  });
</script>

{#if child}
  {@render child({ props: mergedProps })}
{:else}
  <div bind:this={ref} {...mergedProps}>
    {@render children?.()}
  </div>
{/if}
