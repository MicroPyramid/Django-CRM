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
      'text-sidebar-foreground/70 ring-sidebar-ring hover:bg-sidebar-accent hover:text-sidebar-foreground active:bg-sidebar-accent active:text-sidebar-foreground [&>svg]:text-sidebar-foreground/60 outline-hidden flex h-7 min-w-0 items-center gap-2.5 overflow-hidden rounded-md px-2 text-[12px] font-medium transition-all duration-150 focus-visible:ring-2 disabled:pointer-events-none disabled:opacity-50 aria-disabled:pointer-events-none aria-disabled:opacity-50 [&>span:last-child]:truncate [&>svg]:size-3.5 [&>svg]:shrink-0',
      'data-[active=true]:bg-[#fff1ee] data-[active=true]:text-[#ff5c35] dark:data-[active=true]:bg-[#ff7a59]/10 dark:data-[active=true]:text-[#ff7a59]',
      size === 'sm' && 'text-[11px] h-6',
      size === 'md' && 'text-[12px]',
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
