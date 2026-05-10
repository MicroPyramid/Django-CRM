<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Loader2, RotateCcw, Check } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const initial = $derived(data.policy || {});

  let isEnabled = $state(true);
  let windowDays = $state(7);
  let toStatus = $state('Pending');
  let notifyAssigned = $state(true);
  let saving = $state(false);

  $effect(() => {
    isEnabled = initial.is_enabled ?? true;
    windowDays = initial.reopen_window_days ?? 7;
    toStatus = initial.reopen_to_status ?? 'Pending';
    notifyAssigned = initial.notify_assigned ?? true;
  });

  const STATUS_OPTIONS = [
    { value: 'New', label: 'New' },
    { value: 'Assigned', label: 'Assigned' },
    { value: 'Pending', label: 'Pending' }
  ];
</script>

<svelte:head>
  <title>Reopen Policy - Settings - BottleCRM</title>
</svelte:head>

<PageHeader
  title="Ticket Reopen Policy"
  subtitle="Auto-reopen closed tickets when the customer replies"
>
  {#snippet actions()}
    <Button type="submit" form="reopen-policy-form" disabled={saving} class="gap-2">
      {#if saving}
        <Loader2 class="h-4 w-4 animate-spin" />
        Saving…
      {:else}
        <Check class="h-4 w-4" />
        Save changes
      {/if}
    </Button>
  {/snippet}
</PageHeader>

<div class="flex-1 p-4 md:p-6 lg:p-8">
  <form
    id="reopen-policy-form"
    method="POST"
    action="?/update"
    use:enhance={() => {
      saving = true;
      return async ({ result, update }) => {
        await update();
        saving = false;
        if (result.type === 'success') {
          toast.success('Reopen policy saved');
          await invalidateAll();
        } else if (result.type === 'failure') {
          toast.error(form?.error || 'Failed to save policy');
        }
      };
    }}
    class="mx-auto max-w-2xl space-y-6"
  >
    <section
      class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-6 space-y-5"
    >
      <header class="flex items-start gap-3">
        <div
          class="flex h-9 w-9 items-center justify-center rounded-full bg-emerald-100 text-emerald-700 dark:bg-emerald-900/40 dark:text-emerald-300"
        >
          <RotateCcw class="h-4 w-4" />
        </div>
        <div>
          <h2 class="text-base font-medium text-[var(--text-primary)]">
            Auto-reopen on customer reply
          </h2>
          <p class="text-sm text-[var(--text-secondary)]">
            When enabled, a closed ticket is automatically reopened if the customer
            posts a comment within the configured window. Agent comments and internal
            notes never trigger a reopen.
          </p>
        </div>
      </header>

      <!-- Enabled toggle (no name attribute — the hidden input below carries the value) -->
      <div class="flex items-center gap-3">
        <input
          id="is_enabled"
          type="checkbox"
          bind:checked={isEnabled}
          class="h-4 w-4 rounded border-[var(--border-default)] text-[var(--color-primary-default)] focus:ring-2 focus:ring-[var(--color-primary-default)]"
        />
        <Label for="is_enabled" class="cursor-pointer text-sm">
          Enable automatic reopen
        </Label>
      </div>
      <input type="hidden" name="is_enabled" value={isEnabled ? 'true' : 'false'} />

      <!-- Window days -->
      <div class="space-y-2">
        <Label for="reopen_window_days" class="text-sm">
          Reopen window (days)
        </Label>
        <Input
          id="reopen_window_days"
          name="reopen_window_days"
          type="number"
          min="1"
          max="365"
          bind:value={windowDays}
          disabled={!isEnabled}
          class="w-32"
        />
        <p class="text-xs text-[var(--text-secondary)]">
          Replies more than this many days after the ticket was closed will not
          reopen it. Allowed range: 1–365.
        </p>
      </div>

      <!-- Reopen-to status -->
      <div class="space-y-2">
        <Label for="reopen_to_status" class="text-sm">
          Reopen to status
        </Label>
        <select
          id="reopen_to_status"
          name="reopen_to_status"
          bind:value={toStatus}
          disabled={!isEnabled}
          class="w-48 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary-default)] disabled:opacity-50"
        >
          {#each STATUS_OPTIONS as opt (opt.value)}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
        <p class="text-xs text-[var(--text-secondary)]">
          The status the ticket flips to when reopened. Terminal statuses (Closed,
          Rejected, Duplicate) are not allowed.
        </p>
      </div>

      <!-- Notify assigned -->
      <div class="flex items-center gap-3">
        <input
          id="notify_assigned"
          type="checkbox"
          bind:checked={notifyAssigned}
          disabled={!isEnabled}
          class="h-4 w-4 rounded border-[var(--border-default)] text-[var(--color-primary-default)] focus:ring-2 focus:ring-[var(--color-primary-default)] disabled:opacity-50"
        />
        <Label for="notify_assigned" class="cursor-pointer text-sm">
          Notify previously assigned agents on reopen
        </Label>
      </div>
      <input
        type="hidden"
        name="notify_assigned"
        value={notifyAssigned ? 'true' : 'false'}
      />
    </section>

    {#if form?.error}
      <p class="text-sm text-[var(--color-danger-default)]">{form.error}</p>
    {/if}
  </form>
</div>
