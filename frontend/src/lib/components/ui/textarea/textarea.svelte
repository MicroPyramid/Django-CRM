<script>
  import { cn } from '$lib/utils.js';
  let {
    ref = $bindable(null),
    value = $bindable(),
    class: className = '',
    'data-slot': dataSlot = 'textarea',
    ...restProps
  } = $props();
</script>

<textarea
  bind:this={ref}
  data-slot={dataSlot}
  class={cn(
    [
      'flex w-full min-w-0 min-h-[92px] py-[9px] px-3 resize-y',
      'rounded-[var(--r-md)] border border-[color:var(--border)]',
      'bg-[color:var(--bg-input)] text-[13px] text-[color:var(--text)]',
      'leading-[1.55] outline-none field-sizing-content',
      'placeholder:text-[color:var(--text-subtle)]',
      'transition-[border-color,box-shadow] duration-150',
      'hover:border-[color:var(--border-strong)]',
      'focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]',
      'aria-invalid:border-[color:var(--red)] aria-invalid:shadow-[0_0_0_3px_var(--red-soft)]',
      'disabled:cursor-not-allowed disabled:opacity-50'
    ].join(' '),
    className
  )}
  bind:value
  {...restProps}
></textarea>
