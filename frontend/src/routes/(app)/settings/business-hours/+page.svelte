<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Loader2, Clock, Check, Plus, Trash2 } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const calendar = $derived(data.calendar || {});
  const calendarId = $derived(calendar.id || '');

  const WEEKDAYS = [
    { key: 'monday', label: 'Monday' },
    { key: 'tuesday', label: 'Tuesday' },
    { key: 'wednesday', label: 'Wednesday' },
    { key: 'thursday', label: 'Thursday' },
    { key: 'friday', label: 'Friday' },
    { key: 'saturday', label: 'Saturday' },
    { key: 'sunday', label: 'Sunday' }
  ];

  // A short whitelist of common IANA zones; the API accepts any valid zone but
  // a real picker isn't worth it here.
  const TIMEZONES = [
    'UTC',
    'America/New_York',
    'America/Chicago',
    'America/Denver',
    'America/Los_Angeles',
    'Europe/London',
    'Europe/Paris',
    'Europe/Berlin',
    'Asia/Tokyo',
    'Asia/Singapore',
    'Asia/Kolkata',
    'Australia/Sydney'
  ];

  /** @param {string|null|undefined} t */
  const trimSeconds = (t) => (t ? String(t).slice(0, 5) : '');

  let timezone = $state('UTC');
  let name = $state('Default');
  /** @type {Record<string, { open: string, close: string, closed: boolean }>} */
  let days = $state({});
  let saving = $state(false);

  let newHolidayDate = $state('');
  let newHolidayName = $state('');

  $effect(() => {
    timezone = calendar.timezone || 'UTC';
    name = calendar.name || 'Default';
    /** @type {Record<string, { open: string, close: string, closed: boolean }>} */
    const next = {};
    for (const d of WEEKDAYS) {
      const open = trimSeconds(calendar[`${d.key}_open`]);
      const close = trimSeconds(calendar[`${d.key}_close`]);
      next[d.key] = {
        open: open || '09:00',
        close: close || '17:00',
        closed: !open || !close
      };
    }
    days = next;
  });
</script>

<svelte:head>
  <title>Business Hours - Settings - BottleCRM</title>
</svelte:head>

<PageHeader
  title="Business Hours"
  subtitle="Working hours and holidays SLA timers honor"
