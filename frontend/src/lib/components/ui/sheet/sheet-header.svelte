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

<div
  bind:this={ref}
  data-slot="sheet-header"
  class={cn('flex flex-col gap-1.5 p-4', className)}
  {...restProps}
>
  {@render children?.()}
</div>
