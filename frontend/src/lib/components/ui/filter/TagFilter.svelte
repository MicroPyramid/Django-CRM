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
    label: _label = '',
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
      green:
        'bg-emerald-500/15 text-emerald-600 border-emerald-500/30 dark:bg-emerald-500/25 dark:text-emerald-400 dark:border-emerald-400/30',
      red: 'bg-rose-500/15 text-rose-600 border-rose-500/30 dark:bg-rose-500/25 dark:text-rose-400 dark:border-rose-400/30',
      yellow:
        'bg-amber-500/15 text-amber-600 border-amber-500/30 dark:bg-amber-500/25 dark:text-amber-400 dark:border-amber-400/30',
      purple:
        'bg-violet-500/15 text-violet-600 border-violet-500/30 dark:bg-violet-500/25 dark:text-violet-400 dark:border-violet-400/30',
      pink: 'bg-pink-500/15 text-pink-600 border-pink-500/30 dark:bg-pink-500/25 dark:text-pink-400 dark:border-pink-400/30',
      orange:
        'bg-orange-500/15 text-orange-600 border-orange-500/30 dark:bg-orange-500/25 dark:text-orange-400 dark:border-orange-400/30',
      cyan: 'bg-cyan-500/15 text-cyan-600 border-cyan-500/30 dark:bg-cyan-500/25 dark:text-cyan-400 dark:border-cyan-400/30',
      gray: 'bg-slate-500/15 text-slate-600 border-slate-500/30 dark:bg-slate-500/25 dark:text-slate-400 dark:border-slate-400/30'
    };
    return colorMap[color || 'blue'] || colorMap.blue;
  }
</script>

<Popover.Root bind:open>
    <Popover.Trigger asChild class="">
      {#snippet child({ props })}
        <button
          type="button"
          {...props}
          class={cn(
            'inline-flex h-7 items-center gap-1.5 rounded-[var(--r-sm)] border px-2.5 text-[13.5px] font-medium leading-none transition-colors focus:outline-none focus:ring-1 focus:ring-[color:var(--ring)]',
            hasSelection
              ? 'border-[color:var(--violet)]/40 bg-[color:var(--violet-soft)] text-[color:var(--violet-soft-text)]'
              : 'border-[color:var(--border-faint)] bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)] hover:bg-[color:var(--bg-hover)]',
            className
          )}
        >
          <Tag class="size-3.5 shrink-0" />
          <span class="truncate">{displayText}</span>
          {#if hasSelection}
            <span
              class="inline-flex h-[18px] min-w-[18px] items-center justify-center rounded-[var(--r-sm)] px-1.5 text-[11.2px] font-medium tabular-nums text-[color:var(--violet-soft-text)] opacity-90"
            >
              {selectedIds.length}
            </span>
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
              class="-mr-1 ml-0.5 flex size-3.5 shrink-0 items-center justify-center rounded-sm hover:bg-[color:var(--violet)]/15"
              aria-label="Clear filter"
            >
              <X class="size-3" />
            </span>
          {:else}
            <ChevronDown class="size-3.5 shrink-0 opacity-60" />
          {/if}
        </button>
      {/snippet}
    </Popover.Trigger>

    <Popover.Content
      align="start"
      sideOffset={4}
      class="w-[280px] overflow-hidden rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-card)] p-1 shadow-lg shadow-black/5"
    >
      {#if tags.length === 0}
        <div class="flex flex-col items-center justify-center py-6 text-center">
          <Tag class="text-muted-foreground/30 mb-2 h-8 w-8" />
          <p class="text-muted-foreground text-sm font-medium">No tags available</p>
          <p class="text-muted-foreground/60 mt-1 text-xs">Create tags to organize your leads</p>
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
            <span class="text-primary text-xs font-medium">
              {selectedIds.length} tag{selectedIds.length > 1 ? 's' : ''} selected
            </span>
            <button
              type="button"
              onclick={clearAll}
              class="text-primary/70 hover:text-primary text-xs font-medium transition-colors"
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
                isSelected ? 'bg-primary/10 dark:bg-primary/15' : 'hover:bg-muted/80',
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
                    : 'border-border/60 group-hover:border-primary/50 scale-90 bg-transparent group-hover:scale-100'
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
                  isSelected && 'ring-primary/20 ring-1'
                )}
              >
                <Hash class="h-3 w-3 opacity-60" />
                {tag.name}
              </span>

              <!-- Selected indicator glow -->
              {#if isSelected}
                <div
                  class={cn(
                    'bg-primary absolute right-2 h-2 w-2 rounded-full',
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
