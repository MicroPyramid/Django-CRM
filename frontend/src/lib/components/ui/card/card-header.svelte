<script>
  import { cn } from '$lib/utils.js';
  let { ref = $bindable(null), class: className = undefined, children, ...restProps } = $props();
</script>

<div
  bind:this={ref}
  data-slot="card-header"
  class={cn(
    '@container/card-header flex items-center justify-between gap-2',
    'px-4 py-3 border-b border-[color:var(--border-faint)]',
    'has-data-[slot=card-action]:grid-cols-[1fr_auto]',
    className
  )}
  {...restProps}
>
  {@render children?.()}
</div>
