<script>
  import { Building2, AlertTriangle, ShieldAlert, HelpCircle, AlertOctagon, FileWarning, Timer } from '@lucide/svelte';

  /**
   * @typedef {Object} Case
   * @property {string} id
   * @property {string} name
   * @property {string} status
   * @property {string} priority
   * @property {string} [case_type]
   * @property {string} [account_name]
   * @property {boolean} [is_sla_breached]
   * @property {boolean} [is_sla_first_response_breached]
   * @property {boolean} [is_sla_resolution_breached]
   * @property {Array<{id: string, user_details?: {email?: string}, email?: string}>} [assigned_to]
   */

  /** @type {{ item: Case, onclick?: () => void, ondragstart?: (e: DragEvent) => void, ondragend?: () => void }} */
  let { item, onclick, ondragstart, ondragend } = $props();

  // Priority configurations with icons and colors (matching LeadCard rating style)
  const priorityConfig = {
    Urgent: {
      icon: AlertOctagon,
      bg: 'bg-gradient-to-r from-rose-500/25 to-red-500/25',
      text: 'text-rose-600 dark:text-rose-400',
      border: 'border-rose-500/40',
      glow: 'shadow-rose-500/20',
      pulse: true
    },
    High: {
      icon: AlertTriangle,
      bg: 'bg-gradient-to-r from-orange-500/20 to-amber-500/20',
      text: 'text-orange-600 dark:text-orange-400',
      border: 'border-orange-500/30',
      glow: 'shadow-orange-500/10',
      pulse: false
    },
    Normal: {
      icon: ShieldAlert,
      bg: 'bg-gradient-to-r from-blue-500/15 to-indigo-500/15',
      text: 'text-blue-600 dark:text-blue-400',
      border: 'border-blue-500/25',
      glow: 'shadow-blue-500/10',
      pulse: false
    },
    Low: {
      icon: ShieldAlert,
      bg: 'bg-gradient-to-r from-slate-500/10 to-gray-500/10',
      text: 'text-slate-600 dark:text-slate-400',
      border: 'border-slate-500/20',
      glow: 'shadow-slate-500/10',
      pulse: false
    }
  };

  // Case type configurations with icons and colors
  const caseTypeConfig = {
    Question: {
      icon: HelpCircle,
      bg: 'bg-gradient-to-r from-violet-500/15 to-purple-500/15',
      text: 'text-violet-600 dark:text-violet-400',
      label: 'Question'
    },
    Incident: {
      icon: FileWarning,
      bg: 'bg-gradient-to-r from-amber-500/15 to-yellow-500/15',
      text: 'text-amber-600 dark:text-amber-400',
      label: 'Incident'
    },
    Problem: {
      icon: AlertOctagon,
      bg: 'bg-gradient-to-r from-rose-500/15 to-red-500/15',
      text: 'text-rose-600 dark:text-rose-400',
      label: 'Problem'
    }
  };

  // Computed values
  const name = $derived(item.name || 'Untitled Case');
  const priority = $derived(item.priority);
  const caseType = $derived(item.case_type);
  const accountName = $derived(item.account_name);
  const isSlaBreached = $derived(
    item.is_sla_breached || item.is_sla_first_response_breached || item.is_sla_resolution_breached
  );
  const assignees = $derived(item.assigned_to || []);
  const config = $derived(priority ? priorityConfig[priority] : null);
  const typeConfig = $derived(caseType ? caseTypeConfig[caseType] : null);

  /**
   * Get initials from assignee
   * @param {any} assignee
   */
  function getAssigneeInitials(assignee) {
    const email = assignee?.user_details?.email || assignee?.email || '';
    if (!email) return '?';
    return email.charAt(0).toUpperCase();
  }

  /**
   * Get assignee display name
   * @param {any} assignee
   */
  function getAssigneeName(assignee) {
    return assignee?.user_details?.email || assignee?.email || 'Unknown';
  }

  // Generate a consistent color from email for avatar (matching LeadCard style)
  function getAvatarColor(email) {
    const colors = [
      'from-violet-500 to-purple-600',
      'from-cyan-500 to-blue-600',
      'from-emerald-500 to-teal-600',
      'from-amber-500 to-orange-600',
      'from-rose-500 to-pink-600',
      'from-indigo-500 to-blue-600'
    ];
    const hash = email.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[hash % colors.length];
  }

  /**
   * Handle keyboard events
   * @param {KeyboardEvent} e
   */
  function handleKeydown(e) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      onclick?.();
    }
  }
</script>

<div
  class="case-card group relative cursor-pointer overflow-hidden rounded-xl border transition-all duration-300 ease-out
    {isSlaBreached ? 'border-l-[3px] border-l-rose-500' : 'border-white/10 dark:border-white/[0.06]'}
    bg-white/80 dark:bg-white/[0.03]
    backdrop-blur-sm
    hover:border-white/20 dark:hover:border-white/[0.1]
    hover:shadow-lg hover:shadow-black/5 dark:hover:shadow-black/20
    hover:-translate-y-0.5"
  class:urgent-card={priority === 'Urgent'}
  class:sla-breach-card={isSlaBreached}
  draggable="true"
  {onclick}
  onkeydown={handleKeydown}
  {ondragstart}
  {ondragend}
  role="button"
  tabindex="0"
