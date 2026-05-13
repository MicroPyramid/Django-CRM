<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Plus, Trash2, Save, ArrowDownAZ, Play } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const strategies = $derived(data.strategies || []);
  const fields = $derived(data.fields || []);
  const ops = $derived(data.ops || []);
  const rules = $derived(data.rules || []);
  const profiles = $derived(data.profiles || []);
  const teams = $derived(data.teams || []);
  const mailboxes = $derived(data.mailboxes || []);

  let dialogOpen = $state(false);
  /** @type {string|null} */
  let editId = $state(null);
  let dName = $state('');
  let dPriorityOrder = $state(100);
  let dStrategy = $state('direct');
  let dStopProcessing = $state(true);
  let dActive = $state(true);
  /** @type {string[]} */
  let dAssignees = $state([]);
  let dTeam = $state('');
  /** @type {Array<{field:string,op:string,value:any}>} */
  let dConditions = $state([]);

  /** @type {string|null} */
  let testRuleId = $state(null);
  let testTicketId = $state('');
  /** @type {any} */
  let testResult = $state(null);
  let testRunning = $state(false);

  function resetDialog() {
    editId = null;
    dName = '';
    dPriorityOrder = 100;
    dStrategy = 'direct';
    dStopProcessing = true;
    dActive = true;
    dAssignees = [];
    dTeam = '';
    dConditions = [];
  }

  function openCreate() {
    resetDialog();
    dialogOpen = true;
  }

  /** @param {any} rule */
  function openEdit(rule) {
    editId = rule.id;
    dName = rule.name;
    dPriorityOrder = rule.priority_order ?? 100;
    dStrategy = rule.strategy;
    dStopProcessing = !!rule.stop_processing;
    dActive = !!rule.is_active;
    dAssignees = (rule.target_assignees || []).map((/** @type {any} */ p) => p.id);
    dTeam = rule.target_team?.id || '';
    dConditions = JSON.parse(JSON.stringify(rule.conditions || []));
    dialogOpen = true;
  }

  function addCondition() {
    dConditions = [...dConditions, { field: 'priority', op: 'eq', value: '' }];
  }

  /** @param {number} idx */
  function removeCondition(idx) {
    dConditions = dConditions.filter((_, i) => i !== idx);
  }

  /** @param {string} id */
  function toggleAssignee(id) {
    if (dAssignees.includes(id)) {
      dAssignees = dAssignees.filter((x) => x !== id);
    } else {
      dAssignees = [...dAssignees, id];
    }
  }

  function strategyLabel(/** @type {string} */ id) {
    return strategies.find((/** @type {any} */ s) => s.id === id)?.label || id;
  }

  /** @param {any} cond */
  function describeCondition(cond) {
    const f = fields.find((/** @type {any} */ x) => x.id === cond.field)?.label || cond.field;
    const o = ops.find((/** @type {any} */ x) => x.id === cond.op)?.label || cond.op;
    let v = cond.value;
    if (Array.isArray(v)) v = v.join(', ');
    return `${f} ${o} ${v}`;
  }

  async function runTest() {
    if (!testRuleId || !testTicketId.trim()) return;
    testRunning = true;
    testResult = null;
    try {
      const resp = await fetch(`/api/cases/routing-rules/${testRuleId}/test/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ case_id: testTicketId.trim() })
      });
      const json = await resp.json();
      if (!resp.ok) {
        toast.error(json?.errors || 'Test failed');
      } else {
        testResult = json;
      }
    } catch (e) {
      toast.error('Test failed');
    } finally {
      testRunning = false;
    }
  }

  $effect(() => {
    if (form?.success) {
      toast.success('Routing rule saved');
      dialogOpen = false;
      resetDialog();
      invalidateAll();
    } else if (form?.error) {
      const msg = typeof form.error === 'string' ? form.error : JSON.stringify(form.error);
      toast.error(msg);
    }
  });
</script>

<svelte:head>
  <title>Routing Rules - Settings - BottleCRM</title>
</svelte:head>

<PageHeader
  title="Auto-Routing"
  subtitle="Rules evaluated on each new ticket (lower priority order runs first)"
>
  {#snippet actions()}
    <Button onclick={openCreate} class="gap-2">
      <Plus class="h-4 w-4" />
      New rule
    </Button>
  {/snippet}
</PageHeader>

<div class="flex-1 p-4 md:p-6 lg:p-8">
  <div class="mx-auto max-w-5xl space-y-6">
    <section
      class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
    >
      <div class="mb-3 flex items-center gap-2 text-sm text-[var(--text-secondary)]">
        <ArrowDownAZ class="h-4 w-4" />
        Rules run from top to bottom; the first matching rule with
        <code class="text-xs">stop_processing</code> ends evaluation.
      </div>
      {#if rules.length === 0}
        <p class="text-sm text-[var(--text-secondary)]">
          No routing rules yet. New tickets stay unassigned until an admin picks
          someone, or until you add a rule here.
        </p>
      {:else}
        <ul class="divide-y divide-[var(--border-default)]">
          {#each rules as rule (rule.id)}
            <li class="flex items-start justify-between gap-4 py-3">
              <div class="min-w-0 flex-1 space-y-1">
                <div class="flex flex-wrap items-baseline gap-2">
                  <span class="text-sm font-semibold text-[var(--text-primary)]">
                    {rule.name}
                  </span>
                  <span class="text-xs text-[var(--text-secondary)]">
                    order {rule.priority_order}
                  </span>
                  <span
                    class="rounded-full px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide {rule.is_active
                      ? 'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-200'
                      : 'bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400'}"
                  >
                    {rule.is_active ? 'Active' : 'Disabled'}
                  </span>
                  <span
                    class="rounded-full bg-blue-100 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-blue-700 dark:bg-blue-900/40 dark:text-blue-200"
                  >
                    {strategyLabel(rule.strategy)}
                  </span>
                </div>
                {#if rule.conditions?.length}
                  <ul class="text-xs text-[var(--text-secondary)]">
                    {#each rule.conditions as cond, i (i)}
                      <li>{describeCondition(cond)}</li>
                    {/each}
                  </ul>
                {:else}
                  <p class="text-xs italic text-[var(--text-secondary)]">
                    No conditions — matches every new ticket
                  </p>
                {/if}
                {#if rule.strategy === 'by_team' && rule.target_team}
                  <p class="text-xs text-[var(--text-secondary)]">
                    → team: {rule.target_team.name}
                  </p>
                {:else if rule.target_assignees?.length}
                  <p class="text-xs text-[var(--text-secondary)]">
                    → {rule.target_assignees
                      .map((/** @type {any} */ p) => p.user_details?.email || p.email || 'agent')
                      .join(', ')}
                  </p>
                {/if}
              </div>
              <div class="flex shrink-0 items-center gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  onclick={() => {
                    testRuleId = rule.id;
                    testResult = null;
                  }}
                  class="gap-1.5"
                >
                  <Play class="h-3 w-3" />
                  Test
                </Button>
                <Button type="button" size="sm" variant="outline" onclick={() => openEdit(rule)}>
                  Edit
                </Button>
                <form method="POST" action="?/delete" use:enhance>
                  <input type="hidden" name="id" value={rule.id} />
                  <Button type="submit" size="icon" variant="ghost" class="text-red-600">
                    <Trash2 class="h-4 w-4" />
                  </Button>
                </form>
              </div>
            </li>
          {/each}
        </ul>
      {/if}
    </section>

    {#if testRuleId}
      <section
        class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
      >
        <h3 class="mb-2 text-sm font-semibold text-[var(--text-primary)]">
          Test rule against a ticket
        </h3>
        <p class="mb-3 text-xs text-[var(--text-secondary)]">
          Paste a ticket UUID and click Run. The engine evaluates ALL active rules
          in order; the result tells you which rule (if any) would have
          assigned this ticket.
        </p>
        <div class="flex flex-wrap items-end gap-2">
          <div class="min-w-[280px] flex-1">
            <Label for="test-case-id">Ticket ID</Label>
            <Input id="test-case-id" bind:value={testTicketId} placeholder="UUID" />
          </div>
          <Button type="button" onclick={runTest} disabled={testRunning} class="gap-1.5">
            <Play class="h-3 w-3" />
            Run
          </Button>
          <Button type="button" variant="ghost" onclick={() => (testRuleId = null)}>
            Close
          </Button>
        </div>
        {#if testResult}
          <div
            class="mt-3 rounded-md border border-[var(--border-default)] bg-[var(--surface-muted)] p-3 text-sm"
          >
            {#if testResult.matched}
              <p class="font-medium text-emerald-700 dark:text-emerald-300">
                Matched rule: {testResult.rule_name}
              </p>
              <p class="mt-1 text-xs text-[var(--text-secondary)]">
                Strategy: {testResult.strategy}
              </p>
              {#if testResult.would_assign_profile_ids?.length}
                <p class="text-xs text-[var(--text-secondary)]">
                  Would assign profile(s): {testResult.would_assign_profile_ids.join(', ')}
                </p>
              {/if}
              {#if testResult.would_assign_team_id}
                <p class="text-xs text-[var(--text-secondary)]">
                  Would assign team: {testResult.would_assign_team_id}
                </p>
              {/if}
              {#if testResult.reason}
                <p class="text-xs text-amber-700 dark:text-amber-300">
                  Reason: {testResult.reason}
                </p>
              {/if}
            {:else}
              <p class="text-[var(--text-secondary)]">
                No rule matched this ticket.
              </p>
            {/if}
          </div>
        {/if}
      </section>
    {/if}
  </div>
</div>

<Dialog.Root bind:open={dialogOpen}>
  <Dialog.Content class="max-w-2xl">
    <Dialog.Header>
      <Dialog.Title>{editId ? 'Edit routing rule' : 'New routing rule'}</Dialog.Title>
      <Dialog.Description>
        Conditions are AND-ed; create multiple rules for OR. Lower priority
        order runs first.
      </Dialog.Description>
    </Dialog.Header>

    <form method="POST" action={editId ? '?/update' : '?/create'} use:enhance class="space-y-4">
      {#if editId}
        <input type="hidden" name="id" value={editId} />
      {/if}
      <input type="hidden" name="conditions" value={JSON.stringify(dConditions)} />
      <input type="hidden" name="target_assignee_ids" value={JSON.stringify(dAssignees)} />
      <input type="hidden" name="target_team_id" value={dTeam} />
      <input type="hidden" name="strategy" value={dStrategy} />
      <input type="hidden" name="is_active" value={String(dActive)} />
      <input type="hidden" name="stop_processing" value={String(dStopProcessing)} />

      <div class="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <div>
          <Label for="rule-name">Name</Label>
          <Input id="rule-name" name="name" bind:value={dName} required />
        </div>
        <div>
          <Label for="rule-order">Priority order</Label>
          <Input
            id="rule-order"
            type="number"
            min="0"
            name="priority_order"
            bind:value={dPriorityOrder}
          />
        </div>
      </div>

      <div>
        <Label>Conditions</Label>
        <p class="mb-2 text-xs text-[var(--text-secondary)]">
          All conditions must match (AND). Leave empty to match every new ticket.
        </p>
        <ul class="space-y-2">
          {#each dConditions as cond, idx (idx)}
            <li class="flex flex-wrap items-end gap-2">
              <select
                bind:value={cond.field}
                class="rounded border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-1 text-sm"
              >
                {#each fields as f (f.id)}
                  <option value={f.id}>{f.label}</option>
                {/each}
              </select>
              <select
                bind:value={cond.op}
                class="rounded border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-1 text-sm"
              >
                {#each ops as o (o.id)}
                  <option value={o.id}>{o.label}</option>
                {/each}
              </select>
              <Input
                bind:value={cond.value}
                placeholder="value"
                class="max-w-[220px]"
              />
              <Button
                type="button"
                size="icon"
                variant="ghost"
                onclick={() => removeCondition(idx)}
                class="text-red-600"
              >
                <Trash2 class="h-4 w-4" />
              </Button>
            </li>
          {/each}
        </ul>
        <Button type="button" size="sm" variant="outline" onclick={addCondition} class="mt-2 gap-1">
          <Plus class="h-3 w-3" />
          Add condition
        </Button>
      </div>

      <div>
        <Label for="rule-strategy">Strategy</Label>
        <select
          id="rule-strategy"
          bind:value={dStrategy}
          class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-2 text-sm"
        >
          {#each strategies as s (s.id)}
            <option value={s.id}>{s.label}</option>
          {/each}
        </select>
      </div>

      {#if dStrategy === 'by_team'}
        <div>
          <Label for="rule-team">Target team</Label>
          <select
            id="rule-team"
            bind:value={dTeam}
            class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-2 text-sm"
            required
          >
            <option value="">Choose team…</option>
            {#each teams as t (t.id)}
              <option value={t.id}>{t.name}</option>
            {/each}
          </select>
        </div>
      {:else}
        <div>
          <Label>Target assignees</Label>
          <p class="mb-2 text-xs text-[var(--text-secondary)]">
            {dStrategy === 'direct'
              ? 'First selected agent is assigned.'
              : dStrategy === 'round_robin'
                ? 'Agents take turns in order of selection.'
                : 'Agent with the fewest open tickets is picked.'}
          </p>
          <ul class="grid grid-cols-1 gap-1 sm:grid-cols-2">
            {#each profiles as p (p.id)}
              <li>
                <label class="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={dAssignees.includes(p.id)}
                    onchange={() => toggleAssignee(p.id)}
                    class="h-4 w-4 rounded border-[var(--border-default)]"
                  />
                  {p.name}
                </label>
              </li>
            {/each}
          </ul>
        </div>
      {/if}

      <div class="flex flex-wrap gap-4">
        <label class="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            bind:checked={dActive}
            class="h-4 w-4 rounded border-[var(--border-default)]"
          />
          Active
        </label>
        <label class="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            bind:checked={dStopProcessing}
            class="h-4 w-4 rounded border-[var(--border-default)]"
          />
          Stop processing if this rule matches
        </label>
      </div>

      {#if mailboxes.length > 0 && dConditions.some((c) => c.field === 'mailbox_id')}
        <p class="text-xs text-[var(--text-secondary)]">
          Mailbox IDs available: {mailboxes
            .map((/** @type {any} */ m) => `${m.address} → ${m.id}`)
            .join(' • ')}
        </p>
      {/if}

      <Dialog.Footer>
        <Button type="button" variant="ghost" onclick={() => (dialogOpen = false)}>
          Cancel
        </Button>
        <Button type="submit" class="gap-1.5">
          <Save class="h-4 w-4" />
          Save
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
