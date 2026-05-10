<script>
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Loader2 } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';

  /**
   * Manual time entry creation. The "now" defaults make backfilling a 30-min
   * session straightforward — just type a description and submit.
   *
   * @type {{
   *   ticketId: string,
   *   open: boolean,
   *   onOpenChange?: (v: boolean) => void
   * }}
   */
  let { ticketId, open = $bindable(false), onOpenChange } = $props();

  const _toLocalInput = (/** @type {Date} */ d) => {
    const pad = (/** @type {number} */ n) => String(n).padStart(2, '0');
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  };

  const _now = () => new Date();
  const _halfHourAgo = () => new Date(Date.now() - 30 * 60 * 1000);

  let startedAt = $state(_toLocalInput(_halfHourAgo()));
  let endedAt = $state(_toLocalInput(_now()));
  let description = $state('');
  let billable = $state(false);
  let hourlyRate = $state('');
  let submitting = $state(false);

  $effect(() => {
    if (open) {
      startedAt = _toLocalInput(_halfHourAgo());
      endedAt = _toLocalInput(_now());
      description = '';
      billable = false;
      hourlyRate = '';
    }
  });

  async function submit() {
    submitting = true;
    try {
      const body = {
        started_at: new Date(startedAt).toISOString(),
        ended_at: new Date(endedAt).toISOString(),
        description: description.trim(),
        billable
      };
      if (hourlyRate.trim() !== '') {
        body.hourly_rate = hourlyRate.trim();
      }
      const res = await fetch(`/api/cases/${ticketId}/time-entries/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        toast.error(e?.error || 'Failed to add time entry');
        return;
      }
      toast.success('Time entry added.');
      open = false;
      await invalidateAll();
    } finally {
      submitting = false;
    }
  }
</script>

<Dialog.Root bind:open onOpenChange={(v) => onOpenChange?.(v)}>
  <Dialog.Content class="sm:max-w-md">
    <Dialog.Header>
      <Dialog.Title>Log time</Dialog.Title>
      <Dialog.Description>
        Backfill a session you forgot to track. Stays attached to this ticket.
      </Dialog.Description>
    </Dialog.Header>

    <div class="space-y-3">
      <div class="grid grid-cols-2 gap-2">
        <label class="space-y-1 text-sm">
          <span class="font-medium">Start</span>
          <input
            type="datetime-local"
            bind:value={startedAt}
            class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm"
          />
        </label>
        <label class="space-y-1 text-sm">
          <span class="font-medium">End</span>
          <input
            type="datetime-local"
            bind:value={endedAt}
            class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm"
          />
        </label>
      </div>

      <label class="space-y-1 text-sm">
        <span class="font-medium">Description</span>
        <textarea
          bind:value={description}
          rows="3"
          placeholder="What did you work on?"
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm"
        ></textarea>
      </label>

      <div class="flex items-center justify-between gap-3">
        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" bind:checked={billable} />
          <span>Billable</span>
        </label>
        <label class="flex items-center gap-2 text-sm">
          <span class="text-xs text-[var(--text-secondary)]">Rate / hr</span>
          <input
            type="number"
            min="0"
            step="0.01"
            bind:value={hourlyRate}
            placeholder="0.00"
            class="w-24 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-1.5 text-sm"
          />
        </label>
      </div>
    </div>

    <Dialog.Footer>
      <Button
        type="button"
        variant="outline"
        onclick={() => (open = false)}
        disabled={submitting}>Cancel</Button
      >
      <Button type="button" disabled={submitting} onclick={submit}>
        {#if submitting}<Loader2 class="mr-1 h-3.5 w-3.5 animate-spin" />{/if}
        Save entry
      </Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
