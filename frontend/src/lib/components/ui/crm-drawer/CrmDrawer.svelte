<script>
  import { X, Trash2, ChevronDown, ChevronUp } from '@lucide/svelte';
  import * as Sheet from '$lib/components/ui/sheet/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Skeleton } from '$lib/components/ui/skeleton/index.js';
  import { Separator } from '$lib/components/ui/separator/index.js';
  import { cn } from '$lib/utils.js';
  import CrmPropertyRow from './CrmPropertyRow.svelte';

  /**
   * @type {{
   *   open?: boolean,
   *   onOpenChange?: (open: boolean) => void,
   *   data?: Record<string, any> | null,
   *   columns?: any[],
   *   titleKey?: string,
   *   titlePlaceholder?: string,
   *   titleEditable?: boolean,
   *   headerLabel?: string,
   *   onFieldChange?: (field: string, value: any) => void,
   *   onDelete?: () => void,
   *   onClose?: () => void,
   *   loading?: boolean,
   *   mode?: 'view' | 'create',
   *   enableProgressiveDisclosure?: boolean,
   *   class?: string,
   *   activitySection?: import('svelte').Snippet,
   *   footerActions?: import('svelte').Snippet,
   * }}
   */
  let {
    open = $bindable(false),
    onOpenChange,
    data = null,
    columns = [],
    titleKey = 'name',
    titlePlaceholder = 'Untitled',
    titleEditable = true,
    headerLabel = 'Item',
    onFieldChange,
    onDelete,
    onClose,
    loading = false,
    mode = 'view',
    enableProgressiveDisclosure = true,
    class: className,
    activitySection,
    footerActions
  } = $props();

  /**
   * Get field value from data
   * @param {any} col
   */
  function getFieldValue(col) {
    if (!data) return '';
    if (col.getValue) {
      return col.getValue(data);
    }
    return data[col.key] ?? '';
  }

  /**
   * Handle field change
   * @param {string} key
   * @param {any} value
   */
  function handleFieldChange(key, value) {
    onFieldChange?.(key, value);
  }

  /**
   * Handle title change
   * @param {Event} e
   */
  function handleTitleChange(e) {
    const target = /** @type {HTMLInputElement} */ (e.target);
    onFieldChange?.(titleKey, target.value);
  }

  /**
   * Close the drawer
   */
  function closeDrawer() {
    open = false;
    onOpenChange?.(false);
    onClose?.();
  }

  /**
   * Handle delete
   */
  function handleDelete() {
    onDelete?.();
  }

  // Get title value
  const titleValue = $derived(data?.[titleKey] || '');

  // Progressive disclosure state
  let showAllFields = $state(false);

  /**
   * Check if a field has a value
   * @param {any} col
   */
  function fieldHasValue(col) {
    if (!data) return false;
    const value = getFieldValue(col);
    if (value === null || value === undefined || value === '') return false;
    if (Array.isArray(value) && value.length === 0) return false;
    return true;
  }

  /**
   * Check if field should be visible based on progressive disclosure rules
   * @param {any} col
   */
  function shouldShowField(col) {
    if (!enableProgressiveDisclosure) return true;
    if (col.essential === true) return true;
    if (mode === 'create') return showAllFields;
    // In view/edit mode, show fields that have values OR if "show all" is toggled
    return fieldHasValue(col) || showAllFields;
  }

  // Filter out columns hidden in create mode
  const availableColumns = $derived(
    mode === 'create' ? columns.filter((col) => !col.hideOnCreate) : columns
  );

  // Split columns into essential and additional
  const essentialColumns = $derived(
    availableColumns.filter((col) => col.key !== titleKey && col.essential === true)
  );

  const additionalColumns = $derived(
    availableColumns.filter((col) => col.key !== titleKey && col.essential !== true)
  );

  // Get visible additional columns based on mode
  const visibleAdditionalColumns = $derived(
    additionalColumns.filter((col) => shouldShowField(col))
  );

  // Count of hidden additional fields
  const hiddenFieldsCount = $derived(
    mode === 'create'
      ? showAllFields
        ? 0
        : additionalColumns.length
      : additionalColumns.filter((col) => !fieldHasValue(col) && !showAllFields).length
  );

  // Toggle show all fields
  function toggleShowAllFields() {
    showAllFields = !showAllFields;
  }

  // Reset show all fields when drawer closes
  $effect(() => {
    if (!open) {
      showAllFields = false;
    }
  });
</script>

