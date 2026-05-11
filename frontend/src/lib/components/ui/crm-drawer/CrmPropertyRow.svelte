<script>
  import { Check, Calendar as CalendarIcon } from '@lucide/svelte';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
  import * as Popover from '$lib/components/ui/popover/index.js';
  import { Calendar } from '$lib/components/ui/calendar/index.js';
  import { EditableMultiSelect } from '$lib/components/ui/editable-field/index.js';
  import { cn } from '$lib/utils.js';
  import { formatCurrency } from '$lib/utils/formatting.js';
  import { parseDate, getLocalTimeZone } from '@internationalized/date';

  /**
   * @type {{
   *   label: string,
   *   value?: any,
   *   type?: 'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'boolean' | 'multiselect' | 'textarea' | 'color' | 'readonly',
   *   icon?: import('svelte').Component,
   *   options?: any[],
   *   placeholder?: string,
   *   emptyText?: string,
   *   editable?: boolean,
   *   required?: boolean,
   *   error?: string,
   *   id?: string,
   *   prefix?: string,
   *   loading?: boolean,
   *   loadingError?: string,
   *   onRetry?: () => void,
   *   onchange?: (value: any) => void,
   *   class?: string,
   * }}
   */
  let {
    label,
    value = '',
    type = 'text',
    icon: Icon,
    options = [],
    placeholder = '',
    emptyText = '',
    editable = true,
    required = false,
    error = '',
    id = '',
    prefix = '',
    loading = false,
    loadingError = '',
    onRetry,
    onchange,
    class: className
  } = $props();

  // Stable id for ARIA wiring; falls back to a slug of the label
  const inputId = $derived(
    id || `prop-${label.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '')}`
  );
  const labelId = $derived(`${inputId}-label`);
  const errorId = $derived(`${inputId}-error`);

  // Plain-text rendering for read-only text-like fields
  const isPlainReadonly = $derived(
    !editable && (type === 'text' || type === 'email' || type === 'number' || type === 'textarea')
  );

  // Read-only date renders as plain formatted text instead of a disabled-looking button
  const isReadonlyDate = $derived(!editable && type === 'date');

  // Read-only select renders the colored badge as a static span (no dropdown chrome)
  const isReadonlySelect = $derived(!editable && type === 'select');

  /**
   * Get option style for select
   * @param {string} val
   */
  function getOptionStyle(val) {
    if (type !== 'select') return '';
    const opt = options.find((/** @type {any} */ o) => o.value === val);
    return opt?.color || 'bg-gray-100 text-gray-700';
  }

  /**
   * Get option label for select
   * @param {string} val
   */
  function getOptionLabel(val) {
    if (type !== 'select') return val;
    const opt = options.find((/** @type {any} */ o) => o.value === val);
    return opt?.label || val || emptyText || 'Select...';
  }

  /**
   * Get option background color class (for the dot)
   * @param {string} val
   */
  function getOptionBgColor(val) {
    if (type !== 'select') return '';
    const opt = options.find((/** @type {any} */ o) => o.value === val);
    if (!opt?.color) return 'bg-gray-400';
    // Extract bg class from color string (e.g., "bg-emerald-100 text-emerald-700" -> "bg-emerald-500")
    const match = opt.color.match(/bg-(\w+)-\d+/);
    if (match) {
      return `bg-${match[1]}-500`;
    }
    return 'bg-gray-400';
  }

  /**
   * Parse string date to DateValue
   * @param {string} dateStr
   */
  function parseDateValue(dateStr) {
    if (!dateStr) return undefined;
    try {
      return parseDate(dateStr);
    } catch {
      return undefined;
    }
  }

  /**
   * Format date for display. Accepts a YYYY-MM-DD string or an ISO datetime.
   * @param {string} dateStr
   */
  function formatDateDisplay(dateStr) {
    if (!dateStr) return placeholder || 'Pick a date';
    try {
      // If we got just YYYY-MM-DD, pin it to local midnight; otherwise let Date parse the ISO string.
      const isoLike = /T|\s/.test(dateStr) ? dateStr : `${dateStr}T00:00:00`;
      const date = new Date(isoLike);
      if (Number.isNaN(date.getTime())) return dateStr;
      return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  }

  /**
   * Handle calendar date change
   * @param {import('@internationalized/date').DateValue | undefined} dateValue
   */
  function handleCalendarChange(dateValue) {
    if (dateValue) {
      onchange?.(dateValue.toString());
      datePopoverOpen = false;
    }
  }

  // State for date popover
  let datePopoverOpen = $state(false);

  /**
   * Format number with optional currency
   * @param {number | string} val
   */
  function formatNumber(val) {
    const num = typeof val === 'string' ? parseFloat(val) : val;
    if (isNaN(num)) return emptyText || '0';
    if (prefix === '$') {
      return formatCurrency(num);
    }
    return prefix + num.toLocaleString();
  }

  /**
   * Handle text input
   * @param {Event} e
   */
  function handleInput(e) {
    const target = /** @type {HTMLInputElement} */ (e.target);
    onchange?.(target.value);
  }

  /**
   * Handle number input
   * @param {Event} e
   */
  function handleNumberInput(e) {
    const target = /** @type {HTMLInputElement} */ (e.target);
    onchange?.(parseFloat(target.value) || 0);
  }

  /**
   * Handle checkbox toggle
   */
  function handleCheckboxToggle() {
    onchange?.(!value);
  }

  /**
   * Handle color input
   * @param {Event} e
   */
  function handleColorInput(e) {
    const target = /** @type {HTMLInputElement} */ (e.target);
    onchange?.(target.value);
  }

  /**
   * Handle select change
   * @param {string} newValue
   */
  function handleSelectChange(newValue) {
    onchange?.(newValue);
  }

  /**
   * Handle multiselect change
   * @param {string[]} newValue
   */
  function handleMultiSelectChange(newValue) {
    onchange?.(newValue);
  }
</script>

<div class="flex flex-col">
  <div
    class={cn(
      'group hover:bg-muted/40 -mx-3 flex min-h-[44px] items-center rounded-lg px-3 transition-all duration-150',
      className
    )}
  >
    <!-- Label with icon — uses <label for> so clicking focuses the input -->
    <label
      for={inputId}
      id={labelId}
      class="text-muted-foreground flex w-32 shrink-0 items-center gap-2.5 text-[13px] font-medium"
    >
      {#if Icon}
        <div class="bg-muted/50 flex h-6 w-6 items-center justify-center rounded-md">
          <Icon class="text-muted-foreground/70 h-3.5 w-3.5" aria-hidden="true" />
        </div>
      {/if}
      <span>
        {label}
        {#if required}
          <span class="text-destructive ml-0.5" aria-hidden="true">*</span>
        {/if}
      </span>
    </label>

    <!-- Value -->
    <div class="min-w-0 flex-1">
      {#if isPlainReadonly}
        <span
          class={cn(
            'block px-2.5 py-1.5 text-sm',
            type === 'textarea' && 'whitespace-pre-wrap'
          )}
          aria-labelledby={labelId}
        >
          {#if value !== null && value !== undefined && value !== ''}
            <span class="text-foreground font-medium">
              {type === 'number' ? formatNumber(value) : value}
            </span>
          {:else}
            <span class="text-muted-foreground/40 italic">{emptyText || '—'}</span>
          {/if}
        </span>
      {:else if type === 'text' || type === 'email'}
        <input
          id={inputId}
          {type}
          {value}
          oninput={handleInput}
          {placeholder}
          disabled={!editable}
          aria-labelledby={labelId}
          aria-required={required ? 'true' : undefined}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? errorId : undefined}
          class="text-foreground placeholder:text-muted-foreground/40 focus:bg-muted/30 focus:ring-primary/20 w-full rounded-lg border-0 bg-transparent px-2.5 py-1.5 text-sm font-medium transition-all outline-none focus:ring-1 aria-[invalid=true]:ring-1 aria-[invalid=true]:ring-destructive/40"
        />
      {:else if type === 'number'}
        <div class="flex items-center">
          {#if prefix}
            <span class="text-muted-foreground mr-1.5 text-sm font-medium" aria-hidden="true"
              >{prefix}</span
            >
          {/if}
          <input
            id={inputId}
            type="number"
            value={value || 0}
            oninput={handleNumberInput}
            {placeholder}
            disabled={!editable}
            aria-labelledby={labelId}
            aria-required={required ? 'true' : undefined}
            aria-invalid={error ? 'true' : undefined}
            aria-describedby={error ? errorId : undefined}
            class="text-foreground placeholder:text-muted-foreground/40 focus:bg-muted/30 focus:ring-primary/20 w-full rounded-lg border-0 bg-transparent px-2 py-1.5 text-sm font-medium tabular-nums transition-all outline-none focus:ring-1 aria-[invalid=true]:ring-1 aria-[invalid=true]:ring-destructive/40"
          />
        </div>
      {:else if isReadonlyDate}
        <span class="text-foreground block px-2.5 py-1.5 text-sm font-medium" aria-labelledby={labelId}>
          {#if value}
            {formatDateDisplay(value)}
          {:else}
            <span class="text-muted-foreground/40 italic">{emptyText || '—'}</span>
          {/if}
        </span>
      {:else if type === 'date'}
        <Popover.Root bind:open={datePopoverOpen}>
          <Popover.Trigger disabled={!editable} class="w-full">
            {#snippet child({ props })}
              <button
                {...props}
                type="button"
                id={inputId}
                aria-labelledby={labelId}
                aria-describedby={error ? errorId : undefined}
                class={cn(
                  'hover:bg-muted/30 inline-flex w-full items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-sm font-medium transition-all',
                  !value ? 'text-muted-foreground/50' : 'text-foreground',
                  !editable && 'cursor-default hover:bg-transparent',
                  error && 'ring-1 ring-destructive/40'
                )}
              >
                <CalendarIcon class="text-muted-foreground/60 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                {formatDateDisplay(value)}
              </button>
            {/snippet}
          </Popover.Trigger>
          <Popover.Content class="w-auto p-0" align="start">
            <Calendar value={parseDateValue(value)} onValueChange={handleCalendarChange} />
          </Popover.Content>
        </Popover.Root>
      {:else if type === 'textarea'}
        <textarea
          id={inputId}
          oninput={handleInput}
          {placeholder}
          disabled={!editable}
          rows={3}
          aria-labelledby={labelId}
          aria-required={required ? 'true' : undefined}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? errorId : undefined}
          class="text-foreground placeholder:text-muted-foreground/40 focus:bg-muted/30 focus:ring-primary/20 w-full resize-none rounded-lg border-0 bg-transparent px-2.5 py-1.5 text-sm transition-all outline-none focus:ring-1 aria-[invalid=true]:ring-1 aria-[invalid=true]:ring-destructive/40"
          >{value || ''}</textarea
        >
      {:else if isReadonlySelect}
        <span
          aria-labelledby={labelId}
          class="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold ring-1 ring-inset ring-black/5 dark:ring-white/10 {getOptionStyle(
            value
          )}"
        >
          <span
            aria-hidden="true"
            class="h-2 w-2 rounded-full ring-1 ring-inset ring-black/10 dark:ring-white/20 {getOptionBgColor(
              value
            )}"
          ></span>
          {getOptionLabel(value)}
        </span>
      {:else if type === 'select'}
        <DropdownMenu.Root>
          <DropdownMenu.Trigger disabled={!editable}>
            {#snippet child({ props })}
              <button
                {...props}
                type="button"
                id={inputId}
                aria-labelledby={labelId}
                aria-describedby={error ? errorId : undefined}
                class={cn(
                  'inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold shadow-sm ring-1 transition-all duration-150 ring-inset hover:shadow',
                  error ? 'ring-destructive/40' : 'ring-black/5 dark:ring-white/10',
                  getOptionStyle(value)
                )}
              >
                <span
                  aria-hidden="true"
                  class="h-2 w-2 rounded-full ring-1 ring-black/10 ring-inset dark:ring-white/20 {getOptionBgColor(
                    value
                  )}"
                ></span>
                {getOptionLabel(value)}
              </button>
            {/snippet}
          </DropdownMenu.Trigger>
          <DropdownMenu.Content align="start" class="min-w-48 p-1.5">
            {#each options as option (option.value)}
              <DropdownMenu.Item
                onclick={() => handleSelectChange(option.value)}
                class="flex items-center gap-2.5 rounded-lg px-2.5 py-2"
              >
                <span
                  aria-hidden="true"
                  class="h-2.5 w-2.5 rounded-full ring-1 ring-black/10 ring-inset dark:ring-white/20 {option.color?.split(
                    ' '
                  )[0] || 'bg-gray-400'}"
                ></span>
                <span class="font-medium">{option.label}</span>
                {#if value === option.value}
                  <Check class="text-primary ml-auto h-4 w-4" aria-hidden="true" />
                {/if}
              </DropdownMenu.Item>
            {/each}
          </DropdownMenu.Content>
        </DropdownMenu.Root>
      {:else if type === 'checkbox' || type === 'boolean'}
        <button
          type="button"
          id={inputId}
          role="checkbox"
          aria-checked={value ? 'true' : 'false'}
          aria-labelledby={labelId}
          aria-required={required ? 'true' : undefined}
          aria-invalid={error ? 'true' : undefined}
          aria-describedby={error ? errorId : undefined}
          onclick={handleCheckboxToggle}
          disabled={!editable}
          class="flex h-5 w-5 items-center justify-center rounded-md border-2 transition-all duration-150 {value
            ? 'border-primary bg-primary shadow-primary/25 shadow-sm'
            : 'border-muted-foreground/30 hover:border-muted-foreground/50'}"
        >
          {#if value}
            <Check class="text-primary-foreground h-3.5 w-3.5" aria-hidden="true" />
          {/if}
        </button>
      {:else if type === 'color'}
        <div class="flex items-center gap-3 px-2 py-1">
          <input
            id={inputId}
            type="color"
            value={value || '#3B82F6'}
            oninput={handleColorInput}
            disabled={!editable}
            aria-labelledby={labelId}
            aria-required={required ? 'true' : undefined}
            aria-invalid={error ? 'true' : undefined}
            aria-describedby={error ? errorId : undefined}
            class="border-border/50 h-8 w-10 cursor-pointer rounded-lg border bg-transparent p-0.5 shadow-sm"
          />
          <span class="text-muted-foreground font-mono text-xs">{value || '#3B82F6'}</span>
        </div>
      {:else if type === 'multiselect'}
        <EditableMultiSelect
          value={Array.isArray(value) ? value : []}
          {options}
          {placeholder}
          emptyText={emptyText || 'None selected'}
          disabled={!editable}
          {loading}
          error={loadingError}
          {onRetry}
          onchange={handleMultiSelectChange}
        />
      {:else if type === 'readonly'}
        <span class="text-foreground px-2.5 py-1.5 text-sm font-medium" aria-labelledby={labelId}>
          {#if value}
            {value}
          {:else}
            <span class="text-muted-foreground/40 italic">{emptyText || '—'}</span>
          {/if}
        </span>
      {/if}
    </div>
  </div>

  {#if error}
    <p
      id={errorId}
      class="text-destructive ml-32 px-2.5 pt-0.5 pb-1 text-[11.5px] font-medium"
      role="alert"
    >
      {error}
    </p>
  {/if}
</div>
