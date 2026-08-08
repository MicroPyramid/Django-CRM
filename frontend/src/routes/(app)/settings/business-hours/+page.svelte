<script>
  import { resolve } from '$app/paths';
  /**
   * The calendar every response target is measured against.
   *
   * This page is small but it is the reason "answered in 4h" means anything.
   * A ticket opened at 17:20 on Friday and answered at 09:10 on Monday is
   * either fifteen hours late or fifty minutes early, and only this calendar
   * decides which. v1 hid it three levels into a settings dropdown, so the
   * analytics page reported numbers nobody could interpret.
   *
   * Closed days and holidays are shown, not omitted. A blank row for Saturday
   * reads as missing data; "Closed" reads as a decision.
   *
   * "Edit hours" and "Add" open the two panels below. `data.can_edit` only
   * decides whether those controls are offered: it is a display hint decoded
   * from the JWT, never the authorization decision. The backend re-derives
   * admin status from `request.profile` on every write and is what actually
   * refuses a non-admin.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import SettingsFormPanel from '$lib/v2/components/SettingsFormPanel.svelte';
  import ConfirmAction from '$lib/v2/components/ConfirmAction.svelte';
  import { shortDate, relativeDays } from '$lib/v2/format.js';
  import { weeklyHours, isAlwaysOn } from './week.js';
  import { Plus, Clock, TriangleAlert } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let calendar = $derived(data.calendar);

  let weekly = $derived(weeklyHours(calendar.days));

  /** See `week.js`: this is the state where the engine drops the calendar and
   *  runs the clock, so the page has to contradict its own rows. */
  let alwaysOn = $derived(isAlwaysOn(calendar.days));
  const todayName = new Intl.DateTimeFormat('en-GB', { weekday: 'long' }).format(new Date());

  // `null` when the panel is closed. One panel for the week, so only one
  // edit can be in flight at a time.
  let editingHours = $state(false);

  // The week being edited, seeded from `calendar.days` when the panel opens.
  // A day's key is its own name lower-cased ("Monday" → "monday"), the same
  // prefix the model's fourteen flat fields use, so no separate label map is
  // needed here. `closed` drives both the checkbox and whether the two time
  // inputs are disabled; a closed day still carries a sensible default time
  // so re-opening it doesn't hand back a blank field.
  let hourRows = $state(
    /** @type {{ day: string, key: string, open: string, close: string, closed: boolean }[]} */ ([])
  );

  function openHoursEdit() {
    hourRows = calendar.days.map((d) => ({
      day: d.day,
      key: d.day.toLowerCase(),
      open: d.open ?? '09:00',
      close: d.close ?? '17:00',
      closed: !d.open
    }));
    editingHours = true;
  }

  // `null` when the panel is closed.
  let addingHoliday = $state(false);
</script>

