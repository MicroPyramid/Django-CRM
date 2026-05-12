<script>
  import { Select as SelectPrimitive } from 'bits-ui';
  import ChevronDownIcon from '@lucide/svelte/icons/chevron-down';
  import { cn } from '$lib/utils.js';

  let {
    ref = $bindable(null),
    class: className,
    children,
    size = 'default',
    ...restProps
  } = $props();
</script>

<SelectPrimitive.Trigger
  bind:ref
  data-slot="select-trigger"
  data-size={size}
  class={cn(
    [
      'flex w-fit items-center justify-between gap-2 px-3 pr-2.5',
      'rounded-[var(--r-md)] border border-[color:var(--border)]',
      'bg-[color:var(--bg-input)] text-[13px] text-[color:var(--text)]',
      'whitespace-nowrap outline-none select-none leading-none',
      'transition-[border-color,box-shadow] duration-150',
      'hover:border-[color:var(--border-strong)]',
      'focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]',
      'aria-invalid:border-[color:var(--red)] aria-invalid:shadow-[0_0_0_3px_var(--red-soft)]',
      'disabled:cursor-not-allowed disabled:opacity-50',
      'data-[placeholder]:text-[color:var(--text-subtle)]',
      'data-[size=default]:h-9 data-[size=sm]:h-8',
      '*:data-[slot=select-value]:line-clamp-1 *:data-[slot=select-value]:flex *:data-[slot=select-value]:items-center *:data-[slot=select-value]:gap-2',
      "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-[14px] [&_svg]:stroke-[1.7]"
    ].join(' '),
    className
  )}
  {...restProps}
>
  {@render children?.()}
  <ChevronDownIcon class="size-[14px] text-[color:var(--text-subtle)]" />
</SelectPrimitive.Trigger>
