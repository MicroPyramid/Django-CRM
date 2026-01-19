<script>
  import { page } from '$app/stores';
  import { goto, invalidateAll } from '$app/navigation';
  import { enhance } from '$app/forms';
  import { tick } from 'svelte';
  import { toast } from 'svelte-sonner';

  import { PageHeader } from '$lib/components/layout';
  import { CrmDrawer } from '$lib/components/ui/crm-drawer';
  import { CrmTable } from '$lib/components/ui/crm-table';
  import { FilterBar, SearchInput, DateRangeFilter, SelectFilter } from '$lib/components/ui/filter';
  import { Pagination } from '$lib/components/ui/pagination';
  import { Button } from '$lib/components/ui/button';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu';
  import { formatCurrency, formatDate } from '$lib/utils/formatting.js';

  /** @type {{ data: import('./$types').PageData }} */
  let { data } = $props();

  // Estimate status options - using design system tokens
  const ESTIMATE_STATUSES = [
    { value: 'Draft', label: 'Draft', color: 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]' },
    { value: 'Sent', label: 'Sent', color: 'bg-[var(--stage-contacted-bg)] text-[var(--stage-contacted)] dark:bg-[var(--stage-contacted)]/15' },
    { value: 'Viewed', label: 'Viewed', color: 'bg-[var(--stage-qualified-bg)] text-[var(--stage-qualified)] dark:bg-[var(--stage-qualified)]/15' },
    { value: 'Accepted', label: 'Accepted', color: 'bg-[var(--color-success-light)] text-[var(--color-success-default)] dark:bg-[var(--color-success-default)]/15' },
    { value: 'Declined', label: 'Declined', color: 'bg-[var(--color-negative-light)] text-[var(--color-negative-default)] dark:bg-[var(--color-negative-default)]/15' },
    { value: 'Expired', label: 'Expired', color: 'bg-[var(--color-primary-light)] text-[var(--color-primary-default)] dark:bg-[var(--color-primary-default)]/15' }
  ];

  /**
   * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
   * @typedef {{ key: string, label: string, type?: ColumnType, width?: string, editable?: boolean, canHide?: boolean, getValue?: (row: any) => any, emptyText?: string, relationIcon?: string, options?: Array<{value: string, label: string, color: string}> }} ColumnDef
   */

  /** @type {ColumnDef[]} */
  const columns = [
    {
      key: 'estimateNumber',
      label: 'Estimate #',
      type: 'text',
      width: 'w-32',
      editable: false,
      canHide: false
    },
    {
      key: 'clientName',
      label: 'Client',
      type: 'text',
      width: 'w-40',
      editable: false,
      canHide: false
    },
    {
      key: 'title',
      label: 'Title',
      type: 'text',
      width: 'w-44',
      canHide: true,
      getValue: (row) => row.title
    },
    {
      key: 'account',
      label: 'Account',
      type: 'relation',
      width: 'w-36',
      relationIcon: 'building',
      canHide: true,
      getValue: (row) => row.account?.name
    },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      width: 'w-28',
      options: ESTIMATE_STATUSES,
      canHide: true,
      getValue: (row) => row.status
    },
    {
      key: 'issueDate',
      label: 'Issue Date',
      type: 'date',
      width: 'w-28',
      canHide: true,
      getValue: (row) => row.issueDate
    },
    {
      key: 'expiryDate',
      label: 'Valid Until',
      type: 'date',
      width: 'w-28',
      canHide: true,
      getValue: (row) => row.expiryDate
    },
    {
      key: 'totalAmount',
      label: 'Total',
      type: 'number',
      width: 'w-28',
      canHide: false,
      getValue: (row) => formatCurrency(Number(row.totalAmount), row.currency)
    },
    {
      key: 'owner',
      label: 'Owner',
      type: 'relation',
      width: 'w-32',
      relationIcon: 'user',
      canHide: true,
      getValue: (row) => row.owner?.name
    }
  ];

  // Drawer field definitions
  const drawerFields = [
    // Core Info Section
    { key: 'estimateNumber', label: 'Estimate #', type: 'readonly', section: 'core' },
    { key: 'title', label: 'Title', type: 'text', section: 'core' },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      section: 'core',
      options: ESTIMATE_STATUSES
    },
    // Client Section
    { key: 'clientName', label: 'Client Name', type: 'text', section: 'client', required: true },
    { key: 'clientEmail', label: 'Client Email', type: 'email', section: 'client' },
    { key: 'clientPhone', label: 'Client Phone', type: 'text', section: 'client' },
    // Dates Section
    { key: 'issueDate', label: 'Issue Date', type: 'date', section: 'dates' },
    { key: 'expiryDate', label: 'Valid Until', type: 'date', section: 'dates' },
    // Amounts Section (readonly in drawer - calculated from line items)
    {
      key: 'subtotal',
      label: 'Subtotal',
      type: 'readonly',
      section: 'amounts',
      getValue: (row) => formatCurrency(Number(row.subtotal), row.currency)
    },
    {
      key: 'discountAmount',
      label: 'Discount',
      type: 'readonly',
      section: 'amounts',
      getValue: (row) => formatCurrency(Number(row.discountAmount), row.currency)
    },
    {
      key: 'taxAmount',
      label: 'Tax',
      type: 'readonly',
      section: 'amounts',
      getValue: (row) => formatCurrency(Number(row.taxAmount), row.currency)
    },
    {
      key: 'totalAmount',
      label: 'Total',
      type: 'readonly',
      section: 'amounts',
      getValue: (row) => formatCurrency(Number(row.totalAmount), row.currency)
    },
    // Notes Section
    { key: 'notes', label: 'Notes', type: 'textarea', section: 'notes' },
    { key: 'terms', label: 'Terms & Conditions', type: 'textarea', section: 'notes' }
  ];

  // Default visible columns
  const DEFAULT_VISIBLE_COLUMNS = [
    'estimateNumber',
    'clientName',
    'title',
    'status',
    'expiryDate',
    'totalAmount'
  ];

  // Status chip filter definitions
  const STATUS_CHIPS = [
    { key: 'ALL', label: 'All' },
    { key: 'OPEN', label: 'Open', statuses: ['Draft', 'Sent', 'Viewed'] },
    { key: 'ACCEPTED', label: 'Accepted', statuses: ['Accepted'] },
    { key: 'DECLINED', label: 'Declined', statuses: ['Declined'] },
    { key: 'EXPIRED', label: 'Expired', statuses: ['Expired'] }
  ];

  // State
  let filtersExpanded = $state(false);
  let visibleColumns = $state([...DEFAULT_VISIBLE_COLUMNS]);
  let statusChipFilter = $state('ALL');

  // Drawer state
  let drawerOpen = $state(false);
  /** @type {'view' | 'create'} */
  let drawerMode = $state('view');
  let selectedEstimate = $state(null);
  /** @type {Record<string, any>} */
  let drawerFormData = $state({});

  // Form references
  let createForm;
  let updateForm;
  let deleteForm;
  let sendForm;
  let convertForm;
  let acceptForm;
  let declineForm;

  // Form state for hidden forms
  let formState = $state({
    estimateId: '',
    title: '',
    status: 'Draft',
    clientName: '',
    clientEmail: '',
    clientPhone: '',
    issueDate: '',
    expiryDate: '',
    accountId: '',
    contactId: '',
    notes: '',
    terms: ''
  });

  // Derived values
  const filters = $derived(data.filters);
  const pagination = $derived(data.pagination);
  const allEstimates = $derived(data.estimates);
  const template = $derived(data.template);

  // Filter estimates by chip selection (client-side filtering)
  const estimates = $derived.by(() => {
    if (statusChipFilter === 'ALL') {
      return allEstimates;
    }
    const chip = STATUS_CHIPS.find((c) => c.key === statusChipFilter);
    if (!chip?.statuses) return allEstimates;
    return allEstimates.filter((est) => chip.statuses.includes(est.status));
  });

  // Count estimates per chip category
  const chipCounts = $derived.by(() => {
    const counts = { ALL: allEstimates.length };
    STATUS_CHIPS.forEach((chip) => {
      if (chip.statuses) {
        counts[chip.key] = allEstimates.filter((est) => chip.statuses.includes(est.status)).length;
      }
    });
    return counts;
  });

  // Count active filters
  const activeFiltersCount = $derived(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.status) count++;
    if (filters.account) count++;
    if (filters.issue_date_gte || filters.issue_date_lte) count++;
    if (filters.expiry_date_gte || filters.expiry_date_lte) count++;
    return count;
  });

  // Filter handlers
  async function updateFilters(newFilters) {
    const url = new URL($page.url);

    // Clear existing filter params
    [
      'search',
      'status',
      'account',
      'contact',
      'assigned_to',
      'issue_date_gte',
      'issue_date_lte',
      'expiry_date_gte',
      'expiry_date_lte'
    ].forEach((key) => url.searchParams.delete(key));

    // Set new params
    Object.entries(newFilters).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((v) => url.searchParams.append(key, v));
      } else if (value) {
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
  function handleRowClick(estimate) {
    selectedEstimate = estimate;
    drawerMode = 'view';
    drawerOpen = true;
  }

  // Create new estimate
  function openCreateDrawer() {
    selectedEstimate = null;
    drawerMode = 'create';
    drawerFormData = {
      estimateNumber: 'Auto-generated',
      title: '',
      status: 'Draft',
      clientName: '',
      clientEmail: '',
      clientPhone: '',
      issueDate: new Date().toISOString().split('T')[0],
      expiryDate: '',
      // Pre-populate notes/terms from default template
      notes: template?.defaultNotes || '',
      terms: template?.defaultTerms || '',
      lineItems: []
    };
    drawerOpen = true;
  }

  // Close drawer
  function closeDrawer() {
    drawerOpen = false;
    selectedEstimate = null;
    drawerFormData = {};
  }

  // Sync drawer form data when opening
  $effect(() => {
    if (drawerOpen) {
      if (drawerMode === 'create') {
        // Already set in openCreateDrawer
      } else if (selectedEstimate) {
        drawerFormData = { ...selectedEstimate };
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
      formState.status = drawerFormData.status;
      formState.clientName = drawerFormData.clientName;
      formState.clientEmail = drawerFormData.clientEmail;
      formState.clientPhone = drawerFormData.clientPhone;
      formState.issueDate = drawerFormData.issueDate;
      formState.expiryDate = drawerFormData.expiryDate;
      formState.notes = drawerFormData.notes;
      formState.terms = drawerFormData.terms;

      await tick();
      createForm.requestSubmit();
    } else {
      // Populate form state for update
      formState.estimateId = selectedEstimate.id;
      formState.title = drawerFormData.title;
      formState.status = drawerFormData.status;
      formState.clientName = drawerFormData.clientName;
      formState.clientEmail = drawerFormData.clientEmail;
      formState.clientPhone = drawerFormData.clientPhone;
      formState.issueDate = drawerFormData.issueDate;
      formState.expiryDate = drawerFormData.expiryDate;
      formState.notes = drawerFormData.notes;
      formState.terms = drawerFormData.terms;

      await tick();
      updateForm.requestSubmit();
    }
  }

  // Delete handler
  async function handleDelete() {
    if (!selectedEstimate) return;

    if (!confirm('Are you sure you want to delete this estimate?')) return;

    formState.estimateId = selectedEstimate.id;
    await tick();
    deleteForm.requestSubmit();
  }

  // Send estimate handler
  async function handleSend() {
    if (!selectedEstimate) return;

    formState.estimateId = selectedEstimate.id;
    await tick();
    sendForm.requestSubmit();
  }

  // Convert to invoice handler
  async function handleConvert() {
    if (!selectedEstimate) return;

    if (!confirm('Convert this estimate to an invoice?')) return;

    formState.estimateId = selectedEstimate.id;
    await tick();
    convertForm.requestSubmit();
  }

  // Accept estimate handler
  async function handleAccept() {
    if (!selectedEstimate) return;

    formState.estimateId = selectedEstimate.id;
    await tick();
    acceptForm.requestSubmit();
  }

  // Decline estimate handler
  async function handleDecline() {
    if (!selectedEstimate) return;

    formState.estimateId = selectedEstimate.id;
    await tick();
    declineForm.requestSubmit();
  }

  // Download PDF
  function handleDownloadPDF() {
    if (!selectedEstimate) return;

    // Open PDF in new tab
    window.open(`/api/invoices/estimates/${selectedEstimate.id}/pdf/`, '_blank');
  }

  // Status badge color - using design system tokens
  function getStatusColor(status) {
    const statusObj = ESTIMATE_STATUSES.find((s) => s.value === status);
    return statusObj?.color || 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]';
  }

  // Check if estimate is expired
  function isExpired(expiryDate) {
    if (!expiryDate) return false;
    return new Date(expiryDate) < new Date();
  }

  // Column visibility
  function loadColumnConfig() {
    if (typeof window !== 'undefined') {
      const saved = localStorage.getItem('estimates-column-config');
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
      localStorage.setItem('estimates-column-config', JSON.stringify(visibleColumns));
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
        toast.success('Estimate created');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to create estimate');
      }
    };
  }}
