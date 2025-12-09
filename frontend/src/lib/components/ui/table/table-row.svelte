<script>
  import { cn } from '$lib/utils.js';
  /**
   * @type {{
   *   ref?: HTMLElement | null,
   *   class?: string,
   *   children?: import('svelte').Snippet,
   *   [key: string]: any
   * }}
   */
  let { ref = $bindable(null), class: className, children, ...restProps } = $props();
</script>

<tr
  bind:this={ref}
  data-slot="table-row"
  class={cn(
    'hover:[&,&>svelte-css-wrapper]:[&>th,td]:bg-muted/50 data-[state=selected]:bg-muted border-b transition-colors',
    className
  )}
  {...restProps}
>
  {@render children?.()}
</tr>
