<script>
  import { enhance } from '$app/forms';
  import { cn } from '$lib/utils.js';

  /**
   * @typedef {Object} Props
   * @property {'GET' | 'POST' | 'get' | 'post' | 'dialog' | 'DIALOG'} [method]
   * @property {string} [action]
   * @property {'application/x-www-form-urlencoded' | 'multipart/form-data' | 'text/plain'} [enctype]
   * @property {(this: HTMLFormElement, event: SubmitEvent) => void} [onsubmit]
   * @property {import('@sveltejs/kit').SubmitFunction} [useEnhance]
   * @property {string} [class]
   * @property {string} [errorMessage]
   * @property {import('svelte').Snippet} children
   * @property {import('svelte').Snippet} actions
   */

  /** @type {Props} */
  let {
    method = 'POST',
    action = '',
    enctype,
    onsubmit,
    useEnhance = undefined,
    class: className,
    errorMessage = '',
    children,
    actions
  } = $props();

</script>

{#snippet body()}
  <div class="flex flex-col gap-6">
    {@render children()}
  </div>

  <div
    class="fixed inset-x-0 bottom-0 z-20 border-t border-[color:var(--border-faint)] bg-[color:var(--bg)]/95 backdrop-blur-[1px]"
  >
    <div class="mx-auto flex max-w-[680px] items-center justify-between gap-3 px-7 py-3 md:px-8">
      {#if errorMessage}
        <p class="truncate text-[12px] text-[color:var(--red)]">{errorMessage}</p>
      {:else}
        <span></span>
      {/if}
      <div class="flex items-center gap-2">
        {@render actions()}
      </div>
    </div>
  </div>
{/snippet}

{#if useEnhance}
  <form
    {method}
    {action}
    {enctype}
    {onsubmit}
    use:enhance={useEnhance}
    class={cn(
      'mx-auto flex w-full max-w-[680px] flex-col',
      'px-7 pt-4 pb-[88px] md:px-8',
      className
    )}
  >
    {@render body()}
  </form>
{:else}
  <form
    {method}
    {action}
    {enctype}
    {onsubmit}
    class={cn(
      'mx-auto flex w-full max-w-[680px] flex-col',
      'px-7 pt-4 pb-[88px] md:px-8',
      className
    )}
  >
    {@render body()}
  </form>
{/if}
