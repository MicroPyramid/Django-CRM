<script>
  import CheckIcon from '@lucide/svelte/icons/check';
  import { Select as SelectPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  let {
    ref = $bindable(null),
    class: className = '',
    value,
    label = '',
    children: childrenProp,
    ...restProps
  } = $props();
</script>

<SelectPrimitive.Item
  bind:ref
  {value}
  data-slot="select-item"
  class={cn(
    [
      'relative flex w-full cursor-default select-none items-center gap-2',
      'py-1.5 ps-2 pe-8 text-[13.5px] text-[color:var(--text-muted)]',
      'rounded-[var(--r-sm)] outline-hidden',
      'data-[highlighted]:bg-[color:var(--bg-elevated)] data-[highlighted]:text-[color:var(--text)]',
      'data-[state=checked]:text-[color:var(--text)]',
      'data-[disabled]:pointer-events-none data-[disabled]:opacity-50',
      "[&_svg:not([class*='text-'])]:text-[color:var(--text-subtle)]",
      "[&_svg]:pointer-events-none [&_svg]:shrink-0 [&_svg:not([class*='size-'])]:size-[14px]",
      '*:[span]:last:flex *:[span]:last:items-center *:[span]:last:gap-2'
    ].join(' '),
    className
  )}
  {...restProps}
>
  {#snippet children({ selected, highlighted })}
    <span class="absolute end-2 flex size-3.5 items-center justify-center">
      {#if selected}
        <CheckIcon class="size-[14px]" />
      {/if}
    </span>
    {#if childrenProp}
      {@render childrenProp({ selected, highlighted })}
    {:else}
      {label || value}
    {/if}
  {/snippet}
</SelectPrimitive.Item>
