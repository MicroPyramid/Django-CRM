<script>
  import { ChevronDown, Check, X } from '@lucide/svelte';
  import { cn } from '$lib/utils.js';
  import * as Popover from '$lib/components/ui/popover/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';

  /**
   * @typedef {{
   *   value: string,
   *   label: string,
   * }} Option
   */

  /**
   * @type {{
   *   options: Option[],
   *   value?: string | string[],
   *   multiple?: boolean,
   *   placeholder?: string,
   *   label?: string,
   *   allLabel?: string,
   *   class?: string,
   *   onchange?: (value: string | string[]) => void,
   * }}
   */
  let {
    options = [],
    value = $bindable(''),
    multiple = false,
    placeholder = 'Select...',
    label = '',
    allLabel = 'All',
    class: className,
    onchange
  } = $props();

  let open = $state(false);

  const selectedValues = $derived(
    multiple ? (Array.isArray(value) ? value : value ? [value] : []) : []
  );

  const displayText = $derived.by(() => {
    if (multiple) {
      if (selectedValues.length === 0) return placeholder;
      if (selectedValues.length === 1) {
        const opt = options.find((o) => o.value === selectedValues[0]);
        return opt?.label || selectedValues[0];
      }
      return `${selectedValues.length} selected`;
    } else {
      if (!value || value === 'ALL') return allLabel;
      const opt = options.find((o) => o.value === value);
      return opt?.label || value;
    }
  });

  /**
   * @param {string} optValue
   */
  function handleSelect(optValue) {
    if (multiple) {
      const newValues = selectedValues.includes(optValue)
        ? selectedValues.filter((v) => v !== optValue)
        : [...selectedValues, optValue];
      value = newValues;
      onchange?.(newValues);
    } else {
      value = optValue;
      onchange?.(optValue);
      open = false;
    }
  }

  function handleClear() {
    if (multiple) {
      value = [];
      onchange?.([]);
    } else {
      value = 'ALL';
      onchange?.('ALL');
    }
  }

  const hasValue = $derived(multiple ? selectedValues.length > 0 : value && value !== 'ALL');
</script>

<div class={cn('flex flex-col gap-1', className)}>
  {#if label}
    <span class="text-muted-foreground text-xs font-medium">{label}</span>
  {/if}
  <Popover.Root bind:open>
    <Popover.Trigger asChild class="">
      {#snippet child({ props })}
        <button
          type="button"
          class={cn(
            'border-input bg-background hover:bg-accent/50 focus-visible:ring-ring flex h-9 w-full items-center justify-between gap-2 rounded-md border px-3 py-2 text-sm shadow-xs transition-colors focus-visible:ring-2 focus-visible:outline-none',
            hasValue && 'border-primary/50'
          )}
          {...props}
        >
          <span class={cn('truncate', !hasValue && 'text-muted-foreground')}>
            {displayText}
          </span>
          <div class="flex items-center gap-1">
            {#if hasValue}
              <!-- svelte-ignore node_invalid_placement_ssr -->
              <span
                role="button"
                tabindex="0"
                onclick={(e) => {
                  e.stopPropagation();
                  e.preventDefault();
                  handleClear();
                }}
                onkeydown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.stopPropagation();
                    e.preventDefault();
                    handleClear();
                  }
                }}
                class="hover:bg-muted cursor-pointer rounded p-0.5"
              >
                <X class="h-3 w-3" />
              </span>
            {/if}
            <ChevronDown class="h-4 w-4 opacity-50" />
          </div>
        </button>
      {/snippet}
    </Popover.Trigger>
    <Popover.Content align="start" class="w-[200px] p-1">
      {#if !multiple}
        <button
          type="button"
          class={cn(
            'hover:bg-accent relative flex w-full cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none',
            (!value || value === 'ALL') && 'bg-accent'
          )}
          onclick={() => handleSelect('ALL')}
        >
          {#if !value || value === 'ALL'}
            <Check class="mr-2 h-4 w-4" />
          {:else}
            <span class="mr-2 w-4"></span>
          {/if}
          {allLabel}
        </button>
      {/if}
      {#each options as option}
        {@const isSelected = multiple
          ? selectedValues.includes(option.value)
          : value === option.value}
        <button
          type="button"
          class={cn(
            'hover:bg-accent relative flex w-full cursor-pointer items-center rounded-sm px-2 py-1.5 text-sm outline-none',
            isSelected && 'bg-accent'
          )}
          onclick={() => handleSelect(option.value)}
        >
          {#if isSelected}
            <Check class="mr-2 h-4 w-4" />
          {:else}
            <span class="mr-2 w-4"></span>
          {/if}
          {option.label}
        </button>
      {/each}
    </Popover.Content>
  </Popover.Root>
</div>

{#if multiple && selectedValues.length > 0}
  <div class="mt-1 flex flex-wrap gap-1">
    {#each selectedValues as val}
      {@const opt = options.find((o) => o.value === val)}
      <Badge variant="secondary" class="gap-1 text-xs">
        {opt?.label || val}
        <button
          type="button"
          onclick={() => handleSelect(val)}
          class="hover:bg-muted ml-1 rounded-full"
        >
          <X class="h-3 w-3" />
        </button>
      </Badge>
    {/each}
  </div>
{/if}
