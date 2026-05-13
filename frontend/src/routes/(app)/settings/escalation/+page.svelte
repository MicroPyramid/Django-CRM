<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Plus, Trash2, AlertTriangle, Save } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const priorities = $derived(data.priorities || []);
  const actions = $derived(data.actions || []);
  const policies = $derived(data.policies || []);
  const profiles = $derived(data.profiles || []);
  const teams = $derived(data.teams || []);

  const ACTION_LABELS = {
    notify: 'Notify',
    reassign: 'Reassign',
    notify_and_reassign: 'Notify & reassign'
  };

  const policiesByPriority = $derived(
    Object.fromEntries(policies.map((/** @type {any} */ p) => [p.priority, p]))
  );

  const missingPriorities = $derived(
    priorities.filter((/** @type {string} */ p) => !policiesByPriority[p])
  );

  let dialogOpen = $state(false);
  let dialogPriority = $state('');
  let dialogFirstAction = $state('notify');
  let dialogResolutionAction = $state('notify');
  let dialogFirstTargetId = $state('');
  let dialogResolutionTargetId = $state('');
  let dialogNotifyTeamId = $state('');

  /** @param {string} priority */
  function openCreate(priority) {
    dialogPriority = priority;
    dialogFirstAction = 'notify';
    dialogResolutionAction = 'notify';
    dialogFirstTargetId = '';
    dialogResolutionTargetId = '';
    dialogNotifyTeamId = '';
    dialogOpen = true;
  }

  $effect(() => {
    if (form?.success) {
      toast.success('Escalation policy saved');
      dialogOpen = false;
      invalidateAll();
    } else if (form?.error) {
      const message =
        typeof form.error === 'string' ? form.error : JSON.stringify(form.error);
      toast.error(message);
    }
  });
</script>

<svelte:head>
  <title>Escalation Policies - Settings - BottleCRM</title>
</svelte:head>

<PageHeader
  title="Escalation"
  subtitle="When a ticket breaches its first-response or resolution SLA, the configured policy fires once per cooldown window"
/>

