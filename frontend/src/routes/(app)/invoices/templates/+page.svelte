<script>
  import { page } from '$app/stores';
  import { goto, invalidateAll } from '$app/navigation';
  import { enhance } from '$app/forms';
  import { tick } from 'svelte';
  import { toast } from 'svelte-sonner';

  import { PageHeader } from '$lib/components/layout';
  import { CrmDrawer } from '$lib/components/ui/crm-drawer';
  import { CrmTable } from '$lib/components/ui/crm-table';
  import { FilterBar, SearchInput } from '$lib/components/ui/filter';
  import { Pagination } from '$lib/components/ui/pagination';
  import { Button } from '$lib/components/ui/button';

  /** @type {{ data: import('./$types').PageData }} */
  let { data } = $props();

  /**
   * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
   * @typedef {{ key: string, label: string, type?: ColumnType, width?: string, editable?: boolean, canHide?: boolean, getValue?: (row: any) => any, emptyText?: string, relationIcon?: string, options?: Array<{value: string, label: string, color: string}> }} ColumnDef
   */

  /** @type {ColumnDef[]} */
  const columns = [
    {
      key: 'name',
      label: 'Name',
      type: 'text',
      width: 'w-48',
      editable: false,
      canHide: false
    },
    {
      key: 'primaryColor',
      label: 'Primary Color',
      type: 'text',
      width: 'w-32',
      canHide: true,
      getValue: (row) => row.primaryColor
    },
    {
      key: 'isDefault',
      label: 'Default',
      type: 'checkbox',
      width: 'w-24',
      canHide: true,
      getValue: (row) => row.isDefault
    },
    {
      key: 'footerText',
      label: 'Footer',
      type: 'text',
      width: 'w-48',
      canHide: true,
      getValue: (row) => row.footerText
    }
  ];

  // Drawer field definitions
  const drawerFields = [
    { key: 'name', label: 'Name', type: 'text', section: 'core', required: true },
    { key: 'primaryColor', label: 'Primary Color', type: 'color', section: 'branding' },
    { key: 'secondaryColor', label: 'Secondary Color', type: 'color', section: 'branding' },
    { key: 'defaultNotes', label: 'Default Notes', type: 'textarea', section: 'defaults' },
    { key: 'defaultTerms', label: 'Default Terms', type: 'textarea', section: 'defaults' },
    { key: 'footerText', label: 'Footer Text', type: 'text', section: 'defaults' },
    { key: 'isDefault', label: 'Set as Default', type: 'boolean', section: 'settings' }
  ];

  // Default visible columns
  const DEFAULT_VISIBLE_COLUMNS = ['name', 'primaryColor', 'isDefault', 'footerText'];

  // State
  let filtersExpanded = $state(false);
  let visibleColumns = $state([...DEFAULT_VISIBLE_COLUMNS]);

  // Drawer state
  let drawerOpen = $state(false);
  /** @type {'view' | 'create'} */
  let drawerMode = $state('view');
  let selectedTemplate = $state(null);
  /** @type {Record<string, any>} */
  let drawerFormData = $state({});

  // Form references
  let createForm;
  let updateForm;
  let deleteForm;

  // Form state for hidden forms
  let formState = $state({
    templateId: '',
    name: '',
    primaryColor: '#3B82F6',
    secondaryColor: '#1E40AF',
    defaultNotes: '',
    defaultTerms: '',
    footerText: '',
    isDefault: 'false'
  });

  // Derived values
  const filters = $derived(data.filters);
  const pagination = $derived(data.pagination);
  const templates = $derived(data.templates);

  // Count active filters
  const activeFiltersCount = $derived(() => {
    let count = 0;
    if (filters.search) count++;
    return count;
  });

  // Filter handlers
  async function updateFilters(newFilters) {
    const url = new URL($page.url);

    // Clear existing filter params
    ['search'].forEach((key) => url.searchParams.delete(key));

    // Set new params
    Object.entries(newFilters).forEach(([key, value]) => {
      if (value) {
        url.searchParams.set(key, value);
      }
    });

    // Reset to page 1 when filters change
    url.searchParams.set('page', '1');

    await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
  }

  async function clearFilters() {
    await updateFilters({});
  }

  // Pagination handlers
  async function handlePageChange(newPage) {
    const url = new URL($page.url);
    url.searchParams.set('page', newPage.toString());
    await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
  }

  async function handleLimitChange(newLimit) {
    const url = new URL($page.url);
    url.searchParams.set('limit', newLimit.toString());
    url.searchParams.set('page', '1');
    await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
  }

  // Row click handler
  function handleRowClick(template) {
    selectedTemplate = template;
    drawerMode = 'view';
    drawerOpen = true;
  }

  // Create new template
  function openCreateDrawer() {
    selectedTemplate = null;
    drawerMode = 'create';
    drawerFormData = {
      name: '',
      primaryColor: '#3B82F6',
      secondaryColor: '#1E40AF',
      defaultNotes: '',
      defaultTerms: '',
      footerText: '',
      isDefault: false
    };
    drawerOpen = true;
  }

  // Close drawer
  function closeDrawer() {
    drawerOpen = false;
    selectedTemplate = null;
    drawerFormData = {};
  }

  // Sync drawer form data when opening
  $effect(() => {
    if (drawerOpen) {
      if (drawerMode === 'create') {
        // Already set in openCreateDrawer
      } else if (selectedTemplate) {
        drawerFormData = { ...selectedTemplate };
      }
    }
  });

  // Field change handler
  function handleFieldChange(field, value) {
    drawerFormData[field] = value;
  }

  // Save handler
  async function handleDrawerSave() {
    if (drawerMode === 'create') {
      formState.name = drawerFormData.name;
      formState.primaryColor = drawerFormData.primaryColor;
      formState.secondaryColor = drawerFormData.secondaryColor;
      formState.defaultNotes = drawerFormData.defaultNotes;
      formState.defaultTerms = drawerFormData.defaultTerms;
      formState.footerText = drawerFormData.footerText;
      formState.isDefault = drawerFormData.isDefault ? 'true' : 'false';

      await tick();
      createForm.requestSubmit();
    } else {
      formState.templateId = selectedTemplate.id;
      formState.name = drawerFormData.name;
      formState.primaryColor = drawerFormData.primaryColor;
      formState.secondaryColor = drawerFormData.secondaryColor;
      formState.defaultNotes = drawerFormData.defaultNotes;
      formState.defaultTerms = drawerFormData.defaultTerms;
      formState.footerText = drawerFormData.footerText;
      formState.isDefault = drawerFormData.isDefault ? 'true' : 'false';

      await tick();
      updateForm.requestSubmit();
    }
  }

  // Delete handler
  async function handleDelete() {
    if (!selectedTemplate) return;

    if (!confirm('Are you sure you want to delete this template?')) return;

    formState.templateId = selectedTemplate.id;
    await tick();
    deleteForm.requestSubmit();
  }
