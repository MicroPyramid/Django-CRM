<script>
  import { page } from '$app/stores';
  import { goto, invalidateAll } from '$app/navigation';
  import { enhance } from '$app/forms';
  import { tick } from 'svelte';
  import { toast } from 'svelte-sonner';

  import { PageHeader } from '$lib/components/layout';
  import { CrmDrawer } from '$lib/components/ui/crm-drawer';
  import { CrmTable } from '$lib/components/ui/crm-table';
  import { FilterBar, SearchInput, SelectFilter } from '$lib/components/ui/filter';
  import { Pagination } from '$lib/components/ui/pagination';
  import { Button } from '$lib/components/ui/button';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
  import { formatCurrency } from '$lib/utils/formatting.js';

  /** @type {{ data: import('./$types').PageData }} */
  let { data } = $props();

  // Status options
  const STATUS_OPTIONS = [
    { value: 'true', label: 'Active' },
    { value: 'false', label: 'Inactive' }
  ];

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
      key: 'sku',
      label: 'SKU',
      type: 'text',
      width: 'w-28',
      canHide: true,
      getValue: (row) => row.sku
    },
    {
      key: 'category',
      label: 'Category',
      type: 'text',
      width: 'w-32',
      canHide: true,
      getValue: (row) => row.category
    },
    {
      key: 'price',
      label: 'Price',
      type: 'number',
      width: 'w-28',
      canHide: false,
      getValue: (row) => formatCurrency(Number(row.price), row.currency)
    },
    {
      key: 'description',
      label: 'Description',
      type: 'text',
      width: 'w-64',
      canHide: true,
      getValue: (row) => row.description
    }
  ];

  // Drawer field definitions
  const drawerFields = [
    { key: 'name', label: 'Name', type: 'text', section: 'core', required: true },
    { key: 'sku', label: 'SKU', type: 'text', section: 'core' },
    { key: 'category', label: 'Category', type: 'text', section: 'core' },
    { key: 'price', label: 'Price', type: 'number', section: 'pricing' },
    { key: 'currency', label: 'Currency', type: 'text', section: 'pricing' },
    { key: 'isActive', label: 'Active', type: 'boolean', section: 'settings' },
    { key: 'description', label: 'Description', type: 'textarea', section: 'details' }
  ];

  // Default visible columns
  const DEFAULT_VISIBLE_COLUMNS = ['name', 'sku', 'category', 'price', 'description'];

  // State
  let filtersExpanded = $state(false);
  let visibleColumns = $state([...DEFAULT_VISIBLE_COLUMNS]);

  // Drawer state
  let drawerOpen = $state(false);
  /** @type {'view' | 'create'} */
  let drawerMode = $state('view');
  let selectedProduct = $state(null);
  /** @type {Record<string, any>} */
  let drawerFormData = $state({});

  // Form references
  let createForm;
  let updateForm;
  let deleteForm;

  // Form state for hidden forms
  let formState = $state({
    productId: '',
    name: '',
    description: '',
    sku: '',
    price: '0',
    currency: 'USD',
    category: '',
    isActive: 'true'
  });

  // Derived values
  const filters = $derived(data.filters);
  const pagination = $derived(data.pagination);
  const products = $derived(data.products);
  const categories = $derived(data.categories || []);

  // Count active filters
  const activeFiltersCount = $derived(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.category) count++;
    if (filters.is_active) count++;
    return count;
  });

  // Filter handlers
  async function updateFilters(newFilters) {
    const url = new URL($page.url);

    // Clear existing filter params
    ['search', 'category', 'is_active'].forEach((key) => url.searchParams.delete(key));

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
  function handleRowClick(product) {
    selectedProduct = product;
    drawerMode = 'view';
    drawerOpen = true;
  }

  // Create new product
  function openCreateDrawer() {
    selectedProduct = null;
    drawerMode = 'create';
    drawerFormData = {
      name: '',
      description: '',
      sku: '',
      price: '0',
      currency: 'USD',
      category: '',
      isActive: true
    };
    drawerOpen = true;
  }

  // Close drawer
  function closeDrawer() {
    drawerOpen = false;
    selectedProduct = null;
    drawerFormData = {};
  }

  // Sync drawer form data when opening
  $effect(() => {
    if (drawerOpen) {
      if (drawerMode === 'create') {
        // Already set in openCreateDrawer
      } else if (selectedProduct) {
        drawerFormData = { ...selectedProduct };
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
      formState.description = drawerFormData.description;
      formState.sku = drawerFormData.sku;
      formState.price = drawerFormData.price?.toString() || '0';
      formState.currency = drawerFormData.currency;
      formState.category = drawerFormData.category;
      formState.isActive = drawerFormData.isActive ? 'true' : 'false';

      await tick();
      createForm.requestSubmit();
    } else {
      formState.productId = selectedProduct.id;
      formState.name = drawerFormData.name;
      formState.description = drawerFormData.description;
      formState.sku = drawerFormData.sku;
      formState.price = drawerFormData.price?.toString() || '0';
      formState.currency = drawerFormData.currency;
      formState.category = drawerFormData.category;
      formState.isActive = drawerFormData.isActive ? 'true' : 'false';

      await tick();
      updateForm.requestSubmit();
    }
  }

  // Delete handler
  async function handleDelete() {
    if (!selectedProduct) return;

    if (!confirm('Are you sure you want to delete this product?')) return;

    formState.productId = selectedProduct.id;
    await tick();
    deleteForm.requestSubmit();
  }

  // Column visibility
  function loadColumnConfig() {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('products-column-config');
      if (saved) {
        try {
          visibleColumns = JSON.parse(saved);
        } catch (e) {
          visibleColumns = [...DEFAULT_VISIBLE_COLUMNS];
        }
      }
    }
  }

  function saveColumnConfig() {
    if (typeof window !== 'undefined') {
      localStorage.setItem('products-column-config', JSON.stringify(visibleColumns));
    }
  }

  function toggleColumn(key) {
    const column = columns.find((c) => c.key === key);
    if (column && !column.canHide) return;

    if (visibleColumns.includes(key)) {
      visibleColumns = visibleColumns.filter((k) => k !== key);
    } else {
      visibleColumns = [...visibleColumns, key];
    }
    saveColumnConfig();
  }

  // Load column config on mount
  $effect(() => {
    loadColumnConfig();
  });
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
        toast.success('Product created');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to create product');
      }
    };
  }}