>
  <input type="hidden" name="title" value={formState.title} />
  <input type="hidden" name="status" value={formState.status} />
  <input type="hidden" name="clientName" value={formState.clientName} />
  <input type="hidden" name="clientEmail" value={formState.clientEmail} />
  <input type="hidden" name="clientPhone" value={formState.clientPhone} />
  <input type="hidden" name="issueDate" value={formState.issueDate} />
  <input type="hidden" name="expiryDate" value={formState.expiryDate} />
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
        toast.success('Estimate updated');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to update estimate');
      }
    };
  }}
>
  <input type="hidden" name="estimateId" value={formState.estimateId} />
  <input type="hidden" name="title" value={formState.title} />
  <input type="hidden" name="status" value={formState.status} />
  <input type="hidden" name="clientName" value={formState.clientName} />
  <input type="hidden" name="clientEmail" value={formState.clientEmail} />
  <input type="hidden" name="clientPhone" value={formState.clientPhone} />
  <input type="hidden" name="issueDate" value={formState.issueDate} />
  <input type="hidden" name="expiryDate" value={formState.expiryDate} />
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
        toast.success('Estimate deleted');
        closeDrawer();
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to delete estimate');
      }
    };
  }}
>
  <input type="hidden" name="estimateId" value={formState.estimateId} />
