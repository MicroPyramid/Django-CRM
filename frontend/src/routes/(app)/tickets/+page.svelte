<script>
  import { enhance } from '$app/forms';
  import { invalidateAll, goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount, tick } from 'svelte';
  import { toast } from 'svelte-sonner';
  import {
    Briefcase,
    Building2,
    User,
    Users,
    Flag,
    Tag,
    Circle,
    Calendar,
    FileText,
    MessageSquare,
    Activity,
    AlertTriangle,
    BarChart3,
    Loader2,
    Eye,
    Network
  } from '@lucide/svelte';
  import { TicketKanban } from '$lib/components/ui/ticket-kanban';
  import { Button } from '$lib/components/ui/button/index.js';
  import { PageHeader } from '$lib/components/layout';
  import { CrmTable } from '$lib/components/ui/crm-table';
  import { CrmDrawer } from '$lib/components/ui/crm-drawer';
  import { BulkActionBar } from '$lib/components/ui/bulk-action-bar';
  import { TicketStatusChips, TicketListActions } from '$lib/components/tickets';
  import {
    FilterBar,
    SearchInput,
    SelectFilter,
    DateRangeFilter,
    TagFilter
  } from '$lib/components/ui/filter';
  import { Pagination } from '$lib/components/ui/pagination';
  import {
    ticketStatusOptions,
    ticketTypeOptions,
    ticketPriorityOptions
  } from '$lib/utils/table-helpers.js';
  import { useDrawerState } from '$lib/hooks';

  // Account from URL param (for quick action from account page)
  let accountFromUrl = $state(false);
  let accountName = $state('');
  let accountIdFromUrl = $state('');

  /**
   * @typedef {Object} ColumnDef
   * @property {string} key
   * @property {string} label
   * @property {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} [type]
   * @property {string} [width]
   * @property {{ value: string, label: string, color: string }[]} [options]
   * @property {boolean} [editable]
   * @property {boolean} [canHide]
   * @property {string} [relationIcon]
   * @property {(row: any) => any} [getValue]
   */

  // NotionTable column configuration - reordered for scanning priority
  /** @type {ColumnDef[]} */
  const columns = [
    { key: 'subject', label: 'Ticket', type: 'text', width: 'w-[250px]', canHide: false },
    {
      key: 'account',
      label: 'Account',
      type: 'relation',
      relationIcon: 'building',
      width: 'w-40',
      getValue: (/** @type {any} */ row) => row.account
    },
    {
      key: 'priority',
      label: 'Priority',
      type: 'select',
      options: ticketPriorityOptions,
      width: 'w-28'
    },
    { key: 'status', label: 'Status', type: 'select', options: ticketStatusOptions, width: 'w-28' },
    { key: 'ticketType', label: 'Type', type: 'select', options: ticketTypeOptions, width: 'w-28' },
    {
      key: 'owner',
      label: 'Assigned To',
      type: 'relation',
      relationIcon: 'user',
      width: 'w-36',
      getValue: (/** @type {any} */ row) => row.owner
    },
    { key: 'createdAt', label: 'Created', type: 'date', width: 'w-32', editable: false }
  ];

  // Column visibility state
  const STORAGE_KEY = 'tickets-column-config';
  let visibleColumns = $state(columns.map((c) => c.key));

  // Load column visibility from localStorage
  onMount(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        visibleColumns = parsed.filter((/** @type {string} */ key) =>
          columns.some((c) => c.key === key)
        );
      } catch (e) {
        console.error('Failed to parse saved columns:', e);
      }
    }
  });

  // Save column visibility when changed
  $effect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(visibleColumns));
  });

  /**
   * @param {string} key
   */
  function isColumnVisible(key) {
    return visibleColumns.includes(key);
  }

  /**
   * @param {string} key
   */
  function toggleColumn(key) {
    const column = columns.find((c) => c.key === key);
    // @ts-ignore
    if (column?.canHide === false) return;

    if (visibleColumns.includes(key)) {
      visibleColumns = visibleColumns.filter((k) => k !== key);
    } else {
      visibleColumns = [...visibleColumns, key];
    }
  }

  const columnCounts = $derived({
    visible: visibleColumns.length,
    total: columns.length
  });

  // Drawer local form state
  let drawerFormData = $state({
    subject: '',
    description: '',
    accountId: '',
    accountName: '', // Read-only display for edit mode
    assignedTo: /** @type {string[]} */ ([]),
    contacts: /** @type {string[]} */ ([]),
    teams: /** @type {string[]} */ ([]),
    tags: /** @type {string[]} */ ([]),
    priority: 'Normal',
    ticketType: '',
    status: 'New',
    closedOn: ''
  });

  // Track if drawer form has been modified
  let isDrawerDirty = $state(false);
  let isSubmitting = $state(false);

  /** @type {{ data: any }} */
  let { data } = $props();

  // Computed values
  let ticketsData = $derived(data.tickets || []);
  const pagination = $derived(data.pagination || { page: 1, limit: 10, total: 0, totalPages: 0 });

  // View mode (list or kanban)
  /** @type {'list' | 'kanban'} */
  let viewMode = $state('list');

  // Sync viewMode when data changes
  $effect(() => {
    if (data.viewMode) {
      viewMode = data.viewMode;
    }
  });

  // Kanban data from server
  const kanbanData = $derived(data.kanbanData);

  // Dropdown options from server (loaded with page data)
  const formOptions = $derived(data.formOptions || {});
  const accounts = $derived(formOptions.accounts || []);
  const users = $derived(formOptions.users || []);
  const contacts = $derived(formOptions.contacts || []);
  const teams = $derived(formOptions.teams || []);
  const tags = $derived(formOptions.tags || []);
  // Tags with color for filter dropdown
  const allTags = $derived(formOptions.tags || []);

  /**
   * Get account name from server-provided accounts list
   * @param {string} id
   */
  function fetchAccountName(id) {
    const account = accounts.find((a) => a.id === id);
    if (account) {
      accountName = account.name;
    } else {
      accountName = 'Unknown Account';
    }
  }

  /**
   * Clear URL params for accountId and action
   */
  function clearUrlParams() {
    const url = new URL($page.url);
    url.searchParams.delete('action');
    url.searchParams.delete('accountId');
    goto(url.pathname, { replaceState: true, invalidateAll: true });
    accountFromUrl = false;
    accountName = '';
    accountIdFromUrl = '';
  }

  // Drawer state using hook
  const drawer = useDrawerState();

  // URL sync for accountId and action params (quick action from account page)
  $effect(() => {
    const action = $page.url.searchParams.get('action');
    const accountIdParam = $page.url.searchParams.get('accountId');

    if (action === 'create' && !drawer.detailOpen) {
      // Handle account pre-fill from URL BEFORE opening drawer
      if (accountIdParam) {
        accountIdFromUrl = accountIdParam;
        accountFromUrl = true;
        fetchAccountName(accountIdParam);
      }

      drawer.openCreate();

      // Set account in form data after drawer opens
      if (accountIdParam) {
        drawerFormData.accountId = accountIdParam;
      }
    }
  });

  // Account options for drawer select
  const accountOptions = $derived([
    { value: '', label: 'None', color: 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]' },
    ...accounts.map((/** @type {any} */ a) => ({
      value: a.id,
      label: a.name,
      color: 'bg-[var(--color-primary-light)] text-[var(--color-primary-default)]'
    }))
  ]);

  // Drawer columns configuration (with icons and multiselect).
  // The drawer is create-only; account is editable except when pre-filled from URL.
  const drawerColumns = $derived([
    { key: 'subject', label: 'Ticket Title', type: 'text' },
    !accountFromUrl
      ? {
          key: 'accountId',
          label: 'Account',
          type: 'select',
          icon: Building2,
          options: accountOptions,
          emptyText: 'No account'
        }
      : accountFromUrl
        ? {
            key: 'accountDisplay',
            label: 'Account',
            type: 'readonly',
            icon: Building2,
            getValue: () => accountName || 'Loading...'
          }
        : {
            key: 'accountName',
            label: 'Account',
            type: 'readonly',
            icon: Building2,
            emptyText: 'No account'
          },
    {
      key: 'ticketType',
      label: 'Type',
      type: 'select',
      icon: Tag,
      options: ticketTypeOptions,
      emptyText: 'Select type'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      icon: Circle,
      options: ticketStatusOptions
    },
    {
      key: 'priority',
      label: 'Priority',
      type: 'select',
      icon: Flag,
      options: ticketPriorityOptions
    },
    {
      key: 'description',
      label: 'Description',
      type: 'textarea',
      icon: FileText,
      placeholder: 'Describe the ticket...',
      emptyText: 'No description'
    },
    {
      key: 'assignedTo',
      label: 'Assigned To',
      type: 'multiselect',
      icon: User,
      options: users.map((/** @type {any} */ u) => ({ id: u.id, name: u.name })),
      emptyText: 'Unassigned'
    },
    {
      key: 'teams',
      label: 'Teams',
      type: 'multiselect',
      icon: Users,
      options: teams.map((/** @type {any} */ t) => ({ id: t.id, name: t.name })),
      emptyText: 'No teams'
    },
    {
      key: 'contacts',
      label: 'Contacts',
      type: 'multiselect',
      icon: User,
      options: contacts.map((/** @type {any} */ c) => ({ id: c.id, name: c.name, email: c.email })),
      emptyText: 'No contacts'
    },
    {
      key: 'tags',
      label: 'Tags',
      type: 'multiselect',
      icon: Tag,
      options: tags.map((/** @type {any} */ t) => ({ id: t.id, name: t.name })),
      emptyText: 'No tags'
    },
    {
      key: 'closedOn',
      label: 'Close Date',
      type: 'date',
      icon: Calendar,
      emptyText: 'Not set'
    }
  ]);

  // Reset the drawer form when the create drawer opens. Edit/view modes are
  // handled by the dedicated /tickets/[id] route now, so the drawer is create-only.
  $effect(() => {
    if (drawer.detailOpen) {
      drawerFormData = {
        subject: '',
        description: '',
        accountId: accountIdFromUrl || '', // Preserve account from URL if present
        accountName: '',
        assignedTo: [],
        contacts: [],
        teams: [],
        tags: [],
        priority: 'Normal',
        ticketType: '',
        status: 'New',
        closedOn: ''
      };
      isDrawerDirty = false;
    }
  });

  /**
   * Handle field change from drawer
   * @param {string} field
   * @param {any} value
   */
  function handleDrawerFieldChange(field, value) {
    drawerFormData = { ...drawerFormData, [field]: value };
    isDrawerDirty = true;
  }

  // URL-based filter state from server
  const filters = $derived(data.filters || {});

  // Status options for filter dropdown
  const statusFilterOptions = $derived([
    { value: '', label: 'All Statuses' },
    ...ticketStatusOptions
  ]);

  // Priority options for filter dropdown
  const priorityFilterOptions = $derived([
    { value: '', label: 'All Priorities' },
    ...ticketPriorityOptions
  ]);

  // Type options for filter dropdown
  const typeFilterOptions = $derived([{ value: '', label: 'All Types' }, ...ticketTypeOptions]);

  // Count active filters (excluding status since it's handled via chips in header)
  const activeFiltersCount = $derived.by(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.priority) count++;
    if (filters.case_type) count++;
    if (filters.assigned_to?.length > 0) count++;
    if (filters.tags?.length > 0) count++;
    if (filters.created_at_gte || filters.created_at_lte) count++;
    return count;
  });

  /**
   * Update URL with new filters
   * @param {Record<string, any>} newFilters
   */
  async function updateFilters(newFilters) {
    const url = new URL($page.url);
    // Clear existing filter params
    [
      'search',
      'status',
      'priority',
      'case_type',
      'assigned_to',
      'tags',
      'created_at_gte',
      'created_at_lte'
    ].forEach((key) => url.searchParams.delete(key));
    // Set new params
    Object.entries(newFilters).forEach(([key, value]) => {
      if (Array.isArray(value)) {
        value.forEach((v) => url.searchParams.append(key, v));
      } else if (value && value !== 'ALL') {
        url.searchParams.set(key, value);
      }
    });
    await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
  }

  /**
   * Clear all filters
   */
  function clearFilters() {
    updateFilters({});
  }

  /**
   * Handle page change
   * @param {number} newPage
   */
  async function handlePageChange(newPage) {
    const url = new URL($page.url);
    url.searchParams.set('page', newPage.toString());
    await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
  }

  /**
   * Handle limit change
   * @param {number} newLimit
   */
  async function handleLimitChange(newLimit) {
    const url = new URL($page.url);
    url.searchParams.set('limit', newLimit.toString());
    url.searchParams.set('page', '1'); // Reset to first page
    await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
  }

  // Status counts for filter chips
  const openStatuses = ['New', 'Open', 'Pending', 'Assigned'];
  const openCount = $derived(
    ticketsData.filter((/** @type {any} */ c) => openStatuses.includes(c.status)).length
  );
  const closedCount = $derived(
    ticketsData.filter((/** @type {any} */ c) => c.status === 'Closed').length
  );

  // Status chip filter state (client-side quick filter on top of server filters)
  /** @type {'ALL' | 'open' | 'closed'} */
  let statusChipFilter = $state('ALL');
  /** @type {string[]} */
  let selectedIds = $state([]);

  // Filter panel expansion state
  let filtersExpanded = $state(false);

  // Filtered tickets - server already applies main filters, just apply status chip
  const filteredTickets = $derived.by(() => {
    let filtered = ticketsData;
    if (statusChipFilter === 'open') {
      filtered = filtered.filter((/** @type {any} */ c) => openStatuses.includes(c.status));
    } else if (statusChipFilter === 'closed') {
      filtered = filtered.filter((/** @type {any} */ c) => c.status === 'Closed');
    }
    return filtered;
  });

  // Form references for server actions
  /** @type {HTMLFormElement} */
  let createForm;
  /** @type {HTMLFormElement} */
  let updateForm;
  /** @type {HTMLFormElement} */
  let moveTicketForm;

  // Kanban form state for drag-drop
  let kanbanFormState = $state({
    ticketId: '',
    status: '',
    stageId: '',
    aboveTicketId: '',
    belowTicketId: ''
  });

  // Form data state for the create drawer + inline cell edits.
  // `ticketId` is set by the inline-edit path (handleQuickEdit) to drive the ?/update form.
  let formState = $state({
    title: '',
    description: '',
    accountId: '',
    assignedTo: /** @type {string[]} */ ([]),
    contacts: /** @type {string[]} */ ([]),
    teams: /** @type {string[]} */ ([]),
    tags: /** @type {string[]} */ ([]),
    priority: 'Normal',
    ticketType: '',
    status: 'New',
    dueDate: '',
    ticketId: ''
  });

  /**
   * Handle save from drawer
   */
  async function handleSave() {
    if (!drawerFormData.subject?.trim()) {
      toast.error('Ticket title is required');
      return;
    }

    isSubmitting = true;

    // Convert drawer form data to form state
    formState.title = drawerFormData.subject || '';
    formState.description = drawerFormData.description || '';
    formState.accountId = drawerFormData.accountId || '';
    formState.assignedTo = drawerFormData.assignedTo || [];
    formState.contacts = drawerFormData.contacts || [];
    formState.teams = drawerFormData.teams || [];
    formState.tags = drawerFormData.tags || [];
    formState.priority = drawerFormData.priority || 'Normal';
    formState.ticketType = drawerFormData.ticketType || '';
    formState.status = drawerFormData.status || 'New';
    formState.dueDate = drawerFormData.closedOn || '';

    await tick();
    createForm.requestSubmit();
  }

  /**
   * Create an enhance handler for the remaining form actions (?/create and ?/moveTicket).
   * @param {string} successMessage
   */
  function createEnhanceHandler(successMessage) {
    return () => {
      return async ({ result }) => {
        isSubmitting = false;
        if (result.type === 'success') {
          toast.success(successMessage);
          isDrawerDirty = false;
          drawer.closeAll();
          // Clear account URL params if they were set
          if (accountFromUrl) {
            clearUrlParams();
          }
          await invalidateAll();
        } else if (result.type === 'failure') {
          toast.error(result.data?.error || 'Operation failed');
        } else if (result.type === 'error') {
          toast.error('An unexpected error occurred');
        }
      };
    };
  }

  /**
   * Convert ticket to form state for inline editing
   * @param {any} ticketItem
   */
  function ticketToFormState(ticketItem) {
    return {
      ticketId: ticketItem.id,
      title: ticketItem.subject || '',
      description: ticketItem.description || '',
      accountId: ticketItem.account?.id || '',
      assignedTo: (ticketItem.assignedTo || []).map((/** @type {any} */ a) => a.id),
      contacts: (ticketItem.contacts || []).map((/** @type {any} */ c) => c.id),
      teams: (ticketItem.teams || []).map((/** @type {any} */ t) => t.id),
      tags: (ticketItem.tags || []).map((/** @type {any} */ t) => t.id),
      priority: ticketItem.priority || 'Normal',
      ticketType: ticketItem.ticketType || '',
      status: ticketItem.status || 'New',
      dueDate: ticketItem.closedOn ? ticketItem.closedOn.split('T')[0] : ''
    };
  }

  /**
   * Handle inline cell edits - persists to API
   * @param {any} ticketItem
   * @param {string} field
   * @param {any} value
   */
  async function handleQuickEdit(ticketItem, field, value) {
    // Map frontend field names to form state field names
    const fieldMapping = {
      subject: 'title',
      ticketType: 'ticketType',
      priority: 'priority',
      status: 'status',
      closedOn: 'dueDate'
    };

    // Populate form state with current ticket data
    const currentState = ticketToFormState(ticketItem);

    // Update the specific field (use mapped name if exists)
    const formField = fieldMapping[field] || field;
    currentState[formField] = value;

    // Copy to form state
    Object.assign(formState, currentState);

    await tick();
    updateForm.requestSubmit();
  }

  /**
   * Handle row change from CrmTable (inline editing)
   * @param {any} row
   * @param {string} field
   * @param {any} value
   */
  async function handleRowChange(row, field, value) {
    await handleQuickEdit(row, field, value);
  }

  /**
   * Handle view mode change
   * @param {'list' | 'kanban'} mode
   */
  async function updateViewMode(mode) {
    viewMode = mode;
    const url = new URL($page.url);
    if (mode === 'list') {
      url.searchParams.delete('view');
    } else {
      url.searchParams.set('view', mode);
    }
    await goto(url.toString(), { replaceState: true, noScroll: true, invalidateAll: true });
  }

  /**
   * Handle kanban status change (drag-drop)
   * @param {string} ticketId
   * @param {string} targetColumnId
   * @param {string} _columnId
   */
  async function handleKanbanStatusChange(ticketId, targetColumnId, _columnId) {
    kanbanFormState.ticketId = ticketId;
    kanbanFormState.aboveTicketId = '';
    kanbanFormState.belowTicketId = '';

    // Determine mode from kanban data
    // In status-based mode, column.id is a status value (e.g., "New", "Assigned")
    // In pipeline-based mode, column.id is a stage UUID
    if (kanbanData?.mode === 'pipeline') {
      kanbanFormState.status = '';
      kanbanFormState.stageId = targetColumnId;
    } else {
      kanbanFormState.status = targetColumnId;
      kanbanFormState.stageId = '';
    }

    await tick();
    moveTicketForm.requestSubmit();
  }

  /**
   * Handle kanban card click — navigate to the ticket detail route.
   * @param {any} ticketItem
   */
  function handleKanbanCardClick(ticketItem) {
    goto(`/tickets/${ticketItem.id}`);
  }