<div class="flex-1 p-4 md:p-6 lg:p-8">
  <div class="mx-auto max-w-4xl space-y-6">
    <section
      class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-200"
    >
      <div class="flex gap-2">
        <AlertTriangle class="h-4 w-4 flex-shrink-0" />
        <div>
          The escalation scanner runs every 5 minutes via Celery beat. A ticket is
          escalated at most once every 60 minutes and at most 3 times total.
          Tickets without a configured policy for their priority are skipped.
        </div>
      </div>
    </section>

    <section
      class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)]"
    >
      <header class="flex items-center justify-between border-b border-[var(--border-default)] p-4">
        <div>
          <h2 class="text-base font-medium text-[var(--text-primary)]">
            Policies by priority
          </h2>
          <p class="text-sm text-[var(--text-secondary)]">
            One policy per priority. Each policy chooses what happens on a
            first-response breach and a resolution breach independently.
          </p>
        </div>
      </header>

      {#if policies.length === 0 && missingPriorities.length === priorities.length}
        <div class="p-6 text-center text-sm text-[var(--text-secondary)]">
          No policies configured yet. Add one for each priority you want to
          escalate.
        </div>
      {/if}

      {#each policies as policy (policy.id)}
        <form
          method="POST"
          action="?/update"
          use:enhance={() => {
            return async ({ update }) => {
              await update();
            };
          }}
          class="border-b border-[var(--border-default)] p-4 last:border-b-0"
        >
          <input type="hidden" name="id" value={policy.id} />
          <div class="mb-3 flex items-center justify-between">
            <div class="flex items-center gap-2">
              <span class="rounded-full bg-[var(--color-primary-light)] px-2 py-0.5 text-xs font-medium text-[var(--color-primary-default)]">
                {policy.priority}
              </span>
              <input
                type="hidden"
                name="is_active"
                value={policy.is_active === false ? 'false' : 'true'}
              />
              {#if policy.is_active === false}
                <span class="text-xs text-[var(--text-secondary)]">(Inactive)</span>
              {/if}
            </div>
            <div class="flex items-center gap-1">
              <Button type="submit" size="sm" class="gap-1">
                <Save class="h-3.5 w-3.5" />
                Save
              </Button>
            </div>
          </div>

          <div class="grid grid-cols-1 gap-4 md:grid-cols-2">
            <div class="space-y-1.5">
              <Label class="text-xs">First-response breach</Label>
              <select
                name="first_response_action"
                value={policy.first_response_action}
                class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
              >
                {#each actions as a (a)}
                  <option value={a}>{ACTION_LABELS[a]}</option>
                {/each}
              </select>
              <select
                name="first_response_target_id"
                value={policy.first_response_target?.id || ''}
                class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
              >
                <option value="">— Target user —</option>
                {#each profiles as p (p.id)}
                  <option value={p.id}>{p.name}</option>
                {/each}
              </select>
            </div>

            <div class="space-y-1.5">
              <Label class="text-xs">Resolution breach</Label>
              <select
                name="resolution_action"
                value={policy.resolution_action}
                class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
              >
                {#each actions as a (a)}
                  <option value={a}>{ACTION_LABELS[a]}</option>
                {/each}
              </select>
              <select
                name="resolution_target_id"
                value={policy.resolution_target?.id || ''}
                class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
              >
                <option value="">— Target user —</option>
                {#each profiles as p (p.id)}
                  <option value={p.id}>{p.name}</option>
                {/each}
              </select>
            </div>

            <div class="space-y-1.5 md:col-span-2">
              <Label class="text-xs">CC team (optional)</Label>
              <select
                name="notify_team_id"
                value={policy.notify_team?.id || ''}
                class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
              >
                <option value="">— None —</option>
                {#each teams as t (t.id)}
                  <option value={t.id}>{t.name}</option>
                {/each}
              </select>
            </div>
          </div>
        </form>
      {/each}

      {#if missingPriorities.length > 0}
        <div class="border-t border-[var(--border-default)] p-4">
          <p class="mb-2 text-xs text-[var(--text-secondary)]">Missing policies:</p>
          <div class="flex flex-wrap gap-2">
            {#each missingPriorities as priority (priority)}
              <Button
                variant="outline"
                size="sm"
                onclick={() => openCreate(priority)}
                class="gap-1"
              >
                <Plus class="h-3.5 w-3.5" />
                {priority}
              </Button>
            {/each}
          </div>
        </div>
      {/if}
    </section>

    {#if policies.length > 0}
      <section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4">
        <h3 class="mb-3 text-sm font-medium text-[var(--text-primary)]">Delete a policy</h3>
        <div class="flex flex-wrap gap-2">
          {#each policies as policy (policy.id)}
            <form method="POST" action="?/delete" use:enhance class="inline">
              <input type="hidden" name="id" value={policy.id} />
              <Button
                type="submit"
                variant="outline"
                size="sm"
                class="gap-1 text-[var(--color-danger-default)]"
              >
                <Trash2 class="h-3.5 w-3.5" />
                {policy.priority}
              </Button>
            </form>
          {/each}
        </div>
      </section>
    {/if}
  </div>
</div>

<Dialog.Root bind:open={dialogOpen}>
  <Dialog.Content class="sm:max-w-md">
    <Dialog.Header>
      <Dialog.Title>New escalation policy</Dialog.Title>
      <Dialog.Description>
        Add an escalation policy for {dialogPriority} tickets.
      </Dialog.Description>
    </Dialog.Header>

    <form
      method="POST"
      action="?/create"
      use:enhance={() => {
        return async ({ update }) => {
          await update();
        };
      }}
      class="space-y-4"
    >
      <input type="hidden" name="priority" value={dialogPriority} />
      <input type="hidden" name="is_active" value="true" />

      <div class="space-y-1.5">
        <Label class="text-xs">First-response action</Label>
        <select
          name="first_response_action"
          bind:value={dialogFirstAction}
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
        >
          {#each actions as a (a)}
            <option value={a}>{ACTION_LABELS[a]}</option>
          {/each}
        </select>
        <select
          name="first_response_target_id"
          bind:value={dialogFirstTargetId}
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
        >
          <option value="">— Target user —</option>
          {#each profiles as p (p.id)}
            <option value={p.id}>{p.name}</option>
          {/each}
        </select>
      </div>

      <div class="space-y-1.5">
        <Label class="text-xs">Resolution action</Label>
        <select
          name="resolution_action"
          bind:value={dialogResolutionAction}
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
        >
          {#each actions as a (a)}
            <option value={a}>{ACTION_LABELS[a]}</option>
          {/each}
        </select>
        <select
          name="resolution_target_id"
          bind:value={dialogResolutionTargetId}
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
        >
          <option value="">— Target user —</option>
          {#each profiles as p (p.id)}
            <option value={p.id}>{p.name}</option>
          {/each}
        </select>
      </div>

      <div class="space-y-1.5">
        <Label class="text-xs">CC team (optional)</Label>
        <select
          name="notify_team_id"
          bind:value={dialogNotifyTeamId}
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
        >
          <option value="">— None —</option>
          {#each teams as t (t.id)}
            <option value={t.id}>{t.name}</option>
          {/each}
        </select>
      </div>

      <Dialog.Footer>
        <Button type="button" variant="outline" onclick={() => (dialogOpen = false)}>
          Cancel
        </Button>
        <Button type="submit">Create</Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
