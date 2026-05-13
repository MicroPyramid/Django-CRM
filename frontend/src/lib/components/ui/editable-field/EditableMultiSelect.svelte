<script>
  import { ChevronDown, X, Search, AlertCircle, RotateCw } from '@lucide/svelte';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { Skeleton } from '$lib/components/ui/skeleton/index.js';
  import { cn } from '$lib/utils.js';

  /**
   * @typedef {Object} SelectOption
   * @property {string} [id]
   * @property {string} [value]
   * @property {string} [name]
   * @property {string} [label]
   * @property {string} [email]
   */

  /**
   * @type {{
   *   value?: string[],
   *   options?: SelectOption[],
   *   placeholder?: string,
   *   emptyText?: string,
   *   disabled?: boolean,
   *   loading?: boolean,
   *   error?: string,
   *   onRetry?: () => void,
   *   onchange?: (value: string[]) => void,
   *   class?: string,
   *   maxDisplay?: number,
   *   searchThreshold?: number,
   * }}
   */
  let {
    value = [],
    options = [],
    placeholder = 'Select...',
    emptyText = 'None selected',
    disabled = false,
    loading = false,
    error = '',
    onRetry,
    onchange,
    class: className,
    maxDisplay = 3,
    searchThreshold = 6
  } = $props();

  let isOpen = $state(false);
  let query = $state('');

  // Reset the search query whenever the dropdown closes
  $effect(() => {
    if (!isOpen) query = '';
  });

  /**
   * Toggle an option
   * @param {string} id
   */
  function toggleOption(id) {
    const newValue = value.includes(id) ? value.filter((v) => v !== id) : [...value, id];
    onchange?.(newValue);
  }

  /**
   * Remove an option
   * @param {Event} e
   * @param {string} id
   */
  function removeOption(e, id) {
    e.stopPropagation();
    const newValue = value.filter((v) => v !== id);
    onchange?.(newValue);
  }

  /**
   * Normalize option data so shared drawers can pass either `{ id, name }`
   * or `{ value, label }` without crashing keyed each blocks.
   * @returns {Array<SelectOption & { id: string, name: string }>}
   */
  const normalizedOptions = $derived(
    options
      .map((opt) => {
        const id = opt?.id ?? opt?.value;
        if (!id) return null;

        return {
          ...opt,
          id,
          name: opt?.name ?? opt?.label ?? opt?.email ?? id
        };
      })
      .filter(Boolean)
  );

  // Show the search input once there are enough options to make it useful
  const showSearch = $derived(!loading && !error && normalizedOptions.length >= searchThreshold);

  const filteredOptions = $derived.by(() => {
    const q = query.trim().toLowerCase();
    if (!q) return normalizedOptions;
    return normalizedOptions.filter((opt) => {
      const name = (opt.name || '').toLowerCase();
      const email = (opt.email || '').toLowerCase();
      return name.includes(q) || email.includes(q);
    });
  });

  /**
   * Get selected options
   */
  const selectedOptions = $derived(normalizedOptions.filter((opt) => value.includes(opt.id)));

  /**
   * Get display options (limited to maxDisplay)
   */
  const displayOptions = $derived(selectedOptions.slice(0, maxDisplay));

  /**
   * Get remaining count
   */
  const remainingCount = $derived(
    selectedOptions.length > maxDisplay ? selectedOptions.length - maxDisplay : 0
  );
</script>