</script>

<svelte:head>
  <title>Tickets - BottleCRM</title>
</svelte:head>

<PageHeader title="Tickets" subtitle="{filteredTickets.length} of {ticketsData.length} tickets">
  {#snippet actions()}
    <div class="flex items-center gap-2">
      <TicketStatusChips
        value={statusChipFilter}
        total={ticketsData.length}
        {openCount}
        {closedCount}
        onChange={(v) => (statusChipFilter = v)}
      />
      <Button
        variant={data.watchingOnly ? 'default' : 'outline'}
        size="sm"
        class="gap-1.5"
        onclick={() => {
          const url = new URL($page.url);
          if (data.watchingOnly) url.searchParams.delete('watching');
          else url.searchParams.set('watching', 'true');
          url.searchParams.delete('page');
          goto(url.pathname + (url.search ? url.search : ''));
        }}
        title={data.watchingOnly
          ? 'Show all tickets'
          : 'Show only tickets you are watching'}
      >
        <Eye class="h-3.5 w-3.5" />
        Watching
      </Button>
      <Button
        variant="outline"
        size="sm"
        class="gap-1.5"
        onclick={() => goto('/tickets/analytics')}
        title="Open the analytics dashboard"
      >
        <BarChart3 class="h-3.5 w-3.5" />
        Analytics
      </Button>
      <div class="bg-border mx-1 h-6 w-px"></div>
      <TicketListActions
        {viewMode}
        {filtersExpanded}
        {activeFiltersCount}
        {columns}
        visibleCount={columnCounts.visible}
        totalCount={columnCounts.total}
        {isColumnVisible}
        onViewMode={updateViewMode}
        onToggleFilters={() => (filtersExpanded = !filtersExpanded)}
        onToggleColumn={toggleColumn}
        onCreate={drawer.openCreate}
      />
    </div>
  {/snippet}
</PageHeader>

<div class="flex-1">
  <!-- Collapsible Filter Bar -->
  <FilterBar
    minimal={true}
    expanded={filtersExpanded}
    activeCount={activeFiltersCount}
    onClear={clearFilters}
    class="pb-4"
  >
    <SearchInput
      value={filters.search}
      onchange={(value) => updateFilters({ ...filters, search: value })}
      placeholder="Search tickets..."
    />
    <SelectFilter
      label="Priority"
      options={priorityFilterOptions}
      value={filters.priority}
      onchange={(value) => updateFilters({ ...filters, priority: value })}
    />
    <SelectFilter
      label="Type"
      options={typeFilterOptions}
      value={filters.case_type}
      onchange={(value) => updateFilters({ ...filters, case_type: value })}
    />
    <DateRangeFilter
      label="Created"
      startDate={filters.created_at_gte}
      endDate={filters.created_at_lte}
      onchange={(start, end) =>
        updateFilters({ ...filters, created_at_gte: start, created_at_lte: end })}
    />
    <TagFilter
      tags={allTags}
      value={filters.tags}
      onchange={(ids) => updateFilters({ ...filters, tags: ids })}
    />
  </FilterBar>

  {#if viewMode === 'list'}
    <CrmTable
      data={filteredTickets}
      {columns}
      bind:visibleColumns
      bind:selectedIds
      selectable={true}
      onRowChange={handleRowChange}
      onRowClick={(row) => goto(`/tickets/${row.id}`)}
    >
      {#snippet cellSuffix(row, column)}
        {#if column.key === 'subject' && row.escalationCount > 0}
          <span
            class="ml-2 inline-flex items-center gap-1 rounded-full bg-amber-100 px-1.5 py-0.5 align-middle text-[10px] font-medium text-amber-800 dark:bg-amber-900/30 dark:text-amber-300"
            title={row.lastEscalationFiredAt
              ? `Escalated ${row.escalationCount}× — last ${new Date(row.lastEscalationFiredAt).toLocaleString()}`
              : `Escalated ${row.escalationCount}×`}
          >
            <AlertTriangle class="h-3 w-3" />
            Escalated
          </span>
        {/if}
        {#if column.key === 'subject' && (row.isProblem || row.childCount > 0)}
          <span
            class="ml-2 inline-flex items-center gap-1 rounded-full bg-purple-100 px-1.5 py-0.5 align-middle text-[10px] font-medium text-purple-800 dark:bg-purple-900/30 dark:text-purple-300"
            title={row.isProblem
              ? `Problem ticket · ${row.childCount} linked child${row.childCount === 1 ? '' : 'ren'}`
              : `${row.childCount} linked child${row.childCount === 1 ? '' : 'ren'}`}
          >
            <Network class="h-3 w-3" />
            {row.isProblem ? 'Problem' : 'Tree'}
          </span>
        {/if}
      {/snippet}
      {#snippet emptyState()}
        <div class="flex flex-col items-center justify-center py-16 text-center">
          <div
            class="mb-4 flex size-16 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--surface-sunken)]"
          >
            <Briefcase class="size-8 text-[var(--text-tertiary)]" />
          </div>
          <h3 class="text-lg font-medium text-[var(--text-primary)]">No tickets found</h3>
          <p class="mt-1 text-sm text-[var(--text-secondary)]">
            Try adjusting your filters or create a new ticket
          </p>
        </div>
      {/snippet}
    </CrmTable>

    <!-- Pagination (only for list view) -->
    <Pagination
      page={pagination.page}
      limit={pagination.limit}
      total={pagination.total}
      onPageChange={handlePageChange}
      onLimitChange={handleLimitChange}
    />
  {:else}
    <TicketKanban
      data={kanbanData}
      loading={false}
      onStatusChange={handleKanbanStatusChange}
      onCardClick={handleKanbanCardClick}
    />
  {/if}
</div>

<BulkActionBar
  count={selectedIds.length}
  onClear={() => (selectedIds = [])}
  actions={[
    {
      label: 'Mark Closed',
      onClick: async () => {
        const today = new Date().toISOString().split('T')[0];
        await fetch('?/bulkUpdate', {
          method: 'POST',
          headers: { 'x-sveltekit-action': 'true' },
          body: new URLSearchParams({
            ids: JSON.stringify(selectedIds),
            fields: JSON.stringify({ status: 'Closed', closed_on: today })
          })
        });
        selectedIds = [];
        await invalidateAll();
        toast.success('Tickets marked closed');
      }
    },
    {
      label: 'Delete',
      variant: 'destructive',
      onClick: async () => {
        if (!confirm(`Delete ${selectedIds.length} ticket(s)?`)) return;
        await fetch('?/bulkDelete', {
          method: 'POST',
          headers: { 'x-sveltekit-action': 'true' },
          body: new URLSearchParams({ ids: JSON.stringify(selectedIds) })
        });
        selectedIds = [];
        await invalidateAll();
        toast.success('Tickets deleted');
      }
    }
  ]}
/>

<!-- Ticket create drawer (edit/view live on /tickets/[id]) -->
<CrmDrawer
  bind:open={drawer.detailOpen}
  onOpenChange={(open) => {
    if (!open) {
      drawer.closeAll();
      if (accountFromUrl) {
        clearUrlParams();
      }
    }
  }}
  data={drawerFormData}
  columns={drawerColumns}
  titleKey="subject"
  titlePlaceholder="Ticket title"
  headerLabel="New Ticket"
  onFieldChange={handleDrawerFieldChange}
  onClose={() => drawer.closeAll()}
  loading={drawer.loading}
  mode="create"
>
  {#snippet footerActions()}
    <Button variant="outline" onclick={() => drawer.closeAll()} disabled={isSubmitting}>
      Cancel
    </Button>
    <Button onclick={handleSave} disabled={isSubmitting}>
      {#if isSubmitting}
        <Loader2 class="mr-2 h-4 w-4 animate-spin" />
        Creating...
      {:else}
        Create Ticket
      {/if}
    </Button>
  {/snippet}
</CrmDrawer>

<!-- Hidden forms for server actions -->
<form
  method="POST"
  action="?/create"
  bind:this={createForm}
  use:enhance={createEnhanceHandler('Ticket created successfully')}
  class="hidden"
>
  <input type="hidden" name="title" value={formState.title} />
  <input type="hidden" name="description" value={formState.description} />
  <input type="hidden" name="accountId" value={formState.accountId} />
  <input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
  <input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
  <input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
  <input type="hidden" name="tags" value={JSON.stringify(formState.tags)} />
  <input type="hidden" name="priority" value={formState.priority} />
  <input type="hidden" name="ticketType" value={formState.ticketType} />
  <input type="hidden" name="dueDate" value={formState.dueDate} />
</form>

<!-- Hidden form for inline cell edits from the list table -->
<form
  method="POST"
  action="?/update"
  bind:this={updateForm}
  use:enhance={createEnhanceHandler('Ticket updated successfully')}
  class="hidden"
>
  <input type="hidden" name="ticketId" value={formState.ticketId} />
  <input type="hidden" name="title" value={formState.title} />
  <input type="hidden" name="description" value={formState.description} />
  <input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
  <input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
  <input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
  <input type="hidden" name="tags" value={JSON.stringify(formState.tags)} />
  <input type="hidden" name="priority" value={formState.priority} />
  <input type="hidden" name="ticketType" value={formState.ticketType} />
  <input type="hidden" name="status" value={formState.status} />
  <input type="hidden" name="dueDate" value={formState.dueDate} />
</form>

<form
  method="POST"
  action="?/moveTicket"
  bind:this={moveTicketForm}
  use:enhance={createEnhanceHandler('Ticket moved successfully')}
  class="hidden"
>
  <input type="hidden" name="ticketId" value={kanbanFormState.ticketId} />
  <input type="hidden" name="status" value={kanbanFormState.status} />
  <input type="hidden" name="stageId" value={kanbanFormState.stageId} />
  <input type="hidden" name="aboveTicketId" value={kanbanFormState.aboveTicketId} />
  <input type="hidden" name="belowTicketId" value={kanbanFormState.belowTicketId} />
</form>
