<script>
  import { invalidateAll } from '$app/navigation';
  import { page } from '$app/stores';
  import { toast } from 'svelte-sonner';
  import { Plus, Trophy, Target, User, Users, Trash2, X } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import { SearchInput } from '$lib/components/ui/filter';
  import { Pagination } from '$lib/components/ui/pagination';
  import { Progress } from '$lib/components/ui/progress/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import * as Select from '$lib/components/ui/select/index.js';
  import * as Sheet from '$lib/components/ui/sheet/index.js';
  import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
  import { formatCurrency } from '$lib/utils/formatting.js';
  import { orgSettings } from '$lib/stores/org.js';
  import { getCurrentUser } from '$lib/api.js';

  const goalTypeOptions = [
    {
      value: 'REVENUE',
      label: 'Revenue',
      color: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400'
    },
    {
      value: 'DEALS_CLOSED',
      label: 'Deals Closed',
      color: 'bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400'
    }
  ];

  const periodTypeOptions = [
    { value: 'MONTHLY', label: 'Monthly' },
    { value: 'QUARTERLY', label: 'Quarterly' },
    { value: 'YEARLY', label: 'Yearly' },
    { value: 'CUSTOM', label: 'Custom' }
  ];

  const statusOptions = [
    {
      value: 'on_track',
      label: 'On Track',
      color: 'bg-emerald-50 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-400'
    },
    {
      value: 'at_risk',
      label: 'At Risk',
      color: 'bg-amber-50 text-amber-700 dark:bg-amber-500/15 dark:text-amber-400'
    },
    {
      value: 'behind',
      label: 'Behind',
      color: 'bg-red-50 text-red-700 dark:bg-red-500/15 dark:text-red-400'
    },
    {
      value: 'completed',
      label: 'Completed',
      color: 'bg-blue-50 text-blue-700 dark:bg-blue-500/15 dark:text-blue-400'
    }
  ];

  /** @type {{ data: any }} */
  let { data } = $props();

  const orgCurrency = $derived($orgSettings.default_currency || 'USD');
  const currentUser = $derived(getCurrentUser());
  const isAdmin = $derived(currentUser?.role === 'ADMIN' || currentUser?.is_superuser);

  const userOptions = $derived(
    (data.options?.users || []).map((u) => ({
      id: u.id,
      name: u.name || u.email,
      email: u.email
    }))
  );

  const teamOptions = $derived(
    (data.options?.teams || []).map((t) => ({
      id: t.id,
      name: t.name
    }))
  );

  // Drawer state
  let drawerOpen = $state(false);
  let selectedGoal = $state(null);
  let isCreating = $state(false);

  // Filter state
  let activeFilter = $state('all');
  let searchValue = $state('');

  // Delete confirmation
  let deleteDialogOpen = $state(false);
  let goalToDelete = $state(null);

  // Form state
  let formData = $state({
    name: '',
    goalType: 'REVENUE',
    targetValue: '',
    periodType: 'MONTHLY',
    periodStart: '',
    periodEnd: '',
    assignedTo: '',
    team: ''
  });

  /**
   * Format period display
   * @param {any} row
   */
  function formatPeriod(row) {
    if (!row.periodStart || !row.periodEnd) return '-';
    const start = new Date(row.periodStart);
    const end = new Date(row.periodEnd);
    const monthNames = [
      'Jan',
      'Feb',
      'Mar',
      'Apr',
      'May',
      'Jun',
      'Jul',
      'Aug',
      'Sep',
      'Oct',
      'Nov',
      'Dec'
    ];
    if (row.periodType === 'MONTHLY') {
      return `${monthNames[start.getMonth()]} ${start.getFullYear()}`;
    }
    if (row.periodType === 'QUARTERLY') {
      const quarter = Math.floor(start.getMonth() / 3) + 1;
      return `Q${quarter} ${start.getFullYear()}`;
    }
    if (row.periodType === 'YEARLY') {
      return `${start.getFullYear()}`;
    }
    return `${monthNames[start.getMonth()]} ${start.getDate()} - ${monthNames[end.getMonth()]} ${end.getDate()}, ${end.getFullYear()}`;
  }

  /**
   * Get period dates based on period type
   * @param {string} periodType
   */
  function getDefaultPeriodDates(periodType) {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();

    switch (periodType) {
      case 'MONTHLY': {
        const start = new Date(year, month, 1);
        const end = new Date(year, month + 1, 0);
        return {
          start: start.toISOString().split('T')[0],
          end: end.toISOString().split('T')[0]
        };
      }
      case 'QUARTERLY': {
        const qStart = Math.floor(month / 3) * 3;
        const start = new Date(year, qStart, 1);
        const end = new Date(year, qStart + 3, 0);
        return {
          start: start.toISOString().split('T')[0],
          end: end.toISOString().split('T')[0]
        };
      }
      case 'YEARLY': {
        return {
          start: `${year}-01-01`,
          end: `${year}-12-31`
        };
      }
      default:
        return { start: '', end: '' };
    }
  }

  function openCreateDrawer() {
    isCreating = true;
    selectedGoal = null;
    const dates = getDefaultPeriodDates('MONTHLY');
    formData = {
      name: '',
      goalType: 'REVENUE',
      targetValue: '',
      periodType: 'MONTHLY',
      periodStart: dates.start,
      periodEnd: dates.end,
      assignedTo: '',
      team: ''
    };
    drawerOpen = true;
  }

  /** @param {any} goal */
  function openEditDrawer(goal) {
    isCreating = false;
    selectedGoal = goal;
    formData = {
      name: goal.name,
      goalType: goal.goalType,
      targetValue: String(goal.targetValue),
      periodType: goal.periodType,
      periodStart: goal.periodStart || '',
      periodEnd: goal.periodEnd || '',
      assignedTo: goal.assignedToId || '',
      team: goal.teamId || ''
    };
    drawerOpen = true;
  }

  /** @param {string} periodType */
  function handlePeriodTypeChange(periodType) {
    formData.periodType = periodType;
    if (periodType !== 'CUSTOM') {
      const dates = getDefaultPeriodDates(periodType);
      formData.periodStart = dates.start;
      formData.periodEnd = dates.end;
    }
  }

  /** @param {Event} e */
  async function handleSubmit(e) {
    e.preventDefault();
    const form = /** @type {HTMLFormElement} */ (e.target);
    const fd = new FormData(form);

    // Set form data values
    fd.set('name', formData.name);
    fd.set('goalType', formData.goalType);
    fd.set('targetValue', formData.targetValue);
    fd.set('periodType', formData.periodType);
    fd.set('periodStart', formData.periodStart);
    fd.set('periodEnd', formData.periodEnd);
    if (formData.assignedTo) fd.set('assignedTo', formData.assignedTo);
    if (formData.team) fd.set('team', formData.team);

    if (!isCreating && selectedGoal) {
      fd.set('goalId', selectedGoal.id);
    }

    try {
      const response = await fetch(
        isCreating ? '?/create' : '?/update',
        { method: 'POST', body: fd }
      );
      const result = await response.json();

      if (result.type === 'success' || result.data?.success) {
        toast.success(isCreating ? 'Goal created successfully' : 'Goal updated successfully');
        drawerOpen = false;
        await invalidateAll();
      } else {
        toast.error(result.data?.message || 'Failed to save goal');
      }
    } catch (err) {
      toast.error('Failed to save goal');
    }
  }

  /** @param {any} goal */
  function confirmDelete(goal) {
    goalToDelete = goal;
    deleteDialogOpen = true;
  }

  async function handleDelete() {
    if (!goalToDelete) return;

    const fd = new FormData();
    fd.set('goalId', goalToDelete.id);

    try {
      const response = await fetch('?/delete', { method: 'POST', body: fd });
      const result = await response.json();

      if (result.type === 'success' || result.data?.success) {
        toast.success('Goal deleted successfully');
        deleteDialogOpen = false;
        goalToDelete = null;
        drawerOpen = false;
        await invalidateAll();
      } else {
        toast.error(result.data?.message || 'Failed to delete goal');
      }
    } catch (err) {
      toast.error('Failed to delete goal');
    }
  }

  // Filter goals
  const filteredGoals = $derived.by(() => {
    let goals = data.goals || [];

    if (activeFilter === 'active') {
      goals = goals.filter((g) => g.isActive && g.status !== 'completed');
    } else if (activeFilter === 'completed') {
      goals = goals.filter((g) => g.status === 'completed');
    } else if (activeFilter === 'behind') {
      goals = goals.filter((g) => g.status === 'behind' || g.status === 'at_risk');
    }

    if (searchValue) {
      goals = goals.filter((g) => g.name.toLowerCase().includes(searchValue.toLowerCase()));
    }

    return goals;
  });

  /**
   * Get color class for status
   * @param {string} statusValue
   */
  function getStatusColor(statusValue) {
    switch (statusValue) {
      case 'on_track':
        return 'text-emerald-600 dark:text-emerald-400';
      case 'at_risk':
        return 'text-amber-600 dark:text-amber-400';
      case 'behind':
        return 'text-red-600 dark:text-red-400';
      case 'completed':
        return 'text-blue-600 dark:text-blue-400';
      default:
        return 'text-[var(--text-secondary)]';
    }
  }

  /**
   * Get progress bar color
   * @param {number} percent
   */
  function getProgressColor(percent) {
    if (percent >= 100) return '[&>[data-slot=progress-indicator]]:bg-blue-500';
    if (percent >= 75) return '[&>[data-slot=progress-indicator]]:bg-emerald-500';
    if (percent >= 50) return '[&>[data-slot=progress-indicator]]:bg-amber-500';
    return '[&>[data-slot=progress-indicator]]:bg-red-500';
  }