<div class={cn('group', className)}>
  <DropdownMenu.Root bind:open={isOpen}>
    <DropdownMenu.Trigger {disabled} class="w-full">
      <button
        type="button"
        class={cn(
          'flex min-h-[36px] w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
          !disabled && 'hover:bg-muted/50 cursor-pointer',
          disabled && 'cursor-default opacity-50'
        )}
      >
        <div class="flex flex-1 flex-wrap items-center gap-1.5">
          {#if selectedOptions.length === 0}
            <span class="text-muted-foreground italic">{emptyText}</span>
          {:else}
            {#each displayOptions as opt (opt.id)}
              <Badge variant="secondary" class="gap-1 pr-1">
                <span class="max-w-[120px] truncate">{opt.name}</span>
                {#if !disabled}
                  <button
                    type="button"
                    aria-label="Remove {opt.name}"
                    class="hover:bg-muted rounded-sm p-0.5"
                    onclick={(e) => removeOption(e, opt.id)}
                  >
                    <X class="h-3 w-3" aria-hidden="true" />
                  </button>
                {/if}
              </Badge>
            {/each}
            {#if remainingCount > 0}
              <Badge variant="outline" class="text-xs">+{remainingCount}</Badge>
            {/if}
          {/if}
        </div>
        <ChevronDown
          aria-hidden="true"
          class={cn(
            'text-muted-foreground h-4 w-4 shrink-0 transition-transform',
            isOpen && 'rotate-180'
          )}
        />
      </button>
    </DropdownMenu.Trigger>
    <DropdownMenu.Content class="max-h-72 w-64 overflow-hidden p-0" align="start">
      {#if showSearch}
        <div class="border-border/40 bg-background sticky top-0 z-10 border-b p-1.5">
          <div class="relative">
            <Search
              aria-hidden="true"
              class="text-muted-foreground/60 pointer-events-none absolute top-1/2 left-2 h-3.5 w-3.5 -translate-y-1/2"
            />
            <input
              type="search"
              bind:value={query}
              placeholder="Search…"
              aria-label="Search options"
              class="focus:ring-primary/30 placeholder:text-muted-foreground/50 w-full rounded-md border-0 bg-transparent py-1.5 pr-2 pl-7 text-xs outline-none focus:ring-1"
            />
          </div>
        </div>
      {/if}

      <div class="max-h-56 overflow-y-auto p-1">
        {#if loading}
          <div class="space-y-1.5 px-1 py-1.5" aria-busy="true" aria-live="polite">
            {#each { length: 3 } as _, i (i)}
              <div class="flex items-center gap-2 px-1.5 py-1">
                <Skeleton class="h-3.5 w-3.5 rounded" />
                <Skeleton class="h-3.5 flex-1 rounded" />
              </div>
            {/each}
          </div>
        {:else if error}
          <div class="flex items-start gap-2 px-2 py-3 text-xs" role="alert">
            <AlertCircle
              class="text-destructive mt-0.5 h-4 w-4 shrink-0"
              aria-hidden="true"
            />
            <div class="flex-1 space-y-1.5">
              <p class="text-destructive font-medium">{error}</p>
              {#if onRetry}
                <button
                  type="button"
                  onclick={onRetry}
                  class="text-primary hover:bg-primary/10 inline-flex items-center gap-1 rounded px-1.5 py-0.5 text-[11px] font-medium"
                >
                  <RotateCw class="h-3 w-3" aria-hidden="true" />
                  Retry
                </button>
              {/if}
            </div>
          </div>
        {:else if normalizedOptions.length === 0}
          <div class="text-muted-foreground px-2 py-4 text-center text-sm">
            No options available
          </div>
        {:else if filteredOptions.length === 0}
          <div class="text-muted-foreground px-2 py-4 text-center text-xs">
            No matches for "{query}"
          </div>
        {:else}
          <DropdownMenu.CheckboxGroup value={value}>
            {#each filteredOptions as opt (opt.id)}
              <DropdownMenu.CheckboxItem
                checked={value.includes(opt.id)}
                onCheckedChange={() => toggleOption(opt.id)}
                closeOnSelect={false}
                class=""
              >
                <div class="flex flex-col">
                  <span>{opt.name}</span>
                  {#if opt.email && opt.email !== opt.name}
                    <span class="text-muted-foreground text-xs">{opt.email}</span>
                  {/if}
                </div>
              </DropdownMenu.CheckboxItem>
            {/each}
          </DropdownMenu.CheckboxGroup>
        {/if}
      </div>
    </DropdownMenu.Content>
  </DropdownMenu.Root>
</div>
