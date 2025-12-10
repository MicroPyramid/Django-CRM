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
    class={cn('w-[480px] overflow-hidden border-l border-border/50 bg-background/95 p-0 backdrop-blur-xl sm:max-w-[480px]', className)}
  >
    {#if loading}
      <!-- Loading skeleton with premium styling -->
      <div class="flex h-full flex-col">
        <!-- Header skeleton -->
        <div class="relative border-b border-border/40 px-6 py-4">
          <div class="flex items-center justify-between">
            <Skeleton class="h-4 w-16 rounded-md" />
            <Skeleton class="h-8 w-8 rounded-lg" />
          </div>
        </div>

        <!-- Content skeleton -->
        <div class="flex-1 overflow-y-auto">
          <div class="px-6 pt-8 pb-6">
            <Skeleton class="h-9 w-64 rounded-lg" />
          </div>
          <div class="space-y-2 px-6 pb-8">
            {#each { length: 6 } as _}
              <div class="flex items-center gap-4 rounded-lg bg-muted/20 px-3 py-3">
                <Skeleton class="h-6 w-6 rounded-md" />
                <Skeleton class="h-4 w-24" />
                <Skeleton class="ml-auto h-5 w-32 rounded-md" />
              </div>
            {/each}
          </div>
        </div>
      </div>
    {:else}
      <div class="flex h-full flex-col">
        <!-- Premium Header -->
        <div class="relative border-b border-border/40 bg-gradient-to-b from-muted/30 to-transparent">
          <!-- Ambient glow -->
          <div class="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
            <div class="absolute -top-12 left-1/4 h-24 w-48 rounded-full bg-primary/5 blur-2xl"></div>
          </div>

          <div class="relative flex items-center justify-between px-6 py-4">
            <div class="flex items-center gap-2">
              <span class="rounded-md bg-primary/10 px-2 py-1 text-xs font-semibold uppercase tracking-wider text-primary">
                {headerLabel}
              </span>
              {#if mode === 'create'}
                <span class="text-xs text-muted-foreground">New</span>
              {/if}
            </div>
            <button
              onclick={closeDrawer}
              class="flex h-8 w-8 items-center justify-center rounded-lg text-muted-foreground transition-all duration-150 hover:bg-muted/60 hover:text-foreground"
            >
              <X class="h-4 w-4" />
            </button>
          </div>
        </div>

        <!-- Scrollable content -->
        <div class="flex-1 overflow-x-hidden overflow-y-auto">
          <!-- Title section with elegant styling -->
          <div class="px-6 pt-8 pb-6">
            {#if titleEditable}
              <input
                type="text"
                value={titleValue}
                oninput={handleTitleChange}
                placeholder={titlePlaceholder}
                class="w-full border-0 bg-transparent text-2xl font-bold tracking-tight text-foreground outline-none placeholder:text-muted-foreground/30"
                style="letter-spacing: -0.025em;"
              />
            {:else}
              <h2
                class="text-2xl font-bold tracking-tight text-foreground"
                style="letter-spacing: -0.025em;"
              >
                {titleValue || titlePlaceholder}
              </h2>
            {/if}
          </div>

          <!-- Properties section with refined spacing -->
          <div class="px-6 pb-8">
            {#if enableProgressiveDisclosure && essentialColumns.length > 0}
              <!-- Essential fields section -->
              <div class="space-y-1">
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
              </div>

              <!-- Progressive disclosure toggle with refined styling -->
              {#if hiddenFieldsCount > 0 || showAllFields}
                <button
                  type="button"
                  onclick={toggleShowAllFields}
                  class="group -mx-3 my-4 flex w-full items-center gap-2.5 rounded-lg px-3 py-2.5 text-[13px] font-medium text-muted-foreground transition-all duration-150 hover:bg-muted/40 hover:text-foreground"
                >
                  <div class="flex h-6 w-6 items-center justify-center rounded-md bg-muted/50 transition-colors group-hover:bg-muted">
                    {#if showAllFields}
                      <ChevronUp class="h-3.5 w-3.5" />
                    {:else}
                      <ChevronDown class="h-3.5 w-3.5" />
                    {/if}
                  </div>
                  {#if showAllFields}
                    <span>Hide additional fields</span>
                  {:else}
                    <span>Show {hiddenFieldsCount} more {hiddenFieldsCount === 1 ? 'field' : 'fields'}</span>
                  {/if}
                </button>
              {/if}

              <!-- Additional fields -->
              {#if visibleAdditionalColumns.length > 0}
                <div class="space-y-1">
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
                </div>
              {/if}
            {:else}
              <!-- Original behavior: show all fields when no essential fields defined -->
              <div class="space-y-1">
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
              </div>
            {/if}
          </div>

          <!-- Activity section with refined styling -->
          {#if activitySection}
            <div class="mx-6 h-px bg-gradient-to-r from-transparent via-border to-transparent"></div>
            <div class="px-6 py-6">
              {@render activitySection()}
            </div>
          {/if}
        </div>

        <!-- Premium Footer -->
        <div class="relative mt-auto border-t border-border/40 bg-gradient-to-t from-muted/20 to-transparent">
          <div class="flex items-center justify-between px-6 py-4">
            <!-- Delete button -->
            {#if onDelete && mode !== 'create'}
              <button
                onclick={handleDelete}
                class="group flex items-center gap-2 rounded-lg px-3 py-2 text-sm font-medium text-destructive transition-all duration-150 hover:bg-destructive/10"
              >
                <Trash2 class="h-4 w-4 transition-transform group-hover:scale-110" />
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
