<script>
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Card from '$lib/components/ui/card/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { Separator } from '$lib/components/ui/separator/index.js';
  import * as Table from '$lib/components/ui/table/index.js';
  import * as Progress from '$lib/components/ui/progress/index.js';
  import { PageHeader } from '$lib/components/layout';
  import { Download, CheckCircle, XCircle, Clock, Loader2, ArrowLeft, ChevronDown, ChevronRight, AlertTriangle } from '@lucide/svelte';
  import { formatRelativeDate } from '$lib/utils/formatting.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  // Server data (reactive to load function)
  let serverJob = $derived(data.activeJob);
  let serverHistory = $derived(data.importHistory || []);

  // Poll overrides (null = use server data)
  /** @type {any} */
  let polledJob = $state(null);
  /** @type {any[] | null} */
  let polledHistory = $state(null);

  // Effective values: poll data wins when present
  let activeJob = $derived(polledJob ?? serverJob);
  let importHistory = $derived(polledHistory ?? serverHistory);

  const OBJECT_TYPES = [
    { value: 'Account', label: 'Accounts', description: 'Companies and organizations', depends: [] },
    { value: 'Contact', label: 'Contacts', description: 'People associated with accounts', depends: ['Account'] },
    { value: 'Opportunity', label: 'Opportunities', description: 'Sales deals and pipeline', depends: ['Account'] },
    { value: 'Product2', label: 'Products', description: 'Product catalog', depends: [] },
    { value: 'Order', label: 'Orders', description: 'Sales orders', depends: ['Account'] },
    { value: 'Quote', label: 'Quotes', description: 'Price quotes and estimates', depends: ['Account', 'Contact'] }
  ];

  /** @type {Set<string>} */
  let selectedTypes = $state(new Set());
  let isStarting = $state(false);
  let isCancelling = $state(false);

  /** @type {ReturnType<typeof setInterval> | null} */
  let pollTimer = null;

  let isImportActive = $derived(
    activeJob && (activeJob.status === 'IN_PROGRESS' || activeJob.status === 'PENDING')
  );

  let overallProgress = $derived.by(() => {
    if (!activeJob) return 0;
    const total = activeJob.total_records || 0;
    const done = (activeJob.imported_count || 0) + (activeJob.skipped_count || 0) + (activeJob.error_count || 0);
    return total > 0 ? Math.round((done / total) * 100) : 0;
  });

  /** @type {Set<string>} */
  let expandedJobs = $state(new Set());

  function toggleJobExpand(/** @type {string} */ jobId) {
    const s = new Set(expandedJobs);
    s.has(jobId) ? s.delete(jobId) : s.add(jobId);
    expandedJobs = s;
  }

  function getObjectLabel(/** @type {string} */ value) {
    return OBJECT_TYPES.find((t) => t.value === value)?.label ?? value;
  }

  $effect(() => {
    if (form?.importError) toast.error(form.importError);
    if (form?.importCancelled) toast.success('Import cancelled');
  });

  // ── Polling ──────────────────────────────────────────────────────────
  let pollInFlight = false;

  async function pollJobStatus() {
    if (pollInFlight) return;
    pollInFlight = true;

    const jobId = activeJob?.id;
    if (!jobId) { pollInFlight = false; return; }

    try {
      const res = await fetch(`/api/salesforce-import-poll?job=${jobId}&_=${Date.now()}`);
      if (!res.ok) return;
      const result = await res.json();

      if (result.job) {
        polledJob = result.job;
      }
      if (result.jobs?.length) {
        polledHistory = result.jobs;
      }

      const st = result.job?.status;
      if (st && st !== 'IN_PROGRESS' && st !== 'PENDING') {
        stopPolling();
      }
    } catch {
      // ignore poll errors
    } finally {
      pollInFlight = false;
    }
  }

  function startPolling() {
    stopPolling();
    pollJobStatus();
    pollTimer = setInterval(pollJobStatus, 3000);
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer);
      pollTimer = null;
    }
  }

  // Track whether polling should be active separately to avoid reactive cycle
  // (isImportActive depends on polledJob which gets updated by polling)
  let shouldPoll = $state(false);

  $effect(() => {
    shouldPoll = !!isImportActive;
  });

  $effect(() => {
    if (shouldPoll) {
      startPolling();
    } else {
      stopPolling();
    }
    return () => stopPolling();
  });

  // ── Helpers ──────────────────────────────────────────────────────────
  function toggleType(/** @type {string} */ value) {
    const s = new Set(selectedTypes);
    s.has(value) ? s.delete(value) : s.add(value);
    selectedTypes = s;
  }

  function isSelected(/** @type {string} */ value) {
    return selectedTypes.has(value);
  }

  function getStatusBadgeClass(/** @type {string} */ s) {
    const map = /** @type {Record<string, string>} */ ({
      COMPLETED: 'bg-emerald-100 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-400 border-emerald-200 dark:border-emerald-800',
      FAILED: 'bg-red-100 text-red-700 dark:bg-red-950 dark:text-red-400 border-red-200 dark:border-red-800',
      CANCELLED: 'bg-amber-100 text-amber-700 dark:bg-amber-950 dark:text-amber-400 border-amber-200 dark:border-amber-800',
      IN_PROGRESS: 'bg-blue-100 text-blue-700 dark:bg-blue-950 dark:text-blue-400 border-blue-200 dark:border-blue-800',
      PENDING: 'bg-gray-100 text-gray-700 dark:bg-gray-800 dark:text-gray-400 border-gray-200 dark:border-gray-700',
    });
    return map[s] ?? map['PENDING'];
  }

  function getStatusIcon(/** @type {string} */ s) {
    return /** @type {Record<string, any>} */ ({ COMPLETED: CheckCircle, FAILED: XCircle, IN_PROGRESS: Loader2, PENDING: Clock })[s] ?? Clock;
  }
