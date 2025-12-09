<script>
  import { ChevronLeft, ChevronRight } from '@lucide/svelte';
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
      'flex flex-col gap-3 border-t border-gray-100 pt-4 sm:flex-row sm:items-center sm:justify-between dark:border-gray-800',
      className
    )}
  >
    <!-- Left side: showing info -->
    <div class="flex items-center gap-4">
      <p class="text-muted-foreground text-sm">
        Showing <span class="text-foreground font-medium">{startItem}</span>
        to <span class="text-foreground font-medium">{endItem}</span>
        of <span class="text-foreground font-medium">{total}</span> results
      </p>
    </div>

    <!-- Right side: limit selector and page navigation -->
    <div class="flex items-center gap-4">
      <!-- Rows per page selector -->
      <div class="flex items-center gap-2">
        <span class="text-muted-foreground text-sm">Rows per page:</span>
        <Popover.Root bind:open={limitPopoverOpen}>
          <Popover.Trigger asChild class="">
            {#snippet child({ props })}
              <button
                type="button"
                class="border-input bg-background hover:bg-accent/50 focus-visible:ring-ring flex h-8 items-center gap-1 rounded-md border px-2.5 text-sm shadow-xs focus-visible:ring-2 focus-visible:outline-none"
                {...props}
              >
                {limit}
                <ChevronRight class="h-3.5 w-3.5 rotate-90 opacity-50" />
              </button>
            {/snippet}
          </Popover.Trigger>
          <Popover.Content align="end" class="w-24 p-1">
            {#each limitOptions as option}
              <button
                type="button"
                class={cn(
                  'hover:bg-accent relative flex w-full cursor-pointer items-center justify-center rounded-sm px-2 py-1.5 text-sm outline-none',
                  option === limit && 'bg-accent font-medium'
                )}
                onclick={() => handleLimitSelect(option)}
              >
                {option}
              </button>
            {/each}
          </Popover.Content>
        </Popover.Root>
      </div>

      <!-- Page navigation -->
      <div class="flex items-center gap-1">
        <Button
          variant="outline"
          size="icon-sm"
          disabled={page <= 1}
          onclick={handlePrevious}
          aria-label="Previous page"
        >
          <ChevronLeft class="h-4 w-4" />
        </Button>

        <span class="min-w-[100px] text-center text-sm">
          Page <span class="font-medium">{page}</span> of
          <span class="font-medium">{totalPages}</span>
        </span>

        <Button
          variant="outline"
          size="icon-sm"
          disabled={page >= totalPages}
          onclick={handleNext}
          aria-label="Next page"
        >
          <ChevronRight class="h-4 w-4" />
        </Button>
      </div>
    </div>
  </div>
{/if}