>
  <!-- Subtle gradient overlay for depth -->
  <div class="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/50 via-transparent to-transparent dark:from-white/[0.02]"></div>

  <!-- Urgent/SLA breach animated glow -->
  {#if priority === 'Urgent' || isSlaBreached}
    <div class="urgent-glow pointer-events-none absolute -inset-[1px] rounded-xl bg-gradient-to-r from-rose-500/20 via-red-500/20 to-rose-500/20 opacity-0 blur-sm transition-opacity duration-300 group-hover:opacity-100"></div>
  {/if}

  <div class="relative p-3.5">
    <!-- Header: Title + SLA Warning -->
    <div class="flex items-start justify-between gap-2">
      <h4 class="flex-1 truncate text-[0.9rem] font-semibold leading-tight tracking-tight text-gray-900 dark:text-white/95">
        {name}
      </h4>

      {#if isSlaBreached}
        <div class="sla-warning flex shrink-0 items-center gap-1 rounded-full bg-gradient-to-r from-rose-500/25 to-red-500/25 px-2 py-0.5 text-rose-600 dark:text-rose-400" title="SLA Breached">
          <Timer class="h-3.5 w-3.5" />
          <span class="text-[0.6rem] font-bold uppercase tracking-wider">SLA</span>
        </div>
      {/if}
    </div>

    <!-- Account -->
    {#if accountName}
      <div class="mt-1.5 flex items-center gap-1.5">
        <Building2 class="h-3.5 w-3.5 shrink-0 text-gray-400 dark:text-gray-500" />
        <span class="truncate text-sm text-gray-600 dark:text-gray-400">{accountName}</span>
      </div>
    {/if}

    <!-- Meta row: Case Type + Priority -->
    <div class="mt-3 flex items-center gap-2">
      {#if typeConfig}
        {@const TypeIcon = typeConfig.icon}
        <div class="flex items-center gap-1 rounded-lg px-2 py-1 {typeConfig.bg}">
          <TypeIcon class="h-3.5 w-3.5 {typeConfig.text}" />
          <span class="text-xs font-medium {typeConfig.text}">{typeConfig.label}</span>
        </div>
      {/if}

      {#if config}
        {@const PriorityIcon = config.icon}
        <div class="priority-badge flex shrink-0 items-center gap-1 rounded-full px-2 py-0.5 text-[0.65rem] font-bold uppercase tracking-wider {config.bg} {config.text} {config.border} border"
          class:priority-pulse={config.pulse}>
          <PriorityIcon class="h-3 w-3" />
          {priority}
        </div>
      {/if}
    </div>

    <!-- Footer: Assignees -->
    {#if assignees.length > 0}
      <div class="mt-3 flex items-center justify-between">
        <div class="flex items-center -space-x-2">
          {#each assignees.slice(0, 3) as assignee, i (assignee.id)}
            <div
              class="relative flex h-7 w-7 items-center justify-center rounded-full bg-gradient-to-br {getAvatarColor(getAssigneeName(assignee))} text-[0.7rem] font-semibold text-white shadow-sm ring-2 ring-white dark:ring-gray-900"
              style="z-index: {3 - i}"
              title={getAssigneeName(assignee)}
            >
              {getAssigneeInitials(assignee)}
            </div>
          {/each}
          {#if assignees.length > 3}
            <div
              class="relative flex h-7 w-7 items-center justify-center rounded-full bg-gray-200 text-[0.65rem] font-bold text-gray-600 ring-2 ring-white dark:bg-gray-700 dark:text-gray-300 dark:ring-gray-900"
              style="z-index: 0"
            >
              +{assignees.length - 3}
            </div>
          {/if}
        </div>

        <!-- Urgent indicator -->
        {#if priority === 'Urgent' && !isSlaBreached}
          <div class="flex items-center gap-1 text-rose-500 dark:text-rose-400" title="Urgent priority">
            <AlertOctagon class="h-4 w-4" />
          </div>
        {/if}
      </div>
    {/if}
  </div>
</div>

<style>
  .case-card {
    --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
    box-shadow: var(--card-shadow);
  }

  .case-card:hover {
    --card-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.08), 0 8px 10px -6px rgba(0, 0, 0, 0.04);
  }

  :global(.dark) .case-card {
    --card-shadow: 0 1px 3px rgba(0, 0, 0, 0.2), 0 1px 2px rgba(0, 0, 0, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.03);
  }

  :global(.dark) .case-card:hover {
    --card-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.4), 0 8px 20px -8px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
  }

  .case-card:active {
    cursor: grabbing;
    transform: rotate(1.5deg) scale(1.03);
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.2);
  }

  :global(.dark) .case-card:active {
    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 30px -5px rgba(34, 211, 238, 0.15);
  }

  .case-card:focus-visible {
    outline: 2px solid rgb(34 211 238);
    outline-offset: 2px;
  }

  /* Urgent card special styling */
  .urgent-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(255, 251, 250, 0.95) 100%);
  }

  :global(.dark) .urgent-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0%, rgba(251, 113, 133, 0.03) 100%);
  }

  /* SLA breach card special styling */
  .sla-breach-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(254, 242, 242, 0.95) 100%);
  }

  :global(.dark) .sla-breach-card {
    background: linear-gradient(135deg, rgba(255, 255, 255, 0.04) 0%, rgba(239, 68, 68, 0.05) 100%);
  }

  /* SLA warning badge animation */
  .sla-warning {
    animation: sla-pulse 2s ease-in-out infinite;
  }

  @keyframes sla-pulse {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.6;
    }
  }

  /* Priority badge pulse for Urgent */
  .priority-pulse {
    animation: pulse-glow 2s ease-in-out infinite;
  }

  @keyframes pulse-glow {
    0%, 100% {
      opacity: 1;
    }
    50% {
      opacity: 0.7;
    }
  }

  /* Urgent glow effect */
  .urgent-glow {
    background-size: 200% 100%;
    animation: shimmer-glow 3s ease-in-out infinite;
  }

  @keyframes shimmer-glow {
    0%, 100% {
      background-position: 0% 50%;
    }
    50% {
      background-position: 100% 50%;
    }
  }
</style>
