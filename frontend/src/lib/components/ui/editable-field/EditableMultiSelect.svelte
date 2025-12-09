<script>
  import { ChevronDown, X } from '@lucide/svelte';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { cn } from '$lib/utils.js';

  /**
   * @typedef {Object} SelectOption
   * @property {string} id
   * @property {string} name
   * @property {string} [email]
   */

  /**
   * @type {{
   *   value?: string[],
   *   options?: SelectOption[],
   *   placeholder?: string,
   *   emptyText?: string,
   *   disabled?: boolean,
   *   onchange?: (value: string[]) => void,
   *   class?: string,
   *   maxDisplay?: number,
   * }}
   */
  let {
    value = [],
    options = [],
    placeholder = 'Select...',
    emptyText = 'None selected',
    disabled = false,
    onchange,
    class: className,
    maxDisplay = 3
  } = $props();

  let isOpen = $state(false);

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
   * Get selected options
   */
  const selectedOptions = $derived(options.filter((opt) => value.includes(opt.id)));

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
                    class="hover:bg-muted rounded-sm p-0.5"
                    onclick={(e) => removeOption(e, opt.id)}
                  >
                    <X class="h-3 w-3" />
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
          class={cn(
            'text-muted-foreground h-4 w-4 shrink-0 transition-transform',
            isOpen && 'rotate-180'
          )}
        />
      </button>
    </DropdownMenu.Trigger>
    <DropdownMenu.Content class="max-h-64 w-64 overflow-y-auto" align="start">
      {#if options.length === 0}
        <div class="text-muted-foreground px-2 py-4 text-center text-sm">No options available</div>
      {:else}
        <DropdownMenu.CheckboxGroup>
          {#each options as opt (opt.id)}
            <DropdownMenu.CheckboxItem
              checked={value.includes(opt.id)}
              onCheckedChange={() => toggleOption(opt.id)}
              class=""
            >
              <div class="flex flex-col">
                <span>{opt.name}</span>
                {#if opt.email}
                  <span class="text-muted-foreground text-xs">{opt.email}</span>
                {/if}
              </div>
            </DropdownMenu.CheckboxItem>
          {/each}
        </DropdownMenu.CheckboxGroup>
      {/if}
    </DropdownMenu.Content>
  </DropdownMenu.Root>
</div>