<PageHeader title="Business hours">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    {calendar.name} · {calendar.timezone} ·
    {#if alwaysOn}
      no day open, so targets run around the clock
    {:else}
      <span class="v2-num">{weekly}</span> hours a week
    {/if}
  {/snippet}
  {#snippet actions()}
    {#if data.can_edit && !editingHours}
      <button class="v2-btn v2-btn-primary" onclick={openHoursEdit}>Edit hours</button>
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    <div class="v2-split">
      <div>
        <div class="v2-label" style="margin-bottom:10px">Open hours</div>

        {#if editingHours}
          <SettingsFormPanel
            title="Edit business hours"
            action="?/updateHours"
            error={form?.updateHours?.error}
            submitLabel="Save hours"
            oncancel={() => (editingHours = false)}
            ondone={() => (editingHours = false)}
          >
            {#snippet fields()}
              <div class="v2-field">
                <label for="bh-name">Name</label>
                <input
                  id="bh-name"
                  class="v2-input"
                  name="name"
                  maxlength="100"
                  required
                  value={calendar.name}
                />
              </div>

              <div class="v2-field">
                <label for="bh-timezone">Timezone</label>
                <input
                  id="bh-timezone"
                  class="v2-input"
                  name="timezone"
                  maxlength="64"
                  required
                  value={calendar.timezone}
                  placeholder="America/New_York"
                />
                <p class="v2-hint">IANA timezone name.</p>
              </div>

              <div class="v2-field v2-sfp-wide">
                <label for="bh-day-0-open">Week</label>
                {#each hourRows as row, i (row.key)}
                  <div style="display:flex;gap:10px;align-items:center;margin-bottom:8px">
                    <span style="width:84px;font-size:13px;flex:none">{row.day}</span>
                    <label
                      style="display:flex;gap:6px;align-items:center;font-size:12px;font-weight:400;flex:none"
                    >
                      <input
                        type="checkbox"
                        name="{row.key}_closed"
                        value="true"
                        bind:checked={row.closed}
                      />
                      Closed
                    </label>
                    <input
                      id={i === 0 ? 'bh-day-0-open' : undefined}
                      class="v2-input"
                      type="time"
                      name="{row.key}_open"
                      bind:value={row.open}
                      disabled={row.closed}
                      style="width:auto"
                    />
                    <span class="v2-sub">to</span>
                    <input
                      class="v2-input"
                      type="time"
                      name="{row.key}_close"
                      bind:value={row.close}
                      disabled={row.closed}
                      style="width:auto"
                    />
                  </div>
                {/each}
              </div>
            {/snippet}
          </SettingsFormPanel>
        {/if}

        {#if alwaysOn}
          <div class="v2-bh-banner">
            <TriangleAlert size={17} style="color:var(--v2-clay);flex:none;margin-top:1px" />
            <div>
              <div style="font-weight:600;font-size:13px">
                Every day is closed, and the clock still runs
              </div>
              <p class="v2-sub" style="font-size:12px;margin:4px 0 0">
                A four-hour target expires four hours after the ticket arrives, weekend or not. The
                engine drops a calendar that never opens rather than treating it as permanently
                shut, so open at least one day to make this calendar count.
              </p>
            </div>
          </div>
        {/if}

        <div class="v2-card" style="overflow:hidden">
          {#each calendar.days as d (d.day)}
            <div class="v2-setting" style={d.day === todayName ? 'background:var(--v2-hover)' : ''}>
              <div class="v2-setting-body">
                <b>{d.day}</b>
                {#if d.day === todayName}
                  <span class="v2-sub" style="font-size:11px">today</span>
                {/if}
              </div>
              {#if d.open && d.close}
                <span class="v2-num" style="font-size:13px">{d.open} - {d.close}</span>
              {:else}
                <!-- Named, not blank. A blank cell reads as missing data. -->
                <span class="v2-sub" style="font-size:12.5px">Closed</span>
              {/if}
            </div>
          {/each}
        </div>

        {#if calendar.is_default}
          <p class="v2-sub" style="font-size:11.5px;margin-top:11px">
            This is the default calendar, so it applies to every ticket that does not have a more
            specific one.
          </p>
        {/if}
      </div>

      <div>
        <div style="display:flex;align-items:baseline;margin-bottom:10px">
          <div class="v2-label">Holidays</div>
          {#if data.can_edit && !addingHoliday}
            <button
              class="v2-btn v2-btn-sm"
              style="margin-left:auto"
              onclick={() => (addingHoliday = true)}
            >
              <Plus size={12} />Add
            </button>
          {/if}
        </div>

        {#if addingHoliday}
          <SettingsFormPanel
            title="Add holiday"
            action="?/addHoliday"
            error={form?.addHoliday?.error}
            submitLabel="Add holiday"
            oncancel={() => (addingHoliday = false)}
            ondone={() => (addingHoliday = false)}
          >
            {#snippet fields()}
              <div class="v2-field">
                <label for="bh-holiday-date">Date</label>
                <input id="bh-holiday-date" class="v2-input" type="date" name="date" required />
              </div>
              <div class="v2-field">
                <label for="bh-holiday-name">Name</label>
                <input
                  id="bh-holiday-name"
                  class="v2-input"
                  name="name"
                  maxlength="100"
                  required
                  placeholder="Christmas"
                />
              </div>
            {/snippet}
          </SettingsFormPanel>
        {/if}

        {#if form?.removeHoliday?.error}
          <p class="v2-error" style="margin-bottom:12px">{form.removeHoliday.error}</p>
        {/if}
        {#if form?.holidayAlreadyNamed}
          <!-- The POST is idempotent on date and answers 200 with the row that
               was already stored, so the name just typed was discarded. Silence
               here reads as a successful rename. -->
          <p class="v2-sub" style="margin-bottom:12px;font-size:12px">
            That date was already a holiday, called
            <b style="font-weight:600">{form.holidayAlreadyNamed}</b>. The name you typed was not
            saved: remove it and add it again to rename it.
          </p>
        {/if}

        <div class="v2-card" style="overflow:hidden">
          {#each calendar.holidays as h (h.id)}
            <div class="v2-setting">
              <div class="v2-setting-body">
                <b>{h.name}</b>
                <span class="v2-sub" style="font-size:11.5px">{relativeDays(h.date)}</span>
              </div>
              <span class="v2-num" style="font-size:12.5px">{shortDate(h.date)}</span>
              {#if data.can_edit}
                <ConfirmAction
                  action="?/removeHoliday"
                  label="Remove"
                  confirmLabel="Remove"
                  explain="Deletes it. The day counts as working time again."
                  hidden={{ holiday_id: h.id }}
                />
              {/if}
            </div>
          {:else}
            <p class="v2-sub" style="padding:14px 16px;font-size:12.5px;margin:0">
              No holidays set. Targets will keep running on public holidays.
            </p>
          {/each}
        </div>

        <div
          style="display:flex;gap:10px;align-items:flex-start;margin-top:18px;padding:14px 16px;border:1px solid var(--v2-line);border-radius:var(--v2-radius)"
        >
          <Clock size={16} style="color:var(--v2-slate);flex:none;margin-top:1px" />
          <div>
            <div style="font-weight:600;font-size:13px">What this changes</div>
            <p class="v2-sub" style="font-size:12px;margin:4px 0 0">
              {#if alwaysOn}
                <!-- The claim above this branch is false when nothing is open:
                     `_has_any_open_window` is what decides whether the calendar
                     is consulted at all, and with no open day it is not. -->
                With no day open, targets do not count anything out: they run on the wall clock, through
                evenings, weekends and the holidays below.
              {:else}
                Response and resolution targets count only the time inside these hours. A ticket
                opened at 17:20 on Friday
                {#if calendar.days[0].open}
                  starts its clock at <span class="v2-num">{calendar.days[0].open}</span> on Monday,
                {:else}
                  <!-- Monday can be marked closed from this page now, so the
                       fixed "Monday morning" framing can no longer assume an
                       open time exists to quote. -->
                  starts its clock whenever the week next opens,
                {/if}
                so the weekend does not spend a four-hour target.
              {/if}
            </p>
            <p class="v2-sub" style="font-size:12px;margin:8px 0 0">
              <a href={resolve('/tickets/analytics')} style="color:inherit">Service analytics</a> is measured
              on this calendar.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>

<style>
  .v2-bh-banner {
    display: flex;
    gap: 11px;
    align-items: flex-start;
    padding: 14px 16px;
    margin-bottom: 12px;
    border: 1px solid var(--v2-line);
    border-radius: var(--v2-radius);
    background: var(--v2-card);
  }
</style>