>
  {#snippet actions()}
    <Button type="submit" form="business-hours-form" disabled={saving} class="gap-2">
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
    id="business-hours-form"
    method="POST"
    action="?/update"
    use:enhance={() => {
      saving = true;
      return async ({ result, update }) => {
        await update();
        saving = false;
        if (result.type === 'success') {
          toast.success('Business hours saved');
          await invalidateAll();
        } else if (result.type === 'failure') {
          toast.error(form?.error || 'Failed to save');
        }
      };
    }}
    class="mx-auto max-w-3xl space-y-6"
  >
    <input type="hidden" name="id" value={calendarId} />
    <input type="hidden" name="name" value={name} />

    <section
      class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-6 space-y-5"
    >
      <header class="flex items-start gap-3">
        <div
          class="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
        >
          <Clock class="h-4 w-4" />
        </div>
        <div>
          <h2 class="text-base font-medium text-[var(--text-primary)]">
            Working hours
          </h2>
          <p class="text-sm text-[var(--text-secondary)]">
            Tickets opened outside these hours don't burn SLA. Holidays and customer-wait
            time (status Pending) are excluded automatically.
          </p>
        </div>
      </header>

      <div class="space-y-2">
        <Label for="timezone" class="text-sm">Timezone</Label>
        <select
          id="timezone"
          name="timezone"
          bind:value={timezone}
          class="w-72 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary-default)]"
        >
          {#each TIMEZONES as tz (tz)}
            <option value={tz}>{tz}</option>
          {/each}
        </select>
      </div>

      <div class="overflow-hidden rounded-md border border-[var(--border-default)]">
        <table class="w-full text-sm">
          <thead class="bg-[var(--surface-muted)] text-xs uppercase tracking-wide text-[var(--text-secondary)]">
            <tr>
              <th class="px-3 py-2 text-left">Day</th>
              <th class="px-3 py-2 text-left">Closed</th>
              <th class="px-3 py-2 text-left">Open</th>
              <th class="px-3 py-2 text-left">Close</th>
            </tr>
          </thead>
          <tbody>
            {#each WEEKDAYS as d (d.key)}
              <tr class="border-t border-[var(--border-default)]">
                <td class="px-3 py-2">{d.label}</td>
                <td class="px-3 py-2">
                  <input
                    type="checkbox"
                    bind:checked={days[d.key].closed}
                    class="h-4 w-4 rounded border-[var(--border-default)]"
                    aria-label={`Mark ${d.label} closed`}
                  />
                  <input
                    type="hidden"
                    name={`${d.key}_closed`}
                    value={days[d.key].closed ? 'true' : 'false'}
                  />
                </td>
                <td class="px-3 py-2">
                  <Input
                    type="time"
                    name={`${d.key}_open`}
                    bind:value={days[d.key].open}
                    disabled={days[d.key].closed}
                    class="w-32"
                  />
                </td>
                <td class="px-3 py-2">
                  <Input
                    type="time"
                    name={`${d.key}_close`}
                    bind:value={days[d.key].close}
                    disabled={days[d.key].closed}
                    class="w-32"
                  />
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>

    {#if form?.error}
      <p class="text-sm text-[var(--color-danger-default)]">{form.error}</p>
    {/if}
  </form>

  <section
    class="mx-auto mt-6 max-w-3xl rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-6 space-y-4"
  >
    <header>
      <h2 class="text-base font-medium text-[var(--text-primary)]">Holidays</h2>
      <p class="text-sm text-[var(--text-secondary)]">
        Full days off in the calendar's timezone. SLA timers skip them entirely.
      </p>
    </header>

    <form
      method="POST"
      action="?/addHoliday"
      use:enhance={() => async ({ result, update }) => {
        await update();
        if (result.type === 'success') {
          newHolidayDate = '';
          newHolidayName = '';
          toast.success('Holiday added');
          await invalidateAll();
        } else if (result.type === 'failure') {
          toast.error('Failed to add holiday');
        }
      }}
      class="flex flex-wrap items-end gap-3"
    >
      <input type="hidden" name="id" value={calendarId} />
      <div class="space-y-1">
        <Label for="holiday_date" class="text-xs">Date</Label>
        <Input
          id="holiday_date"
          name="date"
          type="date"
          bind:value={newHolidayDate}
          required
          class="w-48"
        />
      </div>
      <div class="flex-1 space-y-1">
        <Label for="holiday_name" class="text-xs">Name</Label>
        <Input
          id="holiday_name"
          name="name"
          type="text"
          maxlength="100"
          placeholder="e.g. Christmas Day"
          bind:value={newHolidayName}
          required
        />
      </div>
      <Button type="submit" variant="outline" class="gap-1">
        <Plus class="h-4 w-4" />
        Add
      </Button>
    </form>

    {#if (calendar.holidays || []).length === 0}
      <p class="text-sm text-[var(--text-secondary)]">No holidays configured.</p>
    {:else}
      <ul class="divide-y divide-[var(--border-default)] rounded-md border border-[var(--border-default)]">
        {#each calendar.holidays as h (h.id)}
          <li class="flex items-center justify-between gap-2 px-3 py-2 text-sm">
            <span class="flex items-center gap-3">
              <span class="font-mono text-xs text-[var(--text-secondary)]">{h.date}</span>
              <span>{h.name}</span>
            </span>
            <form
              method="POST"
              action="?/removeHoliday"
              use:enhance={() => async ({ result, update }) => {
                await update();
                if (result.type === 'success') {
                  toast.success('Holiday removed');
                  await invalidateAll();
                } else if (result.type === 'failure') {
                  toast.error('Failed to remove holiday');
                }
              }}
            >
              <input type="hidden" name="id" value={calendarId} />
              <input type="hidden" name="hid" value={h.id} />
              <Button
                type="submit"
                variant="ghost"
                size="sm"
                class="h-7 w-7 p-0 text-[var(--text-secondary)] hover:text-[var(--color-danger-default)]"
                aria-label="Remove holiday"
                title="Remove holiday"
              >
                <Trash2 class="h-4 w-4" />
              </Button>
            </form>
          </li>
        {/each}
      </ul>
    {/if}
  </section>
</div>
