<script>
  import { cn } from '$lib/utils.js';

  /**
   * @type {{
   *   ref?: HTMLInputElement | null,
   *   value?: string | number,
   *   type?: string,
   *   files?: FileList | null,
   *   class?: string,
   *   'data-slot'?: string,
   *   [key: string]: any
   * }}
   */
  let {
    ref = $bindable(null),
    value = $bindable(),
    type = 'text',
    files = $bindable(),
    class: className,
    'data-slot': dataSlot = 'input',
    ...restProps
  } = $props();

  const baseClass = [
    'flex h-9 w-full min-w-0 px-3',
    'rounded-[var(--r-md)] border border-[color:var(--border)]',
    'bg-[color:var(--bg-input)] text-[13.5px] text-[color:var(--text)]',
    'leading-none outline-none',
    'placeholder:text-[color:var(--text-subtle)]',
    'transition-[border-color,box-shadow] duration-150',
    'hover:border-[color:var(--border-strong)]',
    'focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]',
    'aria-invalid:border-[color:var(--red)] aria-invalid:shadow-[0_0_0_3px_var(--red-soft)]',
    'disabled:cursor-not-allowed disabled:opacity-50',
    'selection:bg-[color:var(--text)] selection:text-[color:var(--bg)]'
  ].join(' ');
</script>

{#if type === 'file'}
  <input
    bind:this={ref}
    data-slot={dataSlot}
    class={cn(baseClass, 'pt-1.5 text-[13px] font-medium', className)}
    type="file"
    bind:files
    bind:value
    {...restProps}
  />
{:else}
  <input
    bind:this={ref}
    data-slot={dataSlot}
    class={cn(baseClass, className)}
    {type}
    bind:value
    {...restProps}
  />
{/if}
