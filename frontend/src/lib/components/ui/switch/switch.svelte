<script>
  import { Switch as SwitchPrimitive } from 'bits-ui';
  import { cn } from '$lib/utils.js';

  /**
   * @type {{
   *   ref?: HTMLButtonElement | null,
   *   checked?: boolean,
   *   class?: string,
   *   children?: import('svelte').Snippet,
   *   [key: string]: any
   * }}
   */
  let {
    ref = $bindable(null),
    checked = $bindable(false),
    class: className,
    ...restProps
  } = $props();
</script>

<SwitchPrimitive.Root
  bind:ref
  bind:checked
  data-slot="switch"
  class={cn(
    [
      'relative inline-flex h-[18px] w-8 shrink-0 cursor-pointer items-center',
      'rounded-full border border-transparent',
      'bg-[color:var(--border)] data-[state=checked]:bg-[color:var(--text)]',
      'transition-colors duration-150',
      'focus-visible:shadow-[0_0_0_3px_var(--focus-ring)] outline-none',
      'disabled:cursor-not-allowed disabled:opacity-50'
    ].join(' '),
    className
  )}
  {...restProps}
>
  <SwitchPrimitive.Thumb
    data-slot="switch-thumb"
    class={cn(
      'pointer-events-none block size-[14px] rounded-full bg-[color:var(--bg)]',
      'shadow-[0_1px_2px_rgba(0,0,0,0.15)]',
      'transition-transform duration-150',
      'translate-x-0.5 data-[state=checked]:translate-x-[16px]'
    )}
  />
</SwitchPrimitive.Root>
