<script>
  import { Select as SelectPrimitive } from 'bits-ui';
  import SelectPortal from './select-portal.svelte';
  import SelectScrollUpButton from './select-scroll-up-button.svelte';
  import SelectScrollDownButton from './select-scroll-down-button.svelte';
  import { cn } from '$lib/utils.js';
  let {
    ref = $bindable(null),
    class: className = '',
    sideOffset = 4,
    portalProps = {},
    children,
    preventScroll = true,
    ...restProps
  } = $props();
</script>

<SelectPortal {...portalProps}>
  <SelectPrimitive.Content
    bind:ref
    {sideOffset}
    {preventScroll}
    data-slot="select-content"
    class={cn(
      [
        'relative z-50 min-w-[8rem] overflow-hidden overflow-x-hidden overflow-y-auto',
        'rounded-[var(--r-md)] border border-[color:var(--border-faint)]',
        'bg-[color:var(--bg-card)] text-[13px] text-[color:var(--text)]',
        'shadow-[0_8px_24px_-12px_rgba(0,0,0,0.16)]',
        'max-h-(--bits-select-content-available-height) origin-(--bits-select-content-transform-origin)',
        'data-[state=open]:animate-in data-[state=closed]:animate-out',
        'data-[state=closed]:fade-out-0 data-[state=open]:fade-in-0',
        'data-[state=closed]:zoom-out-95 data-[state=open]:zoom-in-95',
        'data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-end-2',
        'data-[side=right]:slide-in-from-start-2 data-[side=top]:slide-in-from-bottom-2',
        'data-[side=bottom]:translate-y-1 data-[side=left]:-translate-x-1',
        'data-[side=right]:translate-x-1 data-[side=top]:-translate-y-1'
      ].join(' '),
      className
    )}
    {...restProps}
  >
    <SelectScrollUpButton />
    <SelectPrimitive.Viewport
      class={cn(
        'h-(--bits-select-anchor-height) w-full min-w-(--bits-select-anchor-width) scroll-my-1 p-1'
      )}
    >
      {@render children?.()}
    </SelectPrimitive.Viewport>
    <SelectScrollDownButton />
  </SelectPrimitive.Content>
</SelectPortal>
