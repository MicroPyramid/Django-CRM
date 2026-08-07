<script>
  import { resolve } from '$app/paths';
  /**
   * One task: what it is, what it is attached to, who is on it, and the one
   * control that finishes it.
   *
   * A task is an action item, not a person or a record, so the page is built
   * around the verb. The identity mark is a completion circle at the leading
   * edge of the title, the universal "tick to finish" control, and it is the
   * same one-field PATCH the list row sends, in the position the eye already
   * goes to. Everything below is the note, the parent record, the people, and
   * the conversation.
   *
   * Brought to the shape of the lead and contact detail pages: the flat
   * read-only comment list is now a writable activity feed that takes comments
   * AND files, day-grouped and filterable. Nothing is faked. Every event kind
   * is backed by a row that exists (`Task` has no history table, so there are no
   * invented status events beyond the record's own creation).
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import NextAction from '$lib/v2/components/NextAction.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import Avatar from '$lib/v2/components/Avatar.svelte';
  import { relativeDays, longDate, shortDate, daysSince } from '$lib/v2/format.js';
  import { TASK_PRIORITY_TONE, TASK_STATUS_TONE } from '$lib/v2/enums.js';
  import { enhance } from '$app/forms';
  import {
    ChevronRight,
    CircleCheck,
    Circle,
    Paperclip,
    MessageSquare,
    Sparkles,
    X
  } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let { task, activity, contacts, owners, canDelete } = $derived(data);

  let late = $derived.by(() => {
    if (!task.due_date || task.is_done) return 0;
    const n = daysSince(task.due_date) ?? 0;
    return n > 0 ? n : 0;
  });

  /**
   * The next single step, said as a step.
   *
   * A task has exactly one, and which one depends on two facts the page
   * already shows, so this is not new information, it is the same
   * information with the verb attached. A finished task has no next step.
   */
  let next = $derived.by(() => {
    if (task.is_done) return null;
    if (late) {
      return {
        label: `${late} ${late === 1 ? 'day' : 'days'} late`,
        text: `This was due ${longDate(task.due_date)}. Finish it or move the date. Leaving it late does neither.`
      };
    }
    if (!task.due_date) {
      return {
        label: 'No due date',
        text: 'Nothing will bring this back to your attention. Give it a date, or close it if it is not really a task.'
      };
    }
    return null;
  });

  // ── comment composer ─────────────────────────────────────────────────────
  let comment = $state('');
  let saving = $state(false);

  // The picked file's name, mirrored out of the input so the composer can show
  // and clear it. `fileInput` is the element itself. A file input's value can
  // only be cleared through the DOM, not by rebinding.
  let fileName = $state('');
  /** @type {HTMLInputElement | undefined} */
  let fileInput;

  /** @param {Event} e */
  function pickFile(e) {
    fileName = /** @type {HTMLInputElement} */ (e.currentTarget).files?.[0]?.name ?? '';
  }
  function clearFile() {
    if (fileInput) fileInput.value = '';
    fileName = '';
  }

  // A task accepts a file on its own, the API saves the attachment in a block
  // separate from the comment, so the composer sends when there is either text
  // or a file, and the button says which it will do.
  let canSubmit = $derived(Boolean(comment.trim() || fileName));

  // ── activity feed ────────────────────────────────────────────────────────
  // Three real kinds (comment / file / created). The filter only appears once
  // there is a file to filter. With nothing but comments it would sort one pile.
  let hasFiles = $derived(activity.some((/** @type {any} */ e) => e.type === 'file'));
  let filter = $state(/** @type {'all'|'comments'|'files'} */ ('all'));
  let shown = $derived(
    filter === 'files'
      ? activity.filter((/** @type {any} */ e) => e.type === 'file')
      : filter === 'comments'
        ? activity.filter((/** @type {any} */ e) => e.type !== 'file')
        : activity
  );
  let newestId = $derived(shown[0]?.id ?? null);

  /**
   * The line under an event: "Attached" for a file, the author where known, then
   * how long ago, joined so no separator dangles when a part is missing.
   * @param {{type:string,by:string|null,at:string}} e
   */
  function metaFor(e) {
    const parts = [];
    if (e.type === 'file') parts.push('Attached');
    if (e.by) parts.push(e.by);
    parts.push(relativeDays(e.at));
    return parts.join(' · ');
  }

  /** @param {string} iso */
  function dayGroup(iso) {
    const n = daysSince(iso);
    if (n === 0) return 'Today';
    if (n === 1) return 'Yesterday';
    return shortDate(iso);
  }

  // Interleave day headers so each date is announced once, in order.
  let feed = $derived.by(() => {
    /** @type {Array<{kind:'day',id:string,label:string}|{kind:'event',id:string,event:any}>} */
    const out = [];
    let last = null;
    for (const e of shown) {
      const g = dayGroup(e.at);
      if (g !== last) {
        out.push({ kind: 'day', id: `day-${g}-${e.id}`, label: g });
        last = g;
      }
      out.push({ kind: 'event', id: e.id, event: e });
    }
    return out;
  });
