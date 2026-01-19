<script>
  import { enhance } from '$app/forms';
  import { invalidateAll, goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount, tick } from 'svelte';
  import { toast } from 'svelte-sonner';
  import {
    Plus,
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
    Loader2,
    Eye,
    Filter,
    List,
    Columns
  } from '@lucide/svelte';
  import { CaseKanban } from '$lib/components/ui/case-kanban';
  import { Button } from '$lib/components/ui/button/index.js';
  import { PageHeader } from '$lib/components/layout';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
  import { CrmTable } from '$lib/components/ui/crm-table';
  import { CrmDrawer } from '$lib/components/ui/crm-drawer';
  import { CommentSection } from '$lib/components/ui/comment-section';
  import { getCurrentUser } from '$lib/api.js';
  import {
    FilterBar,
    SearchInput,
    SelectFilter,
    DateRangeFilter,
    TagFilter
  } from '$lib/components/ui/filter';
  import { Pagination } from '$lib/components/ui/pagination';
  import {
    caseStatusOptions,
    caseTypeOptions,
    casePriorityOptions
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
    { key: 'subject', label: 'Case', type: 'text', width: 'w-[250px]', canHide: false },
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
      options: casePriorityOptions,
      width: 'w-28'
    },
    { key: 'status', label: 'Status', type: 'select', options: caseStatusOptions, width: 'w-28' },
    { key: 'caseType', label: 'Type', type: 'select', options: caseTypeOptions, width: 'w-28' },
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
  const STORAGE_KEY = 'cases-column-config';
  let visibleColumns = $state(columns.map((c) => c.key));
  let currentUser = $state(null);

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
    currentUser = getCurrentUser();
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
    caseType: '',
    status: 'New',
    closedOn: ''
  });

  // Track if drawer form has been modified
  let isDrawerDirty = $state(false);
  let isSubmitting = $state(false);

  /** @type {{ data: any }} */
  let { data } = $props();

  // Computed values
  let casesData = $derived(data.cases || []);
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

  // Drawer columns configuration (with icons and multiselect)
  // Account is only editable on create (and not when pre-filled from URL), read-only on edit
  const drawerColumns = $derived([
    { key: 'subject', label: 'Case Title', type: 'text' },
    // Account field: readonly when pre-filled from URL or in edit mode
    drawer.mode === 'create' && !accountFromUrl
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
      key: 'caseType',
      label: 'Type',
      type: 'select',
      icon: Tag,
      options: caseTypeOptions,
      emptyText: 'Select type'
    },
    {
      key: 'status',
      label: 'Status',
      type: 'select',
      icon: Circle,
      options: caseStatusOptions
    },
    {
      key: 'priority',
      label: 'Priority',
      type: 'select',
      icon: Flag,
      options: casePriorityOptions
    },
    {
      key: 'description',
      label: 'Description',
      type: 'textarea',
      icon: FileText,
      placeholder: 'Describe the case...',
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

  // Reset drawer form when case changes or drawer opens
  $effect(() => {
    if (drawer.detailOpen) {
      if (drawer.mode === 'create') {
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
          caseType: '',
          status: 'New',
          closedOn: ''
        };
      } else if (drawer.selected) {
        const caseItem = drawer.selected;
        drawerFormData = {
          subject: caseItem.subject || '',
          description: caseItem.description || '',
          accountId: caseItem.account?.id || '',
          accountName: caseItem.account?.name || '', // Read-only display
          assignedTo: (caseItem.assignedTo || []).map((/** @type {any} */ a) => a.id),
          contacts: (caseItem.contacts || []).map((/** @type {any} */ c) => c.id),
          teams: (caseItem.teams || []).map((/** @type {any} */ t) => t.id),
          tags: (caseItem.tags || []).map((/** @type {any} */ t) => t.id),
          priority: caseItem.priority || 'Normal',
          caseType: caseItem.caseType || '',
          status: caseItem.status || 'New',
          closedOn: caseItem.closedOn ? caseItem.closedOn.split('T')[0] : ''
        };
      }
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
    ...caseStatusOptions
  ]);

  // Priority options for filter dropdown
  const priorityFilterOptions = $derived([
    { value: '', label: 'All Priorities' },
    ...casePriorityOptions
  ]);

  // Type options for filter dropdown
  const typeFilterOptions = $derived([{ value: '', label: 'All Types' }, ...caseTypeOptions]);

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
    casesData.filter((/** @type {any} */ c) => openStatuses.includes(c.status)).length
  );
  const closedCount = $derived(
    casesData.filter((/** @type {any} */ c) => c.status === 'Closed').length
  );

  // Status chip filter state (client-side quick filter on top of server filters)
  let statusChipFilter = $state('ALL');

  // Filter panel expansion state
  let filtersExpanded = $state(false);

  // Filtered cases - server already applies main filters, just apply status chip
  const filteredCases = $derived.by(() => {
    let filtered = casesData;
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
  let deleteForm;
  /** @type {HTMLFormElement} */
  let closeForm;
  /** @type {HTMLFormElement} */
  let reopenForm;
  /** @type {HTMLFormElement} */
  let moveCaseForm;

  // Kanban form state for drag-drop
  let kanbanFormState = $state({
    caseId: '',
    status: '',
    stageId: '',
    aboveCaseId: '',
    belowCaseId: ''
  });

  // Form data state
  let formState = $state({
    title: '',
    description: '',
    accountId: '',
    assignedTo: /** @type {string[]} */ ([]),
    contacts: /** @type {string[]} */ ([]),
    teams: /** @type {string[]} */ ([]),
    tags: /** @type {string[]} */ ([]),
    priority: 'Normal',
    caseType: '',
    status: 'New',
    dueDate: '',
    caseId: ''
  });

  /**
   * Handle save from drawer
   */
  async function handleSave() {
    if (!drawerFormData.subject?.trim()) {
      toast.error('Case title is required');
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
    formState.caseType = drawerFormData.caseType || '';
    formState.status = drawerFormData.status || 'New';
    formState.dueDate = drawerFormData.closedOn || '';

    await tick();

    if (drawer.mode === 'edit' && drawer.selected) {
      formState.caseId = drawer.selected.id;
      await tick();
      updateForm.requestSubmit();
    } else {
      createForm.requestSubmit();
    }
  }

  /**
   * Handle case delete
   */
  async function handleDelete() {
    if (!drawer.selected) return;
    if (!confirm(`Are you sure you want to delete "${drawer.selected.subject}"?`)) return;

    formState.caseId = drawer.selected.id;
    await tick();
    deleteForm.requestSubmit();
  }

  /**
   * Handle case close
   */
  async function handleClose() {
    if (!drawer.selected) return;

    formState.caseId = drawer.selected.id;
    await tick();
    closeForm.requestSubmit();
  }

  /**
   * Handle case reopen
   */
  async function handleReopen() {
    if (!drawer.selected) return;

    formState.caseId = drawer.selected.id;
    await tick();
    reopenForm.requestSubmit();
  }

  /**
   * Create enhance handler for form actions
   * @param {string} successMessage
   * @param {boolean} closeDetailDrawer
   */
  function createEnhanceHandler(successMessage, closeDetailDrawer = false) {
    return () => {
      return async ({ result }) => {
        isSubmitting = false;
        if (result.type === 'success') {
          toast.success(successMessage);
          isDrawerDirty = false;
          if (closeDetailDrawer) {
            drawer.closeDetail();
          } else {
            drawer.closeAll();
          }
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
   * Convert case to form state for inline editing
   * @param {any} caseItem
   */
  function caseToFormState(caseItem) {
    return {
      caseId: caseItem.id,
      title: caseItem.subject || '',
      description: caseItem.description || '',
      accountId: caseItem.account?.id || '',
      assignedTo: (caseItem.assignedTo || []).map((/** @type {any} */ a) => a.id),
      contacts: (caseItem.contacts || []).map((/** @type {any} */ c) => c.id),
      teams: (caseItem.teams || []).map((/** @type {any} */ t) => t.id),
      tags: (caseItem.tags || []).map((/** @type {any} */ t) => t.id),
      priority: caseItem.priority || 'Normal',
      caseType: caseItem.caseType || '',
      status: caseItem.status || 'New',
      dueDate: caseItem.closedOn ? caseItem.closedOn.split('T')[0] : ''
    };
  }

  /**
   * Handle inline cell edits - persists to API
   * @param {any} caseItem
   * @param {string} field
   * @param {any} value
   */
  async function handleQuickEdit(caseItem, field, value) {
    // Map frontend field names to form state field names
    const fieldMapping = {
      subject: 'title',
      caseType: 'caseType',
      priority: 'priority',
      status: 'status',
      closedOn: 'dueDate'
    };

    // Populate form state with current case data
    const currentState = caseToFormState(caseItem);

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
   * @param {string} caseId
   * @param {string} targetColumnId
   * @param {string} _columnId
   */
  async function handleKanbanStatusChange(caseId, targetColumnId, _columnId) {
    kanbanFormState.caseId = caseId;
    kanbanFormState.aboveCaseId = '';
    kanbanFormState.belowCaseId = '';

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
    moveCaseForm.requestSubmit();
  }

  /**
   * Handle kanban card click (open drawer)
   * @param {any} caseItem
   */
  function handleKanbanCardClick(caseItem) {
    // Find full case data and open drawer
    const fullCase = casesData.find((c) => c.id === caseItem.id);
    if (fullCase) {
      drawer.openDetail(fullCase);
    } else {
      // Use kanban card data directly
      drawer.openDetail({
        id: caseItem.id,
        subject: caseItem.name,
        status: caseItem.status,
        priority: caseItem.priority,
        caseType: caseItem.case_type,
        account: caseItem.account_name ? { name: caseItem.account_name } : null,
        assignedTo: caseItem.assigned_to || []
      });
    }
  }
</script>

<svelte:head>
  <title>Cases - BottleCRM</title>
</svelte:head>

<PageHeader title="Cases" subtitle="{filteredCases.length} of {casesData.length} cases">
  {#snippet actions()}
    <div class="flex items-center gap-2">
      <!-- Status Filter Chips -->
      <div class="flex gap-1">
        <button
          type="button"
          onclick={() => (statusChipFilter = 'ALL')}
          class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
          'ALL'
            ? 'bg-[var(--color-primary-default)] text-white'
            : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]'}"
        >
          All
          <span
            class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'ALL'
              ? 'bg-[var(--color-primary-dark)] text-white/90'
              : 'bg-[var(--border-default)] text-[var(--text-tertiary)]'}"
          >
            {casesData.length}
          </span>
        </button>
        <button
          type="button"
          onclick={() => (statusChipFilter = 'open')}
          class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
          'open'
            ? 'bg-[var(--stage-qualified)] text-white'
            : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]'}"
        >
          Open
          <span
            class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'open'
              ? 'bg-black/20 text-white/90'
              : 'bg-[var(--border-default)] text-[var(--text-tertiary)]'}"
          >
            {openCount}
          </span>
        </button>
        <button
          type="button"
          onclick={() => (statusChipFilter = 'closed')}
          class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
          'closed'
            ? 'bg-[var(--text-secondary)] text-white'
            : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]'}"
        >
          Closed
          <span
            class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'closed'
              ? 'bg-[var(--text-tertiary)] text-white/90'
              : 'bg-[var(--border-default)] text-[var(--text-tertiary)]'}"
          >
            {closedCount}
          </span>
        </button>
      </div>

      <div class="bg-border mx-1 h-6 w-px"></div>

      <!-- View Mode Toggle -->
      <div class="border-input bg-background inline-flex rounded-lg border p-1">
        <Button
          variant={viewMode === 'list' ? 'secondary' : 'ghost'}
          size="sm"
          onclick={() => updateViewMode('list')}
          class="h-8 px-3"
        >
          <List class="mr-1.5 h-4 w-4" />
          List
        </Button>
        <Button
          variant={viewMode === 'kanban' ? 'secondary' : 'ghost'}
          size="sm"
          onclick={() => updateViewMode('kanban')}
          class="h-8 px-3"
        >
          <Columns class="mr-1.5 h-4 w-4" />
          Board
        </Button>
      </div>

      <div class="bg-border mx-1 h-6 w-px"></div>

      <!-- Filter Toggle Button -->
      <Button
        variant={filtersExpanded ? 'secondary' : 'outline'}
        size="sm"
        class="gap-2"
        onclick={() => (filtersExpanded = !filtersExpanded)}
      >
        <Filter class="h-4 w-4" />
        Filters
        {#if activeFiltersCount > 0}
          <span
            class="rounded-full bg-[var(--color-primary-light)] px-1.5 py-0.5 text-xs font-medium text-[var(--color-primary-default)]"
          >
            {activeFiltersCount}
          </span>
        {/if}
      </Button>

      <DropdownMenu.Root>
        <DropdownMenu.Trigger>
          {#snippet child({ props })}
            <Button {...props} variant="outline" size="sm" class="gap-2">
              <Eye class="h-4 w-4" />
              Columns
              {#if columnCounts.visible < columnCounts.total}
                <span
                  class="rounded-full bg-[var(--color-primary-light)] px-1.5 py-0.5 text-xs font-medium text-[var(--color-primary-default)]"
                >
                  {columnCounts.visible}/{columnCounts.total}
                </span>
              {/if}
            </Button>
          {/snippet}
        </DropdownMenu.Trigger>
        <DropdownMenu.Content align="end" class="w-48">
          <DropdownMenu.Label>Toggle columns</DropdownMenu.Label>
          <DropdownMenu.Separator />
          {#each columns as column (column.key)}
            <DropdownMenu.CheckboxItem
              class=""
              checked={isColumnVisible(column.key)}
              onCheckedChange={() => toggleColumn(column.key)}
              disabled={column.canHide === false}
            >
              {column.label}
            </DropdownMenu.CheckboxItem>
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Root>

      <Button onclick={drawer.openCreate}>
        <Plus class="mr-2 h-4 w-4" />
        New Case
      </Button>
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
      placeholder="Search cases..."
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
      data={filteredCases}
      {columns}
      bind:visibleColumns
      onRowChange={handleRowChange}
      onRowClick={(row) => drawer.openDetail(row)}
    >
      {#snippet emptyState()}
        <div class="flex flex-col items-center justify-center py-16 text-center">
          <div class="mb-4 flex size-16 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--surface-sunken)]">
            <Briefcase class="size-8 text-[var(--text-tertiary)]" />
          </div>
          <h3 class="text-[var(--text-primary)] text-lg font-medium">No cases found</h3>
          <p class="text-[var(--text-secondary)] mt-1 text-sm">Try adjusting your filters or create a new case</p>
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
    <CaseKanban
      data={kanbanData}
      loading={false}
      onStatusChange={handleKanbanStatusChange}
      onCardClick={handleKanbanCardClick}
    />
  {/if}
</div>

<!-- Case Drawer -->
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
  titlePlaceholder="Case title"
  headerLabel={drawer.mode === 'create' ? 'New Case' : 'Case'}
  onFieldChange={handleDrawerFieldChange}
  onDelete={handleDelete}
  onClose={() => drawer.closeAll()}
  loading={drawer.loading}
  mode={drawer.mode === 'create' ? 'create' : 'view'}
>
  {#snippet activitySection()}
    {#if drawer.mode !== 'create' && drawer.selected}
      <CommentSection
        entityId={drawer.selected.id}
        entityType="cases"
        initialComments={drawer.selected.comments || []}
        currentUserEmail={currentUser?.email}
        isAdmin={currentUser?.organizations?.some(o => o.role === 'ADMIN')}
      />
    {/if}
  {/snippet}

  {#snippet footerActions()}
    {#if drawer.mode !== 'create' && drawer.selected}
      {#if drawerFormData.status === 'Closed'}
        <Button variant="outline" onclick={handleReopen} disabled={isSubmitting}>Reopen</Button>
      {:else}
        <Button variant="outline" onclick={handleClose} disabled={isSubmitting}>Close Case</Button>
      {/if}
    {/if}
    <Button variant="outline" onclick={() => drawer.closeAll()} disabled={isSubmitting}>
      Cancel
    </Button>
    {#if isDrawerDirty || drawer.mode === 'create'}
      <Button onclick={handleSave} disabled={isSubmitting}>
        {#if isSubmitting}
          <Loader2 class="mr-2 h-4 w-4 animate-spin" />
          {drawer.mode === 'create' ? 'Creating...' : 'Saving...'}
        {:else}
          {drawer.mode === 'create' ? 'Create Case' : 'Save Changes'}
        {/if}
      </Button>
    {/if}
  {/snippet}
</CrmDrawer>

<!-- Hidden forms for server actions -->
<form
  method="POST"
  action="?/create"
  bind:this={createForm}
  use:enhance={createEnhanceHandler('Case created successfully')}
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
  <input type="hidden" name="caseType" value={formState.caseType} />
  <input type="hidden" name="dueDate" value={formState.dueDate} />
</form>

<form
  method="POST"
  action="?/update"
  bind:this={updateForm}
  use:enhance={createEnhanceHandler('Case updated successfully')}
  class="hidden"
>
  <input type="hidden" name="caseId" value={formState.caseId} />
  <input type="hidden" name="title" value={formState.title} />
  <input type="hidden" name="description" value={formState.description} />
  <input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
  <input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
  <input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
  <input type="hidden" name="tags" value={JSON.stringify(formState.tags)} />
  <input type="hidden" name="priority" value={formState.priority} />
  <input type="hidden" name="caseType" value={formState.caseType} />
  <input type="hidden" name="status" value={formState.status} />
  <input type="hidden" name="dueDate" value={formState.dueDate} />
</form>

<form
  method="POST"
  action="?/delete"
  bind:this={deleteForm}
  use:enhance={createEnhanceHandler('Case deleted successfully', true)}
  class="hidden"
>
  <input type="hidden" name="caseId" value={formState.caseId} />
</form>

<form
  method="POST"
  action="?/close"
  bind:this={closeForm}
  use:enhance={createEnhanceHandler('Case closed successfully')}
  class="hidden"
>
  <input type="hidden" name="caseId" value={formState.caseId} />
</form>

<form
  method="POST"
  action="?/reopen"
  bind:this={reopenForm}
  use:enhance={createEnhanceHandler('Case reopened successfully')}
  class="hidden"
>
  <input type="hidden" name="caseId" value={formState.caseId} />
</form>

<form
  method="POST"
  action="?/moveCase"
  bind:this={moveCaseForm}
  use:enhance={createEnhanceHandler('Case moved successfully', false)}
  class="hidden"
>
  <input type="hidden" name="caseId" value={kanbanFormState.caseId} />
  <input type="hidden" name="status" value={kanbanFormState.status} />
  <input type="hidden" name="stageId" value={kanbanFormState.stageId} />
  <input type="hidden" name="aboveCaseId" value={kanbanFormState.aboveCaseId} />
  <input type="hidden" name="belowCaseId" value={kanbanFormState.belowCaseId} />
</form>
