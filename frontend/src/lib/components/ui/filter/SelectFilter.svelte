<script>
  import { ChevronDown, Check, X, CircleDot } from '@lucide/svelte';
  import { cn } from '$lib/utils.js';
  import * as Popover from '$lib/components/ui/popover/index.js';

  /**
   * @typedef {{
   *   value: string,
   *   label: string,
   *   icon?: any,
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
            'select-filter-trigger group',
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
            hasValue && 'border-primary/40 bg-primary/[0.03] dark:border-primary/30 dark:bg-primary/[0.08]',
            // Open state
            open && 'ring-2 ring-primary/20 dark:ring-primary/30'
          )}
          {...props}
        >
          <span
            class={cn(
              'truncate transition-colors duration-150',
              hasValue ? 'text-foreground font-medium' : 'text-muted-foreground'
            )}
          >
            {displayText}
          </span>

          <div class="flex shrink-0 items-center gap-1">
            {#if hasValue}
              <!-- Active indicator dot -->
              <div class="h-1.5 w-1.5 rounded-full bg-primary animate-in fade-in zoom-in duration-200"></div>
              <!-- Clear button -->
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
        'select-filter-content',
        'w-[220px] overflow-hidden rounded-xl p-1',
        'border border-border/60 bg-popover/95 backdrop-blur-md',
        'shadow-lg shadow-black/5',
        'dark:border-white/[0.08] dark:bg-popover/90',
        'dark:shadow-[0_8px_32px_-4px_rgba(0,0,0,0.5)]',
        'animate-in fade-in-0 zoom-in-95 duration-150'
      )}
    >
      <!-- All option -->
      {#if !multiple}
        <button
          type="button"
          class={cn(
            'select-option group',
            'relative flex w-full cursor-pointer items-center gap-2.5',
            'rounded-lg px-2.5 py-2 text-sm',
            'transition-all duration-150',
            'outline-none',
            (!value || value === 'ALL')
              ? 'bg-primary/10 text-primary dark:bg-primary/20'
              : 'text-foreground/80 hover:bg-muted/80 hover:text-foreground'
          )}
          onclick={() => handleSelect('ALL')}
        >
          <div
            class={cn(
              'flex h-4 w-4 items-center justify-center rounded-full',
              'border transition-all duration-150',
              (!value || value === 'ALL')
                ? 'border-primary bg-primary text-primary-foreground scale-100'
                : 'border-border bg-transparent scale-90 group-hover:scale-100 group-hover:border-primary/50'
            )}
          >
            {#if !value || value === 'ALL'}
              <Check class="h-2.5 w-2.5" />
            {/if}
          </div>
          <span class="font-medium">{allLabel}</span>
        </button>
        <div class="my-1 h-px bg-border/50 dark:bg-white/[0.06]"></div>
      {/if}

      <!-- Options -->
      <div class="max-h-[240px] overflow-y-auto">
        {#each options as option, i}
          {@const isSelected = multiple
            ? selectedValues.includes(option.value)
            : value === option.value}
          <button
            type="button"
            class={cn(
              'select-option group',
              'relative flex w-full cursor-pointer items-center gap-2.5',
              'rounded-lg px-2.5 py-2 text-sm',
              'transition-all duration-150',
              'outline-none',
              isSelected
                ? 'bg-primary/10 text-primary dark:bg-primary/20'
                : 'text-foreground/80 hover:bg-muted/80 hover:text-foreground',
              'animate-in fade-in-0 slide-in-from-left-1'
            )}
            style="animation-delay: {i * 20}ms"
            onclick={() => handleSelect(option.value)}
          >
            <div
              class={cn(
                'flex h-4 w-4 shrink-0 items-center justify-center rounded-full',
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
            <span class={cn('truncate', isSelected && 'font-medium')}>
              {option.label}
            </span>
          </button>
        {/each}
      </div>
    </Popover.Content>
  </Popover.Root>
</div>

<!-- Multi-select badges (outside dropdown) -->
{#if multiple && selectedValues.length > 0}
  <div class="mt-2 flex flex-wrap gap-1.5">
    {#each selectedValues as val, i}
      {@const opt = options.find((o) => o.value === val)}
      <span
        class={cn(
          'inline-flex items-center gap-1 rounded-full',
          'bg-primary/10 px-2.5 py-1 text-xs font-medium text-primary',
          'dark:bg-primary/20',
          'animate-in fade-in zoom-in duration-200'
        )}
        style="animation-delay: {i * 50}ms"
      >
        {opt?.label || val}
        <button
          type="button"
          onclick={() => handleSelect(val)}
          class={cn(
            'flex h-4 w-4 items-center justify-center rounded-full',
            'transition-all duration-150',
            'hover:bg-primary/20 dark:hover:bg-primary/30',
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
  .select-filter-trigger {
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03);
  }

  :global(.dark) .select-filter-trigger {
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
  }

  .select-filter-trigger:focus {
    box-shadow:
      inset 0 1px 2px rgba(0, 0, 0, 0.02),
      0 0 0 3px var(--ring);
  }

  :global(.dark) .select-filter-trigger:focus {
    box-shadow:
      inset 0 1px 2px rgba(0, 0, 0, 0.1),
      0 0 0 3px var(--ring),
      0 0 20px -4px var(--primary);
  }

  .select-option {
    position: relative;
  }

  .select-option::before {
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

  :global(.dark) .select-option:hover::before {
    opacity: 0.03;
  }
</style>
