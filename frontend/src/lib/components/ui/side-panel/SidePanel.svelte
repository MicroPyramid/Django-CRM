<script>
  import { X, ChevronLeft } from '@lucide/svelte';
  import { cn } from '$lib/utils.js';
  import { sidePanelHidden } from './index.js';

  /**
   * @typedef {Object} Props
   * @property {string} [class]
   * @property {import('svelte').Snippet} [head]
   * @property {import('svelte').Snippet} [body]
   * @property {import('svelte').Snippet} [empty]
   * @property {boolean} [hasActive]
   */

  /** @type {Props} */
  let { class: className, head, body, empty, hasActive = true } = $props();

  function close() {
    sidePanelHidden.set(true);
  }

  function reopen() {
    sidePanelHidden.set(false);
  }
</script>

{#if $sidePanelHidden}
  <button
    type="button"
    onclick={reopen}
    aria-label="Show side panel"
    class="fixed right-0 top-1/2 z-30 hidden h-16 w-3 -translate-y-1/2 items-center justify-center rounded-l-md border border-r-0 border-[color:var(--border)] bg-[color:var(--bg-card)] text-[color:var(--text-subtle)] hover:text-[color:var(--text)] hover:bg-[color:var(--bg-hover)] xl:flex"
  >
    <ChevronLeft class="size-3.5" />
  </button>
{:else}
  <aside
    class={cn(
      'fixed right-0 top-0 z-20 hidden h-screen w-[380px] flex-col border-l border-[color:var(--border-faint)] bg-[color:var(--bg-card)] xl:flex',
      className
    )}
  >
    <div class="flex items-start justify-between gap-2 border-b border-[color:var(--border-faint)] px-[22px] pt-5 pb-4">
      <div class="min-w-0 flex-1">
        {#if hasActive && head}
          {@render head()}
        {:else}
          <p class="text-[13px] text-[color:var(--text-subtle)]">No row selected</p>
        {/if}
      </div>
      <button
        type="button"
        onclick={close}
        aria-label="Hide side panel"
        class="-mr-1 inline-flex size-7 shrink-0 items-center justify-center rounded-md text-[color:var(--text-subtle)] hover:bg-[color:var(--bg-hover)] hover:text-[color:var(--text)]"
      >
        <X class="size-4" />
      </button>
    </div>

    <div class="flex-1 overflow-y-auto px-[22px] py-[18px]">
      {#if hasActive && body}
        <div class="flex flex-col gap-5">
          {@render body()}
        </div>
      {:else if empty}
        {@render empty()}
      {:else}
        <p class="text-[12px] text-[color:var(--text-subtle)]">Click a row to peek.</p>
      {/if}
    </div>
  </aside>
{/if}
