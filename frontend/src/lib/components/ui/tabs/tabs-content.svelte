<script>
  import { Tabs as TabsPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  let { ref = $bindable(null), class: className, value, ...restProps } = $props();
</script>

<TabsPrimitive.Content
  bind:ref
  data-slot="tabs-content"
  {value}
  class={cn('flex-1 outline-none', className)}
  {...restProps}
/>