</script>

<svelte:head>
  <title>Sales Goals - BottleCRM</title>
</svelte:head>

<div class="space-y-6 p-6 md:p-8">
  <!-- Header -->
  <div class="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
    <div class="flex items-center gap-3">
      <div
        class="flex size-10 items-center justify-center rounded-[var(--radius-lg)] bg-gradient-to-br from-amber-500 to-orange-600 shadow-lg"
      >
        <Trophy class="size-5 text-white" />
      </div>
      <div>
        <h1 class="text-2xl font-bold tracking-tight text-[var(--text-primary)]">Sales Goals</h1>
        <p class="text-sm text-[var(--text-secondary)]">
          Track targets and measure team performance
        </p>
      </div>
    </div>

    {#if isAdmin}
      <Button onclick={openCreateDrawer} class="gap-2">
        <Plus class="size-4" />
        New Goal
      </Button>
    {/if}
  </div>

  <!-- Filter Chips -->
  <div class="flex items-center gap-2">
    {#each [
      { key: 'all', label: 'All' },
      { key: 'active', label: 'Active' },
      { key: 'completed', label: 'Completed' },
      { key: 'behind', label: 'Needs Attention' }
    ] as filter}
      <button
        class="rounded-full px-3 py-1.5 text-xs font-medium transition-colors {activeFilter ===
        filter.key
          ? 'bg-[var(--color-primary-default)] text-white'
          : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)] hover:bg-[var(--surface-raised)]'}"
        onclick={() => (activeFilter = filter.key)}
      >
        {filter.label}
      </button>
    {/each}

    <div class="ml-auto w-64">
      <SearchInput bind:value={searchValue} placeholder="Search goals..." />
    </div>
  </div>

  <!-- Goals Table -->
  {#if filteredGoals.length === 0}
    <div
      class="flex flex-col items-center justify-center rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--surface-raised)] py-16"
    >
      <div
        class="mb-4 flex size-16 items-center justify-center rounded-full bg-amber-50 dark:bg-amber-500/10"
      >
        <Target class="size-8 text-amber-500" />
      </div>
      <h3 class="mb-1 text-lg font-semibold text-[var(--text-primary)]">No goals set yet</h3>
      <p class="mb-4 text-sm text-[var(--text-secondary)]">
        Create your first sales goal to start tracking performance.
      </p>
      {#if isAdmin}
        <Button onclick={openCreateDrawer} variant="outline" class="gap-2">
          <Plus class="size-4" />
          Create Goal
        </Button>
      {/if}
    </div>
  {:else}
    <div
      class="overflow-hidden rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--surface-raised)]"
    >
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-[var(--border-default)] bg-[var(--surface-sunken)]">
            {#each ['Goal', 'Type', 'Target', 'Progress', 'Period', 'Assigned To', 'Status'] as label}
              <th
                class="px-4 py-3 text-left text-xs font-semibold tracking-wider text-[var(--text-secondary)] uppercase"
              >
                {label}
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each filteredGoals as goal (goal.id)}
            <tr
              class="cursor-pointer border-b border-[var(--border-default)] transition-colors hover:bg-[var(--surface-sunken)]/50"
              onclick={() => openEditDrawer(goal)}
            >
              <!-- Name -->
              <td class="px-4 py-3 font-medium text-[var(--text-primary)]">
                {goal.name}
              </td>
              <!-- Type -->
              <td class="px-4 py-3">
                <span class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium {goalTypeOptions.find((o) => o.value === goal.goalType)?.color || ''}">
                  {goalTypeOptions.find((o) => o.value === goal.goalType)?.label || goal.goalType}
                </span>
              </td>
              <!-- Target -->
              <td class="px-4 py-3 text-[var(--text-primary)]">
                {#if goal.goalType === 'REVENUE'}
                  {formatCurrency(goal.targetValue, orgCurrency, true)}
                {:else}
                  {goal.targetValue} deals
                {/if}
              </td>
              <!-- Progress -->
              <td class="px-4 py-3">
                <div class="flex items-center gap-2">
                  <Progress
                    value={goal.progressPercent}
                    max={100}
                    class="h-2 w-20 {getProgressColor(goal.progressPercent)}"
                  />
                  <span class="text-xs font-medium text-[var(--text-primary)]">
                    {goal.progressPercent}%
                  </span>
                </div>
              </td>
              <!-- Period -->
              <td class="px-4 py-3 text-[var(--text-secondary)]">
                {formatPeriod(goal)}
              </td>
              <!-- Assigned To -->
              <td class="px-4 py-3">
                {#if goal.assignedTo}
                  <div class="flex items-center gap-1.5">
                    <User class="size-3.5 text-[var(--text-tertiary)]" />
                    <span class="text-[var(--text-secondary)]">{goal.assignedTo.name}</span>
                  </div>
                {:else if goal.team}
                  <div class="flex items-center gap-1.5">
                    <Users class="size-3.5 text-[var(--text-tertiary)]" />
                    <span class="text-[var(--text-secondary)]">{goal.team.name}</span>
                  </div>
                {:else}
                  <span class="text-[var(--text-tertiary)]">-</span>
                {/if}
              </td>
              <!-- Status -->
              <td class="px-4 py-3">
                <span
                  class="inline-flex rounded-full px-2 py-0.5 text-xs font-medium {statusOptions.find((o) => o.value === goal.status)?.color || ''}"
                >
                  {statusOptions.find((o) => o.value === goal.status)?.label || goal.status}
                </span>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {/if}

  <!-- Pagination -->
  {#if data.pagination && data.pagination.total > data.pagination.limit}
    <Pagination
      page={data.pagination.page}
      total={data.pagination.total}
      limit={data.pagination.limit}
    />
  {/if}

  <!-- Leaderboard Section -->
  {#if data.leaderboard && data.leaderboard.length > 0}
    <div
      class="rounded-[var(--radius-xl)] border border-[var(--border-default)] bg-[var(--surface-raised)] p-6"
    >
      <div class="mb-4 flex items-center gap-3">
        <div
          class="flex size-9 items-center justify-center rounded-[var(--radius-md)] bg-amber-50 dark:bg-amber-500/15"
        >
          <Trophy class="size-5 text-amber-500" />
        </div>
        <div>
          <h2 class="text-base font-semibold text-[var(--text-primary)]">Leaderboard</h2>
          <p class="text-xs text-[var(--text-tertiary)]">Current period top performers</p>
        </div>
      </div>

      <div class="space-y-3">
        {#each data.leaderboard as entry (entry.goalId)}
          <div
            class="flex items-center gap-4 rounded-[var(--radius-md)] border border-[var(--border-default)] p-3"
          >
            <!-- Rank -->
            <div
              class="flex size-8 items-center justify-center rounded-full text-sm font-bold
                {entry.rank === 1
                ? 'bg-amber-100 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400'
                : entry.rank === 2
                  ? 'bg-gray-100 text-gray-600 dark:bg-gray-500/20 dark:text-gray-400'
                  : entry.rank === 3
                    ? 'bg-orange-100 text-orange-600 dark:bg-orange-500/20 dark:text-orange-400'
                    : 'bg-[var(--surface-sunken)] text-[var(--text-secondary)]'}"
            >
              {entry.rank}
            </div>
            <!-- User Info -->
            <div class="min-w-0 flex-1">
              <p class="truncate text-sm font-medium text-[var(--text-primary)]">
                {entry.user?.name || entry.user?.email}
              </p>
              <p class="text-xs text-[var(--text-tertiary)]">{entry.goalName}</p>
            </div>
            <!-- Progress -->
            <div class="flex items-center gap-3">
              <Progress
                value={entry.percent}
                max={100}
                class="h-1.5 w-24 {getProgressColor(entry.percent)}"
              />
              <span class="w-12 text-right text-sm font-semibold text-[var(--text-primary)]">
                {entry.percent}%
              </span>
            </div>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</div>

<!-- Create/Edit Drawer -->
<Sheet.Root bind:open={drawerOpen}>
  <Sheet.Content side="right" class="w-[480px] overflow-hidden border-l p-0 sm:max-w-[480px]">
    <form onsubmit={handleSubmit} class="flex h-full flex-col">
      <!-- Header -->
      <div class="flex items-center justify-between border-b border-[var(--border-default)] px-6 py-4">
        <div class="flex items-center gap-2">
          <span class="rounded-md bg-[var(--color-primary-default)]/10 px-2 py-1 text-xs font-semibold uppercase text-[var(--color-primary-default)]">
            Goal
          </span>
          {#if isCreating}
            <span class="text-xs text-[var(--text-tertiary)]">New</span>
          {/if}
        </div>
        <button
          type="button"
          onclick={() => (drawerOpen = false)}
          class="flex size-8 items-center justify-center rounded-lg text-[var(--text-secondary)] transition-colors hover:bg-[var(--surface-sunken)]"
        >
          <X class="size-4" />
        </button>
      </div>
      <div class="flex-1 space-y-4 overflow-y-auto p-6">
      <!-- Name -->
      <div>
        <label for="goal-name" class="mb-1.5 block text-xs font-medium text-[var(--text-secondary)]"
          >Goal Name</label
        >
        <Input id="goal-name" bind:value={formData.name} placeholder="e.g., Q1 Revenue Target" required />
      </div>

      <!-- Goal Type -->
      <div>
        <label for="goal-type" class="mb-1.5 block text-xs font-medium text-[var(--text-secondary)]"
          >Goal Type</label
        >
        <Select.Root
          type="single"
          value={formData.goalType}
          onValueChange={(v) => (formData.goalType = v)}
        >
          <Select.Trigger class="w-full">
            {goalTypeOptions.find((o) => o.value === formData.goalType)?.label || 'Select type'}
          </Select.Trigger>
          <Select.Content>
            {#each goalTypeOptions as opt}
              <Select.Item value={opt.value}>{opt.label}</Select.Item>
            {/each}
          </Select.Content>
        </Select.Root>
      </div>

      <!-- Target Value -->
      <div>
        <label
          for="target-value"
          class="mb-1.5 block text-xs font-medium text-[var(--text-secondary)]"
        >
          Target {formData.goalType === 'REVENUE' ? 'Amount' : 'Count'}
        </label>
        <Input
          id="target-value"
          type="number"
          step={formData.goalType === 'REVENUE' ? '0.01' : '1'}
          min="1"
          bind:value={formData.targetValue}
          placeholder={formData.goalType === 'REVENUE' ? '100000' : '50'}
          required
        />
      </div>

      <!-- Period Type -->
      <div>
        <label class="mb-1.5 block text-xs font-medium text-[var(--text-secondary)]"
          >Period Type</label
        >
        <Select.Root
          type="single"
          value={formData.periodType}
          onValueChange={(v) => handlePeriodTypeChange(v)}
        >
          <Select.Trigger class="w-full">
            {periodTypeOptions.find((o) => o.value === formData.periodType)?.label || 'Select period'}
          </Select.Trigger>
          <Select.Content>
            {#each periodTypeOptions as opt}
              <Select.Item value={opt.value}>{opt.label}</Select.Item>
            {/each}
          </Select.Content>
        </Select.Root>
      </div>

      <!-- Period Dates -->
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label
            for="period-start"
            class="mb-1.5 block text-xs font-medium text-[var(--text-secondary)]">Start Date</label
          >
          <Input
            id="period-start"
            type="date"
            bind:value={formData.periodStart}
            required
            disabled={formData.periodType !== 'CUSTOM'}
          />
        </div>
        <div>
          <label
            for="period-end"
            class="mb-1.5 block text-xs font-medium text-[var(--text-secondary)]">End Date</label
          >
          <Input
            id="period-end"
            type="date"
            bind:value={formData.periodEnd}
            required
            disabled={formData.periodType !== 'CUSTOM'}
          />
        </div>
      </div>

      <!-- Assigned To -->
      <div>
        <label class="mb-1.5 block text-xs font-medium text-[var(--text-secondary)]"
          >Assign to User</label
        >
        <Select.Root
          type="single"
          value={formData.assignedTo}
          onValueChange={(v) => {
            formData.assignedTo = v;
            if (v) formData.team = '';
          }}
        >
          <Select.Trigger class="w-full">
            {userOptions.find((u) => u.id === formData.assignedTo)?.name || 'Select user (optional)'}
          </Select.Trigger>
          <Select.Content>
            <Select.Item value="">None</Select.Item>
            {#each userOptions as user}
              <Select.Item value={user.id}>{user.name}</Select.Item>
            {/each}
          </Select.Content>
        </Select.Root>
      </div>

      <!-- Team -->
      <div>
        <label class="mb-1.5 block text-xs font-medium text-[var(--text-secondary)]"
          >Assign to Team</label
        >
        <Select.Root
          type="single"
          value={formData.team}
          onValueChange={(v) => {
            formData.team = v;
            if (v) formData.assignedTo = '';
          }}
        >
          <Select.Trigger class="w-full">
            {teamOptions.find((t) => t.id === formData.team)?.name || 'Select team (optional)'}
          </Select.Trigger>
          <Select.Content>
            <Select.Item value="">None</Select.Item>
            {#each teamOptions as team}
              <Select.Item value={team.id}>{team.name}</Select.Item>
            {/each}
          </Select.Content>
        </Select.Root>
      </div>

      <!-- Progress (read-only, edit mode only) -->
      {#if !isCreating && selectedGoal}
        <div
          class="rounded-[var(--radius-md)] border border-[var(--border-default)] bg-[var(--surface-sunken)] p-4"
        >
          <h3 class="mb-3 text-sm font-semibold text-[var(--text-primary)]">Current Progress</h3>
          <div class="space-y-2">
            <div class="flex items-center justify-between text-sm">
              <span class="text-[var(--text-secondary)]">Progress</span>
              <span class="font-medium {getStatusColor(selectedGoal.status)}">
                {selectedGoal.progressPercent}%
              </span>
            </div>
            <Progress
              value={selectedGoal.progressPercent}
              max={100}
              class="h-2 {getProgressColor(selectedGoal.progressPercent)}"
            />
            <div class="flex items-center justify-between text-xs text-[var(--text-tertiary)]">
              <span>
                Achieved: {selectedGoal.goalType === 'REVENUE'
                  ? formatCurrency(selectedGoal.progressValue, orgCurrency, true)
                  : `${selectedGoal.progressValue} deals`}
              </span>
              <span>
                Target: {selectedGoal.goalType === 'REVENUE'
                  ? formatCurrency(selectedGoal.targetValue, orgCurrency, true)
                  : `${selectedGoal.targetValue} deals`}
              </span>
            </div>
          </div>
        </div>
      {/if}
    </div>

    <!-- Footer Actions -->
    <div
      class="flex items-center justify-between border-t border-[var(--border-default)] px-6 py-4"
    >
      <div>
        {#if !isCreating && selectedGoal && isAdmin}
          <Button
            type="button"
            variant="ghost"
            class="text-red-600 hover:bg-red-50 hover:text-red-700"
            onclick={() => confirmDelete(selectedGoal)}
          >
            <Trash2 class="mr-1.5 size-4" />
            Delete
          </Button>
        {/if}
      </div>
      <div class="flex gap-2">
        <Button type="button" variant="outline" onclick={() => (drawerOpen = false)}>
          Cancel
        </Button>
        {#if isAdmin}
          <Button type="submit">
            {isCreating ? 'Create Goal' : 'Save Changes'}
          </Button>
        {/if}
      </div>
    </div>
  </form>
  </Sheet.Content>
</Sheet.Root>

<!-- Delete Confirmation -->
<AlertDialog.Root bind:open={deleteDialogOpen}>
  <AlertDialog.Content>
    <AlertDialog.Header>
      <AlertDialog.Title>Delete Goal</AlertDialog.Title>
      <AlertDialog.Description>
        Are you sure you want to delete "{goalToDelete?.name}"? This action cannot be undone.
      </AlertDialog.Description>
    </AlertDialog.Header>
    <AlertDialog.Footer>
      <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
      <AlertDialog.Action
        class="bg-red-600 text-white hover:bg-red-700"
        onclick={handleDelete}
      >
        Delete
      </AlertDialog.Action>
    </AlertDialog.Footer>
  </AlertDialog.Content>
</AlertDialog.Root>
