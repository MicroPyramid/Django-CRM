<script>
  import { Tabs as TabsPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  let { ref = $bindable(null), class: className, ...restProps } = $props();
</script>

<TabsPrimitive.List
  bind:ref
  data-slot="tabs-list"
  class={cn(
    'inline-flex w-full items-center gap-4 px-0',
    'border-b border-[color:var(--border-faint)]',
    'text-[color:var(--text-muted)]',
    className
  )}
  {...restProps}
/>