</form>

<form
  bind:this={sendForm}
  method="POST"
  action="?/send"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Estimate sent');
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to send estimate');
      }
    };
  }}
>
  <input type="hidden" name="estimateId" value={formState.estimateId} />
</form>

<form
  bind:this={convertForm}
  method="POST"
  action="?/convert"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Estimate converted to invoice');
        closeDrawer();
        invalidateAll();
        // Optionally navigate to the new invoice
        if (result.data?.invoiceId) {
          goto(`/invoices?selected=${result.data.invoiceId}`);
        }
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to convert estimate');
      }
    };
  }}
>
  <input type="hidden" name="estimateId" value={formState.estimateId} />
</form>

<form
  bind:this={acceptForm}
  method="POST"
  action="?/accept"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Estimate accepted');
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to accept estimate');
      }
    };
  }}
>
  <input type="hidden" name="estimateId" value={formState.estimateId} />
</form>

<form
  bind:this={declineForm}
  method="POST"
  action="?/decline"
  class="hidden"
  use:enhance={() => {
    return async ({ result }) => {
      if (result.type === 'success') {
        toast.success('Estimate declined');
        invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {string} */ (result.data?.error) || 'Failed to decline estimate');
      }
    };
  }}
>
  <input type="hidden" name="estimateId" value={formState.estimateId} />
