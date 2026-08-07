<script>
  import { resolve } from '$app/paths';
  /**
   * The task calendar. One month at a time, dated tasks sitting on the day they
   * are due. The view that answers "what is coming" the way a list can't.
   *
   * Two layouts from one set of cells: a seven-column grid on a wide screen, an
   * agenda (only the days that carry work) on a phone, where a 7×6 grid would be
   * unreadable. Both come from `data.weeks`/`data.agenda`, so they can never
   * show different tasks. Everything here is read-only, the tick, the edit and
   * the drag all live on the other two task views; this one is for seeing.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SectionTabs from '$lib/v2/components/SectionTabs.svelte';
  import { count } from '$lib/v2/format.js';
  import { TASK_PRIORITY_TONE } from '$lib/v2/enums.js';
  import { ChevronLeft, ChevronRight, CalendarDays } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  const TONE_VAR = {
    ink: 'var(--v2-ink)',
    slate: 'var(--v2-slate)',
    clay: 'var(--v2-clay)',
    rust: 'var(--v2-rust)',
    moss: 'var(--v2-moss)'
  };

  /** Overdue trumps priority. A late card is rust whatever it was set to. */
  const dot = (/** @type {any} */ t) =>
    t.overdue ? TONE_VAR.rust : (TONE_VAR[TASK_PRIORITY_TONE[t.priority]] ?? TONE_VAR.slate);

  const CAP = 4; // chips per cell before it collapses to "+N more"
</script>

