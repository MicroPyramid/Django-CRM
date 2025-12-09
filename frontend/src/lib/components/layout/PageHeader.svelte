<script>
  /**
   * @typedef {Object} Props
   * @property {string} title - Page title
   * @property {string} [subtitle] - Optional subtitle
   * @property {import('svelte').Snippet} [actions] - Optional actions snippet
   */

  /** @type {Props} */
  let { title, subtitle = '', actions } = $props();
</script>

<header
  class="bg-background/95 supports-[backdrop-filter]:bg-background/60 sticky top-0 z-10 border-b backdrop-blur"
>
  <div class="flex h-14 items-center justify-between px-4 md:px-6">
    <div class="space-y-0.5">
      <h1 class="text-foreground text-lg font-semibold">{title}</h1>
      {#if subtitle}
        <p class="text-muted-foreground text-sm">{subtitle}</p>
      {/if}
    </div>
    {#if actions}
      <div class="flex items-center gap-2">
        {@render actions()}
      </div>
    {/if}
  </div>
</header>
