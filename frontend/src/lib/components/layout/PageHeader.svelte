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
  class="sticky top-0 z-10 border-b border-border/40 bg-gradient-to-r from-background via-background to-background/95 backdrop-blur-2xl supports-[backdrop-filter]:bg-background/60"
>
  <!-- Ambient glow effect for dark mode -->
  <div
    class="pointer-events-none absolute inset-0 overflow-hidden"
    aria-hidden="true"
  >
    <div
      class="absolute -top-24 left-1/4 h-48 w-96 rounded-full bg-primary/5 blur-3xl dark:bg-primary/10"
    ></div>
    <div
      class="absolute -top-24 right-1/4 h-48 w-64 rounded-full bg-accent/5 blur-3xl dark:bg-cyan-500/8"
    ></div>
  </div>

  <div class="relative flex min-h-[4.5rem] items-center justify-between gap-6 px-6 py-4 md:px-8">
    <!-- Title Section -->
    <div class="flex flex-col gap-1">
      <div class="flex items-baseline gap-3">
        <h1
          class="text-2xl font-bold tracking-tight text-foreground md:text-[1.75rem]"
          style="letter-spacing: -0.025em;"
        >
          {title}
        </h1>
        {#if subtitle}
          <span class="hidden items-center gap-2 sm:flex">
            <span class="h-1 w-1 rounded-full bg-muted-foreground/30"></span>
            <p class="text-sm font-medium text-muted-foreground/80">{subtitle}</p>
          </span>
        {/if}
      </div>
      {#if subtitle}
        <p class="text-sm font-medium text-muted-foreground/80 sm:hidden">{subtitle}</p>
      {/if}
    </div>

    <!-- Actions Section -->
    {#if actions}
      <div class="flex items-center gap-2 md:gap-3">
        {@render actions()}
      </div>
    {/if}
  </div>

  <!-- Bottom accent line -->
  <div
    class="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-border/60 to-transparent"
  ></div>
</header>
