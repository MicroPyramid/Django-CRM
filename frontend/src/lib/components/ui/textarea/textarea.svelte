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
      'flex min-h-[92px] w-full min-w-0 resize-y px-3 py-[9px]',
      'rounded-[var(--r-md)] border border-[color:var(--border)]',
      'bg-[color:var(--bg-input)] text-[13px] text-[color:var(--text)]',
      'field-sizing-content leading-[1.55] outline-none',
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
  {...restProps}></textarea>
