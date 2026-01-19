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
  import { formatCurrency, formatDate } from '$lib/utils/formatting.js';

  /** @type {{ data: import('./$types').PageData }} */
  let { data } = $props();

  // Frequency options - using design system tokens
  const FREQUENCIES = [
    { value: 'WEEKLY', label: 'Weekly', color: 'bg-[var(--stage-contacted-bg)] text-[var(--stage-contacted)]' },
    { value: 'BIWEEKLY', label: 'Bi-weekly', color: 'bg-[var(--stage-qualified-bg)] text-[var(--stage-qualified)]' },
    { value: 'MONTHLY', label: 'Monthly', color: 'bg-[var(--color-success-light)] text-[var(--color-success-default)]' },
    { value: 'QUARTERLY', label: 'Quarterly', color: 'bg-[var(--stage-negotiation-bg)] text-[var(--stage-negotiation)]' },
    { value: 'SEMI_ANNUALLY', label: 'Semi-annually', color: 'bg-[var(--color-primary-light)] text-[var(--color-primary-default)]' },
    { value: 'YEARLY', label: 'Yearly', color: 'bg-[var(--stage-proposal-bg)] text-[var(--stage-proposal)]' },
    { value: 'CUSTOM', label: 'Custom', color: 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]' }
  ];

  // Status options
  const STATUS_OPTIONS = [
    { value: 'true', label: 'Active' },
    { value: 'false', label: 'Paused' }
  ];

  // Payment terms options
  const PAYMENT_TERMS = [
    { value: 'DUE_ON_RECEIPT', label: 'Due on Receipt' },
    { value: 'NET_7', label: 'Net 7' },
    { value: 'NET_15', label: 'Net 15' },
    { value: 'NET_30', label: 'Net 30' },
    { value: 'NET_45', label: 'Net 45' },
    { value: 'NET_60', label: 'Net 60' },
    { value: 'NET_90', label: 'Net 90' }
  ];

  /**
   * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
   * @typedef {{ key: string, label: string, type?: ColumnType, width?: string, editable?: boolean, canHide?: boolean, getValue?: (row: any) => any, emptyText?: string, relationIcon?: string, options?: Array<{value: string, label: string, color: string}> }} ColumnDef
   */

  /** @type {ColumnDef[]} */
  const columns = [
    {
      key: 'title',
      label: 'Title',
      type: 'text',
      width: 'w-48',
      editable: false,
      canHide: false
    },
    {
      key: 'clientName',
      label: 'Client',
      type: 'text',
      width: 'w-40',
      canHide: false,
      getValue: (row) => row.clientName
    },
    {
      key: 'frequency',
      label: 'Frequency',
      type: 'select',
      width: 'w-28',
      options: FREQUENCIES,
      canHide: true,
      getValue: (row) => row.frequency
    },
    {
      key: 'nextGenerationDate',
      label: 'Next Invoice',
      type: 'date',
      width: 'w-28',
      canHide: true,
      getValue: (row) => row.nextGenerationDate
    },
    {
      key: 'totalAmount',
      label: 'Amount',
      type: 'number',
      width: 'w-28',
      canHide: false,
      getValue: (row) => formatCurrency(Number(row.totalAmount), row.currency)
    },
    {
      key: 'invoicesGenerated',
      label: 'Generated',
      type: 'number',
      width: 'w-24',
      canHide: true,
      getValue: (row) => row.invoicesGenerated
    },
    {
      key: 'account',
      label: 'Account',
      type: 'relation',
      width: 'w-36',
      relationIcon: 'building',
      canHide: true,
      getValue: (row) => row.account?.name
    }
  ];

  // Drawer field definitions
  const drawerFields = [
    // Core Info Section
    { key: 'title', label: 'Title', type: 'text', section: 'core', required: true },
    {
      key: 'isActive',
      label: 'Active',
      type: 'boolean',
      section: 'core'
    },
    // Client Section
    { key: 'clientName', label: 'Client Name', type: 'text', section: 'client', required: true },
    { key: 'clientEmail', label: 'Client Email', type: 'email', section: 'client' },
    // Schedule Section
    {
      key: 'frequency',
      label: 'Frequency',
      type: 'select',
      section: 'schedule',
      options: FREQUENCIES
    },
    { key: 'customDays', label: 'Custom Days', type: 'number', section: 'schedule' },
    { key: 'startDate', label: 'Start Date', type: 'date', section: 'schedule' },
    { key: 'endDate', label: 'End Date', type: 'date', section: 'schedule' },
    { key: 'nextGenerationDate', label: 'Next Invoice Date', type: 'date', section: 'schedule' },
    // Settings Section
    {
      key: 'paymentTerms',
      label: 'Payment Terms',
      type: 'select',
      section: 'settings',
      options: PAYMENT_TERMS
    },
    {
      key: 'autoSend',
      label: 'Auto Send',
      type: 'boolean',
      section: 'settings'
    },
    // Amounts Section
    {
      key: 'subtotal',
      label: 'Subtotal',
      type: 'readonly',
      section: 'amounts',
      getValue: (row) => formatCurrency(Number(row.subtotal), row.currency)
    },
    {
      key: 'totalAmount',
      label: 'Total',
      type: 'readonly',
      section: 'amounts',
      getValue: (row) => formatCurrency(Number(row.totalAmount), row.currency)
    },
    // Stats Section
    {
      key: 'invoicesGenerated',
      label: 'Invoices Generated',
      type: 'readonly',
      section: 'stats'
    },
    // Notes Section
    { key: 'notes', label: 'Notes', type: 'textarea', section: 'notes' },
    { key: 'terms', label: 'Terms & Conditions', type: 'textarea', section: 'notes' }
  ];

  // Default visible columns
  const DEFAULT_VISIBLE_COLUMNS = [
    'title',
    'clientName',
    'frequency',
    'nextGenerationDate',
    'totalAmount'
  ];

  // State
  let filtersExpanded = $state(false);
  let visibleColumns = $state([...DEFAULT_VISIBLE_COLUMNS]);

  // Drawer state
  let drawerOpen = $state(false);
  /** @type {'view' | 'create'} */
  let drawerMode = $state('view');
  let selectedRecurring = $state(null);
  /** @type {Record<string, any>} */
  let drawerFormData = $state({});

  // Form references
  let createForm;
  let updateForm;
  let deleteForm;
  let toggleForm;

  // Form state for hidden forms
  let formState = $state({
    recurringId: '',
    title: '',
    isActive: 'true',
    clientName: '',
    clientEmail: '',
    frequency: 'MONTHLY',
    customDays: '',
    startDate: '',
    endDate: '',
    paymentTerms: 'NET_30',
    autoSend: 'false',
    accountId: '',
    contactId: '',
    notes: '',
    terms: ''
  });

  // Derived values
  const filters = $derived(data.filters);
  const pagination = $derived(data.pagination);
  const recurringInvoices = $derived(data.recurringInvoices);

  // Count active filters
  const activeFiltersCount = $derived(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.is_active) count++;
    if (filters.frequency) count++;
    if (filters.account) count++;
    return count;
  });

  // Filter handlers
  async function updateFilters(newFilters) {
    const url = new URL($page.url);

    // Clear existing filter params
    ['search', 'is_active', 'frequency', 'account'].forEach((key) => url.searchParams.delete(key));

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
  function handleRowClick(recurring) {
    selectedRecurring = recurring;
    drawerMode = 'view';
    drawerOpen = true;
  }

  // Create new recurring invoice
  function openCreateDrawer() {
    selectedRecurring = null;
    drawerMode = 'create';
    drawerFormData = {
      title: '',
      isActive: true,
      clientName: '',
      clientEmail: '',
      frequency: 'MONTHLY',
      customDays: null,
      startDate: new Date().toISOString().split('T')[0],
      endDate: '',
      paymentTerms: 'NET_30',
      autoSend: false,
      notes: '',
      terms: '',
      lineItems: []
    };
    drawerOpen = true;
  }

  // Close drawer
  function closeDrawer() {
    drawerOpen = false;
    selectedRecurring = null;
    drawerFormData = {};
  }

  // Sync drawer form data when opening
  $effect(() => {
    if (drawerOpen) {
      if (drawerMode === 'create') {
        // Already set in openCreateDrawer
      } else if (selectedRecurring) {
        drawerFormData = { ...selectedRecurring };
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
      // Populate form state for create
      formState.title = drawerFormData.title;
      formState.isActive = drawerFormData.isActive ? 'true' : 'false';
      formState.clientName = drawerFormData.clientName;
      formState.clientEmail = drawerFormData.clientEmail;
      formState.frequency = drawerFormData.frequency;
      formState.customDays = drawerFormData.customDays?.toString() || '';
      formState.startDate = drawerFormData.startDate;
      formState.endDate = drawerFormData.endDate;
      formState.paymentTerms = drawerFormData.paymentTerms;
      formState.autoSend = drawerFormData.autoSend ? 'true' : 'false';
      formState.notes = drawerFormData.notes;
      formState.terms = drawerFormData.terms;

      await tick();
      createForm.requestSubmit();
    } else {
      // Populate form state for update
      formState.recurringId = selectedRecurring.id;
      formState.title = drawerFormData.title;
      formState.isActive = drawerFormData.isActive ? 'true' : 'false';
      formState.clientName = drawerFormData.clientName;
      formState.clientEmail = drawerFormData.clientEmail;
      formState.frequency = drawerFormData.frequency;
      formState.customDays = drawerFormData.customDays?.toString() || '';
      formState.startDate = drawerFormData.startDate;
      formState.endDate = drawerFormData.endDate;
      formState.paymentTerms = drawerFormData.paymentTerms;
      formState.autoSend = drawerFormData.autoSend ? 'true' : 'false';
      formState.notes = drawerFormData.notes;
      formState.terms = drawerFormData.terms;

      await tick();
      updateForm.requestSubmit();
    }
  }

  // Delete handler
  async function handleDelete() {
    if (!selectedRecurring) return;

    if (!confirm('Are you sure you want to delete this recurring invoice?')) return;

    formState.recurringId = selectedRecurring.id;
    await tick();
    deleteForm.requestSubmit();
  }

  // Toggle active/paused handler
  async function handleToggle() {
    if (!selectedRecurring) return;

    formState.recurringId = selectedRecurring.id;
    await tick();
    toggleForm.requestSubmit();
  }

  // Format frequency label
  function getFrequencyLabel(frequency) {
    const freq = FREQUENCIES.find((f) => f.value === frequency);
    return freq?.label || frequency;
  }

  // Column visibility
  function loadColumnConfig() {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('recurring-invoices-column-config');
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
      localStorage.setItem('recurring-invoices-column-config', JSON.stringify(visibleColumns));
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
        toast.success('Recurring invoice created');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(
          /** @type {string} */ (result.data?.error) || 'Failed to create recurring invoice'
        );
      }
    };
  }}
