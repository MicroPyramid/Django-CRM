<script>
  import { cn } from '$lib/utils.js';

  /**
   * @type {{
   *   title?: string | import('svelte').Snippet,
   *   actions?: import('svelte').Snippet,
   *   meta?: import('svelte').Snippet,
   *   children?: import('svelte').Snippet,
   *   padded?: boolean,
   *   class?: string,
   *   ref?: HTMLElement | null,
   *   [key: string]: any
   * }}
   */
  let {
    title,
    actions,
    meta,
    children,
    padded = true,
    class: className,
    ref = $bindable(null),
    ...restProps
  } = $props();

  const hasTitleRow = $derived(!!title || !!actions || !!meta);
  /** @type {import('svelte').Snippet | undefined} */
  const titleSnippet = $derived(typeof title === 'function' ? title : undefined);
  const titleText = $derived(typeof title === 'string' ? title : '');
</script>

<section
  bind:this={ref}
  data-slot="section-card"
  class={cn(
    'rounded-[var(--r-lg)] border border-[color:var(--border-subtle)] bg-[color:var(--surface-default)] text-[color:var(--text)]',
    padded && 'px-5 py-4',
    className
  )}
  {...restProps}
>
  {#if hasTitleRow}
    <header
      data-slot="section-card-header"
      class={cn(
        'flex items-center justify-between gap-3',
        children && 'mb-3'
      )}
    >
      <div class="flex min-w-0 items-center gap-2">
        {#if titleSnippet}
          {@render titleSnippet()}
        {:else if titleText}
          <h3
            class="truncate text-[16px] font-medium leading-[1.3] text-[color:var(--text-primary)]"
          >
            {titleText}
          </h3>
        {/if}
        {#if meta}
          {@render meta()}
        {/if}
      </div>
      {#if actions}
        <div class="flex shrink-0 items-center gap-1.5">
          {@render actions()}
        </div>
      {/if}
    </header>
  {/if}
  {#if children}
    {@render children()}
  {/if}
</section>
