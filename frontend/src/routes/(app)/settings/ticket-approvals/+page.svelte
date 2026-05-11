<script>
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { ShieldCheck, Loader2, Plus, Trash2, Edit3 } from '@lucide/svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import { Button } from '$lib/components/ui/button/index.js';

  /** @type {{ data: any }} */
  let { data } = $props();

  const rules = $derived(data.rules || []);
  /** @type {Array<{id: string, name: string}>} */
  const profiles = $derived(data.profiles || []);
  /** @type {Array<{id: string, name: string}>} */
  const teams = $derived(data.teams || []);

  let editingId = $state(/** @type {string | null} */ (null));
  let pending = $state(false);
  let creating = $state(false);

  /** @type {{ name: string, match_priority: string, match_case_type: string, match_team_id: string, approver_role: string, approver_ids: string[], is_active: boolean }} */
  let draft = $state(makeBlankDraft());

  function makeBlankDraft() {
    return {
      name: '',
      match_priority: '',
      match_case_type: '',
      match_team_id: '',
      approver_role: 'ADMIN',
      approver_ids: /** @type {string[]} */ ([]),
      is_active: true
    };
  }

  /** @param {any} rule */
  function startEdit(rule) {
    editingId = rule.id;
    draft = {
      name: rule.name || '',
      match_priority: rule.match_priority || '',
      match_case_type: rule.match_case_type || '',
      match_team_id: rule.match_team?.id || '',
      approver_role: rule.approver_role || 'ADMIN',
      approver_ids: (rule.approvers || []).map(
        /** @param {{id: string}} p */ (p) => p.id
      ),
      is_active: !!rule.is_active
    };
    creating = false;
  }

  function startCreate() {
    editingId = null;
    creating = true;
    draft = makeBlankDraft();
  }

  function cancelEdit() {
    editingId = null;
    creating = false;
    draft = makeBlankDraft();
  }

  function buildPayload() {
    /** @type {Record<string, unknown>} */
    const body = {
      name: draft.name,
      approver_role: draft.approver_role,
      is_active: draft.is_active,
      approver_ids: draft.approver_ids
    };
    if (draft.match_priority) body.match_priority = draft.match_priority;
    else body.match_priority = null;
    if (draft.match_case_type) body.match_case_type = draft.match_case_type;
    else body.match_case_type = null;
    body.match_team_id = draft.match_team_id || null;
    return body;
  }

  async function save() {
    if (!draft.name.trim()) {
      toast.error('Name is required.');
      return;
    }
    pending = true;
    try {
      const payload = buildPayload();
      const url = editingId
        ? `/api/cases/approval-rules/${editingId}/`
        : '/api/cases/approval-rules/';
      const method = editingId ? 'PUT' : 'POST';
      const res = await fetch(url, {
        method,
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        toast.error(body?.error || JSON.stringify(body?.errors) || 'Save failed');
        return;
      }
      toast.success(editingId ? 'Rule updated' : 'Rule created');
      cancelEdit();
      await invalidateAll();
    } finally {
      pending = false;
    }
  }

  /** @param {string} id */
  async function destroy(id) {
    if (!window.confirm('Delete this rule? Rules with history will be disabled instead.'))
      return;
    pending = true;
    try {
      const res = await fetch(`/api/cases/approval-rules/${id}/`, {
        method: 'DELETE'
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        toast.error(body?.error || 'Delete failed');
        return;
      }
      toast.success('Rule removed');
      await invalidateAll();
    } finally {
      pending = false;
    }
  }

  /** @param {string} id */
  function toggleApprover(id) {
    if (draft.approver_ids.includes(id)) {
      draft.approver_ids = draft.approver_ids.filter((x) => x !== id);
    } else {
      draft.approver_ids = [...draft.approver_ids, id];
    }
  }
</script>

<svelte:head>
  <title>Approval rules - Settings - BottleCRM</title>
</svelte:head>

<PageHeader title="Approval rules">
  {#snippet titleIcon()}
    <ShieldCheck class="size-4" />
  {/snippet}
  {#snippet actions()}
    {#if !creating && editingId === null}
      <Button onclick={startCreate} disabled={pending}>
        <Plus class="mr-1 h-4 w-4" /> New rule
      </Button>
    {/if}
  {/snippet}
</PageHeader>

<div class="flex flex-col gap-4 p-4">
  <p class="text-sm text-[var(--text-secondary)]">
    Active rules block the close transition until an approval is recorded.
    Filters combine — a rule with priority=Urgent + case_type=Incident matches
    only urgent incidents. The most-specific active rule wins.
  </p>

  {#if creating || editingId !== null}
    <section class="rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-4">
      <h2 class="mb-3 text-sm font-medium">
        {editingId ? 'Edit rule' : 'New rule'}
      </h2>
      <div class="grid gap-3 sm:grid-cols-2">
        <label class="space-y-1 text-sm">
          <span class="font-medium">Name</span>
          <input
            type="text"
            bind:value={draft.name}
            class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm"
          />
        </label>

        <label class="space-y-1 text-sm">
          <span class="font-medium">Priority filter</span>
          <select
            bind:value={draft.match_priority}
            class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm"
          >
            <option value="">Any priority</option>
            <option value="Low">Low</option>
            <option value="Normal">Normal</option>
            <option value="High">High</option>
            <option value="Urgent">Urgent</option>
          </select>
        </label>

        <label class="space-y-1 text-sm">
          <span class="font-medium">Ticket type filter</span>
          <select
            bind:value={draft.match_case_type}
            class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm"
          >
            <option value="">Any type</option>
            <option value="Question">Question</option>
            <option value="Incident">Incident</option>
            <option value="Problem">Problem</option>
          </select>
        </label>

        <label class="space-y-1 text-sm">
          <span class="font-medium">Team filter</span>
          <select
            bind:value={draft.match_team_id}
            class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm"
          >
            <option value="">Any team</option>
            {#each teams as t (t.id)}
              <option value={t.id}>{t.name}</option>
            {/each}
          </select>
        </label>

        <label class="space-y-1 text-sm">
          <span class="font-medium">Fallback approver role</span>
          <select
            bind:value={draft.approver_role}
            class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm"
          >
            <option value="ADMIN">Any admin</option>
            <option value="MANAGER">Any manager (when role exists)</option>
          </select>
        </label>

        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" bind:checked={draft.is_active} />
          <span>Active</span>
        </label>
      </div>

      <fieldset class="mt-3 rounded-md border border-[var(--border-default)] p-3">
        <legend class="px-1 text-xs font-medium">Explicit approvers</legend>
        {#if profiles.length === 0}
          <p class="text-xs text-[var(--text-secondary)]">No profiles loaded.</p>
        {:else}
          <div class="grid gap-1.5 sm:grid-cols-2">
            {#each profiles as p (p.id)}
              <label class="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={draft.approver_ids.includes(p.id)}
                  onchange={() => toggleApprover(p.id)}
                />
                <span>{p.name}</span>
              </label>
            {/each}
          </div>
        {/if}
      </fieldset>

      <div class="mt-3 flex gap-2">
        <Button onclick={save} disabled={pending}>
          {#if pending}<Loader2 class="mr-1 h-3.5 w-3.5 animate-spin" />{/if}
          {editingId ? 'Save changes' : 'Create rule'}
        </Button>
        <Button variant="ghost" onclick={cancelEdit} disabled={pending}>
          Cancel
        </Button>
      </div>
    </section>
  {/if}

  {#if rules.length === 0}
    <p class="rounded-md border border-[var(--border-default)] bg-[var(--surface-muted)] p-4 text-center text-sm text-[var(--text-secondary)]">
      No approval rules yet.
    </p>
  {:else}
    <ul class="flex flex-col gap-2">
      {#each rules as r (r.id)}
        <li class="flex flex-wrap items-center justify-between gap-2 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-3 text-sm">
          <div class="flex flex-col">
            <span class="font-medium">
              {r.name}
              {#if !r.is_active}
                <span class="ml-2 rounded bg-[var(--surface-muted)] px-1.5 text-[10px] text-[var(--text-secondary)]">
                  inactive
                </span>
              {/if}
            </span>
            <span class="text-xs text-[var(--text-secondary)]">
              {[
                r.match_priority && `priority=${r.match_priority}`,
                r.match_case_type && `type=${r.match_case_type}`,
                r.match_team?.name && `team=${r.match_team.name}`,
                `role=${r.approver_role}`
              ]
                .filter(Boolean)
                .join(' · ')}
            </span>
            {#if (r.approvers || []).length > 0}
              <span class="text-xs text-[var(--text-secondary)]">
                Explicit: {(r.approvers || []).map(/** @param {{email: string}} p */ (p) => p.email).join(', ')}
              </span>
            {/if}
          </div>
          <div class="flex gap-1">
            <Button
              size="sm"
              variant="ghost"
              onclick={() => startEdit(r)}
              disabled={pending}
            >
              <Edit3 class="mr-1 h-3.5 w-3.5" /> Edit
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onclick={() => destroy(r.id)}
              disabled={pending}
            >
              <Trash2 class="mr-1 h-3.5 w-3.5" /> Delete
            </Button>
          </div>
        </li>
      {/each}
    </ul>
  {/if}
</div>
