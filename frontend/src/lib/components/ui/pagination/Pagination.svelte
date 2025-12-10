<script>
  import { ChevronLeft, ChevronRight, ChevronsUpDown } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Popover from '$lib/components/ui/popover/index.js';
  import { cn } from '$lib/utils.js';

  /**
   * @type {{
   *   page?: number,
   *   limit?: number,
   *   total?: number,
   *   limitOptions?: number[],
   *   class?: string,
   *   onPageChange?: (page: number) => void,
   *   onLimitChange?: (limit: number) => void,
   * }}
   */
  let {
    page = 1,
    limit = 10,
    total = 0,
    limitOptions = [10, 25, 50, 100],
    class: className,
    onPageChange,
    onLimitChange
  } = $props();

  const totalPages = $derived(Math.ceil(total / limit) || 1);
  const startItem = $derived((page - 1) * limit + 1);
  const endItem = $derived(Math.min(page * limit, total));

  let limitPopoverOpen = $state(false);

  function handlePrevious() {
    if (page > 1) {
      onPageChange?.(page - 1);
    }
  }

  function handleNext() {
    if (page < totalPages) {
      onPageChange?.(page + 1);
    }
  }

  /**
   * @param {number} newLimit
   */
  function handleLimitSelect(newLimit) {
    limitPopoverOpen = false;
    if (newLimit !== limit) {
      onLimitChange?.(newLimit);
    }
  }
</script>

{#if total > 0}
  <div
    class={cn(
      'relative mt-6 flex flex-col items-center gap-4 px-1 sm:flex-row sm:justify-between',
      className
    )}
  >
    <!-- Left side: Results summary with refined typography -->
    <div class="flex items-center gap-2">
      <p class="text-sm text-muted-foreground">
        Showing
        <span class="mx-1 inline-flex items-center justify-center rounded-md bg-muted/50 px-2 py-0.5 font-semibold tabular-nums text-foreground">
          {startItem}–{endItem}
        </span>
        of
        <span class="ml-1 font-semibold text-foreground">{total}</span>
        results
      </p>
    </div>

    <!-- Right side: Controls -->
    <div class="flex items-center gap-3">
      <!-- Rows per page selector -->
      <div class="flex items-center gap-2">
        <span class="text-xs font-medium uppercase tracking-wide text-muted-foreground/70">Rows</span>
        <Popover.Root bind:open={limitPopoverOpen}>
          <Popover.Trigger asChild class="">
            {#snippet child({ props })}
              <button
                type="button"
                class="group inline-flex h-9 items-center gap-1.5 rounded-lg border border-border/60 bg-card/50 px-3 text-sm font-medium text-foreground shadow-sm backdrop-blur-sm transition-all duration-150 hover:border-border hover:bg-card focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50"
                {...props}
              >
                <span class="tabular-nums">{limit}</span>
                <ChevronsUpDown class="h-3.5 w-3.5 text-muted-foreground transition-colors group-hover:text-foreground" />
              </button>
            {/snippet}
          </Popover.Trigger>
          <Popover.Content align="end" class="w-28 p-1.5">
            <div class="flex flex-col gap-0.5">
              {#each limitOptions as option}
                <button
                  type="button"
                  class={cn(
                    'flex w-full items-center justify-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    option === limit
                      ? 'bg-primary text-primary-foreground'
                      : 'text-foreground hover:bg-muted'
                  )}
                  onclick={() => handleLimitSelect(option)}
                >
                  {option}
                </button>
              {/each}
            </div>
          </Popover.Content>
        </Popover.Root>
      </div>

      <!-- Divider -->
      <div class="h-5 w-px bg-border/60"></div>

      <!-- Page navigation -->
      <div class="flex items-center gap-1.5">
        <button
          type="button"
          disabled={page <= 1}
          onclick={handlePrevious}
          aria-label="Previous page"
          class="group inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border/60 bg-card/50 text-muted-foreground shadow-sm backdrop-blur-sm transition-all duration-150 hover:border-border hover:bg-card hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-40"
        >
          <ChevronLeft class="h-4 w-4 transition-transform group-hover:-translate-x-0.5" />
        </button>

        <!-- Page indicator pill -->
        <div class="flex min-w-[7rem] items-center justify-center gap-1 rounded-lg border border-border/40 bg-muted/30 px-3 py-1.5">
          <span class="text-sm font-semibold tabular-nums text-foreground">{page}</span>
          <span class="text-xs text-muted-foreground">/</span>
          <span class="text-sm tabular-nums text-muted-foreground">{totalPages}</span>
        </div>

        <button
          type="button"
          disabled={page >= totalPages}
          onclick={handleNext}
          aria-label="Next page"
          class="group inline-flex h-9 w-9 items-center justify-center rounded-lg border border-border/60 bg-card/50 text-muted-foreground shadow-sm backdrop-blur-sm transition-all duration-150 hover:border-border hover:bg-card hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:opacity-40"
        >
          <ChevronRight class="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
        </button>
      </div>
    </div>
  </div>
{/if}
