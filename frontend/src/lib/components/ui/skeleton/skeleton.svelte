<script>
  import { cn } from '$lib/utils.js';
  let { ref = $bindable(null), class: className, ...restProps } = $props();
</script>

<div
  bind:this={ref}
  data-slot="skeleton"
  class={cn('bg-accent animate-pulse rounded-md', className)}
  {...restProps}
></div>
