<script>
  import { ChevronDown, Check, X } from '@lucide/svelte';
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
    label: _label = '',
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

<Popover.Root bind:open>
    <Popover.Trigger asChild class="">
      {#snippet child({ props })}
        <button
          type="button"
          {...props}
          class={cn(
            'inline-flex h-7 items-center gap-1.5 rounded-[var(--r-sm)] border px-2.5 text-[13.5px] font-medium leading-none transition-colors focus:outline-none focus:ring-1 focus:ring-[color:var(--ring)]',
            hasValue
              ? 'border-[color:var(--violet)]/40 bg-[color:var(--violet-soft)] text-[color:var(--violet-soft-text)]'
              : 'border-[color:var(--border-faint)] bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)] hover:bg-[color:var(--bg-hover)]',
            className
          )}
        >
          <span class="truncate">{displayText}</span>
          {#if hasValue}
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
      class="w-[220px] overflow-hidden rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-card)] p-1 shadow-lg shadow-black/5"
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
            !value || value === 'ALL'
              ? 'bg-primary/10 text-primary dark:bg-primary/20'
              : 'text-foreground/80 hover:bg-muted/80 hover:text-foreground'
          )}
          onclick={() => handleSelect('ALL')}
        >
          <div
            class={cn(
              'flex h-4 w-4 items-center justify-center rounded-full',
              'border transition-all duration-150',
              !value || value === 'ALL'
                ? 'border-primary bg-primary text-primary-foreground scale-100'
                : 'border-border group-hover:border-primary/50 scale-90 bg-transparent group-hover:scale-100'
            )}
          >
            {#if !value || value === 'ALL'}
              <Check class="h-2.5 w-2.5" />
            {/if}
          </div>
          <span class="font-medium">{allLabel}</span>
        </button>
        <div class="bg-border/50 my-1 h-px dark:bg-white/[0.06]"></div>
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
                  : 'border-border/60 group-hover:border-primary/50 scale-90 bg-transparent group-hover:scale-100'
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
