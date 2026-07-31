<script>
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
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import { shortDate, relativeDays } from '$lib/v2/format.js';
  import { Plus, Clock } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let calendar = $derived(data.calendar);

  /** Hours a day is open, for the weekly total. */
  function hours(d) {
    if (!d.open || !d.close) return 0;
    const [oh, om] = d.open.split(':').map(Number);
    const [ch, cm] = d.close.split(':').map(Number);
    return (ch * 60 + cm - (oh * 60 + om)) / 60;
  }

  let weekly = $derived(calendar.days.reduce((a, d) => a + hours(d), 0));
  const todayName = new Intl.DateTimeFormat('en-GB', { weekday: 'long' }).format(new Date());
</script>

<PageHeader title="Business hours">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    {calendar.name} · {calendar.timezone} ·
    <span class="v2-num">{weekly}</span> hours a week
  {/snippet}
  {#snippet actions()}
    <button class="v2-btn v2-btn-primary">Edit hours</button>
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    <div class="v2-split">
      <div>
        <div class="v2-label" style="margin-bottom:10px">Open hours</div>
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
                <span class="v2-num" style="font-size:13px">{d.open} – {d.close}</span>
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
          <button class="v2-btn v2-btn-sm" style="margin-left:auto"><Plus size={12} />Add</button>
        </div>
        <div class="v2-card" style="overflow:hidden">
          {#each calendar.holidays as h (h.id)}
            <div class="v2-setting">
              <div class="v2-setting-body">
                <b>{h.name}</b>
                <span class="v2-sub" style="font-size:11.5px">{relativeDays(h.date)}</span>
              </div>
              <span class="v2-num" style="font-size:12.5px">{shortDate(h.date)}</span>
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
              Response and resolution targets count only the time inside these hours. A ticket
              opened at 17:20 on Friday starts its clock at
              <span class="v2-num">{calendar.days[0].open}</span> on Monday, so the weekend does not spend
              a four-hour target.
            </p>
            <p class="v2-sub" style="font-size:12px;margin:8px 0 0">
              <a href="/v2/tickets/analytics" style="color:inherit">Service analytics</a> is measured
              on this calendar.
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
