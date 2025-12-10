<script>
  import { Filter, X, ChevronDown, ChevronUp, Sparkles } from '@lucide/svelte';
  import { cn } from '$lib/utils.js';
  import { Button } from '$lib/components/ui/button/index.js';

  /**
   * @type {{
   *   activeCount?: number,
   *   collapsible?: boolean,
   *   defaultExpanded?: boolean,
   *   expanded?: boolean,
   *   minimal?: boolean,
   *   class?: string,
   *   onClear?: () => void,
   *   children?: import('svelte').Snippet,
   * }}
   */
  let {
    activeCount = 0,
    collapsible = false,
    defaultExpanded = true,
    expanded: externalExpanded,
    minimal = false,
    class: className,
    onClear,
    children
  } = $props();

  // Use a function to capture initial value
  let internalExpanded = $state((() => defaultExpanded)());

  // Use external expanded if provided, otherwise use internal state
  const isExpanded = $derived(externalExpanded !== undefined ? externalExpanded : internalExpanded);
</script>

{#if minimal}
  <!-- Minimal mode: sleek inline filter row with glass effect -->
  {#if isExpanded}
    <div
      class={cn(
        'filter-bar-minimal',
        'relative flex flex-wrap items-end gap-3 px-4 py-3',
        'from-muted/40 via-muted/20 to-muted/40 bg-gradient-to-r',
        'border-border/50 border backdrop-blur-sm',
        'dark:from-white/[0.02] dark:via-white/[0.04] dark:to-white/[0.02]',
        'dark:border-white/[0.06]',
        'transition-all duration-300 ease-out',
        className
      )}
    >
      <!-- Subtle gradient overlay -->
      <div
        class="pointer-events-none absolute inset-0 opacity-0 transition-opacity duration-500 group-hover:opacity-100 dark:opacity-[0.02]"
        style="background: radial-gradient(ellipse at 50% 0%, var(--accent-primary) 0%, transparent 70%);"
      ></div>

      <!-- Filter content -->
      <div class="relative z-10 flex flex-wrap items-end gap-3">
        {@render children?.()}
      </div>

      <!-- Clear button with animation -->
      {#if activeCount > 0 && onClear}
        <div class="relative z-10 ml-auto flex items-center gap-2">
          <div
            class="bg-primary/10 dark:bg-primary/20 flex items-center gap-1.5 rounded-full px-2.5 py-1"
          >
            <Sparkles class="text-primary h-3 w-3" />
            <span class="text-primary text-xs font-semibold">
              {activeCount} active
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onclick={onClear}
            class="group/clear text-muted-foreground hover:bg-destructive/10 hover:text-destructive dark:hover:bg-destructive/20 h-8 gap-1.5 rounded-lg px-3 text-xs font-medium transition-all"
          >
            <X class="h-3.5 w-3.5 transition-transform group-hover/clear:rotate-90" />
            Clear all
          </Button>
        </div>
      {/if}
    </div>
  {/if}
{:else}
  <!-- Full mode: Refined card with premium styling -->
  <div
    class={cn(
      'filter-bar-full',
      'overflow-hidden rounded-xl',
      'bg-card/80 backdrop-blur-md',
      'border-border/60 border',
      'shadow-sm',
      'dark:bg-card/60 dark:border-white/[0.08]',
      'dark:shadow-[0_4px_24px_-4px_rgba(0,0,0,0.3)]',
      'transition-all duration-300',
      className
    )}
  >
    <!-- Header -->
    <div
      class={cn(
        'flex items-center justify-between px-4 py-2.5',
        'from-muted/30 bg-gradient-to-r to-transparent',
        'dark:from-white/[0.02] dark:to-transparent'
      )}
    >
      <button
        type="button"
        class={cn(
          'group flex items-center gap-2.5 text-sm font-semibold',
          'text-foreground/80 hover:text-foreground transition-colors',
          !collapsible && 'cursor-default'
        )}
        onclick={() => collapsible && (internalExpanded = !internalExpanded)}
        disabled={!collapsible}
      >
        <div
          class={cn(
            'flex h-7 w-7 items-center justify-center rounded-lg',
            'bg-primary/10 text-primary',
            'dark:bg-primary/20',
            'transition-all duration-200',
            collapsible && 'group-hover:bg-primary/20 group-hover:scale-105'
          )}
        >
          <Filter class="h-3.5 w-3.5" />
        </div>
        <span class="tracking-tight">Filters</span>
        {#if activeCount > 0}
          <span
            class={cn(
              'inline-flex items-center justify-center',
              'h-5 min-w-5 rounded-full px-1.5',
              'bg-primary text-primary-foreground text-[10px] font-bold',
              'animate-in fade-in zoom-in duration-200'
            )}
          >
            {activeCount}
          </span>
        {/if}
        {#if collapsible}
          <div class="ml-1 transition-transform duration-200" class:rotate-180={isExpanded}>
            <ChevronDown class="h-4 w-4 opacity-50" />
          </div>
        {/if}
      </button>

      {#if activeCount > 0 && onClear}
        <Button
          variant="ghost"
          size="sm"
          onclick={onClear}
          class="group/clear text-muted-foreground hover:bg-destructive/10 hover:text-destructive h-7 gap-1.5 rounded-lg px-2.5 text-xs font-medium transition-all"
        >
          <X class="h-3 w-3 transition-transform group-hover/clear:rotate-90" />
          Clear all
        </Button>
      {/if}
    </div>

    <!-- Filter content with smooth expand/collapse -->
    {#if !collapsible || isExpanded}
      <div
        class={cn(
          'border-border/40 border-t px-4 py-4',
          'dark:border-white/[0.04]',
          'animate-in fade-in slide-in-from-top-2 duration-200'
        )}
      >
        <div class="flex flex-wrap items-end gap-4">
          {@render children?.()}
        </div>
      </div>
    {/if}
  </div>
{/if}

<style>
  .filter-bar-minimal {
    --filter-glow: 0 0 0 1px var(--border);
  }

  .filter-bar-minimal:focus-within {
    --filter-glow: 0 0 0 1px var(--ring), 0 0 20px -8px var(--accent-primary);
  }

  :global(.dark) .filter-bar-minimal:focus-within {
    --filter-glow: 0 0 0 1px var(--ring), 0 0 30px -10px var(--accent-primary);
  }

  .filter-bar-minimal {
    box-shadow: var(--filter-glow);
  }
</style>
