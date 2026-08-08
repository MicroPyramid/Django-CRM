<script>
  import { resolve } from '$app/paths';
  /**
   * Tasks are the one list where the row itself is the work, so every row
   * carries the control that finishes it. v1 needed a click into a detail
   * page to tick a checkbox, which is why nobody ticked them.
   *
   * Now on the real API, and the tick is a PATCH. The mock left a note saying
   * this must never become "a tick that looks saved and is not", so the row
   * shows a pending state while the request is in flight and takes whatever
   * the server says, rather than assuming it worked.
   */
  import { page } from '$app/state';
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SectionTabs from '$lib/v2/components/SectionTabs.svelte';
  import FilterBar from '$lib/v2/components/FilterBar.svelte';
  import StatCard from '$lib/v2/components/StatCard.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import Avatar from '$lib/v2/components/Avatar.svelte';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import { count, relativeDays, daysSince } from '$lib/v2/format.js';
  import { TASK_PRIORITY_TONE, TASK_STATUS_TONE } from '$lib/v2/enums.js';
  import { enhance } from '$app/forms';
  import { CircleCheck, Circle, Plus } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let totals = $derived(data.totals);
  let tasks = $derived(data.tasks);

  /** Rows with a save in flight, so the tick can show it is thinking. */
  let saving = $state(/** @type {Record<string, boolean>} */ ({}));

  /** Overdue is only meaningful for something still open. */
  const overdueDays = (/** @type {any} */ t) => {
    if (!t.due_date || t.is_done) return 0;
    const n = daysSince(t.due_date) ?? 0;
    return n > 0 ? n : 0;
  };
</script>

