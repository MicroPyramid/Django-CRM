<script>
  import { invalidateAll, goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount, tick } from 'svelte';
  import { toast } from 'svelte-sonner';
  import {
    Plus,
    Eye,
    Building2,
    Target,
    DollarSign,
    Calendar,
    Percent,
    User,
    Users,
    Briefcase,
    Globe,
    FileText,
    Trophy,
    XCircle,
    Banknote,
    Contact,
    Tags,
    Filter,
    Package,
    Trash2,
    Receipt,
    Clock
  } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
  import { CrmDrawer } from '$lib/components/ui/crm-drawer';
  import { CommentSection } from '$lib/components/ui/comment-section';
  import { getCurrentUser } from '$lib/api.js';
  import { CrmTable } from '$lib/components/ui/crm-table';
  import {
    FilterBar,
    SearchInput,
    SelectFilter,
    DateRangeFilter,
    TagFilter
  } from '$lib/components/ui/filter';
  import { Pagination } from '$lib/components/ui/pagination';
  import { Input } from '$lib/components/ui/input/index.js';
  import * as Select from '$lib/components/ui/select/index.js';
  import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
  import { formatCurrency, formatRelativeDate } from '$lib/utils/formatting.js';
  import {
    OPPORTUNITY_STAGES as stages,
    OPPORTUNITY_TYPES,
    OPPORTUNITY_SOURCES,
    CURRENCY_CODES
  } from '$lib/constants/filters.js';
  import { orgSettings } from '$lib/stores/org.js';

  const STORAGE_KEY = 'opportunities-crm-columns';

  // Account from URL param (for quick action from account page)
  let accountFromUrl = $state(false);
  let accountName = $state('');
  let accountIdFromUrl = $state('');

  // Stage options with colors - using design system tokens
  const stageOptions = [
    {
      value: 'PROSPECTING',
      label: 'Prospecting',
      color: 'bg-[var(--stage-new-bg)] text-[var(--stage-new)] dark:bg-[var(--stage-new)]/15'
    },
    {
      value: 'QUALIFICATION',
      label: 'Qualification',
      color:
        'bg-[var(--stage-qualified-bg)] text-[var(--stage-qualified)] dark:bg-[var(--stage-qualified)]/15'
    },
    {
      value: 'PROPOSAL',
      label: 'Proposal',
      color:
        'bg-[var(--stage-proposal-bg)] text-[var(--stage-proposal)] dark:bg-[var(--stage-proposal)]/15'
    },
    {
      value: 'NEGOTIATION',
      label: 'Negotiation',
      color:
        'bg-[var(--stage-negotiation-bg)] text-[var(--stage-negotiation)] dark:bg-[var(--stage-negotiation)]/15'
    },
    {
      value: 'CLOSED_WON',
      label: 'Won',
      color: 'bg-[var(--stage-won-bg)] text-[var(--stage-won)] dark:bg-[var(--stage-won)]/15'
    },
    {
      value: 'CLOSED_LOST',
      label: 'Lost',
      color: 'bg-[var(--stage-lost-bg)] text-[var(--stage-lost)] dark:bg-[var(--stage-lost)]/15'
    }
  ];

  // Type options - using design system tokens
  const typeOptions = OPPORTUNITY_TYPES.map((t) => ({
    value: t.value,
    label: t.label,
    color: 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]'
  }));

  // Source options - using design system tokens
  const sourceOptions = OPPORTUNITY_SOURCES.map((s) => ({
    value: s.value,
    label: s.label,
    color:
      'bg-[var(--color-primary-light)] text-[var(--color-primary-default)] dark:bg-[var(--color-primary-default)]/15'
  }));

  // Currency options - using design system tokens
  const currencyOptions = CURRENCY_CODES.filter((c) => c.value).map((c) => ({
    value: c.value,
    label: c.label,
    color: 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]'
  }));

  /**
   * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
   * @typedef {{ key: string, label: string, type?: ColumnType, width?: string, editable?: boolean, canHide?: boolean, getValue?: (row: any) => any, emptyText?: string, relationIcon?: string, options?: any[], format?: (value: any) => string, cellClass?: (row: any) => string }} ColumnDef
   */

  /** @type {ColumnDef[]} */
  const columns = [
    {
      key: 'name',
      label: 'Opportunity',
      type: 'text',
      width: 'w-48',
      canHide: false,
      emptyText: 'Untitled'
    },
    {
      key: 'account',
      label: 'Account',
      type: 'relation',
      width: 'w-40',
      relationIcon: 'building',
      editable: false,
      getValue: (row) => row.account?.name,
      emptyText: ''
    },
    {
      key: 'amount',
      label: 'Amount',
      type: 'number',
      width: 'w-32',
      format: (value, row) => formatAmount(value, row?.currency)
    },
    { key: 'stage', label: 'Stage', type: 'select', options: stageOptions, width: 'w-32' },
    { key: 'closedOn', label: 'Close Date', type: 'date', width: 'w-36' },
    {
      key: 'assignedTo',
      label: 'Assigned To',
      type: 'relation',
      width: 'w-40',
      relationIcon: 'user',
      editable: false,
      getValue: (row) => {
        const users = row.assignedTo || [];
        if (users.length === 0) return null;
        if (users.length === 1) return users[0].name;
        return `${users[0].name} +${users.length - 1}`;
      },
      emptyText: ''
    },
    // Hidden by default
    {
      key: 'probability',
      label: 'Probability',
      type: 'number',
      width: 'w-28',
      canHide: true,
      format: (value) => (value != null ? `${value}%` : '-')
    },
    {
      key: 'opportunityType',
      label: 'Type',
      type: 'select',
      options: typeOptions,
      width: 'w-32',
      canHide: true
    },
    {
      key: 'daysInStage',
      label: 'Age',
      type: 'text',
      width: 'w-20',
      canHide: true,
      editable: false,
      getValue: (row) => {
        if (['CLOSED_WON', 'CLOSED_LOST'].includes(row.stage)) return '-';
        return `${row.daysInStage ?? 0}d`;
      },
      format: (value, row) => {
        if (['CLOSED_WON', 'CLOSED_LOST'].includes(row?.stage)) return '-';
        return `${row?.daysInStage ?? 0}d`;
      },
      cellClass: (row) => {
        if (row.agingStatus === 'red') return 'text-red-600 font-semibold';
        if (row.agingStatus === 'yellow') return 'text-amber-500 font-medium';
        return 'text-green-600';
      }
    }
  ];

  // Default visible columns (excludes probability and type)
  const DEFAULT_VISIBLE_COLUMNS = ['name', 'account', 'amount', 'stage', 'closedOn', 'assignedTo'];

  /** @type {{ data: any }} */
  let { data } = $props();

  // Options for form
  const formOptions = $derived({
    accounts: data.options?.accounts || [],
    contacts: data.options?.contacts || [],
    tags: data.options?.tags || [],
    users: data.options?.users || [],
    teams: data.options?.teams || [],
    products: data.options?.products || []
  });

  // Product options for line items dropdown
  const productOptions = $derived(
    formOptions.products.map((p) => ({
      value: p.id,
      label: p.name,
      price: p.price,
      sku: p.sku
    }))
  );

  // Account options for select field
  const accountOptions = $derived(
    formOptions.accounts.map((a) => ({
      value: a.id,
      label: a.name
    }))
  );

  // Contact options for multiselect (uses id/name format)
  const contactOptions = $derived(
    formOptions.contacts.map((c) => ({
      id: c.id,
      name: c.name || c.email,
      email: c.email
    }))
  );

  // User options for assignedTo multiselect (uses id/name format)
  const userOptions = $derived(
    formOptions.users.map((u) => ({
      id: u.id,
      name: u.name || u.email,
      email: u.email
    }))
  );

  // Team options for teams multiselect (uses id/name format)
  const teamOptions = $derived(
    formOptions.teams.map((t) => ({
      id: t.id,
      name: t.name
    }))
  );

  // Tag options for tags multiselect (uses id/name format)
  const tagOptions = $derived(
    formOptions.tags.map((t) => ({
      id: t.id,
      name: t.name
    }))
  );

  /**
   * Lookup account name from server-provided accounts list
   * @param {string} id
   */
  function fetchAccountName(id) {
    const account = formOptions.accounts.find((a) => a.id === id);
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

  // Drawer column definitions for CrmDrawer (derived since some options come from data)
  const drawerColumns = $derived([
    { key: 'name', label: 'Name', type: 'text' },
    // Account field: readonly when pre-filled from URL, select otherwise
    accountFromUrl
      ? {
          key: 'account',
          label: 'Account',
          type: 'readonly',
          icon: Building2,
          getValue: () => accountName || 'Loading...'
        }
      : {
          key: 'account',
          label: 'Account',
          type: 'select',
          icon: Building2,
          options: accountOptions,
          placeholder: 'Select account'
        },
    {
      key: 'stage',
      label: 'Stage',
      type: 'select',
      icon: Target,
      options: stageOptions
    },
    {
      key: 'opportunityType',
      label: 'Type',
      type: 'select',
      icon: Briefcase,
      options: typeOptions,
      placeholder: 'Select type'
    },
    {
      key: 'amount',
      label: 'Amount',
      type: 'number',
      icon: DollarSign,
      placeholder: '0'
    },
    {
      key: 'currency',
      label: 'Currency',
      type: 'select',
      icon: Banknote,
      options: currencyOptions,
      placeholder: 'Select currency'
    },
    {
      key: 'probability',
      label: 'Probability',
      type: 'number',
      icon: Percent,
      placeholder: '0'
    },
    {
      key: 'closedOn',
      label: 'Close Date',
      type: 'date',
      icon: Calendar
    },
    {
      key: 'leadSource',
      label: 'Lead Source',
      type: 'select',
      icon: Globe,
      options: sourceOptions,
      placeholder: 'Select source'
    },
    {
      key: 'contacts',
      label: 'Contacts',
      type: 'multiselect',
      icon: Contact,
      options: contactOptions,
      placeholder: 'Select contacts'
    },
    {
      key: 'assignedTo',
      label: 'Assigned To',
      type: 'multiselect',
      icon: Users,
      options: userOptions,
      placeholder: 'Select users'
    },
    {
      key: 'teams',
      label: 'Teams',
      type: 'multiselect',
      icon: Users,
      options: teamOptions,
      placeholder: 'Select teams'
    },
    {
      key: 'tags',
      label: 'Tags',
      type: 'multiselect',
      icon: Tags,
      options: tagOptions,
      placeholder: 'Select tags'
    },
    {
      key: 'description',
      label: 'Notes',
      type: 'textarea',
      icon: FileText,
      placeholder: 'Add notes...'
    }
  ]);

  // URL-based filter state from server
  const filters = $derived(data.filters || {});

  // Stage options for filter dropdown (includes ALL option)
  const stageFilterOptions = $derived([{ value: '', label: 'All Stages' }, ...stageOptions]);

  // Count active filters (excluding stage since it's handled via chips in header)
  const activeFiltersCount = $derived.by(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.account) count++;
    if (filters.assigned_to?.length > 0) count++;
    if (filters.tags?.length > 0) count++;
    if (filters.created_at_gte || filters.created_at_lte) count++;
    if (filters.closed_on_gte || filters.closed_on_lte) count++;
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
      'stage',
      'account',
      'assigned_to',
      'tags',
      'created_at_gte',
      'created_at_lte',
      'closed_on_gte',
      'closed_on_lte',
      'rotten'
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

  // Column visibility state - use defaults (excludes probability and type)
  let visibleColumns = $state([...DEFAULT_VISIBLE_COLUMNS]);

  // Drawer state
  let drawerOpen = $state(false);
  /** @type {'view' | 'create'} */
  let drawerMode = $state('view');
  /** @type {string | null} */
  let selectedRowId = $state(null);
  let isLoading = $state(false);

  // Empty opportunity template for create mode
  const emptyOpportunity = {
    name: '',
    account: '',
    stage: 'PROSPECTING',
    opportunityType: '',
    amount: 0,
    currency: '',
    probability: 50,
    closedOn: '',
    leadSource: '',
    contacts: [],
    assignedTo: [],
    teams: [],
    tags: [],
    description: ''
  };

  // Drawer form data - mutable copy for editing
  let drawerFormData = $state({ ...emptyOpportunity });

  // Reset form data when opportunity changes or drawer opens
  $effect(() => {
    if (drawerOpen) {
      if (drawerMode === 'create') {
        drawerFormData = {
          ...emptyOpportunity,
          currency: $orgSettings.default_currency || 'USD',
          account: accountIdFromUrl || '' // Preserve account from URL if present
        };
      } else if (selectedRow) {
        // Extract IDs for multiselect fields and account select
        drawerFormData = {
          ...selectedRow,
          // Account ID for select
          account: selectedRow.account?.id || '',
          // Currency with fallback to org default
          currency: selectedRow.currency || $orgSettings.default_currency || 'USD',
          // Extract IDs for multiselect fields
          contacts: (selectedRow.contacts || []).map((/** @type {any} */ c) => c.id),
          assignedTo: (selectedRow.assignedTo || []).map((/** @type {any} */ u) => u.id),
          teams: (selectedRow.teams || []).map((/** @type {any} */ t) => t.id),
          tags: (selectedRow.tags || []).map((/** @type {any} */ t) => t.id)
        };
      }
    }
  });

  // Computed values - opportunities are already filtered server-side
  const opportunities = $derived(data.opportunities || []);
  const pagination = $derived(data.pagination || { page: 1, limit: 10, total: 0, totalPages: 0 });
  const stats = $derived(data.stats || { total: 0, totalValue: 0, wonValue: 0, pipeline: 0 });

  // Status chip filter for quick filtering (client-side on top of server filters)
  let statusChipFilter = $state('ALL');

  // Filter panel expansion state
  let filtersExpanded = $state(false);

  // Status stages for filtering
  const openStages = ['PROSPECTING', 'QUALIFICATION', 'PROPOSAL', 'NEGOTIATION'];

  // Apply only status chip filter (all other filters are server-side)
  const filteredOpportunities = $derived.by(() => {
    return opportunities.filter((/** @type {any} */ opp) => {
      // Apply status chip filter
      if (statusChipFilter === 'open') {
        return openStages.includes(opp.stage);
      } else if (statusChipFilter === 'won') {
        return opp.stage === 'CLOSED_WON';
      } else if (statusChipFilter === 'lost') {
        return opp.stage === 'CLOSED_LOST';
      } else if (statusChipFilter === 'stale') {
        return opp.agingStatus === 'red';
      }
      return true;
    });
  });

  // Status counts for filter chips
  const openCount = $derived(
    opportunities.filter((/** @type {any} */ o) => openStages.includes(o.stage)).length
  );
  const wonCount = $derived(
    opportunities.filter((/** @type {any} */ o) => o.stage === 'CLOSED_WON').length
  );
  const lostCount = $derived(
    opportunities.filter((/** @type {any} */ o) => o.stage === 'CLOSED_LOST').length
  );
  const staleCount = $derived(
    opportunities.filter((/** @type {any} */ o) => o.agingStatus === 'red').length
  );

  let currentUser = $state(null);

  // Load column visibility from localStorage
  onMount(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        visibleColumns = JSON.parse(saved);
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

  // URL sync for accountId and action params (quick action from account page)
  $effect(() => {
    const action = $page.url.searchParams.get('action');
    const accountIdParam = $page.url.searchParams.get('accountId');

    if (action === 'create' && !drawerOpen) {
      // Handle account pre-fill from URL BEFORE opening drawer
      if (accountIdParam) {
        accountIdFromUrl = accountIdParam;
        accountFromUrl = true;
        fetchAccountName(accountIdParam);
      }

      openCreate();

      // Set account in form data after drawer opens
      if (accountIdParam) {
        drawerFormData.account = accountIdParam;
      }
    }
  });

  /**
   * @param {string} key
   */
  function toggleColumn(key) {
    const col = columns.find((c) => c.key === key);
    if (col?.canHide === false) return;

    if (visibleColumns.includes(key)) {
      visibleColumns = visibleColumns.filter((k) => k !== key);
    } else {
      visibleColumns = [...visibleColumns, key];
    }
  }

  /**
   * Handle row change from NotionTable (inline editing)
   * @param {any} row
   * @param {string} field
   * @param {any} value
   */
  async function handleRowChange(row, field, value) {
    const column = columns.find((c) => c.key === field);
    await saveFieldValue(row.id, field, value, column?.type);
  }

  /**
   * @param {string} rowId
   * @param {string} field
   * @param {any} value
   * @param {string} [fieldType]
   */
  async function saveFieldValue(rowId, field, value, fieldType) {
    try {
      const form = new FormData();
      form.append('opportunityId', rowId);

      // Map field names to API field names
      const fieldMapping = /** @type {Record<string, string>} */ ({
        name: 'name',
        account: 'accountId',
        amount: 'amount',
        currency: 'currency',
        probability: 'probability',
        stage: 'stage',
        opportunityType: 'opportunityType',
        closedOn: 'closedOn',
        leadSource: 'leadSource',
        description: 'description'
      });

      // Multi-select fields need special handling
      const multiSelectFields = ['contacts', 'assignedTo', 'teams', 'tags'];

      if (multiSelectFields.includes(field)) {
        // Send as JSON array
        form.append(field, JSON.stringify(Array.isArray(value) ? value : []));
      } else {
        const apiField = fieldMapping[field];
        if (apiField) {
          // Convert value based on type
          let apiValue = value;
          if (fieldType === 'number') {
            apiValue = parseFloat(value) || 0;
          }
          form.append(apiField, apiValue?.toString() || '');
        }
      }

      // Need to send required fields too
      const opp = filteredOpportunities.find((/** @type {any} */ o) => o.id === rowId);
      if (opp) {
        if (field !== 'name') form.append('name', opp.name || '');
        if (field !== 'stage') form.append('stage', opp.stage || 'PROSPECTING');
      }

      const response = await fetch('?/update', { method: 'POST', body: form });
      const result = await response.json();

      if (result.type === 'success' || result.data?.success) {
        toast.success('Changes saved');
        await invalidateAll();
      } else {
        toast.error(result.data?.message || 'Failed to save changes');
      }
    } catch (err) {
      console.error('Error saving field:', err);
      toast.error('Failed to save changes');
    }
  }

  /**
   * @param {number | null} value
   * @param {string} [currency='USD']
   */
  function formatAmount(value, currency = 'USD') {
    if (!value) return '-';
    return formatCurrency(value, currency || 'USD');
  }

  /**
   * @param {string | null} dateStr
   */
  function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  }

  /**
   * @param {string} value
   * @param {{ value: string, label: string, color: string }[]} options
   */
  function getOptionStyle(value, options) {
    const option = options.find((o) => o.value === value);
    return option?.color ?? 'bg-gray-100 text-gray-600';
  }

  /**
   * @param {string} value
   * @param {{ value: string, label: string, color: string }[]} options
   */
  function getOptionLabel(value, options) {
    const option = options.find((o) => o.value === value);
    return option?.label ?? value;
  }

  // Drawer functions
  /**
   * @param {string} rowId
   */
  function openDrawer(rowId) {
    selectedRowId = rowId;
    drawerMode = 'view';
    drawerOpen = true;
  }

  function openCreate() {
    selectedRowId = null;
    drawerMode = 'create';
    drawerOpen = true;
  }

  function closeDrawer() {
    drawerOpen = false;
    selectedRowId = null;
    // Clear account URL params if they were set
    if (accountFromUrl) {
      clearUrlParams();
    }
  }

  /**
   * Handle field change from CrmDrawer - just updates local state
   * @param {string} field
   * @param {any} value
   */
  function handleDrawerFieldChange(field, value) {
    // Update local form data only - no auto-save
    drawerFormData = { ...drawerFormData, [field]: value };
  }

  /**
   * Handle save for view/edit mode
   */
  async function handleDrawerUpdate() {
    if (drawerMode !== 'view' || !selectedRowId) return;

    isLoading = true;
    try {
      const form = new FormData();
      form.append('opportunityId', selectedRowId);
      form.append('name', drawerFormData.name || 'Opportunity');
      form.append('stage', drawerFormData.stage || 'PROSPECTING');
      form.append('amount', drawerFormData.amount?.toString() || '0');
      form.append('probability', drawerFormData.probability?.toString() || '50');
      if (drawerFormData.account) {
        form.append('accountId', drawerFormData.account);
      }
      if (drawerFormData.opportunityType) {
        form.append('opportunityType', drawerFormData.opportunityType);
      }
      if (drawerFormData.currency) {
        form.append('currency', drawerFormData.currency);
      }
      if (drawerFormData.closedOn) {
        form.append('closedOn', drawerFormData.closedOn);
      }
      if (drawerFormData.leadSource) {
        form.append('leadSource', drawerFormData.leadSource);
      }
      if (drawerFormData.description) {
        form.append('description', drawerFormData.description);
      }
      // Multi-select fields - send as JSON arrays
      form.append('contacts', JSON.stringify(drawerFormData.contacts || []));
      form.append('assignedTo', JSON.stringify(drawerFormData.assignedTo || []));
      form.append('teams', JSON.stringify(drawerFormData.teams || []));
      form.append('tags', JSON.stringify(drawerFormData.tags || []));

      const response = await fetch('?/update', { method: 'POST', body: form });
      const result = await response.json();

      if (result.type === 'success' || result.data?.success) {
        toast.success('Opportunity updated');
        closeDrawer();
        await invalidateAll();
      } else {
        toast.error(result.data?.message || 'Failed to update opportunity');
      }
    } catch (err) {
      console.error('Update error:', err);
      toast.error('An error occurred');
    } finally {
      isLoading = false;
    }
  }

  /**
   * Handle save for create mode
   */
  async function handleDrawerSave() {
    if (drawerMode !== 'create') return;

    isLoading = true;
    try {
      const form = new FormData();
      form.append('name', drawerFormData.name || 'New Opportunity');
      form.append('stage', drawerFormData.stage || 'PROSPECTING');
      form.append('amount', drawerFormData.amount?.toString() || '0');
      form.append('probability', drawerFormData.probability?.toString() || '50');
      // Use drawerFormData.account or fall back to accountIdFromUrl
      const accountId = drawerFormData.account || accountIdFromUrl;
      if (accountId) {
        form.append('accountId', accountId);
      }
      if (drawerFormData.opportunityType) {
        form.append('opportunityType', drawerFormData.opportunityType);
      }
      if (drawerFormData.currency) {
        form.append('currency', drawerFormData.currency);
      }
      if (drawerFormData.closedOn) {
        form.append('closedOn', drawerFormData.closedOn);
      }
      if (drawerFormData.leadSource) {
        form.append('leadSource', drawerFormData.leadSource);
      }
      if (drawerFormData.description) {
        form.append('description', drawerFormData.description);
      }
      // Multi-select fields - send as JSON arrays
      if (drawerFormData.contacts?.length > 0) {
        form.append('contacts', JSON.stringify(drawerFormData.contacts));
      }
      if (drawerFormData.assignedTo?.length > 0) {
        form.append('assignedTo', JSON.stringify(drawerFormData.assignedTo));
      }
      if (drawerFormData.teams?.length > 0) {
        form.append('teams', JSON.stringify(drawerFormData.teams));
      }
      if (drawerFormData.tags?.length > 0) {
        form.append('tags', JSON.stringify(drawerFormData.tags));
      }

      const response = await fetch('?/create', { method: 'POST', body: form });
      const result = await response.json();

      if (result.type === 'success' || result.data?.success) {
        toast.success('Opportunity created');
        closeDrawer();
        await invalidateAll();
      } else {
        toast.error(result.data?.message || 'Failed to create opportunity');
      }
    } catch (err) {
      console.error('Create error:', err);
      toast.error('An error occurred');
    } finally {
      isLoading = false;
    }
  }

  /**
   * Mark opportunity as won
   */
  async function handleMarkWon() {
    if (!selectedRowId) return;
    await saveFieldValue(selectedRowId, 'stage', 'CLOSED_WON');
    toast.success('Opportunity marked as won!');
  }

  /**
   * Mark opportunity as lost
   */
  async function handleMarkLost() {
    if (!selectedRowId) return;
    await saveFieldValue(selectedRowId, 'stage', 'CLOSED_LOST');
    toast.success('Opportunity marked as lost');
  }

  async function deleteSelectedRow() {
    if (!selectedRowId) return;

    isLoading = true;
    try {
      const form = new FormData();
      form.append('opportunityId', selectedRowId);
      const response = await fetch('?/delete', { method: 'POST', body: form });
      const result = await response.json();

      if (result.type === 'success' || result.data?.success) {
        toast.success('Opportunity deleted');
        closeDrawer();
        await invalidateAll();
      } else {
        toast.error(result.data?.message || 'Failed to delete opportunity');
      }
    } catch (err) {
      console.error('Delete error:', err);
      toast.error('An error occurred while deleting');
    } finally {
      isLoading = false;
    }
  }

  // Open create drawer for new opportunity
  function addNewRow() {
    openCreate();
  }

  // Get selected row data
  const selectedRow = $derived(
    filteredOpportunities.find((/** @type {any} */ r) => r.id === selectedRowId)
  );

  // Check if opportunity is closed (won or lost)
  const isClosed = $derived(
    selectedRow?.stage === 'CLOSED_WON' || selectedRow?.stage === 'CLOSED_LOST'
  );
  const isWon = $derived(selectedRow?.stage === 'CLOSED_WON');
  const isLost = $derived(selectedRow?.stage === 'CLOSED_LOST');

  // Line items from selected row
  const lineItems = $derived(selectedRow?.lineItems || []);
  const hasLineItems = $derived(lineItems.length > 0);
  const canCreateInvoice = $derived(isWon && hasLineItems);

  // New line item form state
  let newLineItemProductId = $state('');
  let newLineItemQty = $state(1);
  let newLineItemPrice = $state(0);
  let isAddingLineItem = $state(false);
  let isDeletingLineItem = $state(''); // Holds the ID of the line item being deleted
  let createInvoiceDialogOpen = $state(false);
  let productSearchQuery = $state('');

  // Filter products based on search query
  const filteredProductOptions = $derived.by(() => {
    if (!productSearchQuery.trim()) {
      return productOptions;
    }
    const query = productSearchQuery.toLowerCase();
    return productOptions.filter(
      (p) => p.label.toLowerCase().includes(query) || (p.sku && p.sku.toLowerCase().includes(query))
    );
  });

  /**
   * Handle product selection for new line item
   * @param {string} productId
   */
  function handleProductSelect(productId) {
    newLineItemProductId = productId;
    const product = formOptions.products.find((p) => p.id === productId);
    if (product) {
      newLineItemPrice = product.price || 0;
    }
  }

  /**
   * Add a new line item
   */
  async function addLineItem() {
    if (!selectedRowId || !newLineItemProductId) return;

    isAddingLineItem = true;
    try {
      const form = new FormData();
      form.append('opportunityId', selectedRowId);
      form.append('productId', newLineItemProductId);
      form.append('quantity', newLineItemQty.toString());
      form.append('unitPrice', newLineItemPrice.toString());

      const response = await fetch('?/addLineItem', { method: 'POST', body: form });
      const result = await response.json();

      if (result.type === 'success' || result.data?.success) {
        toast.success('Product added');
        // Reset form
        newLineItemProductId = '';
        newLineItemQty = 1;
        newLineItemPrice = 0;
        await invalidateAll();
      } else {
        toast.error(result.data?.message || 'Failed to add product');
      }
    } catch (err) {
      console.error('Add line item error:', err);
      toast.error('An error occurred');
    } finally {
      isAddingLineItem = false;
    }
  }

  /**
   * Delete a line item
   * @param {string} lineItemId
   */
  async function deleteLineItem(lineItemId) {
    if (!selectedRowId || isDeletingLineItem) return;

    isDeletingLineItem = lineItemId;
    try {
      const form = new FormData();
      form.append('opportunityId', selectedRowId);
      form.append('lineItemId', lineItemId);

      const response = await fetch('?/deleteLineItem', { method: 'POST', body: form });
      const result = await response.json();

      if (result.type === 'success' || result.data?.success) {
        toast.success('Product removed');
        await invalidateAll();
      } else {
        toast.error(result.data?.message || 'Failed to remove product');
      }
    } catch (err) {
      console.error('Delete line item error:', err);
      toast.error('An error occurred');
    } finally {
      isDeletingLineItem = '';
    }
  }

  /**
   * Create invoice from opportunity (called after confirmation)
   */
  async function confirmCreateInvoice() {
    if (!selectedRowId || !canCreateInvoice) return;

    createInvoiceDialogOpen = false;
    isLoading = true;
    try {
      const form = new FormData();
      form.append('opportunityId', selectedRowId);

      const response = await fetch('?/createInvoice', { method: 'POST', body: form });
      const result = await response.json();

      if (result.type === 'success' || result.data?.success) {
        toast.success('Invoice created');
        // Navigate to the new invoice
        if (result.data?.invoiceId) {
          goto(`/invoices/${result.data.invoiceId}`);
        } else {
          goto('/invoices');
        }
      } else {
        toast.error(result.data?.message || 'Failed to create invoice');
      }
    } catch (err) {
      console.error('Create invoice error:', err);
      toast.error('An error occurred');
    } finally {
      isLoading = false;
    }
  }
</script>

<svelte:head>
  <title>Opportunities - BottleCRM</title>
</svelte:head>

<PageHeader title="Opportunities" subtitle="Pipeline: {formatCurrency(stats.pipeline)}">
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
            {opportunities.length}
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
          onclick={() => (statusChipFilter = 'won')}
          class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
          'won'
            ? 'bg-[var(--stage-won)] text-white'
            : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]'}"
        >
          Won
          <span
            class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'won'
              ? 'bg-black/20 text-white/90'
              : 'bg-[var(--border-default)] text-[var(--text-tertiary)]'}"
          >
            {wonCount}
          </span>
        </button>
        <button
          type="button"
          onclick={() => (statusChipFilter = 'lost')}
          class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
          'lost'
            ? 'bg-[var(--stage-lost)] text-white'
            : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]'}"
        >
          Lost
          <span
            class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'lost'
              ? 'bg-black/20 text-white/90'
              : 'bg-[var(--border-default)] text-[var(--text-tertiary)]'}"
          >
            {lostCount}
          </span>
        </button>
        {#if staleCount > 0}
          <button
            type="button"
            onclick={() => (statusChipFilter = 'stale')}
            class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
            'stale'
              ? 'bg-red-600 text-white'
              : 'bg-red-50 text-red-600 hover:bg-red-100 dark:bg-red-900/20 dark:text-red-400 dark:hover:bg-red-900/30'}"
          >
            <Clock class="h-3.5 w-3.5" />
            Stale
            <span
              class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'stale'
                ? 'bg-black/20 text-white/90'
                : 'bg-red-200 text-red-700 dark:bg-red-900/40 dark:text-red-300'}"
            >
              {staleCount}
            </span>
          </button>
        {/if}
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

      <!-- Column Visibility Dropdown -->
      <DropdownMenu.Root>
        <DropdownMenu.Trigger asChild>
          {#snippet child({ props })}
            <Button {...props} variant="outline" size="sm" class="gap-2">
              <Eye class="h-4 w-4" />
              Columns
              {#if visibleColumns.length < columns.length}
                <span
                  class="rounded-full bg-[var(--color-primary-light)] px-1.5 py-0.5 text-xs font-medium text-[var(--color-primary-default)]"
                >
                  {visibleColumns.length}/{columns.length}
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
              checked={visibleColumns.includes(column.key)}
              onCheckedChange={() => toggleColumn(column.key)}
              disabled={column.canHide === false}
            >
              {column.label}
            </DropdownMenu.CheckboxItem>
          {/each}
        </DropdownMenu.Content>
      </DropdownMenu.Root>

      <Button onclick={addNewRow} disabled={isLoading}>
        <Plus class="mr-2 h-4 w-4" />
        New
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
      placeholder="Search opportunities..."
    />
    <DateRangeFilter
      label="Close Date"
      startDate={filters.closed_on_gte}
      endDate={filters.closed_on_lte}
      onchange={(start, end) =>
        updateFilters({ ...filters, closed_on_gte: start, closed_on_lte: end })}
    />
    <DateRangeFilter
      label="Created"
      startDate={filters.created_at_gte}
      endDate={filters.created_at_lte}
      onchange={(start, end) =>
        updateFilters({ ...filters, created_at_gte: start, created_at_lte: end })}
    />
    <TagFilter
      tags={data.options?.tags || []}
      value={filters.tags}
      onchange={(ids) => updateFilters({ ...filters, tags: ids })}
    />
  </FilterBar>
  <!-- Table View -->
  {#if filteredOpportunities.length === 0}
    <div class="flex flex-col items-center justify-center py-16 text-center">
      <div
        class="mb-4 flex size-16 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--surface-sunken)]"
      >
        <Target class="size-8 text-[var(--text-tertiary)]" />
      </div>
      <h3 class="text-lg font-medium text-[var(--text-primary)]">No opportunities found</h3>
      <p class="mt-1 text-sm text-[var(--text-secondary)]">
        Try adjusting your filters or create a new opportunity
      </p>
    </div>
  {:else}
    <CrmTable
      data={filteredOpportunities}
      {columns}
      bind:visibleColumns
      onRowChange={handleRowChange}
      onRowClick={(row) => openDrawer(row.id)}
    >
      {#snippet emptyState()}
        <div class="flex flex-col items-center justify-center py-16 text-center">
          <div
            class="mb-4 flex size-16 items-center justify-center rounded-[var(--radius-xl)] bg-[var(--surface-sunken)]"
          >
            <Target class="size-8 text-[var(--text-tertiary)]" />
          </div>
          <h3 class="text-lg font-medium text-[var(--text-primary)]">No opportunities found</h3>
        </div>
      {/snippet}
    </CrmTable>
  {/if}

  <!-- Pagination -->
  <Pagination
    page={pagination.page}
    limit={pagination.limit}
    total={pagination.total}
    onPageChange={handlePageChange}
    onLimitChange={handleLimitChange}
  />
</div>

<!-- Opportunity Drawer -->
<CrmDrawer
  bind:open={drawerOpen}
  onOpenChange={(open) => !open && closeDrawer()}
  data={drawerFormData}
  columns={drawerColumns}
  titleKey="name"
  titlePlaceholder="Opportunity name"
  headerLabel="Opportunity"
  mode={drawerMode}
  loading={isLoading}
  onFieldChange={handleDrawerFieldChange}
  onDelete={deleteSelectedRow}
  onClose={closeDrawer}
>
  {#snippet activitySection()}
    <!-- Account and Owner info (view mode only) -->
    {#if drawerMode !== 'create' && selectedRow}
      <div class="mb-4">
        <p class="mb-2 text-xs font-medium tracking-wider text-[var(--text-tertiary)] uppercase">
          Details
        </p>
        <div class="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p class="text-xs text-[var(--text-tertiary)]">Account</p>
            <p class="font-medium text-[var(--text-primary)]">
              {selectedRow.account?.name || '-'}
            </p>
          </div>
          {#if selectedRow.createdAt}
            <div>
              <p class="text-xs text-[var(--text-tertiary)]">Created</p>
              <p class="font-medium text-[var(--text-primary)]">
                {formatRelativeDate(selectedRow.createdAt)}
              </p>
            </div>
          {/if}
          {#if !isClosed && selectedRow.daysInStage != null}
            <div>
              <p class="text-xs text-[var(--text-tertiary)]">Days in Stage</p>
              <p class="font-medium {selectedRow.agingStatus === 'red' ? 'text-red-600' : selectedRow.agingStatus === 'yellow' ? 'text-amber-500' : 'text-[var(--text-primary)]'}">
                {selectedRow.daysInStage}d
              </p>
            </div>
          {/if}
          {#if isClosed && selectedRow.closedBy}
            <div>
              <p class="text-xs text-[var(--text-tertiary)]">Closed By</p>
              <p class="font-medium text-[var(--text-primary)]">
                {selectedRow.closedBy.name || '-'}
              </p>
            </div>
          {/if}
          {#if isClosed && selectedRow.closedOn}
            <div>
              <p class="text-xs text-[var(--text-tertiary)]">Closed On</p>
              <p class="font-medium text-[var(--text-primary)]">
                {formatDate(selectedRow.closedOn)}
              </p>
            </div>
          {/if}
        </div>
      </div>

      <!-- Products Section -->
      <div class="mt-6 border-t border-[var(--border-default)] pt-4">
        <div class="mb-3 flex items-center justify-between">
          <p
            class="flex items-center gap-2 text-xs font-medium tracking-wider text-[var(--text-tertiary)] uppercase"
          >
            <Package class="size-4" />
            Products
          </p>
          {#if hasLineItems}
            <span class="text-sm font-medium text-[var(--text-primary)]">
              Total: {formatCurrency(
                selectedRow.lineItemsTotal || 0,
                selectedRow.currency || 'USD'
              )}
            </span>
          {/if}
        </div>

        <!-- Existing line items -->
        {#if hasLineItems}
          <div class="mb-4 space-y-2">
            {#each lineItems as item (item.id)}
              <div
                class="flex items-center justify-between rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-sunken)] px-3 py-2"
              >
                <div class="min-w-0 flex-1">
                  <p class="truncate text-sm font-medium text-[var(--text-primary)]">
                    {item.productName || item.name || 'Custom Item'}
                  </p>
                  <p class="text-xs text-[var(--text-secondary)]">
                    {item.quantity} x {formatCurrency(
                      item.unitPrice,
                      selectedRow.currency || 'USD'
                    )}
                    = {formatCurrency(item.total, selectedRow.currency || 'USD')}
                  </p>
                </div>
                {#if !isClosed}
                  <button
                    type="button"
                    class="ml-2 rounded-[var(--radius-md)] p-1 text-[var(--text-tertiary)] hover:bg-[var(--surface-raised)] hover:text-[var(--color-negative-default)] disabled:cursor-not-allowed disabled:opacity-50"
                    onclick={() => deleteLineItem(item.id)}
                    disabled={isDeletingLineItem === item.id}
                  >
                    {#if isDeletingLineItem === item.id}
                      <svg class="size-4 animate-spin" viewBox="0 0 24 24">
                        <circle
                          class="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          stroke-width="4"
                          fill="none"
                        ></circle>
                        <path
                          class="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                        ></path>
                      </svg>
                    {:else}
                      <Trash2 class="size-4" />
                    {/if}
                  </button>
                {/if}
              </div>
            {/each}
          </div>
        {:else}
          <p class="mb-4 text-sm text-[var(--text-secondary)]">No products added yet.</p>
        {/if}

        <!-- Add product form (only if not closed) -->
        {#if !isClosed}
          <div
            class="space-y-3 rounded-[var(--radius-lg)] border border-[var(--border-default)] bg-[var(--surface-sunken)] p-3"
          >
            <p class="text-xs font-medium text-[var(--text-secondary)]">Add Product</p>
            <div class="grid grid-cols-1 gap-2">
              <Select.Root
                type="single"
                value={newLineItemProductId}
                onValueChange={(v) => {
                  if (v) handleProductSelect(v);
                  productSearchQuery = '';
                }}
                onOpenChange={(open) => {
                  if (!open) productSearchQuery = '';
                }}
              >
                <Select.Trigger class="w-full">
                  {productOptions.find((p) => p.value === newLineItemProductId)?.label ||
                    'Select product...'}
                </Select.Trigger>
                <Select.Content class="max-h-60">
                  <div class="sticky top-0 bg-[var(--surface-raised)] p-2">
                    <Input
                      type="text"
                      placeholder="Search products..."
                      bind:value={productSearchQuery}
                      class="h-8 text-sm"
                      onclick={(e) => e.stopPropagation()}
                      onkeydown={(e) => e.stopPropagation()}
                    />
                  </div>
                  {#if filteredProductOptions.length === 0}
                    <div class="px-3 py-2 text-sm text-gray-500">No products found</div>
                  {:else}
                    {#each filteredProductOptions as product (product.value)}
                      <Select.Item value={product.value}>
                        {product.label}
                        {#if product.sku}
                          <span class="ml-1 text-xs text-gray-400">({product.sku})</span>
                        {/if}
                      </Select.Item>
                    {/each}
                  {/if}
                </Select.Content>
              </Select.Root>
              <div class="flex gap-2">
                <Input
                  type="number"
                  placeholder="Qty"
                  bind:value={newLineItemQty}
                  min="1"
                  class="w-20"
                />
                <Input
                  type="number"
                  placeholder="Price"
                  bind:value={newLineItemPrice}
                  min="0"
                  step="0.01"
                  class="flex-1"
                />
                <Button
                  size="sm"
                  onclick={addLineItem}
                  disabled={isAddingLineItem || !newLineItemProductId}
                >
                  <Plus class="h-4 w-4" />
                </Button>
              </div>
            </div>
          </div>
        {/if}
      </div>

      <!-- Comments Section -->
      <div class="mt-6 border-t border-[var(--border-default)] pt-4">
        <CommentSection
          entityId={selectedRow.id}
          entityType="opportunity"
          initialComments={selectedRow.comments || []}
          currentUserEmail={currentUser?.email}
          isAdmin={currentUser?.organizations?.some((o) => o.role === 'ADMIN')}
        />
      </div>
    {/if}
  {/snippet}

  {#snippet footerActions()}
    {#if drawerMode === 'create'}
      <Button onclick={handleDrawerSave} disabled={isLoading || !drawerFormData.name?.trim()}>
        {isLoading ? 'Creating...' : 'Create Opportunity'}
      </Button>
    {:else}
      {#if !isClosed}
        <Button
          variant="outline"
          class="text-[var(--stage-won)] hover:bg-[var(--stage-won-bg)] hover:text-[var(--stage-won)]"
          onclick={handleMarkWon}
          disabled={isLoading}
        >
          <Trophy class="mr-1.5 size-4" />
          Mark Won
        </Button>
        <Button
          variant="outline"
          class="text-[var(--stage-lost)] hover:bg-[var(--stage-lost-bg)] hover:text-[var(--stage-lost)]"
          onclick={handleMarkLost}
          disabled={isLoading}
        >
          <XCircle class="mr-1.5 size-4" />
          Mark Lost
        </Button>
      {/if}
      {#if canCreateInvoice}
        <AlertDialog.Root bind:open={createInvoiceDialogOpen}>
          <AlertDialog.Trigger asChild>
            {#snippet child({ props })}
              <Button
                {...props}
                variant="outline"
                class="text-[var(--color-primary-default)] hover:bg-[var(--color-primary-light)] hover:text-[var(--color-primary-default)]"
                disabled={isLoading}
              >
                <Receipt class="mr-1.5 size-4" />
                Create Invoice
              </Button>
            {/snippet}
          </AlertDialog.Trigger>
          <AlertDialog.Content>
            <AlertDialog.Header>
              <AlertDialog.Title>Create Invoice</AlertDialog.Title>
              <AlertDialog.Description>
                This will create a new invoice from this opportunity with {lineItems.length} product{lineItems.length ===
                1
                  ? ''
                  : 's'} totaling {formatCurrency(
                  selectedRow?.lineItemsTotal || 0,
                  selectedRow?.currency || 'USD'
                )}.
              </AlertDialog.Description>
            </AlertDialog.Header>
            <AlertDialog.Footer>
              <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
              <AlertDialog.Action onclick={confirmCreateInvoice}>Create Invoice</AlertDialog.Action>
            </AlertDialog.Footer>
          </AlertDialog.Content>
        </AlertDialog.Root>
      {/if}
      <Button onclick={handleDrawerUpdate} disabled={isLoading || !drawerFormData.name?.trim()}>
        {isLoading ? 'Saving...' : 'Save'}
      </Button>
    {/if}
  {/snippet}
</CrmDrawer>
