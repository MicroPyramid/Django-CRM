<script>
  import { tick } from 'svelte';
  import { Check, ChevronDown, Expand, Building2, User } from '@lucide/svelte';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
  import { expandButtonClasses } from '$lib/utils/drag-drop.js';
  import { getOptionStyle, getOptionLabel, getOptionBgColor } from '$lib/utils/table-helpers.js';
  import { formatCurrency } from '$lib/utils/formatting.js';

  /**
   * @typedef {Object} ColumnDef
   * @property {string} key - Field key in data object
   * @property {string} label - Display label for column header
   * @property {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} [type='text']
   * @property {string} [width] - Tailwind width class
   * @property {{ value: string, label: string, color: string }[]} [options] - Options for select type
   * @property {boolean} [editable=true] - Allow inline editing
   * @property {boolean} [canHide=true] - Allow hiding column
   * @property {string} [emptyText='Empty'] - Text when value is empty
   * @property {(value: any, row?: any) => string} [format] - Custom value formatter (receives value and optional row data)
   * @property {(row: any) => any} [getValue] - Custom value getter for nested data
   * @property {string} [relationIcon] - Icon type for relation cells ('building' | 'user')
   */

  /**
   * @type {{
   *   data: any[],
   *   columns: ColumnDef[],
   *   visibleColumns?: string[],
   *   onRowChange?: (row: any, field: string, value: any) => void,
   *   onRowClick?: (row: any) => void,
   *   emptyState?: import('svelte').Snippet,
   *   cellContent?: import('svelte').Snippet<[any, ColumnDef]>
   * }}
   */
  let {
    data = [],
    columns = [],
    visibleColumns = $bindable(/** @type {string[]} */ ([])),
    onRowChange,
    onRowClick,
    emptyState,
    cellContent
  } = $props();

  // Initialize visibleColumns from columns if not provided
  $effect(() => {
    if (visibleColumns.length === 0 && columns.length > 0) {
      visibleColumns = columns.map((c) => c.key);
    }
  });

  // Editing state
  /** @type {{ rowId: string, columnKey: string } | null} */
  let editingCell = $state(null);
  let editValue = $state('');

  /**
   * Get value from row, using custom getter if provided
   * @param {any} row
   * @param {ColumnDef} column
   */
  function getCellValue(row, column) {
    if (column.getValue) {
      return column.getValue(row);
    }
    return row[column.key];
  }

  /**
   * Format value for display
   * @param {any} value
   * @param {ColumnDef} column
   * @param {any} [row] - The full row data (for format functions that need row context)
   */
  function formatValue(value, column, row) {
    if (value == null || value === '') return null;
    if (column.format) return column.format(value, row);
    if (column.type === 'number') return formatCurrency(value);
    if (column.type === 'date') return formatDate(value);
    return value;
  }

  /**
   * @param {string} dateStr
   */
  function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  /**
   * Start editing a cell
   * @param {string} rowId
   * @param {string} columnKey
   */
  async function startEditing(rowId, columnKey) {
    const row = data.find((r) => r.id === rowId);
    const column = columns.find((c) => c.key === columnKey);

    if (!row || !column) return;
    if (column.editable === false) return;
    // Non-editable types
    if (column.type === 'checkbox' || column.type === 'relation' || column.type === 'select')
      return;

    editingCell = { rowId, columnKey };
    const value = getCellValue(row, column);
    editValue = value?.toString() ?? '';

    await tick();

    const input = document.querySelector(`[data-edit-input="${rowId}-${columnKey}"]`);
    if (input) {
      // @ts-ignore
      input.focus();
      // @ts-ignore
      if (input.select) input.select();
    }
  }

  /**
   * Stop editing and optionally save
   * @param {boolean} save
   */
  function stopEditing(save = true) {
    if (!editingCell) return;

    if (save && onRowChange) {
      const { rowId, columnKey } = editingCell;
      const column = columns.find((c) => c.key === columnKey);
      const row = data.find((r) => r.id === rowId);

      if (row && column) {
        /** @type {string | number} */
        let parsedValue = editValue;
        if (column.type === 'number') {
          parsedValue = parseFloat(editValue) || 0;
        }

        const original = getCellValue(row, column);
        if (parsedValue !== original) {
          onRowChange(row, columnKey, parsedValue);
        }
      }
    }

    editingCell = null;
    editValue = '';
  }

  /**
   * @param {KeyboardEvent} e
   */
  function handleKeydown(e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      stopEditing(true);
    } else if (e.key === 'Escape') {
      e.preventDefault();
      stopEditing(false);
    }
  }

  /**
   * Update select value
   * @param {string} rowId
   * @param {string} columnKey
   * @param {string} value
   */
  function updateSelectValue(rowId, columnKey, value) {
    const row = data.find((r) => r.id === rowId);
    if (row && onRowChange) {
      onRowChange(row, columnKey, value);
    }
  }

  /**
   * Toggle checkbox value
   * @param {string} rowId
   * @param {string} columnKey
   */
  function toggleCheckbox(rowId, columnKey) {
    const row = data.find((r) => r.id === rowId);
    const column = columns.find((c) => c.key === columnKey);
    if (row && column && onRowChange) {
      const currentValue = getCellValue(row, column);
      onRowChange(row, columnKey, !currentValue);
    }
  }

  // Derived values
  const visibleColumnDefs = $derived(columns.filter((col) => visibleColumns.includes(col.key)));
