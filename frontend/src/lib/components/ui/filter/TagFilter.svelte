<script>
  import { ChevronDown, Check, X, Tag, Hash } from '@lucide/svelte';
  import { cn } from '$lib/utils.js';
  import * as Popover from '$lib/components/ui/popover/index.js';
  import { getTagColorClass } from '$lib/constants/colors.js';

  /**
   * @typedef {{
   *   id: string,
   *   name: string,
   *   color?: string,
   * }} TagOption
   */

  /**
   * @type {{
   *   tags: TagOption[],
   *   value?: string[],
   *   placeholder?: string,
   *   label?: string,
   *   class?: string,
   *   onchange?: (ids: string[]) => void,
   * }}
   */
  let {
    tags = [],
    value = $bindable([]),
    placeholder = 'Filter by tags...',
    label = 'Tags',
    class: className,
    onchange
  } = $props();

  let open = $state(false);

  const selectedIds = $derived(Array.isArray(value) ? value : []);

  const displayText = $derived.by(() => {
    if (selectedIds.length === 0) return placeholder;
    if (selectedIds.length === 1) {
      const tag = tags.find((t) => t.id === selectedIds[0]);
      return tag?.name || selectedIds[0];
    }
    return `${selectedIds.length} tags`;
  });

  /**
   * @param {string} tagId
   */
  function toggleTag(tagId) {
    const newIds = selectedIds.includes(tagId)
      ? selectedIds.filter((id) => id !== tagId)
      : [...selectedIds, tagId];
    value = newIds;
    onchange?.(newIds);
  }

  function clearAll() {
    value = [];
    onchange?.([]);
  }

  const selectedTags = $derived(tags.filter((t) => selectedIds.includes(t.id)));
  const hasSelection = $derived(selectedIds.length > 0);

  /**
   * Get vibrant color classes for tags
   * @param {string | undefined} color
   */
  function getTagStyle(color) {
    const colorMap = {
      blue: 'bg-blue-500/15 text-blue-600 border-blue-500/30 dark:bg-blue-500/25 dark:text-blue-400 dark:border-blue-400/30',
      green: 'bg-emerald-500/15 text-emerald-600 border-emerald-500/30 dark:bg-emerald-500/25 dark:text-emerald-400 dark:border-emerald-400/30',
      red: 'bg-rose-500/15 text-rose-600 border-rose-500/30 dark:bg-rose-500/25 dark:text-rose-400 dark:border-rose-400/30',
      yellow: 'bg-amber-500/15 text-amber-600 border-amber-500/30 dark:bg-amber-500/25 dark:text-amber-400 dark:border-amber-400/30',
      purple: 'bg-violet-500/15 text-violet-600 border-violet-500/30 dark:bg-violet-500/25 dark:text-violet-400 dark:border-violet-400/30',
      pink: 'bg-pink-500/15 text-pink-600 border-pink-500/30 dark:bg-pink-500/25 dark:text-pink-400 dark:border-pink-400/30',
      orange: 'bg-orange-500/15 text-orange-600 border-orange-500/30 dark:bg-orange-500/25 dark:text-orange-400 dark:border-orange-400/30',
      cyan: 'bg-cyan-500/15 text-cyan-600 border-cyan-500/30 dark:bg-cyan-500/25 dark:text-cyan-400 dark:border-cyan-400/30',
      gray: 'bg-slate-500/15 text-slate-600 border-slate-500/30 dark:bg-slate-500/25 dark:text-slate-400 dark:border-slate-400/30',
    };
    return colorMap[color || 'blue'] || colorMap.blue;
  }
</script>

