<script>
  import { Tabs as TabsPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  let { ref = $bindable(null), class: className, value, ...restProps } = $props();
</script>

<TabsPrimitive.Trigger
  bind:ref
  data-slot="tabs-trigger"
  {value}
  class={cn(
    [
      'relative inline-flex items-center justify-center gap-1.5',
      'px-0 pb-2.5 -mb-px',
      'text-[13px] font-medium leading-none whitespace-nowrap',
      'text-[color:var(--text-muted)]',
      'border-b-2 border-transparent',
      'transition-colors duration-150',
      'hover:text-[color:var(--text)]',
      'data-[state=active]:text-[color:var(--text)] data-[state=active]:border-[color:var(--text)]',
      'focus-visible:outline-none focus-visible:shadow-[0_0_0_3px_var(--focus-ring)] rounded-[var(--r-sm)]',
      'disabled:pointer-events-none disabled:opacity-50',
      "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-4"
    ].join(' '),
    className
  )}
  {...restProps}
/>