</script>

<svelte:head>
  <title>Salesforce Import - BottleCRM</title>
</svelte:head>

<PageHeader title="Import from Salesforce" subtitle="Select data to import">
  {#snippet actions()}
    <Button variant="outline" href="/settings/salesforce" class="gap-2">
      <ArrowLeft class="size-4" />
      Back to Connection
    </Button>
  {/snippet}
</PageHeader>

<div class="mx-auto max-w-4xl space-y-6 p-6 md:p-8">
  <!-- Active Import Progress -->
  {#if activeJob && isImportActive}
    <Card.Root class="border-blue-200 dark:border-blue-800">
      <Card.Header>
        <div class="flex items-center gap-3">
          <Loader2 class="size-5 animate-spin text-blue-600 dark:text-blue-400" />
          <div>
            <Card.Title>Import In Progress</Card.Title>
            <Card.Description>Your Salesforce data is being imported...</Card.Description>
          </div>
        </div>
      </Card.Header>
      <Card.Content>
        <div class="space-y-4">
          <div>
            <div class="mb-2 flex items-center justify-between text-sm">
              <span class="text-muted-foreground">Overall Progress</span>
              <span class="text-foreground font-medium">{overallProgress}%</span>
            </div>
            <Progress.Root value={overallProgress} max={100} class="h-2" />
          </div>

          {#if activeJob.progress_detail && Object.keys(activeJob.progress_detail).length > 0}
            <div class="space-y-3">
              {#each Object.entries(activeJob.progress_detail) as [objType, detail]}
                {@const imported = detail.imported || 0}
                {@const skipped = detail.skipped || 0}
                {@const errors = detail.errors || 0}
                {@const processed = imported + skipped + errors}
                {@const total = detail.total || processed}
                {@const pct = total > 0 ? Math.round((processed / total) * 100) : 0}
                {@const rawStatus = detail.status || 'importing'}
                {@const objStatus = rawStatus === 'done' ? 'COMPLETED' : rawStatus === 'importing' ? 'IN_PROGRESS' : rawStatus === 'error' ? 'FAILED' : 'PENDING'}
                {@const StatusIcon = getStatusIcon(objStatus)}
                <div class="bg-muted/50 rounded-lg p-3">
                  <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                      <StatusIcon
                        class="size-4 {objStatus === 'IN_PROGRESS'
                          ? 'animate-spin text-blue-600 dark:text-blue-400'
                          : objStatus === 'COMPLETED'
                            ? 'text-emerald-600 dark:text-emerald-400'
                            : objStatus === 'FAILED'
                              ? 'text-red-600 dark:text-red-400'
                              : 'text-muted-foreground'}"
                      />
                      <span class="text-foreground text-sm font-medium">{getObjectLabel(objType)}</span>
                      <Badge class={getStatusBadgeClass(objStatus)}>
                        {objStatus}
                      </Badge>
                    </div>
                  </div>
                  {#if processed > 0 || total > 0}
                    <div class="mt-2">
                      <Progress.Root value={pct} max={100} class="h-1" />
                    </div>
                    <div class="mt-1 flex gap-4 text-xs">
                      <span class="text-emerald-600 dark:text-emerald-400">{imported} imported</span>
                      <span class="text-amber-600 dark:text-amber-400">{skipped} skipped</span>
                      <span class="text-red-600 dark:text-red-400">{errors} errors</span>
                    </div>
                  {/if}
                </div>
              {/each}
            </div>
          {/if}

          <Separator />

          <form method="POST" action="?/cancelImport" use:enhance={() => {
            isCancelling = true;
            return async ({ update }) => {
              isCancelling = false;
              await update();
            };
          }}>
            <input type="hidden" name="job_id" value={activeJob.id} />
            <Button type="submit" variant="outline" disabled={isCancelling} class="text-destructive hover:bg-destructive/10 gap-2">
              <XCircle class="size-4" />
              {isCancelling ? 'Cancelling...' : 'Cancel Import'}
            </Button>
            <span class="text-muted-foreground ml-2 text-xs">Already-imported data will be kept.</span>
          </form>
        </div>
      </Card.Content>
    </Card.Root>
  {/if}

  <!-- Completion Summary -->
  {#if activeJob && !isImportActive}
    <Card.Root class={activeJob.status === 'COMPLETED' ? 'border-emerald-200 dark:border-emerald-800' : activeJob.status === 'CANCELLED' ? 'border-amber-200 dark:border-amber-800' : 'border-red-200 dark:border-red-800'}>
      <Card.Header>
        <div class="flex items-center gap-3">
          {#if activeJob.status === 'COMPLETED'}
            <CheckCircle class="size-5 text-emerald-600 dark:text-emerald-400" />
          {:else if activeJob.status === 'CANCELLED'}
            <AlertTriangle class="size-5 text-amber-600 dark:text-amber-400" />
          {:else}
            <XCircle class="size-5 text-red-600 dark:text-red-400" />
          {/if}
          <div>
            <Card.Title>Import {activeJob.status === 'COMPLETED' ? 'Completed' : activeJob.status === 'CANCELLED' ? 'Cancelled' : 'Failed'}</Card.Title>
            <Card.Description>
              {#if activeJob.status === 'COMPLETED'}
                Your Salesforce data has been imported successfully.
              {:else if activeJob.status === 'CANCELLED'}
                The import was cancelled. Already-imported data has been kept.
              {:else}
                The import encountered errors. Check the details below.
              {/if}
            </Card.Description>
          </div>
        </div>
      </Card.Header>
      <Card.Content>
        <div class="flex items-center justify-between text-sm">
          <span class="text-foreground font-medium">Total</span>
          <div class="flex gap-4 text-xs">
            <span class="text-emerald-600 dark:text-emerald-400">{activeJob.imported_count || 0} imported</span>
            <span class="text-amber-600 dark:text-amber-400">{activeJob.skipped_count || 0} skipped</span>
            <span class="text-red-600 dark:text-red-400">{activeJob.error_count || 0} errors</span>
          </div>
        </div>
      </Card.Content>
    </Card.Root>
  {/if}

  <!-- Object Type Selection -->
  {#if !isImportActive}
    <Card.Root>
      <Card.Header>
        <Card.Title>Select Data to Import</Card.Title>
        <Card.Description>Choose which Salesforce objects you want to import. Dependencies will be resolved automatically.</Card.Description>
      </Card.Header>
      <Card.Content>
        <div class="space-y-3">
          {#each OBJECT_TYPES as objType}
            <button
              type="button"
              onclick={() => toggleType(objType.value)}
              class="border-border hover:bg-muted/50 flex w-full items-start gap-3 rounded-lg border p-4 text-left transition-colors
                {isSelected(objType.value) ? 'border-blue-300 bg-blue-50/50 dark:border-blue-700 dark:bg-blue-950/30' : ''}"
            >
              <div class="mt-0.5 flex size-5 shrink-0 items-center justify-center rounded border transition-colors
                {isSelected(objType.value) ? 'border-blue-600 bg-blue-600 dark:border-blue-500 dark:bg-blue-500' : 'border-muted-foreground/30'}">
                {#if isSelected(objType.value)}
                  <svg class="size-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="3">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                {/if}
              </div>
              <div class="flex-1">
                <div class="text-foreground text-sm font-medium">{objType.label}</div>
                <div class="text-muted-foreground text-xs">{objType.description}</div>
                {#if objType.depends.length > 0}
                  <div class="text-muted-foreground/70 mt-1 text-xs">Depends on: {objType.depends.join(', ')}</div>
                {/if}
              </div>
            </button>
          {/each}
        </div>

        <div class="mt-6 flex items-center justify-between">
          <p class="text-muted-foreground text-sm">
            {selectedTypes.size} object{selectedTypes.size !== 1 ? 's' : ''} selected
          </p>
          <form method="POST" action="?/startImport" use:enhance={() => {
            isStarting = true;
            return async ({ result, update }) => {
              isStarting = false;
              if (result.type === 'success' && result.data?.jobId) {
                polledJob = null;
                polledHistory = null;
                toast.success('Import started');
                await goto(`?job=${result.data.jobId}`, { invalidateAll: true });
              } else {
                await update();
              }
            };
          }}>
            <input type="hidden" name="object_types" value={Array.from(selectedTypes).join(',')} />
            <Button type="submit" disabled={selectedTypes.size === 0 || isStarting}
              class="gap-2 border-0 bg-[var(--color-primary-default)] text-white hover:bg-[var(--color-primary-dark)]">
              <Download class="size-4" />
              {isStarting ? 'Starting...' : 'Start Import'}
            </Button>
          </form>
        </div>
      </Card.Content>
    </Card.Root>
  {/if}

  <!-- Import History -->
  {#if importHistory.length > 0}
    <Card.Root>
      <Card.Header>
        <Card.Title>Import History</Card.Title>
        <Card.Description>Click a row to see details</Card.Description>
      </Card.Header>
      <Card.Content class="p-0">
        <Table.Root>
          <Table.Header>
            <Table.Row>
              <Table.Head class="w-8"></Table.Head>
              <Table.Head>Date</Table.Head>
              <Table.Head>Status</Table.Head>
              <Table.Head>Objects</Table.Head>
              <Table.Head class="text-right">Imported</Table.Head>
              <Table.Head class="text-right">Skipped</Table.Head>
              <Table.Head class="text-right">Errors</Table.Head>
            </Table.Row>
          </Table.Header>
          <Table.Body>
            {#each importHistory as job}
              {@const isExpanded = expandedJobs.has(job.id)}
              <Table.Row class="cursor-pointer hover:bg-muted/50" onclick={() => toggleJobExpand(job.id)}>
                <Table.Cell class="w-8 pr-0">
                  {#if isExpanded}
                    <ChevronDown class="text-muted-foreground size-4" />
                  {:else}
                    <ChevronRight class="text-muted-foreground size-4" />
                  {/if}
                </Table.Cell>
                <Table.Cell class="text-muted-foreground text-sm">
                  {job.created_at ? formatRelativeDate(job.created_at) : 'Unknown'}
                </Table.Cell>
                <Table.Cell><Badge class={getStatusBadgeClass(job.status)}>{job.status}</Badge></Table.Cell>
                <Table.Cell class="text-muted-foreground max-w-[200px] truncate text-sm">
                  {(job.object_types || []).join(', ') || 'None'}
                </Table.Cell>
                <Table.Cell class="text-right text-sm text-emerald-600 dark:text-emerald-400">{job.imported_count || 0}</Table.Cell>
                <Table.Cell class="text-right text-sm text-amber-600 dark:text-amber-400">{job.skipped_count || 0}</Table.Cell>
                <Table.Cell class="text-right text-sm text-red-600 dark:text-red-400">{job.error_count || 0}</Table.Cell>
              </Table.Row>

              {#if isExpanded}
                {@const errors = (job.error_log || []).filter((/** @type {any} */ e) => e.level !== 'skip')}
                {@const skips = (job.error_log || []).filter((/** @type {any} */ e) => e.level === 'skip')}
                <Table.Row class="hover:bg-transparent">
                  <Table.Cell colspan={7} class="bg-muted/30 p-0">
                    <div class="space-y-4 p-4">
                      {#if errors.length > 0}
                        <div>
                          <h4 class="mb-2 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-red-600 dark:text-red-400">
                            <AlertTriangle class="size-3.5" />
                            {errors.length} {errors.length === 1 ? 'Error' : 'Errors'}
                          </h4>
                          <div class="max-h-60 space-y-1 overflow-y-auto">
                            {#each errors as err}
                              <div class="border-border flex items-start gap-2 rounded border bg-white px-3 py-2 dark:bg-gray-900/50">
                                <XCircle class="mt-0.5 size-3.5 shrink-0 text-red-500" />
                                <div class="min-w-0 flex-1 text-xs">
                                  <span class="text-muted-foreground">{getObjectLabel(err.object_type)}</span>
                                  {#if err.salesforce_id}
                                    <span class="text-muted-foreground/60 ml-1">({err.salesforce_id})</span>
                                  {/if}
                                  <p class="text-foreground mt-0.5 break-words">{err.error}</p>
                                </div>
                              </div>
                            {/each}
                          </div>
                        </div>
                      {/if}

                      {#if skips.length > 0}
                        <div>
                          <h4 class="mb-2 text-xs font-semibold uppercase tracking-wide text-amber-600 dark:text-amber-400">
                            {skips.length} {skips.length === 1 ? 'Record' : 'Records'} Skipped
                          </h4>
                          <div class="max-h-40 space-y-1 overflow-y-auto">
                            {#each skips as skip}
                              <div class="border-border flex items-start gap-2 rounded border bg-white px-3 py-2 dark:bg-gray-900/50">
                                <Clock class="mt-0.5 size-3.5 shrink-0 text-amber-500" />
                                <div class="min-w-0 flex-1 text-xs">
                                  <span class="text-muted-foreground">{getObjectLabel(skip.object_type)}</span>
                                  {#if skip.salesforce_id}
                                    <span class="text-muted-foreground/60 ml-1">({skip.salesforce_id})</span>
                                  {/if}
                                  <span class="text-foreground ml-1">{skip.error}</span>
                                </div>
                              </div>
                            {/each}
                          </div>
                        </div>
                      {/if}

                      {#if errors.length === 0 && skips.length === 0}
                        <div class="flex items-center gap-2 text-sm text-emerald-600 dark:text-emerald-400">
                          <CheckCircle class="size-4" />
                          All records imported successfully.
                        </div>
                      {/if}
                    </div>
                  </Table.Cell>
                </Table.Row>
              {/if}
            {/each}
          </Table.Body>
        </Table.Root>
      </Card.Content>
    </Card.Root>
  {/if}
</div>
