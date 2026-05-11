<script>
  import { cn } from '$lib/utils.js';

  /**
   * @type {{
   *   children?: import('svelte').Snippet,
   *   empty?: import('svelte').Snippet,
   *   isEmpty?: boolean,
   *   class?: string,
   * }}
   */
  let { children, empty, isEmpty = false, class: className } = $props();
</script>

{#if isEmpty}
  <div class={cn('px-4 py-6 text-center text-[12.5px] text-[color:var(--text-subtle)]', className)}>
    {#if empty}
      {@render empty()}
    {:else}
      No activity yet.
    {/if}
  </div>
{:else}
  <ol class={cn('divide-y divide-[color:var(--border-faint)]', className)}>
    {@render children?.()}
  </ol>
{/if}