>
  <input type="hidden" name="title" value={formState.title} />
  <input type="hidden" name="isActive" value={formState.isActive} />
  <input type="hidden" name="clientName" value={formState.clientName} />
  <input type="hidden" name="clientEmail" value={formState.clientEmail} />
  <input type="hidden" name="frequency" value={formState.frequency} />
  <input type="hidden" name="customDays" value={formState.customDays} />
  <input type="hidden" name="startDate" value={formState.startDate} />
  <input type="hidden" name="endDate" value={formState.endDate} />
  <input type="hidden" name="paymentTerms" value={formState.paymentTerms} />
  <input type="hidden" name="autoSend" value={formState.autoSend} />
  <input type="hidden" name="notes" value={formState.notes} />
  <input type="hidden" name="terms" value={formState.terms} />
  <input type="hidden" name="accountId" value={formState.accountId} />
  <input type="hidden" name="contactId" value={formState.contactId} />
</form>

<form
  bind:this={updateForm}
  method="POST"
  action="?/update"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Recurring invoice updated');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(
          /** @type {string} */ (result.data?.error) || 'Failed to update recurring invoice'
        );
      }
    };
  }}
>
  <input type="hidden" name="recurringId" value={formState.recurringId} />
  <input type="hidden" name="title" value={formState.title} />
  <input type="hidden" name="isActive" value={formState.isActive} />
  <input type="hidden" name="clientName" value={formState.clientName} />
  <input type="hidden" name="clientEmail" value={formState.clientEmail} />
  <input type="hidden" name="frequency" value={formState.frequency} />
  <input type="hidden" name="customDays" value={formState.customDays} />
  <input type="hidden" name="startDate" value={formState.startDate} />
  <input type="hidden" name="endDate" value={formState.endDate} />
  <input type="hidden" name="paymentTerms" value={formState.paymentTerms} />
  <input type="hidden" name="autoSend" value={formState.autoSend} />
  <input type="hidden" name="notes" value={formState.notes} />
  <input type="hidden" name="terms" value={formState.terms} />
  <input type="hidden" name="accountId" value={formState.accountId} />
  <input type="hidden" name="contactId" value={formState.contactId} />