</script>

<PageHeader title={task.title} record>
  {#snippet leading()}
    <!-- The completion control, at the leading edge of the title where task
         software has trained the eye to look. Same one-field PATCH as the list
         row; a filled moss circle means done, and clicking it reopens. -->
    <form method="POST" action="?/toggle" use:enhance style="display:flex">
      <input type="hidden" name="done" value={task.is_done ? 'false' : 'true'} />
      <button
        class="done-toggle"
        class:done={task.is_done}
        type="submit"
        aria-label={task.is_done ? 'Reopen task' : 'Mark task done'}
        title={task.is_done ? 'Reopen task' : 'Mark done'}
      >
        {#if task.is_done}<CircleCheck size={24} />{:else}<Circle size={24} />{/if}
      </button>
    </form>
  {/snippet}
  {#snippet crumb()}
    <a href={resolve('/tasks')}>Tasks</a>
    <ChevronRight size={12} />
    <span>{task.status}</span>
  {/snippet}
  {#snippet sub()}
    {[
      task.related ? `on ${task.related.name}` : 'not attached to a record',
      task.due_date ? `due ${relativeDays(task.due_date)}` : 'no due date',
      task.assigned_names.length ? task.assigned_names.join(', ') : 'nobody assigned'
    ].join(' · ')}
  {/snippet}
  {#snippet actions()}
    <a class="v2-btn" href={resolve(`/tasks/${task.id}/edit`)}>Edit</a>
    {#if canDelete}
      <form method="POST" action="?/delete" use:enhance>
        <button class="v2-btn" type="submit">Delete</button>
      </form>
    {/if}
  {/snippet}
</PageHeader>

<div style="display:flex;flex:1;min-height:0;overflow:hidden">
  <div class="v2-main">
    <div class="v2-scroll">
      <div class="v2-pad" style="padding-top:16px;padding-bottom:32px">
        {#if form?.error}
          <p style="color:var(--v2-rust);font-size:12.5px;margin:0 0 14px" role="alert">
            {form.error}
          </p>
        {/if}

        {#if next}
          <div style="margin-bottom:20px">
            <NextAction label={next.label} text={next.text} />
          </div>
        {/if}

        {#if task.description}
          <div class="v2-label" style="margin-bottom:10px">Note</div>
          <article
            class="v2-card"
            style="padding:16px 18px;max-width:70ch;font-size:13.5px;line-height:1.65;white-space:pre-wrap"
          >
            {task.description}
          </article>
        {:else}
          <p class="v2-sub" style="font-size:12.5px;max-width:70ch;margin:0">
            No note on this task. The title is all anyone else has to go on.
          </p>
        {/if}

        <div class="act-head">
          <div class="v2-label">Activity</div>
          {#if hasFiles}
            <!-- Only real kinds. There is no status/started/moved split because
                 a Task has no history table to draw one from. -->
            <div class="seg" role="tablist" aria-label="Filter activity">
              <button class:on={filter === 'all'} onclick={() => (filter = 'all')}>All</button>
              <button class:on={filter === 'comments'} onclick={() => (filter = 'comments')}
                >Comments</button
              >
              <button class:on={filter === 'files'} onclick={() => (filter = 'files')}>Files</button
              >
            </div>
          {/if}
        </div>

        <!-- The composer. `reset: false` plus clearing state by hand on success
             keeps the box and the binding in step; a failed post keeps the words
             and the picked file. A task takes a comment, a file, or both. -->
        <form
          method="POST"
          action="?/comment"
          enctype="multipart/form-data"
          class="note-form"
          use:enhance={() => {
            saving = true;
            return async ({ result, update }) => {
              saving = false;
              if (result.type === 'success') {
                comment = '';
                clearFile();
              }
              await update({ reset: false });
            };
          }}
        >
          <label class="v2-sr-only" for="comment">Add a comment</label>
          <textarea
            id="comment"
            name="comment"
            rows="3"
            bind:value={comment}
            class="note-input"
            placeholder="What happened? Anyone on this task will see it."></textarea>
          <div class="note-actions">
            <button class="v2-btn v2-btn-primary" type="submit" disabled={saving || !canSubmit}>
              {saving
                ? 'Saving…'
                : comment.trim()
                  ? 'Comment'
                  : fileName
                    ? 'Attach file'
                    : 'Comment'}
            </button>
            <label class="v2-btn" class:has-file={fileName}>
              <Paperclip size={14} />
              <span class="attach-label">{fileName || 'Attach file'}</span>
              <input
                bind:this={fileInput}
                type="file"
                name="attachment"
                onchange={pickFile}
                hidden
              />
            </label>
            {#if fileName}
              <button
                type="button"
                class="v2-btn-quiet clear-file"
                onclick={clearFile}
                title="Remove file"
              >
                <X size={13} />
              </button>
            {/if}
          </div>
        </form>

        <div class="tl">
          {#each feed as row (row.id)}
            {#if row.kind === 'day'}
              <div class="tl-day">{row.label}</div>
            {:else}
              {@const e = row.event}
              <div class="tl-row" class:latest={e.id === newestId}>
                <span class="tl-ico" data-kind={e.type}>
                  {#if e.type === 'file'}<Paperclip size={13} />
                  {:else if e.type === 'status'}<Sparkles size={13} />
                  {:else}<MessageSquare size={13} />{/if}
                </span>
                <div class="tl-body">
                  {#if e.type === 'file' && e.href}
                    <a
                      class="tl-file"
                      href={resolve(e.href)}
                      target="_blank"
                      rel="noreferrer noopener"
                    >
                      {e.body}
                    </a>
                  {:else}
                    <div class="tl-text" class:comment={e.type === 'comment'}>{e.body}</div>
                  {/if}
                  <div class="tl-meta">{metaFor(e)}</div>
                </div>
              </div>
            {/if}
          {:else}
            <p class="v2-sub" style="font-size:12.5px">
              Nothing logged yet. The first comment you add shows up here.
            </p>
          {/each}
        </div>
      </div>
    </div>
  </div>

  <aside class="v2-rail">
    <div class="v2-label v2-rail-head">Task</div>
    <dl class="v2-kv">
      <dt>Status</dt>
      <dd><Pill tone={TASK_STATUS_TONE[task.status]}>{task.status}</Pill></dd>
      <dt>Priority</dt>
      <dd><Pill tone={TASK_PRIORITY_TONE[task.priority]}>{task.priority}</Pill></dd>
      <dt>Due</dt>
      <dd style={late ? 'color:var(--v2-rust);font-weight:600' : ''}>
        {#if !task.due_date}
          <span class="v2-muted">not set</span>
        {:else if late}
          {longDate(task.due_date)} · {late}d late
        {:else}
          {longDate(task.due_date)}
        {/if}
      </dd>
      <dt>Attached to</dt>
      <dd>
        {#if task.related}
          <a href={resolve(task.related.href)}>{task.related.name}</a>
          <span class="v2-sub" style="display:block;font-size:11.5px">{task.related.kind}</span>
        {:else}
          <span class="v2-muted">nothing</span>
        {/if}
      </dd>
      <dt>Created</dt>
      <dd>{longDate(task.created_at)}</dd>
    </dl>

    <div class="v2-label v2-rail-head">Assigned to</div>
    <!-- A multi-select, not a single one. `assigned_to` is many-to-many and
         the API rewrites the whole list on every save, so a one-owner picker
         would silently drop co-assignees, and the seeded org has tasks with
         two. -->
    <form method="POST" action="?/assign" use:enhance style="padding:0 16px 16px">
      <label class="v2-sr-only" for="assigned_to">Assigned to</label>
      <select
        id="assigned_to"
        name="assigned_to"
        multiple
        size={Math.min(owners.length || 1, 5)}
        class="v2-input"
      >
        {#each owners as person (person.id)}
          <option value={person.id} selected={task.assigned_ids.includes(person.id)}>
            {person.name}
          </option>
        {/each}
      </select>
      <p class="v2-sub" style="font-size:11px;margin:6px 0 8px">
        Hold ⌘ or Ctrl to pick more than one. Clearing the list leaves the task with nobody on it.
      </p>
      <button class="v2-btn" type="submit">Save</button>
    </form>

    {#if contacts.length}
      <div class="v2-label v2-rail-head">People</div>
      <div style="padding:0 16px 16px;display:flex;flex-direction:column;gap:8px">
        {#each contacts as person (person.id)}
          <a
            href={resolve(`/contacts/${person.id}`)}
            style="display:flex;gap:8px;align-items:center;color:inherit;text-decoration:none;font-size:12.5px"
          >
            <Avatar name={person.name} size={20} />
            {person.name}
          </a>
        {/each}
      </div>
    {/if}
  </aside>
</div>

<style>
  /* The completion control. An open task shows an empty ring that fills moss on
     hover (a preview of done); a finished task is a solid moss check that dims
     slightly on hover to read as "click to reopen". */
  .done-toggle {
    display: grid;
    place-items: center;
    width: 40px;
    height: 40px;
    border-radius: 50%;
    border: 1.5px solid var(--v2-line);
    background: var(--v2-card);
    color: var(--v2-slate);
    cursor: pointer;
    padding: 0;
    transition:
      border-color 0.12s,
      color 0.12s,
      background 0.12s;
  }
  .done-toggle:hover {
    border-color: var(--v2-moss);
    color: var(--v2-moss);
  }
  .done-toggle:focus-visible {
    outline: 2px solid var(--v2-ember);
    outline-offset: 2px;
  }
  .done-toggle.done {
    background: var(--v2-moss);
    border-color: var(--v2-moss);
    color: var(--v2-paper);
  }
  .done-toggle.done:hover {
    opacity: 0.85;
  }

  /* ── comment composer ───────────────────────────────────────────────────── */
  .note-form {
    max-width: 70ch;
    margin-bottom: 22px;
  }
  .note-input {
    width: 100%;
    padding: 9px 11px;
    font: inherit;
    font-size: 13px;
    color: var(--v2-ink);
    background: var(--v2-card);
    border: 1px solid var(--v2-line);
    border-radius: 8px;
    resize: vertical;
    line-height: 1.5;
  }
  .note-input:focus {
    outline: 2px solid var(--v2-ember);
    outline-offset: -1px;
  }
  .note-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 8px;
    flex-wrap: wrap;
  }
  /* The attach control is a label wrapping a hidden input, so the whole chip is
     the click target. */
  .note-actions label {
    cursor: pointer;
  }
  .note-actions .attach-label {
    max-width: 190px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .note-actions .has-file {
    border-color: var(--v2-slate);
    color: var(--v2-ink);
  }
  .clear-file {
    padding: 5px 7px;
  }

  /* ── activity ───────────────────────────────────────────────────────────── */
  .act-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    max-width: 70ch;
    margin: 26px 0 12px;
  }
  .seg {
    display: flex;
    border: 1px solid var(--v2-line);
    border-radius: 7px;
    overflow: hidden;
    flex: none;
  }
  .seg button {
    padding: 4px 11px;
    font: inherit;
    font-size: 11.8px;
    color: var(--v2-slate);
    background: var(--v2-card);
    border: 0;
    cursor: pointer;
  }
  .seg button + button {
    border-left: 1px solid var(--v2-line);
  }
  .seg button.on {
    color: var(--v2-ink);
    background: var(--v2-hover);
    font-weight: 600;
  }

  .tl {
    max-width: 70ch;
  }
  .tl-day {
    font-size: 11px;
    font-weight: 650;
    letter-spacing: 0.02em;
    color: var(--v2-slate);
    margin: 14px 0 9px;
  }
  .tl-day:first-child {
    margin-top: 0;
  }
  .tl-row {
    display: flex;
    gap: 11px;
    align-items: flex-start;
    padding-bottom: 15px;
  }
  /* A small icon chip instead of a bare dot: the kind of event is legible at a
     glance, which is the whole point of a mixed feed. */
  .tl-ico {
    flex: none;
    width: 26px;
    height: 26px;
    border-radius: 50%;
    display: grid;
    place-items: center;
    background: var(--v2-line-soft);
    border: 1px solid var(--v2-line);
    color: var(--v2-slate);
    margin-top: 1px;
  }
  .tl-row.latest .tl-ico {
    background: var(--v2-ink);
    border-color: var(--v2-ink);
    color: var(--v2-paper);
  }
  .tl-body {
    min-width: 0;
    padding-top: 3px;
  }
  .tl-text {
    font-size: 13px;
    line-height: 1.55;
    color: var(--v2-ink);
    white-space: pre-wrap;
  }
  .tl-file {
    display: inline-flex;
    font-size: 13px;
    font-weight: 550;
    color: var(--v2-ink);
    text-decoration: none;
    overflow-wrap: anywhere;
  }
  .tl-file:hover {
    text-decoration: underline;
  }
  .tl-meta {
    font-size: 11.5px;
    color: var(--v2-slate);
    margin-top: 2px;
    overflow-wrap: anywhere;
  }
</style>