</script>

<!-- Hidden Forms -->
<form
  bind:this={createForm}
  method="POST"
  action="?/create"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Template created');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to create template');
      }
    };
  }}
>
  <input type="hidden" name="name" value={formState.name} />
  <input type="hidden" name="primaryColor" value={formState.primaryColor} />
  <input type="hidden" name="secondaryColor" value={formState.secondaryColor} />
  <input type="hidden" name="defaultNotes" value={formState.defaultNotes} />
  <input type="hidden" name="defaultTerms" value={formState.defaultTerms} />
  <input type="hidden" name="footerText" value={formState.footerText} />
  <input type="hidden" name="isDefault" value={formState.isDefault} />
</form>

<form
  bind:this={updateForm}
  method="POST"
  action="?/update"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Template updated');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to update template');
      }
    };
  }}
>
  <input type="hidden" name="templateId" value={formState.templateId} />
  <input type="hidden" name="name" value={formState.name} />
  <input type="hidden" name="primaryColor" value={formState.primaryColor} />
  <input type="hidden" name="secondaryColor" value={formState.secondaryColor} />
  <input type="hidden" name="defaultNotes" value={formState.defaultNotes} />
  <input type="hidden" name="defaultTerms" value={formState.defaultTerms} />
  <input type="hidden" name="footerText" value={formState.footerText} />
  <input type="hidden" name="isDefault" value={formState.isDefault} />
</form>

<form
  bind:this={deleteForm}
  method="POST"
  action="?/delete"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Template deleted');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to delete template');
      }
    };
  }}
>
  <input type="hidden" name="templateId" value={formState.templateId} />
</form>