>
  <input type="hidden" name="name" value={formState.name} />
  <input type="hidden" name="description" value={formState.description} />
  <input type="hidden" name="sku" value={formState.sku} />
  <input type="hidden" name="price" value={formState.price} />
  <input type="hidden" name="currency" value={formState.currency} />
  <input type="hidden" name="category" value={formState.category} />
  <input type="hidden" name="isActive" value={formState.isActive} />
</form>

<form
  bind:this={updateForm}
  method="POST"
  action="?/update"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Product updated');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to update product');
      }
    };
  }}
>
  <input type="hidden" name="productId" value={formState.productId} />
  <input type="hidden" name="name" value={formState.name} />
  <input type="hidden" name="description" value={formState.description} />
  <input type="hidden" name="sku" value={formState.sku} />
  <input type="hidden" name="price" value={formState.price} />
  <input type="hidden" name="currency" value={formState.currency} />
  <input type="hidden" name="category" value={formState.category} />
  <input type="hidden" name="isActive" value={formState.isActive} />
</form>

<form
  bind:this={deleteForm}
  method="POST"
  action="?/delete"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Product deleted');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to delete product');
      }
    };
  }}
>
  <input type="hidden" name="productId" value={formState.productId} />
</form>

<!-- Page Content -->
<div class="flex flex-col gap-4 p-6">
  <!-- Header -->
  <PageHeader title="Products">
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

      <!-- Column Visibility -->
      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="outline" size="sm" class="gap-2">
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
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                <line x1="9" y1="3" x2="9" y2="21" />
              </svg>
              Columns
            </Button>
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="w-48">
          {#each columns as column}
            <DropdownMenu.CheckboxItem
              class=""
              checked={visibleColumns.includes(column.key)}
              disabled={!column.canHide}
              onCheckedChange={() => toggleColumn(column.key)}
            >
              {column.label}
            </DropdownMenu.CheckboxItem>
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Root>

      <!-- New Product -->
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
        New Product
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
      placeholder="Search products..."
      onchange={(value) => updateFilters({ ...filters, search: value })}
    />

    {#if categories.length > 0}
      <SelectFilter
        label="Category"
        value={filters.category}
        options={categories}
        onchange={(value) => updateFilters({ ...filters, category: value })}
      />
    {/if}

    <SelectFilter
      label="Status"
      value={filters.is_active}
      options={STATUS_OPTIONS}
      onchange={(value) => updateFilters({ ...filters, is_active: value })}
    />
  </FilterBar>

  <!-- Products Table -->
  <CrmTable data={products} {columns} bind:visibleColumns onRowClick={handleRowClick}>
    {#snippet emptyState()}
      <div class="flex flex-col items-center justify-center py-16 text-center">
        <div class="mb-4 flex size-16 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--surface-sunken)]">
          <span class="text-4xl">📦</span>
        </div>
        <h3 class="text-[var(--text-primary)] text-lg font-medium">No products yet</h3>
        <p class="text-[var(--text-secondary)] text-sm">Create your first product to use in invoices</p>
      </div>
    {/snippet}
    {#snippet cellContent(row, column)}
      {#if column.key === 'price'}
        {formatCurrency(Number(row.price), row.currency)}
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

<!-- Product Drawer -->
<CrmDrawer
  bind:open={drawerOpen}
  data={drawerFormData}
  columns={drawerFields}
  titleKey="name"
  titlePlaceholder="New Product"
  headerLabel="Product"
  mode={drawerMode}
  onFieldChange={handleFieldChange}
  onDelete={handleDelete}
  onClose={closeDrawer}
>
  {#snippet footerActions()}
    <div class="flex w-full items-center justify-end gap-2">
      <Button variant="outline" onclick={closeDrawer}>Cancel</Button>
      <Button onclick={handleDrawerSave}>
        {drawerMode === 'create' ? 'Create Product' : 'Save Changes'}
      </Button>
    </div>
  {/snippet}
</CrmDrawer>