<PageHeader title="Tasks">
  {#snippet sub()}
    <span class="v2-num">{count(totals.open)}</span> open ·
    <span class="v2-num" style="color:var(--v2-rust)">{count(totals.overdue)}</span> overdue
  {/snippet}
  {#snippet actions()}
    <a class="v2-btn v2-btn-primary" href={resolve('/tasks/new')}><Plus />New task</a>
  {/snippet}
</PageHeader>

{#if page.url.search}
  <p class="v2-sub" style="font-size:11.5px;margin:8px 0 0">
    These numbers describe the filtered list.
  </p>
{/if}

<SectionTabs set="tasks" />

<div class="v2-pad" style="padding-top:14px;flex:none">
  <div class="v2-stats">
    <StatCard
      label="Overdue"
      value={count(totals.overdue)}
      tone={totals.overdue ? 'rust' : 'slate'}
      detail={totals.overdue ? 'Do these before anything else' : 'Nothing late'}
    />
    <StatCard label="Due this week" value={count(totals.due_this_week)} tone="clay" />
    <StatCard label="Open" value={count(totals.open)} tone="ink" />
    <!-- The mock's fourth card was "Done this week". `Task` has no
         `completed_at`, so nothing records when a task was finished and that
         number could only have been invented. This one is real, and it is the
         more useful of the two: a task with no due date never becomes overdue
         and never appears in "due this week", so nothing ever puts it in front
         of anyone. -->
    <StatCard
      label="No due date"
      value={count(totals.no_due_date)}
      tone={totals.no_due_date ? 'clay' : 'slate'}
      detail={totals.no_due_date ? 'These never come up on their own' : 'Everything is dated'}
    />
  </div>
</div>

<FilterBar page="tasks" url={page.url} people={data.people} meId={data.meId} meta="Newest first" />

{#if form?.error}
  <p class="v2-pad v2-form-error" role="alert">{form.error}</p>
{/if}

<div class="v2-scroll">
  {#if tasks.length === 0}
    <EmptyState
      title={data.showAll ? 'No tasks yet' : 'Nothing on your list'}
      body={data.showAll
        ? 'Tasks show up here when you add one, or when a deal, ticket or lead needs a follow-up scheduled.'
        : 'Everything on your list is done. Show completed to see what you finished.'}
    >
      {#snippet icon()}<CircleCheck size={21} />{/snippet}
      {#snippet actions()}
        <a class="v2-btn v2-btn-primary" href={resolve('/tasks/new')}>New task</a>
        {#if !data.showAll}
          <a class="v2-btn" href={resolve('/tasks?all=1')}>Show completed</a>
        {/if}
      {/snippet}
    </EmptyState>
  {:else}
    <div class="v2-table-wrap">
      <table class="v2-table">
        <thead>
          <tr>
            <th style="width:38px"><span class="v2-sr-only">Done</span></th>
            <th>Task</th>
            <th>Attached to</th>
            <th>Priority</th>
            <th>Status</th>
            <th>Owner</th>
            <th class="v2-r">Due</th>
          </tr>
        </thead>
        <tbody>
          {#each tasks as t (t.id)}
            {@const late = overdueDays(t)}
            <tr style={t.is_done ? 'opacity:.5' : ''}>
              <!-- Not the identifier, so it must not take the title slot, but it
                   is the one control on this row, so it stays on the title line
                   at the left rather than dropping into the meta run. -->
              <td data-m="lead">
                <form
                  method="POST"
                  action="?/toggle"
                  use:enhance={() => {
                    saving[t.id] = true;
                    return async ({ update }) => {
                      await update({ reset: false });
                      saving[t.id] = false;
                    };
                  }}
                >
                  <input type="hidden" name="id" value={t.id} />
                  <input type="hidden" name="done" value={t.is_done ? 'false' : 'true'} />
                  <button
                    type="submit"
                    class="v2-tick"
                    disabled={saving[t.id]}
                    aria-label={t.is_done ? `Reopen ${t.title}` : `Mark ${t.title} done`}
                  >
                    {#if t.is_done}
                      <CircleCheck size={17} style="color:var(--v2-moss)" />
                    {:else}
                      <Circle size={17} />
                    {/if}
                  </button>
                </form>
              </td>
              <td data-m="title" style="white-space:normal;max-width:420px">
                <a
                  href={resolve(`/tasks/${t.id}`)}
                  class="v2-table-primary"
                  style={t.is_done ? 'text-decoration:line-through' : ''}>{t.title}</a
                >
                {#if t.description}
                  <span class="v2-table-secondary v2-task-note">{t.description}</span>
                {/if}
              </td>
              <td>
                {#if t.related}
                  <a href={resolve(t.related.href)} style="color:inherit">{t.related.name}</a>
                  <span class="v2-table-secondary v2-task-kind">{t.related.kind}</span>
                {:else}
                  <span class="v2-muted">—</span>
                {/if}
              </td>
              <td><Pill tone={TASK_PRIORITY_TONE[t.priority]}>{t.priority}</Pill></td>
              <td data-m="tag">
                <Pill tone={TASK_STATUS_TONE[t.status]}>{t.status}</Pill>
              </td>
              <td data-m="hide">
                {#if t.assigned_names.length}
                  <span style="display:flex;gap:5px;align-items:center">
                    {#each t.assigned_names as person (person)}
                      <Avatar name={person} size={22} />
                    {/each}
                  </span>
                {:else}
                  <span class="v2-muted">nobody</span>
                {/if}
              </td>
              <td
                class="v2-r"
                class:v2-muted={!late}
                style={late ? 'color:var(--v2-rust);font-weight:600' : ''}
              >
                {#if !t.due_date}
                  <span class="v2-muted">no due date</span>
                {:else if late}
                  {late}d late
                {:else}
                  {relativeDays(t.due_date)}
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="v2-sub v2-pad" style="font-size:12px;padding-bottom:24px">
      Showing <span class="v2-num">{tasks.length}</span> of
      <span class="v2-num">{count(data.showAll ? totals.count : totals.open)}</span>
      {data.showAll ? 'tasks' : 'open'}
      {#if !data.showAll}
        · <a href={resolve('/tasks?all=1')} style="color:inherit">include completed</a>
      {:else}
        · <a href={resolve('/tasks')} style="color:inherit">open only</a>
      {/if}
    </p>
  {/if}
</div>

<style>
  .v2-task-note,
  .v2-task-kind {
    display: block;
  }
  .v2-tick {
    border: 0;
    background: none;
    padding: 0;
    display: grid;
    place-items: center;
    cursor: pointer;
    color: var(--v2-slate);
  }
  .v2-tick:hover {
    color: var(--v2-ink);
  }
  .v2-tick:disabled {
    cursor: progress;
    opacity: 0.45;
  }
  /* Checking a task off is the main reason this page gets opened on a phone,
     and the target was the 17px icon itself. Grown to 40px and pulled back by
     the overhang, so the target changes but the layout does not. */
  @media (max-width: 768px) {
    .v2-tick {
      min-width: 40px;
      min-height: 40px;
      margin: -9px 0 -9px -11px;
    }
    /* A note long enough to explain itself is long enough to bury the next
       three tasks. Two lines here, the rest on the task itself. */
    .v2-task-note {
      display: -webkit-box;
      -webkit-line-clamp: 2;
      line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
    /* Hidden here rather than with data-m="hide", which would tie at equal
       specificity with the rule above and resolve on stylesheet order. */
    .v2-task-kind {
      display: none;
    }
  }
</style>