</form>

<!-- Page Content -->
<div class="flex flex-col gap-4 p-6">
  <!-- Header -->
  <PageHeader title="Estimates">
    {#snippet actions()}
      <div class="flex items-center gap-2">
        <!-- Status Filter Chips -->
        <div class="flex gap-1">
          {#each STATUS_CHIPS as chip}
            <button
              type="button"
              onclick={() => (statusChipFilter = chip.key)}
              class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
              chip.key
                ? 'bg-[var(--color-primary-default)] text-white'
                : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]'}"
            >
              {chip.label}
              <span
                class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === chip.key
                  ? 'bg-[var(--color-primary-dark)] text-white/90'
                  : 'bg-[var(--border-default)] text-[var(--text-tertiary)]'}"
              >
                {chipCounts[chip.key] || 0}
              </span>
            </button>
          {/each}
        </div>

        <div class="bg-border mx-1 h-6 w-px"></div>

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

        <!-- New Estimate -->
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
          New Estimate
        </Button>
      </div>
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
      placeholder="Search estimates..."
      onchange={(value) => updateFilters({ ...filters, search: value })}
    />

    <SelectFilter
      label="Status"
      value={filters.status}
      options={ESTIMATE_STATUSES}
      onchange={(value) => updateFilters({ ...filters, status: value })}
    />

    <DateRangeFilter
      label="Issue Date"
      startDate={filters.issue_date_gte}
      endDate={filters.issue_date_lte}
      onchange={(start, end) =>
        updateFilters({ ...filters, issue_date_gte: start, issue_date_lte: end })}
    />

    <DateRangeFilter
      label="Valid Until"
      startDate={filters.expiry_date_gte}
      endDate={filters.expiry_date_lte}
      onchange={(start, end) =>
        updateFilters({ ...filters, expiry_date_gte: start, expiry_date_lte: end })}
    />
  </FilterBar>

  <!-- Estimates Table -->
  <CrmTable data={estimates} {columns} bind:visibleColumns onRowClick={handleRowClick}>
    {#snippet emptyState()}
      <div class="flex flex-col items-center justify-center py-16 text-center">
        <div class="mb-4 flex size-16 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--surface-sunken)]">
          <span class="text-4xl">📋</span>
        </div>
        <h3 class="text-[var(--text-primary)] text-lg font-medium">No estimates yet</h3>
        <p class="text-[var(--text-secondary)] text-sm">Create your first estimate to get started</p>
      </div>
    {/snippet}
    {#snippet cellContent(row, column)}
      {#if column.key === 'status'}
        <span
          class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {getStatusColor(
            row.status
          )}"
        >
          {row.status}
        </span>
      {:else if column.key === 'expiryDate'}
        {#if row.expiryDate}
          <span
            class={isExpired(row.expiryDate) && row.status !== 'Accepted' ? 'text-red-600' : ''}
          >
            {formatDate(row.expiryDate)}
          </span>
        {:else}
          -
        {/if}
      {:else if column.key === 'issueDate'}
        {row.issueDate ? formatDate(row.issueDate) : '-'}
      {:else if column.key === 'totalAmount'}
        {formatCurrency(Number(row.totalAmount), row.currency)}
      {:else if column.key === 'account' || column.key === 'contact' || column.key === 'owner'}
        {row[column.key]?.name || '-'}
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

<!-- Estimate Drawer -->
<CrmDrawer
  bind:open={drawerOpen}
  data={drawerFormData}
  columns={drawerFields}
  titleKey="estimateNumber"
  titlePlaceholder="New Estimate"
  headerLabel="Estimate"
  mode={drawerMode}
  onFieldChange={handleFieldChange}
  onDelete={handleDelete}
  onClose={closeDrawer}
>
  {#snippet footerActions()}
    <div class="flex w-full items-center justify-between">
      <div class="flex gap-2">
        {#if drawerMode !== 'create' && selectedEstimate}
          <!-- Download PDF -->
          <Button variant="outline" size="sm" onclick={handleDownloadPDF}>
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
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
              <polyline points="7 10 12 15 17 10" />
              <line x1="12" y1="15" x2="12" y2="3" />
            </svg>
            PDF
          </Button>

          <!-- Send Estimate -->
          {#if selectedEstimate.status === 'Draft'}
            <Button variant="outline" size="sm" onclick={handleSend}>
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
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
              Send
            </Button>
          {/if}

          <!-- Convert to Invoice -->
          {#if selectedEstimate.status === 'Accepted' && !selectedEstimate.convertedToInvoice}
            <Button variant="default" size="sm" onclick={handleConvert}>
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
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
                <line x1="12" y1="18" x2="12" y2="12" />
                <line x1="9" y1="15" x2="15" y2="15" />
              </svg>
              Convert to Invoice
            </Button>
          {/if}

          <!-- Accept/Decline for Sent estimates -->
          {#if selectedEstimate.status === 'Sent' || selectedEstimate.status === 'Viewed'}
            <Button variant="outline" size="sm" class="text-green-600" onclick={handleAccept}>
              Accept
            </Button>
            <Button variant="outline" size="sm" class="text-red-600" onclick={handleDecline}>
              Decline
            </Button>
          {/if}
        {/if}
      </div>

      <div class="flex gap-2">
        <Button variant="outline" onclick={closeDrawer}>Cancel</Button>
        <Button onclick={handleDrawerSave}>
          {drawerMode === 'create' ? 'Create Estimate' : 'Save Changes'}
        </Button>
      </div>
    </div>
  {/snippet}

  {#snippet activitySection()}
    {#if selectedEstimate}
      <div class="border-t pt-4">
        <h4 class="text-muted-foreground mb-2 text-sm font-medium">Activity</h4>
        <div class="space-y-2 text-sm">
          <div class="flex justify-between">
            <span class="text-muted-foreground">Created</span>
            <span>{formatDate(selectedEstimate.createdAt)}</span>
          </div>
          {#if selectedEstimate.sentAt}
            <div class="flex justify-between">
              <span class="text-muted-foreground">Sent</span>
              <span>{formatDate(selectedEstimate.sentAt)}</span>
            </div>
          {/if}
          {#if selectedEstimate.viewedAt}
            <div class="flex justify-between">
              <span class="text-muted-foreground">Viewed</span>
              <span>{formatDate(selectedEstimate.viewedAt)}</span>
            </div>
          {/if}
          {#if selectedEstimate.acceptedAt}
            <div class="flex justify-between">
              <span class="text-muted-foreground">Accepted</span>
              <span>{formatDate(selectedEstimate.acceptedAt)}</span>
            </div>
          {/if}
          {#if selectedEstimate.declinedAt}
            <div class="flex justify-between">
              <span class="text-muted-foreground">Declined</span>
              <span>{formatDate(selectedEstimate.declinedAt)}</span>
            </div>
          {/if}
          {#if selectedEstimate.convertedToInvoice}
            <div class="flex justify-between">
              <span class="text-muted-foreground">Converted to Invoice</span>
              <a
                href="/invoices?selected={selectedEstimate.convertedToInvoice.id}"
                class="text-primary hover:underline"
              >
                {selectedEstimate.convertedToInvoice.invoiceNumber || 'View Invoice'}
              </a>
            </div>
          {/if}
        </div>
      </div>
    {/if}
  {/snippet}
</CrmDrawer>