<!-- Page Content -->
<div class="flex flex-col gap-4 p-6">
  <!-- Header -->
  <PageHeader title="Invoice Templates">
    {#snippet actions()}
      <!-- Back to Invoices -->
      <Button variant="ghost" size="sm" onclick={() => goto('/invoices')}>
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
          class="mr-2"
        >
          <path d="M19 12H5M12 19l-7-7 7-7" />
        </svg>
        Invoices
      </Button>

      <!-- Filters Toggle -->
      <Button
        variant="outline"
        size="sm"
        onclick={() => (filtersExpanded = !filtersExpanded)}
        class="gap-2"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
        </svg>
        Filters
        {#if activeFiltersCount() > 0}
          <span class="rounded-full bg-[var(--color-primary-light)] px-2 py-0.5 text-xs text-[var(--color-primary-default)]">
            {activeFiltersCount()}
          </span>
        {/if}
      </Button>

      <!-- New Template -->
      <Button onclick={openCreateDrawer} class="gap-2">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          stroke-linecap="round"
          stroke-linejoin="round"
        >
          <line x1="12" y1="5" x2="12" y2="19" />
          <line x1="5" y1="12" x2="19" y2="12" />
        </svg>
        New Template
      </Button>
    {/snippet}
  </PageHeader>

  <!-- Filter Bar -->
  <FilterBar
    minimal
    expanded={filtersExpanded}
    activeCount={activeFiltersCount()}
    onClear={clearFilters}
  >
    <SearchInput
      value={filters.search}
      placeholder="Search templates..."
      onchange={(value) => updateFilters({ ...filters, search: value })}
    />
  </FilterBar>

  <!-- Templates Table -->
  <CrmTable data={templates} {columns} bind:visibleColumns onRowClick={handleRowClick}>
    {#snippet emptyState()}
      <div class="flex flex-col items-center justify-center py-16 text-center">
        <div class="mb-4 flex size-16 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--surface-sunken)]">
          <span class="text-4xl">🎨</span>
        </div>
        <h3 class="text-[var(--text-primary)] text-lg font-medium">No templates yet</h3>
        <p class="text-[var(--text-secondary)] text-sm">Create your first invoice template</p>
      </div>
    {/snippet}
    {#snippet cellContent(row, column)}
      {#if column.key === 'isDefault'}
        {#if row.isDefault}
          <span
            class="inline-flex items-center rounded-full bg-[var(--color-primary-light)] px-2 py-0.5 text-xs font-medium text-[var(--color-primary-default)]"
          >
            Default
          </span>
        {:else}
          <span class="text-[var(--text-tertiary)]">-</span>
        {/if}
      {:else if column.key === 'primaryColor'}
        <div class="flex items-center gap-2">
          <div class="h-5 w-5 rounded border border-[var(--border-default)]" style="background-color: {row.primaryColor}"></div>
          <span class="text-xs text-[var(--text-secondary)]">{row.primaryColor}</span>
        </div>
      {:else}
        {row[column.key] || '-'}
      {/if}
    {/snippet}
  </CrmTable>

  <!-- Pagination -->
  <Pagination
    page={pagination.page}
    limit={pagination.limit}
    total={pagination.total}
    limitOptions={[10, 25, 50, 100]}
    onPageChange={handlePageChange}
    onLimitChange={handleLimitChange}
  />
</div>

<!-- Template Drawer -->
<CrmDrawer
  bind:open={drawerOpen}
  data={drawerFormData}
  columns={drawerFields}
  titleKey="name"
  titlePlaceholder="New Template"
  headerLabel="Invoice Template"
  mode={drawerMode}
  onFieldChange={handleFieldChange}
  onDelete={handleDelete}
  onClose={closeDrawer}
>
  {#snippet footerActions()}
    <div class="flex w-full items-center justify-end gap-2">
      <Button variant="outline" onclick={closeDrawer}>Cancel</Button>
      <Button onclick={handleDrawerSave}>
        {drawerMode === 'create' ? 'Create Template' : 'Save Changes'}
      </Button>
    </div>
  {/snippet}

  {#snippet activitySection()}
    {#if selectedTemplate}
      <div class="border-t pt-4">
        <h4 class="text-muted-foreground mb-3 text-sm font-medium">Preview</h4>
        <div
          class="rounded-lg border p-4"
          style="background: linear-gradient(135deg, {selectedTemplate.primaryColor}22, {selectedTemplate.secondaryColor}22);"
        >
          <div class="mb-3 flex items-center gap-3">
            <div
              class="h-8 w-8 rounded"
              style="background-color: {selectedTemplate.primaryColor}"
            ></div>
            <div
              class="h-8 w-8 rounded"
              style="background-color: {selectedTemplate.secondaryColor}"
            ></div>
          </div>
          {#if selectedTemplate.footerText}
            <p class="text-xs text-[var(--text-secondary)] italic">{selectedTemplate.footerText}</p>
          {/if}
        </div>
      </div>
    {/if}
  {/snippet}
</CrmDrawer>