<div class={cn('flex flex-col gap-1.5', className)}>
  {#if label}
    <span class="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground/70">
      {label}
    </span>
  {/if}
  <Popover.Root bind:open>
    <Popover.Trigger asChild class="">
      {#snippet child({ props })}
        <button
          type="button"
          class={cn(
            'tag-filter-trigger group',
            'relative flex h-9 w-full items-center justify-between gap-2',
            'rounded-lg border px-3 py-2',
            'bg-background/60 backdrop-blur-sm',
            'text-sm transition-all duration-200',
            'outline-none',
            // Default state
            'border-input/60',
            'hover:border-input hover:bg-background/80',
            // Focus state
            'focus:border-primary/50 focus:bg-background',
            'focus:ring-2 focus:ring-primary/20',
            // Dark mode
            'dark:bg-white/[0.03] dark:border-white/[0.08]',
            'dark:hover:bg-white/[0.05] dark:hover:border-white/[0.12]',
            'dark:focus:bg-white/[0.06] dark:focus:border-primary/40',
            // Active state
            hasSelection && 'border-primary/40 bg-primary/[0.03] dark:border-primary/30 dark:bg-primary/[0.08]',
            // Open state
            open && 'ring-2 ring-primary/20 dark:ring-primary/30'
          )}
          {...props}
        >
          <div class="flex items-center gap-2">
            <Tag
              class={cn(
                'h-4 w-4 transition-colors duration-200',
                hasSelection ? 'text-primary' : 'text-muted-foreground'
              )}
            />
            <span
              class={cn(
                'truncate transition-colors duration-150',
                hasSelection ? 'text-foreground font-medium' : 'text-muted-foreground'
              )}
            >
              {displayText}
            </span>
          </div>

          <div class="flex shrink-0 items-center gap-1">
            {#if hasSelection}
              <!-- Count badge -->
              <span
                class={cn(
                  'inline-flex h-5 min-w-5 items-center justify-center rounded-full px-1.5',
                  'bg-primary text-[10px] font-bold text-primary-foreground',
                  'animate-in fade-in zoom-in duration-200'
                )}
              >
                {selectedIds.length}
              </span>
              <!-- Clear button -->
              <span
                role="button"
                tabindex="0"
                onclick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  clearAll();
                }}
                onkeydown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.stopPropagation();
                    e.preventDefault();
                    clearAll();
                  }
                }}
                class={cn(
                  'flex h-5 w-5 items-center justify-center rounded-md',
                  'text-muted-foreground/60 transition-all duration-150',
                  'hover:bg-muted hover:text-foreground',
                  'active:scale-90'
                )}
              >
                <X class="h-3 w-3" />
              </span>
            {/if}
            <ChevronDown
              class={cn(
                'h-4 w-4 text-muted-foreground/50 transition-transform duration-200',
                open && 'rotate-180'
              )}
            />
          </div>
        </button>
      {/snippet}
    </Popover.Trigger>

    <Popover.Content
      align="start"
      sideOffset={4}
      class={cn(
        'tag-filter-content',
        'w-[280px] overflow-hidden rounded-xl p-1',
        'border border-border/60 bg-popover/95 backdrop-blur-md',
        'shadow-lg shadow-black/5',
        'dark:border-white/[0.08] dark:bg-popover/90',
        'dark:shadow-[0_8px_32px_-4px_rgba(0,0,0,0.5)]',
        'animate-in fade-in-0 zoom-in-95 duration-150'
      )}
    >
      {#if tags.length === 0}
        <div class="flex flex-col items-center justify-center py-6 text-center">
          <Tag class="mb-2 h-8 w-8 text-muted-foreground/30" />
          <p class="text-sm font-medium text-muted-foreground">No tags available</p>
          <p class="mt-1 text-xs text-muted-foreground/60">Create tags to organize your leads</p>
        </div>
      {:else}
        <!-- Header with selected count -->
        {#if selectedIds.length > 0}
          <div
            class={cn(
              'mb-1 flex items-center justify-between rounded-lg px-2.5 py-2',
              'bg-primary/5 dark:bg-primary/10'
            )}
          >
            <span class="text-xs font-medium text-primary">
              {selectedIds.length} tag{selectedIds.length > 1 ? 's' : ''} selected
            </span>
            <button
              type="button"
              onclick={clearAll}
              class="text-xs font-medium text-primary/70 hover:text-primary transition-colors"
            >
              Clear all
            </button>
          </div>
        {/if}

        <!-- Tags list -->
        <div class="max-h-[280px] space-y-0.5 overflow-y-auto">
          {#each tags as tag, i (tag.id)}
            {@const isSelected = selectedIds.includes(tag.id)}
            <button
              type="button"
              class={cn(
                'tag-option group',
                'relative flex w-full cursor-pointer items-center gap-2.5',
                'rounded-lg px-2.5 py-2',
                'transition-all duration-150',
                'outline-none',
                isSelected
                  ? 'bg-primary/10 dark:bg-primary/15'
                  : 'hover:bg-muted/80',
                'animate-in fade-in-0 slide-in-from-left-1'
              )}
              style="animation-delay: {i * 15}ms"
              onclick={() => toggleTag(tag.id)}
            >
              <!-- Checkbox -->
              <div
                class={cn(
                  'flex h-4 w-4 shrink-0 items-center justify-center rounded',
                  'border transition-all duration-150',
                  isSelected
                    ? 'border-primary bg-primary text-primary-foreground scale-100'
                    : 'border-border/60 bg-transparent scale-90 group-hover:scale-100 group-hover:border-primary/50'
                )}
              >
                {#if isSelected}
                  <Check class="h-2.5 w-2.5" />
                {/if}
              </div>

              <!-- Tag badge -->
              <span
                class={cn(
                  'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5',
                  'text-xs font-semibold',
                  'transition-all duration-150',
                  getTagStyle(tag.color),
                  isSelected && 'ring-1 ring-primary/20'
                )}
              >
                <Hash class="h-3 w-3 opacity-60" />
                {tag.name}
              </span>

              <!-- Selected indicator glow -->
              {#if isSelected}
                <div
                  class={cn(
                    'absolute right-2 h-2 w-2 rounded-full bg-primary',
                    'animate-in fade-in zoom-in duration-200'
                  )}
                ></div>
              {/if}
            </button>
          {/each}
        </div>
      {/if}
    </Popover.Content>
  </Popover.Root>
</div>

<!-- Selected tags as inline badges -->
{#if selectedTags.length > 0}
  <div class="mt-2 flex flex-wrap gap-1.5">
    {#each selectedTags as tag, i (tag.id)}
      <span
        class={cn(
          'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1',
          'text-xs font-semibold',
          'transition-all duration-150',
          getTagStyle(tag.color),
          'animate-in fade-in zoom-in slide-in-from-bottom-1'
        )}
        style="animation-delay: {i * 40}ms"
      >
        <Hash class="h-3 w-3 opacity-60" />
        {tag.name}
        <button
          type="button"
          onclick={() => toggleTag(tag.id)}
          class={cn(
            'flex h-4 w-4 items-center justify-center rounded-full',
            'transition-all duration-150',
            'hover:bg-black/10 dark:hover:bg-white/20',
            'active:scale-90'
          )}
        >
          <X class="h-2.5 w-2.5" />
        </button>
      </span>
    {/each}
  </div>
{/if}

<style>
  .tag-filter-trigger {
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
  }

  :global(.dark) .tag-filter-trigger {
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  .tag-filter-trigger:focus {
    box-shadow:
      inset 0 1px 2px rgba(0, 0, 0, 0.02),
      0 0 0 3px var(--ring);
  }

  :global(.dark) .tag-filter-trigger:focus {
    box-shadow:
      inset 0 1px 2px rgba(0, 0, 0, 0.1),
      0 0 0 3px var(--ring),
      0 0 20px -4px var(--primary);
  }

  .tag-option {
    position: relative;
  }

  .tag-option::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: inherit;
    opacity: 0;
    background: linear-gradient(
      90deg,
      transparent 0%,
      var(--primary) 50%,
      transparent 100%
    );
    transition: opacity 0.3s ease;
  }

  :global(.dark) .tag-option:hover::before {
    opacity: 0.02;
  }
</style>