</form>

<form
  bind:this={deleteForm}
  method="POST"
  action="?/delete"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Recurring invoice deleted');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(
          /** @type {string} */ (result.data?.error) || 'Failed to delete recurring invoice'
        );
      }
    };
  }}
>
  <input type="hidden" name="recurringId" value={formState.recurringId} />
</form>

<form
  bind:this={toggleForm}
  method="POST"
  action="?/toggle"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Status updated');
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to update status');
      }
    };
  }}
>
  <input type="hidden" name="recurringId" value={formState.recurringId} />
</form>

<!-- Page Content -->
<div class="flex flex-col gap-4 p-6">
  <!-- Header -->
  <PageHeader title="Recurring Invoices">
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

      <!-- New Recurring Invoice -->
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
        New Recurring
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
      placeholder="Search recurring..."
      onchange={(value) => updateFilters({ ...filters, search: value })}
    />

    <SelectFilter
      label="Status"
      value={filters.is_active}
      options={STATUS_OPTIONS}
      onchange={(value) => updateFilters({ ...filters, is_active: value })}
    />

    <SelectFilter
      label="Frequency"
      value={filters.frequency}
      options={FREQUENCIES}
      onchange={(value) => updateFilters({ ...filters, frequency: value })}
    />
  </FilterBar>

  <!-- Recurring Invoices Table -->
  <CrmTable data={recurringInvoices} {columns} bind:visibleColumns onRowClick={handleRowClick}>
    {#snippet emptyState()}
      <div class="flex flex-col items-center justify-center py-16 text-center">
        <div class="mb-4 flex size-16 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--surface-sunken)]">
          <span class="text-4xl">🔄</span>
        </div>
        <h3 class="text-[var(--text-primary)] text-lg font-medium">No recurring invoices yet</h3>
        <p class="text-[var(--text-secondary)] text-sm">Create your first recurring invoice template</p>
      </div>
    {/snippet}
    {#snippet cellContent(row, column)}
      {#if column.key === 'frequency'}
        {getFrequencyLabel(row.frequency)}
      {:else if column.key === 'nextGenerationDate'}
        {row.nextGenerationDate ? formatDate(row.nextGenerationDate) : '-'}
      {:else if column.key === 'totalAmount'}
        {formatCurrency(Number(row.totalAmount), row.currency)}
      {:else if column.key === 'invoicesGenerated'}
        {row.invoicesGenerated}
      {:else if column.key === 'account'}
        {row.account?.name || '-'}
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

<!-- Recurring Invoice Drawer -->
<CrmDrawer
  bind:open={drawerOpen}
  data={drawerFormData}
  columns={drawerFields}
  titleKey="title"
  titlePlaceholder="New Recurring Invoice"
  headerLabel="Recurring Invoice"
  mode={drawerMode}
  onFieldChange={handleFieldChange}
  onDelete={handleDelete}
  onClose={closeDrawer}
>
  {#snippet footerActions()}
    <div class="flex w-full items-center justify-between">
      <div class="flex gap-2">
        {#if drawerMode !== 'create' && selectedRecurring}
          <!-- Toggle Active/Paused -->
          <Button
            variant="outline"
            size="sm"
            onclick={handleToggle}
            class={selectedRecurring.isActive ? 'text-orange-600' : 'text-green-600'}
          >
            {#if selectedRecurring.isActive}
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
                <rect x="6" y="4" width="4" height="16" />
                <rect x="14" y="4" width="4" height="16" />
              </svg>
              Pause
            {:else}
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
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              Activate
            {/if}
          </Button>
        {/if}
      </div>

      <div class="flex gap-2">
        <Button variant="outline" onclick={closeDrawer}>Cancel</Button>
        <Button onclick={handleDrawerSave}>
          {drawerMode === 'create' ? 'Create Recurring' : 'Save Changes'}
        </Button>
      </div>
    </div>
  {/snippet}

  {#snippet activitySection()}
    {#if selectedRecurring}
      <div class="border-t pt-4">
        <h4 class="text-muted-foreground mb-2 text-sm font-medium">Statistics</h4>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-muted-foreground">Created</span>
            <span>{formatDate(selectedRecurring.createdAt)}</span>
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Start Date</span>
            <span
              >{selectedRecurring.startDate ? formatDate(selectedRecurring.startDate) : '-'}</span
            >
          </div>
          {#if selectedRecurring.endDate}
            <div class="flex justify-between">
              <span class="text-muted-foreground">End Date</span>
              <span>{formatDate(selectedRecurring.endDate)}</span>
            </div>
          {/if}
          <div class="flex justify-between">
            <span class="text-muted-foreground">Next Invoice</span>
            <span
              >{selectedRecurring.nextGenerationDate
                ? formatDate(selectedRecurring.nextGenerationDate)
                : '-'}</span
            >
          </div>
          <div class="flex justify-between">
            <span class="text-muted-foreground">Invoices Generated</span>
            <span class="font-medium">{selectedRecurring.invoicesGenerated}</span>
          </div>
        </div>
      </div>
    {/if}
  {/snippet}
</CrmDrawer>