<PageHeader title="Tasks">
  {#snippet sub()}
    {data.monthLabel} · <span class="v2-num">{count(data.datedCount)}</span> scheduled
  {/snippet}
  {#snippet actions()}
    <div class="v2-cal-nav">
      <a
        class="v2-btn v2-btn-icon"
        href={resolve(`/tasks/calendar?month=${data.prevMonth}`)}
        aria-label="Previous month"
        data-sveltekit-noscroll
      >
        <ChevronLeft size={15} />
      </a>
      {#if !data.isThisMonth}
        <a
          class="v2-btn v2-btn-sm"
          href={resolve(`/tasks/calendar?month=${data.thisMonth}`)}
          data-sveltekit-noscroll>Today</a
        >
      {/if}
      <a
        class="v2-btn v2-btn-icon"
        href={resolve(`/tasks/calendar?month=${data.nextMonth}`)}
        aria-label="Next month"
        data-sveltekit-noscroll
      >
        <ChevronRight size={15} />
      </a>
    </div>
  {/snippet}
</PageHeader>

<SectionTabs set="tasks" />

<div class="v2-scroll">
  <!-- Wide screens: the month grid. -->
  <div class="v2-cal-grid-wrap">
    <div class="v2-cal-head">
      {#each data.weekdays as label (label)}
        <span class="v2-label">{label}</span>
      {/each}
    </div>
    <div class="v2-cal-grid">
      {#each data.weeks as week, w (w)}
        {#each week as cell (cell.date)}
          <div
            class="v2-cal-cell"
            class:v2-cal-out={!cell.inMonth}
            class:v2-cal-weekend={cell.isWeekend}
            class:v2-cal-today={cell.isToday}
          >
            <div class="v2-cal-daynum">
              {#if cell.isToday}
                <span class="v2-cal-today-badge">{cell.day}</span>
              {:else}
                {cell.day}
              {/if}
            </div>
            <div class="v2-cal-cell-body">
              {#each cell.tasks.slice(0, CAP) as t (t.id)}
                <a
                  class="v2-cal-chip"
                  class:v2-cal-chip-done={t.is_done}
                  href={resolve(`/tasks/${t.id}`)}
                  title={t.title}
                >
                  <i class="v2-cal-dot" style="background:{dot(t)}"></i>
                  <span class="v2-cal-chip-text">{t.title}</span>
                </a>
              {/each}
              {#if cell.tasks.length > CAP}
                <span class="v2-cal-more">+{cell.tasks.length - CAP} more</span>
              {/if}
            </div>
          </div>
        {/each}
      {/each}
    </div>
  </div>

  <!-- Narrow screens: an agenda of the days that actually have work. -->
  <div class="v2-cal-agenda">
    {#if data.agenda.length === 0}
      <div class="v2-state" style="padding:34px 0">
        <div class="v2-state-icon"><CalendarDays size={22} /></div>
        <h3>Nothing scheduled</h3>
        <p>No tasks fall due in {data.monthLabel}.</p>
      </div>
    {:else}
      {#each data.agenda as day (day.date)}
        <div class="v2-cal-agenda-day">
          <div class="v2-cal-agenda-date" class:v2-cal-agenda-today={day.isToday}>
            <span class="v2-num">{day.day}</span>
            {#if day.isToday}<span class="v2-cal-agenda-todaytag">Today</span>{/if}
          </div>
          <div class="v2-cal-agenda-list">
            {#each day.tasks as t (t.id)}
              <a
                class="v2-cal-chip"
                class:v2-cal-chip-done={t.is_done}
                href={resolve(`/tasks/${t.id}`)}
              >
                <i class="v2-cal-dot" style="background:{dot(t)}"></i>
                <span class="v2-cal-chip-text">{t.title}</span>
                {#if t.overdue}<span class="v2-cal-overdue">overdue</span>{/if}
              </a>
            {/each}
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <p class="v2-sub v2-pad v2-cal-foot">
    Tasks without a due date don't appear here,
    <a href={resolve('/tasks')} style="color:inherit">see the task list</a>.
    {#if data.truncated}
      This month has more scheduled tasks than fit on the calendar; the list shows them all.
    {/if}
  </p>
</div>

<style>
  .v2-cal-nav {
    display: flex;
    align-items: center;
    gap: 6px;
  }
  .v2-btn-icon {
    padding-left: 8px;
    padding-right: 8px;
  }

  /* Weekday header, aligned to the grid below it. */
  .v2-cal-head {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 6px;
    padding: 14px 16px 6px;
    flex: none;
  }
  .v2-cal-head .v2-label {
    padding-left: 2px;
  }

  .v2-cal-grid-wrap {
    padding: 0 16px 8px;
  }
  .v2-cal-grid {
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    grid-auto-rows: minmax(96px, auto);
    gap: 6px;
  }
  .v2-cal-cell {
    display: flex;
    flex-direction: column;
    gap: 4px;
    padding: 6px;
    background: var(--v2-card);
    border: 1px solid var(--v2-line);
    border-radius: 8px;
    min-width: 0;
  }
  /* Days spilling in from the neighbouring months recede, so the current month
     reads as one block. */
  .v2-cal-out {
    background: none;
    border-color: transparent;
  }
  .v2-cal-out .v2-cal-daynum {
    color: var(--v2-slate);
    opacity: 0.55;
  }
  .v2-cal-weekend:not(.v2-cal-out) {
    background: color-mix(in srgb, var(--v2-slate) 5%, var(--v2-card));
  }
  .v2-cal-today {
    border-color: var(--v2-ember);
  }
  .v2-cal-daynum {
    font-size: 12px;
    font-weight: 600;
    color: var(--v2-ink);
    line-height: 1;
    display: flex;
    justify-content: flex-end;
  }
  /* Today is the one Ember mark on the page. It is "you are here", the nearest
     thing a calendar has to something that needs you. */
  .v2-cal-today-badge {
    display: inline-grid;
    place-items: center;
    min-width: 19px;
    height: 19px;
    padding: 0 5px;
    border-radius: 9px;
    background: var(--v2-ember);
    color: #fff;
    font-size: 11.5px;
  }
  .v2-cal-cell-body {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-width: 0;
  }

  .v2-cal-chip {
    display: flex;
    align-items: center;
    gap: 5px;
    padding: 2px 5px;
    border-radius: 5px;
    background: var(--v2-paper);
    color: var(--v2-ink);
    font-size: 11.5px;
    line-height: 1.35;
    text-decoration: none;
    min-width: 0;
  }
  .v2-cal-chip:hover {
    background: color-mix(in srgb, var(--v2-slate) 12%, var(--v2-card));
  }
  .v2-cal-chip-done {
    opacity: 0.55;
  }
  .v2-cal-chip-done .v2-cal-chip-text {
    text-decoration: line-through;
  }
  .v2-cal-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    flex: none;
  }
  .v2-cal-chip-text {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    min-width: 0;
  }
  .v2-cal-more {
    font-size: 11px;
    color: var(--v2-slate);
    padding: 1px 5px;
  }
  .v2-cal-overdue {
    margin-left: auto;
    font-size: 10.5px;
    color: var(--v2-rust);
    font-weight: 600;
    flex: none;
  }
  .v2-cal-foot {
    font-size: 12px;
    padding-top: 14px;
    padding-bottom: 24px;
  }

  /* Agenda is the phone view; hidden on wide screens. */
  .v2-cal-agenda {
    display: none;
  }
  .v2-cal-agenda-day {
    display: flex;
    gap: 12px;
    padding: 12px 16px;
    border-bottom: 1px solid var(--v2-line-soft);
  }
  .v2-cal-agenda-date {
    flex: none;
    width: 40px;
    text-align: center;
    color: var(--v2-ink);
  }
  .v2-cal-agenda-date .v2-num {
    font-size: 18px;
    font-weight: 650;
  }
  .v2-cal-agenda-today .v2-num {
    color: var(--v2-ember);
  }
  .v2-cal-agenda-todaytag {
    display: block;
    font-size: 10px;
    color: var(--v2-ember);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }
  .v2-cal-agenda-list {
    display: flex;
    flex-direction: column;
    gap: 5px;
    min-width: 0;
    flex: 1;
  }
  .v2-cal-agenda .v2-cal-chip {
    font-size: 13px;
    padding: 6px 9px;
    border: 1px solid var(--v2-line);
    background: var(--v2-card);
  }

  @media (max-width: 767px) {
    .v2-cal-grid-wrap,
    .v2-cal-head {
      display: none;
    }
    .v2-cal-agenda {
      display: block;
    }
  }
</style>
