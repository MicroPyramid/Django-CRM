<script>
  import { goto } from '$app/navigation';
  import { onMount } from 'svelte';
  import { toast } from 'svelte-sonner';
  import { Loader2 } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';

  /**
   * Picker that turns billable, unbilled, single-currency time entries into
   * a fresh draft invoice. Spec said "on the invoice editor"; we landed it
   * on the invoice list because the underlying endpoint creates a NEW
   * invoice rather than appending to an existing one.
   *
   * @type {{
   *   open: boolean,
   *   onOpenChange?: (v: boolean) => void
   * }}
   */
  let { open = $bindable(false), onOpenChange } = $props();

  /** @type {Array<{id: string, name: string}>} */
  let accounts = $state([]);
  let accountId = $state('');
  /** @type {Array<any>} */
  let entries = $state([]);
  /** @type {Set<string>} */
  let selectedIds = $state(new Set());
  let loadingEntries = $state(false);
  let submitting = $state(false);

  const selectedEntries = $derived(
    entries.filter((e) => selectedIds.has(e.id))
  );
  const selectedCurrencies = $derived(
    new Set(selectedEntries.map((e) => e.currency))
  );
  const selectionMixed = $derived(selectedCurrencies.size > 1);

  $effect(() => {
    if (open) {
      void loadAccounts();
      accountId = '';
      entries = [];
      selectedIds = new Set();
    }
  });

  $effect(() => {
    if (open && accountId) {
      void loadUnbilled(accountId);
    }
  });

  async function loadAccounts() {
    try {
      const res = await fetch('/api/accounts');
      if (!res.ok) return;
      const body = await res.json();
      accounts =
        body?.active_accounts?.open_accounts ||
        body?.results ||
        body?.accounts ||
        [];
    } catch (err) {
      console.warn('Failed to load accounts', err);
    }
  }

  async function loadUnbilled(/** @type {string} */ acctId) {
    loadingEntries = true;
    selectedIds = new Set();
    try {
      const res = await fetch(`/api/time-entries/unbilled/?account=${acctId}`);
      if (!res.ok) {
        entries = [];
        return;
      }
      entries = await res.json();
    } finally {
      loadingEntries = false;
    }
  }

  function toggle(/** @type {string} */ id) {
    const next = new Set(selectedIds);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    selectedIds = next;
  }

  function selectAllInCurrency(/** @type {string} */ currency) {
    const next = new Set(selectedIds);
    for (const e of entries) {
      if (e.currency === currency) next.add(e.id);
    }
    selectedIds = next;
  }

  async function submit() {
    if (selectedIds.size === 0) return;
    if (selectionMixed) {
      toast.error('Pick a single currency to invoice.');
      return;
    }
    submitting = true;
    try {
      const res = await fetch('/api/invoices/from-time-entries/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          account_id: accountId,
          entry_ids: Array.from(selectedIds)
        })
      });
      if (!res.ok) {
        const e = await res.json().catch(() => ({}));
        toast.error(e?.error || 'Failed to create invoice');
        return;
      }
      const body = await res.json();
      toast.success(`Draft invoice ${body.invoice_number} created.`);
      open = false;
      await goto(`/invoices/${body.invoice_id}`);
    } finally {
      submitting = false;
    }
  }

  function formatMinutes(/** @type {number} */ minutes) {
    const h = Math.floor(minutes / 60);
    const m = minutes % 60;
    if (h && m) return `${h}h ${m}m`;
    if (h) return `${h}h`;
    return `${m}m`;
  }
</script>

<Dialog.Root bind:open onOpenChange={(v) => onOpenChange?.(v)}>
  <Dialog.Content class="sm:max-w-2xl">
    <Dialog.Header>
      <Dialog.Title>Create invoice from time entries</Dialog.Title>
      <Dialog.Description>
        Pick an account, then select billable, unbilled time entries. We'll
        create a new draft invoice with one line per entry.
      </Dialog.Description>
    </Dialog.Header>

    <div class="space-y-3">
      <label class="space-y-1 text-sm">
        <span class="font-medium">Account</span>
        <select
          bind:value={accountId}
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm"
        >
          <option value="" disabled>Select an account…</option>
          {#each accounts as a (a.id)}
            <option value={a.id}>{a.name}</option>
          {/each}
        </select>
      </label>

      {#if accountId}
        {#if loadingEntries}
          <div class="flex items-center gap-2 text-xs text-[var(--text-secondary)]">
            <Loader2 class="h-3.5 w-3.5 animate-spin" /> Loading unbilled entries…
          </div>
        {:else if entries.length === 0}
          <p class="rounded-md border border-amber-200 bg-amber-50 p-3 text-sm dark:border-amber-900/40 dark:bg-amber-900/20">
            No unbilled, billable time entries on cases under this account.
          </p>
        {:else}
          {@const grouped = entries.reduce(
            (m, e) => ((m[e.currency] = m[e.currency] || []).push(e), m),
            /** @type {Record<string, any[]>} */ ({})
          )}
          <div class="space-y-3">
            {#each Object.entries(grouped) as [currency, group] (currency)}
              <section class="rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-3">
                <header class="mb-2 flex items-center justify-between">
                  <span class="text-sm font-medium">{currency} ({group.length})</span>
                  <button
                    type="button"
                    onclick={() => selectAllInCurrency(currency)}
                    class="text-xs text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:underline"
                  >
                    Select all in {currency}
                  </button>
                </header>
                <ul class="space-y-1.5 text-xs">
                  {#each group as e (e.id)}
                    <li class="flex items-start gap-2 rounded bg-[var(--surface-muted)] p-2">
                      <input
                        type="checkbox"
                        class="mt-1"
                        checked={selectedIds.has(e.id)}
                        onchange={() => toggle(e.id)}
                      />
                      <div class="min-w-0 flex-1">
                        <p class="truncate">
                          {e.description || 'Untitled session'}
                        </p>
                        <p class="text-[10px] text-[var(--text-secondary)]">
                          {new Date(e.started_at).toLocaleString()} ·
                          {formatMinutes(e.duration_minutes)}
                          {#if e.hourly_rate}· {currency} {e.hourly_rate}/hr{/if}
                        </p>
                      </div>
                    </li>
                  {/each}
                </ul>
              </section>
            {/each}
          </div>
        {/if}

        {#if selectionMixed}
          <p class="rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-800 dark:border-red-900/40 dark:bg-red-900/20 dark:text-red-200">
            Selection contains multiple currencies. Pick entries from a single currency.
          </p>
        {/if}
      {/if}
    </div>

    <Dialog.Footer>
      <Button
        type="button"
        variant="outline"
        onclick={() => (open = false)}
        disabled={submitting}>Cancel</Button
      >
      <Button
        type="button"
        disabled={submitting ||
          !accountId ||
          selectedIds.size === 0 ||
          selectionMixed}
        onclick={submit}
      >
        {#if submitting}<Loader2 class="mr-1 h-3.5 w-3.5 animate-spin" />{/if}
        Create draft ({selectedIds.size})
      </Button>
    </Dialog.Footer>
  </Dialog.Content>
</Dialog.Root>
