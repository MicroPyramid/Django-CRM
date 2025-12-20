<script>
  import { enhance } from '$app/forms';
  import { invalidateAll, goto } from '$app/navigation';
  import { page } from '$app/stores';
  import { onMount, tick } from 'svelte';
  import { toast } from 'svelte-sonner';
  import {
    Plus,
    ChevronLeft,
    ChevronRight,
    CheckSquare,
    Building2,
    Calendar,
    List,
    Flag,
    Circle,
    CheckCircle2,
    Clock,
    RotateCcw,
    Users,
    User,
    Eye,
    FileText,
    Target,
    Briefcase,
    UserPlus,
    Tag,
    Contact,
    Link2,
    Filter,
    Columns
  } from '@lucide/svelte';
  import { TaskKanban } from '$lib/components/ui/task-kanban';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Card from '$lib/components/ui/card/index.js';
  import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
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
  import { cn } from '$lib/utils.js';
  import { TASK_STATUSES as statuses, PRIORITIES as priorities } from '$lib/constants/filters.js';
  import { CrmTable } from '$lib/components/ui/crm-table';
  import { formatRelativeDate } from '$lib/utils/formatting.js';

  // Account from URL param (for quick action from account page)
  let accountFromUrl = $state(false);
  let accountNameFromUrl = $state('');
  let accountIdFromUrl = $state('');

  // Status and priority options with colors
  const statusOptions = [
    {
      value: 'New',
      label: 'New',
      color: 'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400'
    },
    {
      value: 'In Progress',
      label: 'In Progress',
      color: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
    },
    {
      value: 'Completed',
      label: 'Completed',
      color: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400'
    }
  ];

  const priorityOptions = [
    {
      value: 'High',
      label: 'High',
      color: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'
    },
    {
      value: 'Medium',
      label: 'Medium',
      color: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400'
    },
    {
      value: 'Low',
      label: 'Low',
      color: 'bg-gray-100 text-gray-600 dark:bg-gray-800 dark:text-gray-400'
    }
  ];

  // Empty task template for create mode
  const emptyTask = {
    subject: '',
    description: '',
    status: 'New',
    priority: 'Medium',
    dueDate: '',
    accountId: '',
    opportunityId: '',
    caseId: '',
    leadId: '',
    assignedTo: /** @type {string[]} */ ([]),
    contacts: /** @type {string[]} */ ([]),
    teams: /** @type {string[]} */ ([]),
    tags: /** @type {string[]} */ ([])
  };

  /**
   * @typedef {'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'relation'} ColumnType
   * @typedef {{ key: string, label: string, type: ColumnType, width?: string, canHide?: boolean, relationIcon?: string, getValue?: (row: any) => any, options?: { value: string, label: string, color: string }[] }} TaskColumn
   */

  /**
   * Get the related entity display for a task
   * @param {any} row
   * @returns {{ name: string } | null}
   */
  function getRelatedEntity(row) {
    if (row.lead) {
      const leadName =
        row.lead.title || `${row.lead.firstName || ''} ${row.lead.lastName || ''}`.trim() || 'Lead';
      return { name: `Lead: ${leadName}` };
    }
    if (row.opportunity) {
      return { name: `Opp: ${row.opportunity.name || 'Opportunity'}` };
    }
    if (row.case_) {
      return { name: `Case: ${row.case_.subject || row.case_.name || 'Case'}` };
    }
    if (row.account) {
      return { name: `Account: ${row.account.name || 'Account'}` };
    }
    return null;
  }

  /** @type {TaskColumn[]} */
  const taskColumns = [
    { key: 'subject', label: 'Task', type: 'text', width: 'w-64', canHide: false },
    {
      key: 'relatedTo',
      label: 'Related To',
      type: 'relation',
      width: 'w-48',
      relationIcon: 'link',
      getValue: getRelatedEntity
    },
    { key: 'dueDate', label: 'Due Date', type: 'date', width: 'w-36' },
    { key: 'priority', label: 'Priority', type: 'select', options: priorityOptions, width: 'w-28' },
    { key: 'status', label: 'Status', type: 'select', options: statusOptions, width: 'w-36' },
    {
      key: 'assignedTo',
      label: 'Assigned To',
      type: 'relation',
      width: 'w-36',
      relationIcon: 'user',
      getValue: (/** @type {any} */ row) => {
        const assigned = row.assignedTo || [];
        if (assigned.length === 0) return null;
        if (assigned.length === 1) return assigned[0];
        return { name: `${assigned.length} users` };
      }
    },
    // Hidden by default
    {
      key: 'account',
      label: 'Account',
      type: 'relation',
      width: 'w-40',
      relationIcon: 'building',
      canHide: true,
      getValue: (/** @type {any} */ row) => row.account
    },
    {
      key: 'contacts',
      label: 'Contacts',
      type: 'relation',
      width: 'w-36',
      relationIcon: 'contact',
      canHide: true,
      getValue: (/** @type {any} */ row) => {
        const contacts = row.contacts || [];
        if (contacts.length === 0) return null;
        if (contacts.length === 1) return contacts[0];
        return { name: `${contacts.length} contacts` };
      }
    },
    {
      key: 'teams',
      label: 'Teams',
      type: 'relation',
      width: 'w-36',
      relationIcon: 'users',
      canHide: true,
      getValue: (/** @type {any} */ row) => {
        const teams = row.teams || [];
        if (teams.length === 0) return null;
        if (teams.length === 1) return teams[0];
        return { name: `${teams.length} teams` };
      }
    },
    {
      key: 'tags',
      label: 'Tags',
      type: 'relation',
      width: 'w-32',
      relationIcon: 'tag',
      canHide: true,
      getValue: (/** @type {any} */ row) => {
        const tags = row.tags || [];
        if (tags.length === 0) return null;
        if (tags.length === 1) return tags[0];
        return { name: `${tags.length} tags` };
      }
    }
  ];

  // Default visible columns (6 columns: Task, Related To, Due Date, Priority, Status, Assigned To)
  const DEFAULT_VISIBLE_COLUMNS = [
    'subject',
    'relatedTo',
    'dueDate',
    'priority',
    'status',
    'assignedTo'
  ];

  // Column visibility state - use defaults
  const STORAGE_KEY = 'tasks-table-columns';
  let visibleColumns = $state([...DEFAULT_VISIBLE_COLUMNS]);
  let currentUser = $state(null);

  // Load column visibility from localStorage
  onMount(() => {
    const saved = localStorage.getItem(STORAGE_KEY);
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        visibleColumns = parsed.filter((/** @type {string} */ key) =>
          taskColumns.some((c) => c.key === key)
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
    const column = taskColumns.find((c) => c.key === key);
    if (column?.canHide === false) return;

    if (visibleColumns.includes(key)) {
      visibleColumns = visibleColumns.filter((k) => k !== key);
    } else {
      visibleColumns = [...visibleColumns, key];
    }
  }

  const columnCounts = $derived({
    visible: visibleColumns.length,
    total: taskColumns.length
  });

  /** @type {{ data: any }} */
  let { data } = $props();

  // Computed values - tasks come from server
  const tasks = $derived(data.tasks || []);
  const pagination = $derived(data.pagination || { page: 1, limit: 10, total: 0, totalPages: 0 });

  // Dropdown options from server (loaded with page data)
  const formOptions = $derived(data.formOptions || {});
  const accounts = $derived(formOptions.accounts || []);
  const users = $derived(formOptions.users || []);
  const contacts = $derived(formOptions.contacts || []);
  const teams = $derived(formOptions.teams || []);
  const opportunities = $derived(formOptions.opportunities || []);
  const cases = $derived(formOptions.cases || []);
  const leads = $derived(formOptions.leads || []);
  const allTags = $derived(formOptions.tags || []);

  // Dropdown options are now loaded server-side with page data
  // No lazy loading needed

  /**
   * Get account name from server-provided accounts list
   * @param {string} id
   */
  function fetchAccountName(id) {
    const account = accounts.find((a) => a.id === id);
    if (account) {
      accountNameFromUrl = account.name;
    } else {
      accountNameFromUrl = 'Unknown Account';
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
    accountNameFromUrl = '';
    accountIdFromUrl = '';
  }

  // URL-based filter state from server
  const filters = $derived(data.filters || {});

  // Status options for filter dropdown
  const statusFilterOptions = $derived([{ value: '', label: 'All Statuses' }, ...statusOptions]);

  // Priority options for filter dropdown
  const priorityFilterOptions = $derived([
    { value: '', label: 'All Priorities' },
    ...priorityOptions
  ]);

  // Count active filters (excluding status since it's handled via chips in header)
  const activeFiltersCount = $derived.by(() => {
    let count = 0;
    if (filters.search) count++;
    if (filters.priority) count++;
    if (filters.assigned_to?.length > 0) count++;
    if (filters.tags?.length > 0) count++;
    if (filters.due_date_gte || filters.due_date_lte) count++;
    return count;
  });

  /**
   * Update URL with new filters
   * @param {Record<string, any>} newFilters
   */
  async function updateFilters(newFilters) {
    const url = new URL($page.url);
    // Clear existing filter params
    ['search', 'status', 'priority', 'assigned_to', 'tags', 'due_date_gte', 'due_date_lte'].forEach(
      (key) => url.searchParams.delete(key)
    );
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
  const activeStatuses = ['New', 'In Progress'];
  const activeTaskCount = $derived(
    tasks.filter((/** @type {any} */ t) => activeStatuses.includes(t.status)).length
  );
  const completedCount = $derived(
    tasks.filter((/** @type {any} */ t) => t.status === 'Completed').length
  );

  // Status chip filter state (client-side quick filter on top of server filters)
  let statusChipFilter = $state('ALL');

  // Filter panel expansion state
  let filtersExpanded = $state(false);

  // Filtered tasks - server already applies main filters, just apply status chip
  const filteredTasks = $derived.by(() => {
    let filtered = tasks;
    if (statusChipFilter === 'active') {
      filtered = filtered.filter((/** @type {any} */ t) => activeStatuses.includes(t.status));
    } else if (statusChipFilter === 'completed') {
      filtered = filtered.filter((/** @type {any} */ t) => t.status === 'Completed');
    }
    return filtered;
  });

  // Local data for optimistic updates
  let localTasks = $state(/** @type {any[]} */ ([]));

  $effect(() => {
    localTasks = [...filteredTasks];
  });

  // Row detail sheet state
  let sheetOpen = $state(false);
  /** @type {string | null} */
  let selectedTaskId = $state(null);

  // View mode state (list, kanban, or calendar) - sync with server data
  /** @type {'list' | 'kanban' | 'calendar'} */
  let viewMode = $state('list');

  // Sync viewMode when data changes (e.g., on navigation)
  $effect(() => {
    if (data.viewMode) {
      viewMode = data.viewMode;
    }
  });

  // Kanban data from server
  const kanbanData = $derived(data.kanbanData);

  // Form references for server actions
  /** @type {HTMLFormElement} */
  let createForm;
  /** @type {HTMLFormElement} */
  let updateForm;
  /** @type {HTMLFormElement} */
  let deleteForm;
  /** @type {HTMLFormElement} */
  let completeForm;
  /** @type {HTMLFormElement} */
  let reopenForm;
  /** @type {HTMLFormElement} */
  let moveTaskForm;

  // Kanban form state for drag-drop
  let kanbanFormState = $state({
    taskId: '',
    status: '',
    stageId: '',
    aboveTaskId: '',
    belowTaskId: ''
  });

  // Form data state
  let formState = $state({
    taskId: '',
    subject: '',
    description: '',
    status: 'New',
    priority: 'Medium',
    dueDate: '',
    accountId: '',
    accountName: '',
    opportunityId: '',
    opportunityName: '',
    caseId: '',
    caseName: '',
    leadId: '',
    leadName: '',
    assignedTo: /** @type {string[]} */ ([]),
    contacts: /** @type {string[]} */ ([]),
    teams: /** @type {string[]} */ ([]),
    tags: /** @type {string[]} */ ([])
  });

  /**
   * NotionTable callback - handle inline row changes
   * @param {any} row
   * @param {string} field
   * @param {any} value
   */
  async function handleRowChange(row, field, value) {
    // Optimistically update local state
    localTasks = localTasks.map((t) => (t.id === row.id ? { ...t, [field]: value } : t));

    // Prepare form state and submit to server
    formState.taskId = row.id;
    formState.subject = field === 'subject' ? value : row.subject || '';
    formState.description = row.description || '';
    formState.status = field === 'status' ? value : row.status || 'New';
    formState.priority = field === 'priority' ? value : row.priority || 'Medium';
    formState.dueDate = row.dueDate ? row.dueDate.split('T')[0] : '';
    formState.accountId = row.account?.id || '';
    formState.opportunityId = row.opportunity?.id || '';
    formState.caseId = row.case_?.id || '';
    formState.leadId = row.lead?.id || '';
    formState.assignedTo = (row.assignedTo || []).map((/** @type {any} */ a) => a.id);
    formState.contacts = (row.contacts || []).map((/** @type {any} */ c) => c.id);
    formState.teams = (row.teams || []).map((/** @type {any} */ t) => t.id);
    formState.tags = (row.tags || []).map((/** @type {any} */ t) => t.id);

    await tick();
    updateForm.requestSubmit();
  }

  /**
   * NotionTable callback - handle row click to open sheet
   * @param {any} row
   */
  function handleRowClick(row) {
    openTaskSheet(row.id);
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

  async function addNewTask() {
    // Check for account pre-fill from URL params
    const accountIdParam = $page.url.searchParams.get('accountId');
    if (accountIdParam && !accountFromUrl) {
      accountIdFromUrl = accountIdParam;
      accountFromUrl = true;
      fetchAccountName(accountIdParam);
    }

    // Open the sheet for creating a new task
    selectedTaskId = null;
    formState = {
      taskId: '',
      subject: '',
      description: '',
      status: 'New',
      priority: 'Medium',
      dueDate: '',
      accountId: accountIdFromUrl || '',
      accountName: accountNameFromUrl || '',
      opportunityId: '',
      opportunityName: '',
      caseId: '',
      caseName: '',
      leadId: '',
      leadName: '',
      assignedTo: [],
      contacts: [],
      teams: [],
      tags: []
    };
    sheetOpen = true;
  }

  // URL sync for action param (quick action from account page)
  $effect(() => {
    const action = $page.url.searchParams.get('action');

    if (action === 'create' && !sheetOpen) {
      addNewTask();
    }
  });

  // Row detail sheet functions
  /**
   * @param {string} taskId
   */
  function openTaskSheet(taskId) {
    selectedTaskId = taskId;
    const task = localTasks.find((t) => t.id === taskId);
    if (task) {
      formState = {
        taskId: task.id,
        subject: task.subject || '',
        description: task.description || '',
        status: task.status || 'New',
        priority: task.priority || 'Medium',
        dueDate: task.dueDate ? task.dueDate.split('T')[0] : '',
        accountId: task.account?.id || '',
        accountName: task.account?.name || '',
        opportunityId: task.opportunity?.id || '',
        opportunityName: task.opportunity?.name || '',
        caseId: task.case_?.id || '',
        caseName: task.case_?.name || '',
        leadId: task.lead?.id || '',
        leadName: task.lead?.name || '',
        assignedTo: (task.assignedTo || []).map((/** @type {any} */ a) => a.id),
        contacts: (task.contacts || []).map((/** @type {any} */ c) => c.id),
        teams: (task.teams || []).map((/** @type {any} */ t) => t.id),
        tags: (task.tags || []).map((/** @type {any} */ t) => t.id)
      };
    }
    sheetOpen = true;
  }

  function closeTaskSheet() {
    sheetOpen = false;
    selectedTaskId = null;
    // Clear account URL params if they were set
    if (accountFromUrl) {
      clearUrlParams();
    }
  }

  async function deleteSelectedTask() {
    if (!selectedTaskId) return;
    if (!confirm('Are you sure you want to delete this task?')) return;
    formState.taskId = selectedTaskId;
    await tick();
    deleteForm.requestSubmit();
  }

  async function completeSelectedTask() {
    if (!selectedTaskId) return;
    formState.taskId = selectedTaskId;
    await tick();
    completeForm.requestSubmit();
  }

  async function reopenSelectedTask() {
    if (!selectedTaskId) return;
    formState.taskId = selectedTaskId;
    await tick();
    reopenForm.requestSubmit();
  }

  // Get selected task data
  const selectedTask = $derived(localTasks.find((t) => t.id === selectedTaskId));
  const isCreateMode = $derived(selectedTaskId === null && sheetOpen);
  const isCompleted = $derived(formState.status === 'Completed');

  /**
   * Create enhance handler for form actions
   * @param {string} successMessage
   * @param {boolean} closeSheet
   */
  function createEnhanceHandler(successMessage, closeSheet = false) {
    return () => {
      return async (/** @type {any} */ { result }) => {
        if (result.type === 'success') {
          toast.success(successMessage);
          if (closeSheet) {
            closeTaskSheet();
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

  // Calendar state
  let today = new Date();
  let currentDate = $state(new Date(today));
  let selectedDate = $state(today.toISOString().slice(0, 10));

  const monthNames = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December'
  ];

  // Calendar computed values
  const calendarYear = $derived(currentDate.getFullYear());
  const calendarMonth = $derived(currentDate.getMonth());
  const monthStart = $derived(new Date(calendarYear, calendarMonth, 1));
  const monthEnd = $derived(new Date(calendarYear, calendarMonth + 1, 0));
  const startDay = $derived(monthStart.getDay());
  const daysInMonth = $derived(monthEnd.getDate());

  const calendar = $derived.by(() => {
    /** @type {(Date | null)[]} */
    let cal = [];
    for (let i = 0; i < startDay; i++) cal.push(null);
    for (let d = 1; d <= daysInMonth; d++)
      cal.push(new Date(Date.UTC(calendarYear, calendarMonth, d)));
    while (cal.length % 7 !== 0) cal.push(null);
    return cal;
  });

  // Group filtered tasks by due date for calendar
  const tasksByDate = $derived.by(() => {
    /** @type {Record<string, any[]>} */
    const grouped = {};
    for (const t of filteredTasks) {
      if (!t.dueDate) continue;
      const date = (typeof t.dueDate === 'string' ? t.dueDate : t.dueDate?.toISOString?.())?.slice(
        0,
        10
      );
      if (!date) continue;
      if (!grouped[date]) grouped[date] = [];
      grouped[date].push(t);
    }
    return grouped;
  });

  const selectedTasks = $derived(tasksByDate[selectedDate] || []);

  // Monthly stats for calendar
  const monthlyTaskDates = $derived(
    Object.keys(tasksByDate).filter((dateStr) => {
      const taskDate = new Date(dateStr);
      return taskDate.getFullYear() === calendarYear && taskDate.getMonth() === calendarMonth;
    })
  );

  const totalMonthlyTasks = $derived(
    monthlyTaskDates.reduce((total, dateStr) => total + tasksByDate[dateStr].length, 0)
  );

  /**
   * Format date to YYYY-MM-DD string
   * @param {Date} date
   */
  function formatDateString(date) {
    return date.toISOString().slice(0, 10);
  }

  /**
   * Check if date is today
   * @param {Date|null} date
   */
  function isTodayDate(date) {
    return !!(date && formatDateString(date) === today.toISOString().slice(0, 10));
  }

  /**
   * Check if date has tasks
   * @param {Date|null} date
   */
  function hasTasksOnDate(date) {
    return !!(date && tasksByDate[formatDateString(date)]?.length > 0);
  }

  /**
   * Select a day on the calendar
   * @param {Date|null} date
   */
  function selectDay(date) {
    if (date) {
      selectedDate = formatDateString(date);
    }
  }

  function previousMonth() {
    currentDate = new Date(calendarYear, calendarMonth - 1, 1);
  }

  function nextMonth() {
    currentDate = new Date(calendarYear, calendarMonth + 1, 1);
  }

  function goToToday() {
    currentDate = new Date(today);
    selectedDate = today.toISOString().slice(0, 10);
  }

  // Account options for sheet
  const accountOptions = $derived([
    { value: '', label: 'None' },
    ...accounts.map((/** @type {any} */ a) => ({ value: a.id, label: a.name }))
  ]);

  // User options for drawer
  const userOptions = $derived(
    users.map((/** @type {any} */ u) => ({ value: u.id, label: u.name }))
  );

  // Team options for drawer
  const teamOptions = $derived(
    teams.map((/** @type {any} */ t) => ({ value: t.id, label: t.name }))
  );

  // Contact options for drawer
  const contactOptions = $derived(
    contacts.map((/** @type {any} */ c) => ({ value: c.id, label: c.name }))
  );

  // Opportunity options for drawer
  const opportunityOptions = $derived([
    { value: '', label: 'None' },
    ...opportunities.map((/** @type {any} */ o) => ({ value: o.id, label: o.name }))
  ]);

  // Case options for drawer
  const caseOptions = $derived([
    { value: '', label: 'None' },
    ...cases.map((/** @type {any} */ c) => ({ value: c.id, label: c.name }))
  ]);

  // Lead options for drawer
  const leadOptions = $derived([
    { value: '', label: 'None' },
    ...leads.map((/** @type {any} */ l) => ({ value: l.id, label: l.name }))
  ]);

  // Tag options for drawer
  const tagOptions = $derived(
    allTags.map((/** @type {any} */ t) => ({ value: t.id, label: t.name }))
  );

  // Drawer columns for NotionDrawer (derived to use dynamic options)
  // Parent entity fields (account, opportunity, case, lead) are only shown in edit mode
  // Exception: when creating from account quick action, show account as readonly and hide other parent fields
  const drawerColumns = $derived([
    { key: 'subject', label: 'Subject', type: 'text', icon: FileText },
    { key: 'status', label: 'Status', type: 'select', icon: Circle, options: statusOptions },
    { key: 'priority', label: 'Priority', type: 'select', icon: Flag, options: priorityOptions },
    { key: 'dueDate', label: 'Due Date', type: 'date', icon: Calendar },
    // Parent entity field handling:
    // - In edit mode: show readonly for the existing parent entity
    // - In create mode with accountFromUrl: show account as readonly only
    // - In create mode without accountFromUrl: show nothing (parent fields not available in create)
    ...(selectedTaskId
      ? (() => {
          const task = localTasks.find((t) => t.id === selectedTaskId);
          if (!task) return [];
          if (task.account)
            return [{ key: 'accountName', label: 'Account', type: 'readonly', icon: Building2 }];
          if (task.lead)
            return [{ key: 'leadName', label: 'Lead', type: 'readonly', icon: UserPlus }];
          if (task.opportunity)
            return [
              { key: 'opportunityName', label: 'Opportunity', type: 'readonly', icon: Target }
            ];
          if (task.case_)
            return [{ key: 'caseName', label: 'Case', type: 'readonly', icon: Briefcase }];
          return [];
        })()
      : accountFromUrl
        ? [
            {
              key: 'accountDisplay',
              label: 'Account',
              type: 'readonly',
              icon: Building2,
              getValue: () => accountNameFromUrl || 'Loading...'
            }
          ]
        : []),
    {
      key: 'assignedTo',
      label: 'Assigned To',
      type: 'multiselect',
      icon: User,
      options: userOptions
    },
    {
      key: 'contacts',
      label: 'Contacts',
      type: 'multiselect',
      icon: Contact,
      options: contactOptions
    },
    { key: 'teams', label: 'Teams', type: 'multiselect', icon: Users, options: teamOptions },
    { key: 'tags', label: 'Tags', type: 'multiselect', icon: Tag, options: tagOptions },
    { key: 'description', label: 'Description', type: 'textarea' }
  ]);

  // Drawer form data state
  let drawerFormData = $state(/** @type {Record<string, any>} */ ({ ...emptyTask }));

  // Sync drawerFormData when formState changes
  $effect(() => {
    drawerFormData = {
      subject: formState.subject,
      description: formState.description,
      status: formState.status,
      priority: formState.priority,
      dueDate: formState.dueDate,
      accountId: formState.accountId,
      accountName: formState.accountName,
      opportunityId: formState.opportunityId,
      opportunityName: formState.opportunityName,
      caseId: formState.caseId,
      caseName: formState.caseName,
      leadId: formState.leadId,
      leadName: formState.leadName,
      assignedTo: formState.assignedTo,
      contacts: formState.contacts,
      teams: formState.teams,
      tags: formState.tags
    };
  });

  /**
   * Handle field changes from CrmDrawer - just updates local state
   * @param {string} field
   * @param {any} value
   */
  function handleDrawerFieldChange(field, value) {
    // Update drawerFormData only - no auto-save
    drawerFormData = { ...drawerFormData, [field]: value };

    // Also update formState
    formState = { ...formState, [field]: value };
  }

  /**
   * Handle save for view/edit mode
   */
  async function handleDrawerUpdate() {
    if (!selectedTaskId) return;

    await tick();
    updateForm.requestSubmit();
  }

  /**
   * Handle drawer save (for create mode)
   */
  async function handleDrawerSave() {
    await tick();
    if (selectedTaskId) {
      updateForm.requestSubmit();
    } else {
      createForm.requestSubmit();
    }
  }

  /**
   * Handle view mode change (sync with URL for kanban data loading)
   * @param {'list' | 'kanban' | 'calendar'} mode
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
   * @param {string} taskId
   * @param {string} newStatus
   * @param {string} _columnId
   */
  async function handleKanbanStatusChange(taskId, newStatus, _columnId) {
    kanbanFormState.taskId = taskId;
    kanbanFormState.status = newStatus;
    kanbanFormState.stageId = '';
    kanbanFormState.aboveTaskId = '';
    kanbanFormState.belowTaskId = '';
    await tick();
    moveTaskForm.requestSubmit();
  }

  /**
   * Handle kanban card click (open drawer)
   * Kanban tasks have different field names than list tasks, so we handle both cases
   * @param {any} task
   */
  function handleKanbanCardClick(task) {
    // First try to find in localTasks (list data - has full details)
    const listTask = localTasks.find((t) => t.id === task.id);

    if (listTask) {
      // Use list data which has full details
      openTaskSheet(task.id);
    } else {
      // Use kanban task data directly (different field names)
      selectedTaskId = task.id;

      // Extract related entity info from kanban data
      const relatedEntity = task.related_entity;
      let accountId = '';
      let accountName = '';
      let leadId = '';
      let leadName = '';
      let opportunityId = '';
      let opportunityName = '';
      let caseId = '';
      let caseName = '';

      if (relatedEntity) {
        if (relatedEntity.type === 'account') {
          accountId = relatedEntity.id;
          accountName = relatedEntity.name;
        } else if (relatedEntity.type === 'lead') {
          leadId = relatedEntity.id;
          leadName = relatedEntity.name;
        } else if (relatedEntity.type === 'opportunity') {
          opportunityId = relatedEntity.id;
          opportunityName = relatedEntity.name;
        } else if (relatedEntity.type === 'case') {
          caseId = relatedEntity.id;
          caseName = relatedEntity.name;
        }
      }

      formState = {
        taskId: task.id,
        subject: task.title || '', // kanban uses 'title'
        description: '', // Not available in kanban card data
        status: task.status || 'New',
        priority: task.priority || 'Medium',
        dueDate: task.due_date ? task.due_date.split('T')[0] : '', // kanban uses 'due_date'
        accountId,
        accountName,
        opportunityId,
        opportunityName,
        caseId,
        caseName,
        leadId,
        leadName,
        assignedTo: (task.assigned_to || []).map((/** @type {any} */ a) => a.id),
        contacts: [],
        teams: [],
        tags: []
      };
      sheetOpen = true;
    }
  }
</script>

<svelte:head>
  <title>Tasks - BottleCRM</title>
</svelte:head>

<PageHeader title="Tasks" subtitle="{filteredTasks.length} of {tasks.length} tasks">
  {#snippet actions()}
    <div class="flex items-center gap-2">
      <!-- Status Filter Chips -->
      <div class="flex gap-1">
        <button
          type="button"
          onclick={() => (statusChipFilter = 'ALL')}
          class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
          'ALL'
            ? 'bg-gray-900 text-white dark:bg-white dark:text-gray-900'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
        >
          All
          <span
            class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'ALL'
              ? 'bg-gray-700 text-gray-200 dark:bg-gray-200 dark:text-gray-700'
              : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
          >
            {tasks.length}
          </span>
        </button>
        <button
          type="button"
          onclick={() => (statusChipFilter = 'active')}
          class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
          'active'
            ? 'bg-blue-600 text-white dark:bg-blue-500'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
        >
          Active
          <span
            class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'active'
              ? 'bg-blue-700 text-blue-100 dark:bg-blue-600'
              : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
          >
            {activeTaskCount}
          </span>
        </button>
        <button
          type="button"
          onclick={() => (statusChipFilter = 'completed')}
          class="inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-medium transition-colors {statusChipFilter ===
          'completed'
            ? 'bg-emerald-600 text-white dark:bg-emerald-500'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-800 dark:text-gray-400 dark:hover:bg-gray-700'}"
        >
          Completed
          <span
            class="rounded-full px-1.5 py-0.5 text-xs {statusChipFilter === 'completed'
              ? 'bg-emerald-700 text-emerald-100 dark:bg-emerald-600'
              : 'bg-gray-200 text-gray-500 dark:bg-gray-700 dark:text-gray-500'}"
          >
            {completedCount}
          </span>
        </button>
      </div>

      <div class="bg-border mx-1 h-6 w-px"></div>

      <!-- View Toggle -->
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
        <Button
          variant={viewMode === 'calendar' ? 'secondary' : 'ghost'}
          size="sm"
          onclick={() => updateViewMode('calendar')}
          class="h-8 px-3"
        >
          <Calendar class="mr-1.5 h-4 w-4" />
          Calendar
        </Button>
      </div>

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
            class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
          >
            {activeFiltersCount}
          </span>
        {/if}
      </Button>

      {#if viewMode === 'list'}
        <DropdownMenu.Root>
          <DropdownMenu.Trigger>
            {#snippet child({ props })}
              <Button {...props} variant="outline" size="sm" class="gap-2">
                <Eye class="h-4 w-4" />
                Columns
                {#if columnCounts.visible < columnCounts.total}
                  <span
                    class="rounded-full bg-blue-100 px-1.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-400"
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
            {#each taskColumns as column (column.key)}
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
      {/if}

      <Button onclick={addNewTask}>
        <Plus class="mr-2 h-4 w-4" />
        New Task
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
      placeholder="Search tasks..."
    />
    <SelectFilter
      label="Priority"
      options={priorityFilterOptions}
      value={filters.priority}
      onchange={(value) => updateFilters({ ...filters, priority: value })}
    />
    <DateRangeFilter
      label="Due Date"
      startDate={filters.due_date_gte}
      endDate={filters.due_date_lte}
      onchange={(start, end) =>
        updateFilters({ ...filters, due_date_gte: start, due_date_lte: end })}
    />
    <TagFilter
      tags={allTags}
      value={filters.tags}
      onchange={(ids) => updateFilters({ ...filters, tags: ids })}
    />
  </FilterBar>
  {#if viewMode === 'list'}
    <CrmTable
      data={localTasks}
      columns={taskColumns}
      bind:visibleColumns
      onRowChange={handleRowChange}
      onRowClick={handleRowClick}
    >
      {#snippet emptyState()}
        <div class="flex flex-col items-center justify-center py-16 text-center">
          <CheckSquare class="text-muted-foreground/50 mb-4 h-12 w-12" />
          <h3 class="text-foreground text-lg font-medium">No tasks found</h3>
        </div>
      {/snippet}
    </CrmTable>
  {:else if viewMode === 'kanban'}
    <TaskKanban
      data={kanbanData}
      loading={false}
      onStatusChange={handleKanbanStatusChange}
      onCardClick={handleKanbanCardClick}
    />
  {:else}
    <!-- Calendar View -->
    <div class="grid grid-cols-1 gap-6 lg:grid-cols-3">
      <!-- Calendar Section -->
      <div class="lg:col-span-2">
        <Card.Root>
          <!-- Calendar Header -->
          <Card.Header
            class="bg-primary flex flex-row items-center justify-between space-y-0 rounded-t-lg p-4"
          >
            <div class="flex items-center gap-4">
              <Button
                variant="ghost"
                size="icon"
                onclick={previousMonth}
                class="hover:bg-primary-foreground/10 text-primary-foreground h-9 w-9"
              >
                <ChevronLeft class="h-5 w-5" />
              </Button>
              <h2 class="text-primary-foreground text-xl font-semibold">
                {monthNames[calendarMonth]}
                {calendarYear}
              </h2>
              <Button
                variant="ghost"
                size="icon"
                onclick={nextMonth}
                class="hover:bg-primary-foreground/10 text-primary-foreground h-9 w-9"
              >
                <ChevronRight class="h-5 w-5" />
              </Button>
            </div>
            <Button
              variant="secondary"
              size="sm"
              onclick={goToToday}
              class="text-primary-foreground bg-primary-foreground/10 hover:bg-primary-foreground/20"
            >
              Today
            </Button>
          </Card.Header>

          <Card.Content class="p-0">
            <!-- Days of Week -->
            <div class="bg-muted/50 grid grid-cols-7 border-b">
              {#each ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as day}
                <div
                  class="text-muted-foreground border-r p-3 text-center text-sm font-medium last:border-r-0"
                >
                  {day}
                </div>
              {/each}
            </div>

            <!-- Calendar Grid -->
            <div class="grid grid-cols-7">
              {#each calendar as date, i}
                {#if date}
                  <button
                    onclick={() => selectDay(date)}
                    class={cn(
                      'hover:bg-muted/50 relative h-16 border-r border-b p-2 transition-colors last:border-r-0 sm:h-20',
                      formatDateString(date) === selectedDate &&
                        'bg-primary text-primary-foreground hover:bg-primary/90',
                      isTodayDate(date) &&
                        formatDateString(date) !== selectedDate &&
                        'bg-primary/10 text-primary',
                      !isTodayDate(date) &&
                        formatDateString(date) !== selectedDate &&
                        'text-foreground'
                    )}
                  >
                    <div class="text-sm font-medium">
                      {date.getDate()}
                    </div>
                    {#if hasTasksOnDate(date)}
                      <div
                        class={cn(
                          'absolute right-1 bottom-1 h-2 w-2 rounded-full',
                          formatDateString(date) === selectedDate
                            ? 'bg-primary-foreground'
                            : 'bg-primary'
                        )}
                      ></div>
                      <div
                        class={cn(
                          'absolute bottom-1 left-1 text-xs font-medium',
                          formatDateString(date) === selectedDate
                            ? 'text-primary-foreground'
                            : 'text-primary'
                        )}
                      >
                        {tasksByDate[formatDateString(date)].length}
                      </div>
                    {/if}
                  </button>
                {:else}
                  <div class="bg-muted/30 h-16 border-r border-b sm:h-20"></div>
                {/if}
              {/each}
            </div>
          </Card.Content>
        </Card.Root>
      </div>

      <!-- Tasks for Selected Date -->
      <div class="lg:col-span-1">
        <Card.Root class="h-fit">
          <Card.Header class="border-b pb-4">
            <Card.Title class="text-base">
              Tasks for {new Date(selectedDate + 'T00:00:00').toLocaleDateString('en-US', {
                weekday: 'long',
                month: 'long',
                day: 'numeric'
              })}
            </Card.Title>
            <p class="text-muted-foreground text-sm">
              {selectedTasks.length} task{selectedTasks.length !== 1 ? 's' : ''}
            </p>
          </Card.Header>

          <Card.Content class="p-4">
            {#if selectedTasks.length > 0}
              <div class="space-y-3">
                {#each selectedTasks as task}
                  <button
                    type="button"
                    onclick={() => openTaskSheet(task.id)}
                    class="hover:bg-muted bg-muted/50 block w-full rounded-lg border p-3 text-left transition-colors"
                  >
                    <div class="mb-2 flex items-start justify-between gap-2">
                      <h4 class="text-foreground line-clamp-2 flex-1 font-medium">
                        {task.subject}
                      </h4>
                      {#if task.status === 'Completed'}
                        <CheckCircle2 class="text-muted-foreground h-4 w-4 flex-shrink-0" />
                      {:else}
                        <Circle class="text-muted-foreground h-4 w-4 flex-shrink-0" />
                      {/if}
                    </div>

                    {#if task.description}
                      <p class="text-muted-foreground mb-3 line-clamp-2 text-sm">
                        {task.description}
                      </p>
                    {/if}

                    <div class="flex flex-wrap items-center gap-2">
                      {#if task.priority}
                        <span
                          class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium {getOptionStyle(
                            task.priority,
                            priorityOptions
                          )}"
                        >
                          <Flag class="h-3 w-3" />
                          {task.priority}
                        </span>
                      {/if}
                      <span
                        class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium {getOptionStyle(
                          task.status,
                          statusOptions
                        )}"
                      >
                        {task.status}
                      </span>
                    </div>
                  </button>
                {/each}
              </div>
            {:else}
              <div class="py-12 text-center">
                <Calendar class="text-muted-foreground/50 mx-auto mb-4 h-12 w-12" />
                <p class="text-muted-foreground text-sm">No tasks scheduled for this date</p>
                <Button onclick={addNewTask} variant="outline" size="sm" class="mt-4">
                  <Plus class="mr-2 h-4 w-4" />
                  Add Task
                </Button>
              </div>
            {/if}
          </Card.Content>
        </Card.Root>

        <!-- Monthly Stats -->
        <Card.Root class="mt-4">
          <Card.Header class="pb-2">
            <Card.Title class="text-base">This Month</Card.Title>
          </Card.Header>
          <Card.Content class="space-y-2">
            <div class="flex items-center justify-between">
              <span class="text-muted-foreground text-sm">Total Tasks</span>
              <span class="text-foreground font-medium">{totalMonthlyTasks}</span>
            </div>
            <div class="flex items-center justify-between">
              <span class="text-muted-foreground text-sm">Days with Tasks</span>
              <span class="text-foreground font-medium">{monthlyTaskDates.length}</span>
            </div>
          </Card.Content>
        </Card.Root>
      </div>
    </div>
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

<!-- Task Detail Drawer -->
<CrmDrawer
  bind:open={sheetOpen}
  onOpenChange={(open) => !open && closeTaskSheet()}
  data={drawerFormData}
  columns={drawerColumns}
  titleKey="subject"
  titlePlaceholder="Task title"
  headerLabel={isCreateMode ? 'New Task' : 'Task'}
  mode={isCreateMode ? 'create' : 'view'}
  onFieldChange={handleDrawerFieldChange}
  onDelete={deleteSelectedTask}
  onClose={closeTaskSheet}
>
  {#snippet activitySection()}
    <!-- Task metadata (only for existing tasks) -->
    {#if selectedTask && !isCreateMode}
      <div class="space-y-2 text-sm">
        <div class="mb-3 text-[13px] font-medium text-gray-500 dark:text-gray-400">Details</div>
        {#if selectedTask.createdBy}
          <div class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
            <User class="h-3.5 w-3.5" />
            <span>Created by {selectedTask.createdBy.name}</span>
          </div>
        {/if}
        {#if selectedTask.createdAt}
          <div class="flex items-center gap-2 text-gray-600 dark:text-gray-400">
            <Clock class="h-3.5 w-3.5" />
            <span>Created {formatRelativeDate(selectedTask.createdAt)}</span>
          </div>
        {/if}
      </div>

      <!-- Comments Section -->
      <div class="mt-6 border-t pt-4 dark:border-gray-700">
        <CommentSection
          entityId={selectedTask.id}
          entityType="tasks"
          initialComments={selectedTask.comments || []}
          currentUserEmail={currentUser?.email}
          isAdmin={currentUser?.organizations?.some(o => o.role === 'ADMIN')}
        />
      </div>
    {/if}
  {/snippet}

  {#snippet footerActions()}
    {#if isCreateMode}
      <Button variant="outline" size="sm" onclick={closeTaskSheet}>Cancel</Button>
      <Button size="sm" onclick={handleDrawerSave}>Create Task</Button>
    {:else if selectedTask}
      <Button variant="outline" size="sm" onclick={closeTaskSheet}>Cancel</Button>
      {#if isCompleted}
        <Button variant="outline" size="sm" onclick={reopenSelectedTask}>
          <RotateCcw class="mr-2 h-4 w-4" />
          Reopen
        </Button>
      {:else}
        <Button variant="outline" size="sm" onclick={completeSelectedTask}>
          <CheckCircle2 class="mr-2 h-4 w-4" />
          Complete
        </Button>
      {/if}
      <Button size="sm" onclick={handleDrawerUpdate}>Save</Button>
    {/if}
  {/snippet}
</CrmDrawer>

<!-- Hidden forms for server actions -->
<form
  method="POST"
  action="?/create"
  bind:this={createForm}
  use:enhance={createEnhanceHandler('Task created successfully', true)}
  class="hidden"
>
  <input type="hidden" name="subject" value={formState.subject} />
  <input type="hidden" name="description" value={formState.description} />
  <input type="hidden" name="status" value={formState.status} />
  <input type="hidden" name="priority" value={formState.priority} />
  <input type="hidden" name="dueDate" value={formState.dueDate} />
  <input type="hidden" name="accountId" value={formState.accountId} />
  <input type="hidden" name="opportunityId" value={formState.opportunityId} />
  <input type="hidden" name="caseId" value={formState.caseId} />
  <input type="hidden" name="leadId" value={formState.leadId} />
  <input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
  <input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
  <input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
  <input type="hidden" name="tags" value={JSON.stringify(formState.tags)} />
</form>

<form
  method="POST"
  action="?/update"
  bind:this={updateForm}
  use:enhance={createEnhanceHandler('Task updated successfully', true)}
  class="hidden"
>
  <input type="hidden" name="taskId" value={formState.taskId} />
  <input type="hidden" name="subject" value={formState.subject} />
  <input type="hidden" name="description" value={formState.description} />
  <input type="hidden" name="status" value={formState.status} />
  <input type="hidden" name="priority" value={formState.priority} />
  <input type="hidden" name="dueDate" value={formState.dueDate} />
  <input type="hidden" name="accountId" value={formState.accountId} />
  <input type="hidden" name="opportunityId" value={formState.opportunityId} />
  <input type="hidden" name="caseId" value={formState.caseId} />
  <input type="hidden" name="leadId" value={formState.leadId} />
  <input type="hidden" name="assignedTo" value={JSON.stringify(formState.assignedTo)} />
  <input type="hidden" name="contacts" value={JSON.stringify(formState.contacts)} />
  <input type="hidden" name="teams" value={JSON.stringify(formState.teams)} />
  <input type="hidden" name="tags" value={JSON.stringify(formState.tags)} />
</form>

<form
  method="POST"
  action="?/delete"
  bind:this={deleteForm}
  use:enhance={createEnhanceHandler('Task deleted successfully', true)}
  class="hidden"
>
  <input type="hidden" name="taskId" value={formState.taskId} />
</form>

<form
  method="POST"
  action="?/complete"
  bind:this={completeForm}
  use:enhance={createEnhanceHandler('Task completed successfully', true)}
  class="hidden"
>
  <input type="hidden" name="taskId" value={formState.taskId} />
</form>

<form
  method="POST"
  action="?/reopen"
  bind:this={reopenForm}
  use:enhance={createEnhanceHandler('Task reopened successfully', true)}
  class="hidden"
>
  <input type="hidden" name="taskId" value={formState.taskId} />
</form>

<form
  method="POST"
  action="?/moveTask"
  bind:this={moveTaskForm}
  use:enhance={createEnhanceHandler('Task moved successfully', false)}
  class="hidden"
>
  <input type="hidden" name="taskId" value={kanbanFormState.taskId} />
  <input type="hidden" name="status" value={kanbanFormState.status} />
  <input type="hidden" name="stageId" value={kanbanFormState.stageId} />
  <input type="hidden" name="aboveTaskId" value={kanbanFormState.aboveTaskId} />
  <input type="hidden" name="belowTaskId" value={kanbanFormState.belowTaskId} />
</form>