</script>

{#snippet tableBody()}
  {#if data.length === 0}
    {#if emptyState}
      {@render emptyState()}
    {:else}
      <div class="flex flex-col items-center justify-center py-16 text-center">
        <p class="text-muted-foreground text-sm">No items found</p>
      </div>
    {/if}
  {:else}
    <table class="w-full border-collapse">
      <thead>
        <tr class="border-b border-gray-100/60 dark:border-gray-800/60">
          {#if onRowClick}
            <th class="w-8 px-1"></th>
          {/if}
          {#each visibleColumnDefs as column, colIndex (column.key)}
            <th
              class="py-3 pr-4 text-left text-[13px] font-normal text-gray-400 dark:text-gray-500 {colIndex ===
              0
                ? 'pl-0'
                : 'pl-4'} {column.width || ''}"
            >
              {column.label}
            </th>
          {/each}
        </tr>
      </thead>
      <tbody>
        {#each data as row (row.id)}
          <tr
            class="group transition-all duration-100 ease-out hover:bg-gray-50/30 dark:hover:bg-gray-900/30 {onRowClick
              ? 'cursor-pointer'
              : ''}"
            onclick={(e) => {
              if (!onRowClick) return;
              // Don't trigger row click if clicking on interactive elements
              const target = /** @type {HTMLElement} */ (e.target);
              if (
                target.closest('button') ||
                target.closest('input') ||
                target.closest('[data-dropdown-trigger]') ||
                target.closest('[role="menu"]')
              ) {
                return;
              }
              onRowClick(row);
            }}
          >
            {#if onRowClick}
              <td class="w-8 px-1 py-3">
                <button type="button" onclick={() => onRowClick(row)} class={expandButtonClasses}>
                  <Expand class="h-3.5 w-3.5 text-gray-500" />
                </button>
              </td>
            {/if}

            {#each visibleColumnDefs as column, colIndex (column.key)}
              {@const value = getCellValue(row, column)}
              {@const formattedValue = formatValue(value, column, row)}
              <td class="py-3 pr-4 {colIndex === 0 ? 'pl-0' : 'pl-4'} {column.width || ''}">
                {#if cellContent}
                  {@render cellContent(row, column)}
                {:else if column.type === 'text' || column.type === 'email' || column.type === 'number' || !column.type}
                  {#if editingCell?.rowId === row.id && editingCell?.columnKey === column.key && onRowChange}
                    <input
                      type={column.type === 'email'
                        ? 'email'
                        : column.type === 'number'
                          ? 'number'
                          : 'text'}
                      bind:value={editValue}
                      onkeydown={handleKeydown}
                      onblur={() => stopEditing(true)}
                      data-edit-input="{row.id}-{column.key}"
                      class="w-full rounded bg-white px-2 py-1.5 text-sm shadow-sm ring-1 ring-gray-200 transition-shadow duration-100 outline-none focus:ring-blue-300 dark:bg-gray-900 dark:ring-gray-700"
                    />
                  {:else if onRowChange && column.editable !== false}
                    <button
                      type="button"
                      onclick={() => startEditing(row.id, column.key)}
                      class="-mx-2 -my-1.5 w-full cursor-text rounded px-2 py-1.5 text-left text-sm text-gray-900 transition-colors duration-75 hover:bg-gray-100/50 dark:text-gray-100 dark:hover:bg-gray-800/50"
                    >
                      {#if formattedValue}
                        {formattedValue}
                      {:else}
                        <span class="text-gray-400">{column.emptyText || 'Empty'}</span>
                      {/if}
                    </button>
                  {:else}
                    <span class="text-sm text-gray-900 dark:text-gray-100">
                      {#if formattedValue}
                        {formattedValue}
                      {:else}
                        <span class="text-gray-400">{column.emptyText || 'Empty'}</span>
                      {/if}
                    </span>
                  {/if}
                {:else if column.type === 'date'}
                  {#if editingCell?.rowId === row.id && editingCell?.columnKey === column.key && onRowChange}
                    <input
                      type="date"
                      bind:value={editValue}
                      onkeydown={handleKeydown}
                      onblur={() => stopEditing(true)}
                      data-edit-input="{row.id}-{column.key}"
                      class="w-full rounded bg-white px-2 py-1.5 text-sm shadow-sm ring-1 ring-gray-200 transition-shadow duration-100 outline-none focus:ring-blue-300 dark:bg-gray-900 dark:ring-gray-700"
                    />
                  {:else if onRowChange && column.editable !== false}
                    <button
                      type="button"
                      onclick={() => startEditing(row.id, column.key)}
                      class="-mx-2 -my-1.5 w-full cursor-text rounded px-2 py-1.5 text-left text-sm text-gray-900 transition-colors duration-75 hover:bg-gray-100/50 dark:text-gray-100 dark:hover:bg-gray-800/50"
                    >
                      {#if formattedValue}
                        {formattedValue}
                      {:else}
                        <span class="text-gray-400">{column.emptyText || 'Empty'}</span>
                      {/if}
                    </button>
                  {:else}
                    <span class="text-sm text-gray-900 dark:text-gray-100">
                      {#if formattedValue}
                        {formattedValue}
                      {:else}
                        <span class="text-gray-400">{column.emptyText || 'Empty'}</span>
                      {/if}
                    </span>
                  {/if}
                {:else if column.type === 'select' && column.options}
                  {#if onRowChange}
                    <DropdownMenu.Root>
                      <DropdownMenu.Trigger>
                        {#snippet child({ props })}
                          <button
                            {...props}
                            type="button"
                            class="inline-flex items-center gap-1 rounded-full px-2.5 py-1 text-xs font-medium transition-opacity hover:opacity-80 {getOptionStyle(
                              value,
                              column.options
                            )}"
                          >
                            {getOptionLabel(value, column.options)}
                            <ChevronDown class="h-3 w-3 opacity-60" />
                          </button>
                        {/snippet}
                      </DropdownMenu.Trigger>
                      <DropdownMenu.Content align="start" class="w-36">
                        {#each column.options as option (option.value)}
                          <DropdownMenu.Item
                            onclick={() => updateSelectValue(row.id, column.key, option.value)}
                            class="flex items-center gap-2"
                          >
                            <span
                              class="h-2 w-2 rounded-full {getOptionBgColor(option.value, [
                                option
                              ])}"
                            ></span>
                            {option.label}
                            {#if value === option.value}
                              <Check class="ml-auto h-4 w-4" />
                            {/if}
                          </DropdownMenu.Item>
                        {/each}
                      </DropdownMenu.Content>
                    </DropdownMenu.Root>
                  {:else}
                    <span
                      class="inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium {getOptionStyle(
                        value,
                        column.options
                      )}"
                    >
                      {getOptionLabel(value, column.options)}
                    </span>
                  {/if}
                {:else if column.type === 'checkbox'}
                  {#if onRowChange}
                    <button
                      type="button"
                      onclick={() => toggleCheckbox(row.id, column.key)}
                      class="flex h-5 w-5 items-center justify-center rounded border transition-colors {value
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300 hover:border-gray-400'}"
                    >
                      {#if value}
                        <Check class="h-3.5 w-3.5 text-white" />
                      {/if}
                    </button>
                  {:else}
                    <span
                      class="flex h-5 w-5 items-center justify-center rounded border {value
                        ? 'border-blue-500 bg-blue-500'
                        : 'border-gray-300'}"
                    >
                      {#if value}
                        <Check class="h-3.5 w-3.5 text-white" />
                      {/if}
                    </span>
                  {/if}
                {:else if column.type === 'relation'}
                  <button
                    type="button"
                    onclick={() => onRowClick?.(row)}
                    class="-mx-2 -my-1.5 w-full cursor-pointer rounded px-2 py-1.5 text-left text-sm text-gray-900 transition-colors duration-75 hover:bg-gray-100/50 dark:text-gray-100 dark:hover:bg-gray-800/50"
                  >
                    {#if value}
                      <div class="flex items-center gap-1.5">
                        {#if column.relationIcon === 'user'}
                          <User class="h-3.5 w-3.5 text-gray-400" />
                        {:else}
                          <Building2 class="h-3.5 w-3.5 text-gray-400" />
                        {/if}
                        <span class="truncate"
                          >{typeof value === 'object' ? value.name || value.email : value}</span
                        >
                      </div>
                    {:else}
                      <span class="text-gray-400">-</span>
                    {/if}
                  </button>
                {/if}
              </td>
            {/each}
          </tr>
        {/each}
      </tbody>
    </table>
  {/if}
{/snippet}

{@render tableBody()}