<Sheet.Root bind:open onOpenChange={(value) => onOpenChange?.(value)}>
  <Sheet.Content
    side="right"
    class={cn('w-[440px] overflow-hidden p-0 sm:max-w-[440px]', className)}
  >
    {#if loading}
      <!-- Loading skeleton -->
      <div class="flex h-full flex-col">
        <div
          class="flex items-center justify-between border-b border-gray-100 px-4 py-3 dark:border-gray-800"
        >
          <Skeleton class="h-4 w-16" />
          <Skeleton class="h-6 w-6 rounded" />
        </div>
        <div class="flex-1 overflow-y-auto">
          <div class="px-6 pt-6 pb-4">
            <Skeleton class="h-8 w-48" />
          </div>
          <div class="space-y-3 px-4 pb-6">
            {#each { length: 6 } as _}
              <div class="flex items-center gap-2 py-2">
                <Skeleton class="h-4 w-28" />
                <Skeleton class="h-6 w-32" />
              </div>
            {/each}
          </div>
        </div>
      </div>
    {:else}
      <div class="flex h-full flex-col">
        <!-- Header with close button -->
        <div
          class="flex items-center justify-between border-b border-gray-100 px-4 py-3 dark:border-gray-800"
        >
          <span class="text-sm text-gray-500 dark:text-gray-400">{headerLabel}</span>
          <button
            onclick={closeDrawer}
            class="rounded p-1 transition-colors duration-75 hover:bg-gray-100 dark:hover:bg-gray-800"
          >
            <X class="h-4 w-4 text-gray-400" />
          </button>
        </div>

        <!-- Scrollable content -->
        <div class="flex-1 overflow-x-hidden overflow-y-auto">
          <!-- Title section -->
          <div class="px-6 pt-6 pb-4">
            {#if titleEditable}
              <input
                type="text"
                value={titleValue}
                oninput={handleTitleChange}
                placeholder={titlePlaceholder}
                class="w-full border-0 bg-transparent text-2xl font-semibold outline-none placeholder:text-gray-300 focus:ring-0 dark:placeholder:text-gray-600"
              />
            {:else}
              <h2 class="text-2xl font-semibold text-gray-900 dark:text-gray-100">
                {titleValue || titlePlaceholder}
              </h2>
            {/if}
          </div>

          <!-- Properties section -->
          <div class="px-4 pb-6">
            {#if enableProgressiveDisclosure && essentialColumns.length > 0}
              <!-- Essential fields (always shown) -->
              {#each essentialColumns as col (col.key)}
                <CrmPropertyRow
                  label={col.label}
                  value={getFieldValue(col)}
                  type={col.type || 'text'}
                  icon={col.icon}
                  options={col.options}
                  placeholder={col.placeholder}
                  emptyText={col.emptyText}
                  editable={col.editable !== false}
                  prefix={col.prefix}
                  onchange={(value) => handleFieldChange(col.key, value)}
                />
              {/each}

              <!-- Progressive disclosure toggle button -->
              {#if hiddenFieldsCount > 0 || showAllFields}
                <button
                  type="button"
                  onclick={toggleShowAllFields}
                  class="group -mx-2 my-2 flex w-full items-center gap-2 rounded px-2 py-2 text-[13px] text-gray-500 transition-colors duration-75 hover:bg-gray-50/60 hover:text-gray-700 dark:text-gray-400 dark:hover:bg-gray-800/40 dark:hover:text-gray-300"
                >
                  {#if showAllFields}
                    <ChevronUp class="h-4 w-4" />
                    <span>Hide additional fields</span>
                  {:else}
                    <ChevronDown class="h-4 w-4" />
                    <span
                      >Show {hiddenFieldsCount} more {hiddenFieldsCount === 1
                        ? 'field'
                        : 'fields'}</span
                    >
                  {/if}
                </button>
              {/if}

              <!-- Additional fields (conditionally shown) -->
              {#each visibleAdditionalColumns as col (col.key)}
                <CrmPropertyRow
                  label={col.label}
                  value={getFieldValue(col)}
                  type={col.type || 'text'}
                  icon={col.icon}
                  options={col.options}
                  placeholder={col.placeholder}
                  emptyText={col.emptyText}
                  editable={col.editable !== false}
                  prefix={col.prefix}
                  onchange={(value) => handleFieldChange(col.key, value)}
                />
              {/each}
            {:else}
              <!-- Original behavior: show all fields when no essential fields defined -->
              {#each columns as col (col.key)}
                {#if col.key !== titleKey}
                  <CrmPropertyRow
                    label={col.label}
                    value={getFieldValue(col)}
                    type={col.type || 'text'}
                    icon={col.icon}
                    options={col.options}
                    placeholder={col.placeholder}
                    emptyText={col.emptyText}
                    editable={col.editable !== false}
                    prefix={col.prefix}
                    onchange={(value) => handleFieldChange(col.key, value)}
                  />
                {/if}
              {/each}
            {/if}
          </div>

          <!-- Activity section (optional) -->
          {#if activitySection}
            <Separator class="mx-4" />
            <div class="px-4 py-4">
              {@render activitySection()}
            </div>
          {/if}
        </div>

        <!-- Footer -->
        <div class="mt-auto border-t border-gray-100 px-4 py-3 dark:border-gray-800">
          <div class="flex items-center justify-between">
            <!-- Delete button -->
            {#if onDelete && mode !== 'create'}
              <button
                onclick={handleDelete}
                class="flex items-center gap-2 rounded px-3 py-1.5 text-sm text-red-600 transition-colors duration-75 hover:bg-red-50 dark:hover:bg-red-900/20"
              >
                <Trash2 class="h-4 w-4" />
                Delete
              </button>
            {:else}
              <div></div>
            {/if}

            <!-- Custom footer actions -->
            {#if footerActions}
              <div class="flex items-center gap-2">
                {@render footerActions()}
              </div>
            {/if}
          </div>
        </div>
      </div>
    {/if}
  </Sheet.Content>
</Sheet.Root>
