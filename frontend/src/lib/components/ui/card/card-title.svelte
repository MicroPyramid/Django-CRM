<script>
  import { cn } from '$lib/utils.js';
  let { ref = $bindable(null), class: className = undefined, children, ...restProps } = $props();
</script>

<div
  bind:this={ref}
  data-slot="card-title"
  class={cn(
    'text-[10px] font-medium uppercase tracking-[0.06em] leading-none text-[color:var(--text-muted)]',
    className
  )}
  {...restProps}
>
  {@render children?.()}
</div>
