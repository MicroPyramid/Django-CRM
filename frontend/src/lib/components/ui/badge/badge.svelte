<script module>
  import { tv } from 'tailwind-variants';

  export const badgeVariants = tv({
    base: [
      'inline-flex w-fit shrink-0 items-center justify-center gap-1 overflow-hidden whitespace-nowrap',
      'rounded-full border text-[10.5px] font-medium leading-none',
      'transition-[color,background-color,border-color] duration-150',
      'focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]',
      '[&>svg]:pointer-events-none [&>svg]:size-3'
    ].join(' '),
    variants: {
      variant: {
        // Legacy shadcn variants — kept for back-compat with existing callers.
        default: 'bg-primary text-primary-foreground border-transparent px-2 py-0.5 [a&]:hover:bg-primary/90',
        secondary:
          'bg-secondary text-secondary-foreground border-transparent px-2 py-0.5 [a&]:hover:bg-secondary/90',
        destructive:
          'bg-destructive text-white border-transparent px-2 py-0.5 [a&]:hover:bg-destructive/90 dark:bg-destructive/70',
        outline:
          'text-foreground border-[color:var(--border-faint)] bg-[color:var(--bg-elevated)] px-2 py-0.5',

        // New design-system tag variants — spec §6.4.
        customer:
          'bg-[color:var(--green-soft)] text-[color:var(--green-soft-text)] border-transparent px-[7px] py-px',
        vip:
          'bg-[color:var(--violet-soft)] text-[color:var(--violet-soft-text)] border-transparent px-[7px] py-px',
        meeting:
          'bg-[color:var(--amber-soft)] text-[color:var(--amber-soft-text)] border-transparent px-[7px] py-px',
        neutral:
          'bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)] border-[color:var(--border-faint)] px-[7px] py-px',
        count:
          'bg-[color:var(--bg-elevated)] text-[color:var(--text-subtle)] border-[color:var(--border-faint)] px-[5px] py-px text-[10px]'
      }
    },
    defaultVariants: {
      variant: 'default'
    }
  });

  // Variants that render the 5px dot prefix (every spec variant except `count`).
  const DOT_VARIANTS = new Set(['customer', 'vip', 'meeting', 'neutral']);
</script>

<script>
  import { cn } from '$lib/utils.js';

  /**
   * @type {{
   *   ref?: HTMLElement | null,
   *   href?: string,
   *   class?: string,
   *   variant?: 'default' | 'secondary' | 'destructive' | 'outline' | 'customer' | 'vip' | 'meeting' | 'neutral' | 'count',
   *   children?: import('svelte').Snippet,
   *   [key: string]: any
   * }}
   */
  let {
    ref = $bindable(null),
    href = undefined,
    class: className,
    variant = 'default',
    children,
    ...restProps
  } = $props();

  const showDot = $derived(DOT_VARIANTS.has(variant));
</script>

<svelte:element
  this={href ? 'a' : 'span'}
  bind:this={ref}
  data-slot="badge"
  data-variant={variant}
  {href}
  class={cn(badgeVariants({ variant }), className)}
  {...restProps}
>
  {#if showDot}
    <span
      aria-hidden="true"
      class="inline-block size-[5px] rounded-full bg-current shrink-0"
    ></span>
  {/if}
  {@render children?.()}
</svelte:element>
