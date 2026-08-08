<script>
  import { resolve } from '$app/paths';
  /**
   * The kanban board.
   *
   * Two things the model already knows that v1 drew over:
   *
   * 1. `BoardColumn.limit` is a WIP limit. It is stored, and v1 rendered a
   *    column at 6/4 exactly like one at 2/5, so the limit was a number
   *    nobody could act on. Here the count is against the limit and a column
   *    over it says so, because that is the entire purpose of setting one.
   * 2. `is_completed` is `completed_at is not None`, not "sits in Done". A
   *    card can be dragged into Done and never marked complete; it stays open
   *    work and stays overdue. Both checks key off the timestamp, so the board
   *    and every count agree with the API.
   *
   * Moving a card is a drag. The lane state is optimistic, the card follows
   * the cursor and the counts update immediately, and the drop is persisted
   * with `PUT /boards/tasks/<id>/`. If the server refuses (it validates the
   * target column and the membership), we reload and the card snaps back, so
   * the board never claims a move the backend didn't make.
   */
  import { dndzone } from 'svelte-dnd-action';
  import { flip } from 'svelte/animate';
  import { invalidateAll } from '$app/navigation';
  import { deserialize, enhance } from '$app/forms';
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SectionTabs from '$lib/v2/components/SectionTabs.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import Avatar from '$lib/v2/components/Avatar.svelte';
  import StatCard from '$lib/v2/components/StatCard.svelte';
  import { count, shortDate, daysSince } from '$lib/v2/format.js';
  import { BOARD_PRIORITY_LABEL, BOARD_PRIORITY_TONE } from '$lib/v2/enums.js';
  import { Plus, ChevronDown, TriangleAlert } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  const FLIP_MS = 160;

  /** Join the flat `columns` + `tasks` into draggable lanes. */
  function buildLanes(/** @type {any} */ d) {
    return d.columns.map((/** @type {any} */ c) => ({
      ...c,
      cards: d.tasks
        .filter((/** @type {any} */ t) => t.column_id === c.id)
        .sort((/** @type {any} */ a, /** @type {any} */ b) => a.order - b.order)
    }));
  }

  // Lanes are optimistic local state: dnd mutates them on drag, and we resync
  // from the server only when `load` actually re-runs (a genuine reload), an
  // optimistic move touches `lanes`, not `data`, so it is never clobbered.
  // svelte-ignore state_referenced_locally
  let lanes = $state(buildLanes(data));
  /** @type {any} */
  let lastData;
  $effect(() => {
    if (lastData !== undefined && data !== lastData) lanes = buildLanes(data);
    lastData = data;
  });

  let moveError = $state('');

  // Adding cards and columns. A card form opens under one lane at a time; the
  // column form opens once at the end. Both post to the page's actions and
  // reload on success, so the new record arrives from the API rather than being
  // guessed at. The same rule the drag follows.
  let addingCardTo = $state(/** @type {string | null} */ (null));
  let addCardBusy = $state(false);
  let addCardError = $state('');
  let showAddColumn = $state(false);
  let addColumnBusy = $state(false);
  let addColumnError = $state('');

  // Only ever seen on the empty state, where there is no board to add to yet.
  let createBoardBusy = $state(false);
  let createBoardError = $state('');

  function openCardForm(/** @type {string} */ columnId) {
    addingCardTo = columnId;
    addCardError = '';
  }
  function closeCardForm() {
    addingCardTo = null;
    addCardError = '';
  }

  const isDone = (/** @type {any} */ t) => t.completed_at !== null;
  const isOverdue = (/** @type {any} */ t) =>
    !isDone(t) && t.due_date !== null && new Date(t.due_date) < new Date();
  const overCount = (/** @type {any} */ lane) =>
    lane.limit !== null && lane.cards.length > lane.limit;

  // Counts follow the live lanes, so a drag updates them with no round-trip and
  // they still match the API on the next load.
  let totals = $derived.by(() => {
    const cards = lanes.flatMap((l) => l.cards);
    const now = new Date();
    return {
      open: cards.filter((c) => c.completed_at === null).length,
      overdue: cards.filter(
        (c) => c.completed_at === null && c.due_date !== null && new Date(c.due_date) < now
      ).length,
      unassigned: cards.filter((c) => c.assigned_to.length === 0).length,
      over_limit: lanes.filter((l) => l.limit !== null && l.cards.length > l.limit).length
    };
  });

  function onConsider(/** @type {any} */ lane, /** @type {any} */ e) {
    lane.cards = e.detail.items;
  }

  async function onFinalize(/** @type {any} */ lane, /** @type {any} */ e) {
    lane.cards = e.detail.items;
    const movedId = e.detail.info?.id;
    const index = e.detail.items.findIndex((/** @type {any} */ c) => c.id === movedId);
    // Finalize fires on both lanes of a cross-column move; only the lane that
    // now holds the card (the destination) persists it.
    if (index === -1) return;
    await persistMove(movedId, lane.id, index);
  }

  async function persistMove(
    /** @type {string} */ id,
    /** @type {string} */ column,
    /** @type {number} */ order
  ) {
    const body = new FormData();
    body.set('id', id);
    body.set('column', column);
    body.set('order', String(order));
    try {
      const res = await fetch('?/move', { method: 'POST', body });
      const result = deserialize(await res.text());
      if (result.type === 'success') {
        moveError = '';
      } else {
        moveError =
          (result.type === 'failure' && /** @type {any} */ (result.data)?.error) ||
          'Could not move the card; reverted.';
        await invalidateAll();
      }
    } catch {
      moveError = 'Could not move the card, reverted.';
      await invalidateAll();
    }
  }
</script>

<PageHeader title="Tasks">
  {#snippet sub()}
    {#if data.board}
      {data.board.name}{data.board.description ? ` · ${data.board.description}` : ''}
    {:else}
      Boards
    {/if}
  {/snippet}
  {#snippet actions()}
    <!-- The board picker is a control, not navigation, so it stays out of the
         sidebar. Boards come and go, and a sidebar that grows a row per board
         stops being a map. A single board needs no picker. -->
    {#if data.boards.length > 1}
      <!-- A GET form: picking a board navigates to `?board=<id>` and re-runs
           load, which SvelteKit routes client-side, no goto() needed. -->
      <form method="GET" class="v2-board-form">
        <select
          name="board"
          class="v2-btn v2-board-select"
          value={data.board?.id}
          onchange={(e) => e.currentTarget.form?.requestSubmit()}
        >
          {#each data.boards as b (b.id)}
            <option value={b.id}>{b.name}</option>
          {/each}
        </select>
      </form>
    {:else if data.board}
      <button class="v2-btn" disabled>
        {data.board.name}<ChevronDown size={13} />
      </button>
    {/if}
  {/snippet}
</PageHeader>

<SectionTabs set="tasks" />

{#if !data.board}
  <!-- This used to say "Create one from the mobile app to see it here." The
       mobile app has no boards, and no client called POST /boards/, so an org
       that had never been given one through the API was stuck here. -->
  <div class="v2-pad" style="padding-top:32px">
    <div class="v2-empty">
      <Plus size={22} style="opacity:0.4" />
      <p class="v2-empty-title">No boards yet</p>
      <p class="v2-sub" style="max-width:34ch;text-align:center">
        A board organises work into columns you drag cards between. It starts with To Do, In
        Progress and Done, and you can rename them later.
      </p>
      <form
        class="v2-lane-add-form"
        style="max-width:20rem;margin-top:14px"
        method="POST"
        action="?/create"
        use:enhance={() => {
          createBoardBusy = true;
          return async ({ result }) => {
            createBoardBusy = false;
            if (result.type === 'success') {
              createBoardError = '';
              await invalidateAll();
            } else if (result.type === 'failure') {
              createBoardError =
                /** @type {any} */ (result.data)?.error || 'Could not create the board.';
            } else if (result.type === 'error') {
              createBoardError = 'Could not create the board.';
            }
          };
        }}
      >
        <!-- svelte-ignore a11y_autofocus -->
        <input
          class="v2-input"
          name="name"
          placeholder="Board name"
          maxlength="255"
          required
          autofocus
        />
        <button class="v2-btn v2-btn-primary" type="submit" disabled={createBoardBusy}>
          {createBoardBusy ? 'Creating…' : 'Create board'}
        </button>
      </form>
      {#if createBoardError}
        <p class="v2-error" role="status">{createBoardError}</p>
      {/if}
    </div>
  </div>
{:else}
  {#if moveError}
    <div class="v2-pad" style="padding-top:12px;flex:none">
      <div class="v2-move-error" role="status">
        <TriangleAlert size={13} style="flex:none" />
        <span>{moveError}</span>
      </div>
    </div>
  {/if}

  <div class="v2-pad" style="padding-top:16px;flex:none">
    <div class="v2-stats">
      <StatCard label="Open cards" value={count(totals.open)} tone="ink" />
      <StatCard
        label="Overdue"
        value={count(totals.overdue)}
        tone={totals.overdue > 0 ? 'rust' : 'slate'}
        detail="Past due and not marked done"
      />
      <StatCard
        label="Unassigned"
        value={count(totals.unassigned)}
        tone={totals.unassigned > 0 ? 'clay' : 'slate'}
      />
      <StatCard
        label="Columns over limit"
        value={count(totals.over_limit)}
        tone={totals.over_limit > 0 ? 'clay' : 'slate'}
        detail="More cards than the column allows"
      />
    </div>
  </div>

  <div class="v2-board" style="padding-top:16px">
    {#each lanes as lane (lane.id)}
      {@const over = overCount(lane)}
      <section class="v2-lane">
        <div class="v2-lane-head">
          <span class="v2-label">{lane.name}</span>
          <!-- Count against limit, in one figure. A bare "6" cannot be wrong;
               "6 / 4" can, which is the point of writing it down. -->
          <span class="v2-num" style={over ? 'color:var(--v2-clay);font-weight:650' : ''}>
            {lane.cards.length}{#if lane.limit !== null}&thinsp;/&thinsp;{lane.limit}{/if}
          </span>
        </div>

        {#if over}
          <div class="v2-lane-over">
            <TriangleAlert size={12} style="flex:none" />
            <span>{lane.cards.length - lane.limit} over the limit of {lane.limit}</span>
          </div>
        {/if}

        <div
          class="v2-lane-body"
          use:dndzone={{ items: lane.cards, flipDurationMs: FLIP_MS }}
          onconsider={(e) => onConsider(lane, e)}
          onfinalize={(e) => onFinalize(lane, e)}
        >
          {#each lane.cards as t (t.id)}
            {@const overdue = isOverdue(t)}
            {@const done = isDone(t)}
            <div
              class="v2-deal-card v2-card-drag"
              animate:flip={{ duration: FLIP_MS }}
              style="opacity:{done ? 0.65 : 1}"
            >
              <div style="font-weight:600;letter-spacing:-0.012em;line-height:1.3;font-size:13px">
                {t.title}
              </div>
              {#if t.account}
                <div class="v2-sub" style="margin-top:2px">{t.account.name}</div>
              {/if}

              <div style="margin-top:9px;display:flex;gap:5px;flex-wrap:wrap">
                <Pill tone={BOARD_PRIORITY_TONE[t.priority]}
                  >{BOARD_PRIORITY_LABEL[t.priority]}</Pill
                >
                {#if overdue}
                  <Pill tone="rust">{daysSince(t.due_date)}d late</Pill>
                {/if}
              </div>

              <div class="v2-deal-card-foot">
                {#if t.assigned_to.length}
                  {#each t.assigned_to as p (p.id)}
                    <Avatar name={p.name} size={21} />
                  {/each}
                {:else}
                  <!-- Named, not an empty slot. A blank reads as a rendering gap. -->
                  <span class="v2-sub" style="font-size:11.5px">Unassigned</span>
                {/if}
                {#if t.due_date}
                  <span class="v2-sub" style="margin-left:auto;font-size:11.5px">
                    {done ? 'done ' : ''}{shortDate(done ? t.completed_at : t.due_date)}
                  </span>
                {/if}
              </div>

              {#if lane.name === 'Done' && !done}
                <!-- In the Done column with completed_at still null. It is open
                     work by every count on this page, and by the API's. -->
                <div class="v2-card-flag">
                  <TriangleAlert size={12} style="flex:none" />
                  <span>In Done, never marked complete, still counted as open</span>
                </div>
              {/if}
            </div>
          {/each}
        </div>
        {#if lane.cards.length === 0}
          <p class="v2-sub v2-lane-empty">Drop a card here</p>
        {/if}

        <!-- Add a card. Any board member can, so it sits on every lane. Kept
             outside the dndzone above so it never becomes a drop target. -->
        {#if addingCardTo === lane.id}
          <form
            class="v2-lane-add-form"
            method="POST"
            action="?/addCard"
            use:enhance={() => {
              addCardBusy = true;
              return async ({ result }) => {
                addCardBusy = false;
                if (result.type === 'success') {
                  closeCardForm();
                  await invalidateAll();
                } else if (result.type === 'failure') {
                  addCardError =
                    /** @type {any} */ (result.data)?.error || 'Could not add the card.';
                } else if (result.type === 'error') {
                  addCardError = 'Could not add the card.';
                }
              };
            }}
          >
            <input type="hidden" name="column" value={lane.id} />
            <!-- svelte-ignore a11y_autofocus -->
            <input
              class="v2-input v2-lane-add-input"
              name="title"
              placeholder="Card title"
              required
              autofocus
              disabled={addCardBusy}
            />
            <textarea
              class="v2-input v2-lane-add-input"
              name="description"
              placeholder="Description (optional)"
              rows="2"
              disabled={addCardBusy}></textarea>
            <select class="v2-input v2-lane-add-input" name="priority" disabled={addCardBusy}>
              {#each Object.entries(BOARD_PRIORITY_LABEL) as [value, label] (value)}
                <option {value} selected={value === 'medium'}>{label}</option>
              {/each}
            </select>
            {#if addCardError}
              <p class="v2-lane-add-error" role="alert">{addCardError}</p>
            {/if}
            <div class="v2-lane-add-actions">
              <button type="submit" class="v2-btn v2-btn-primary v2-btn-sm" disabled={addCardBusy}>
                {addCardBusy ? 'Adding…' : 'Add card'}
              </button>
              <button
                type="button"
                class="v2-btn v2-btn-sm"
                onclick={closeCardForm}
                disabled={addCardBusy}
              >
                Cancel
              </button>
            </div>
          </form>
        {:else}
          <button class="v2-lane-add" onclick={() => openCardForm(lane.id)}>
            <Plus size={13} /> Add card
          </button>
        {/if}
      </section>
    {/each}

    <!-- Add a column. Owner/admin only: the control is hidden for a member
         because the backend would 403, and a button that only ever fails is
         worse than no button. The server still enforces it regardless. -->
    {#if data.canManageColumns}
      <section class="v2-lane v2-lane-add-column">
        {#if showAddColumn}
          <form
            class="v2-lane-add-form"
            method="POST"
            action="?/addColumn"
            use:enhance={() => {
              addColumnBusy = true;
              return async ({ result }) => {
                addColumnBusy = false;
                if (result.type === 'success') {
                  showAddColumn = false;
                  addColumnError = '';
                  await invalidateAll();
                } else if (result.type === 'failure') {
                  addColumnError =
                    /** @type {any} */ (result.data)?.error || 'Could not add the column.';
                } else if (result.type === 'error') {
                  addColumnError = 'Could not add the column.';
                }
              };
            }}
          >
            <input type="hidden" name="board" value={data.board.id} />
            <!-- Append, don't prepend: a column defaulting to order 0 would land
                 in front of "To Do". Send one past the current highest. -->
            <input
              type="hidden"
              name="order"
              value={lanes.length ? Math.max(...lanes.map((l) => l.order ?? 0)) + 1 : 0}
            />
            <div class="v2-lane-add-row">
              <!-- svelte-ignore a11y_autofocus -->
              <input
                class="v2-input v2-lane-add-input"
                name="name"
                placeholder="Column name"
                required
                autofocus
                disabled={addColumnBusy}
              />
              <input
                class="v2-lane-add-color"
                type="color"
                name="color"
                value="#6b7280"
                aria-label="Column colour"
                disabled={addColumnBusy}
              />
            </div>
            {#if addColumnError}
              <p class="v2-lane-add-error" role="alert">{addColumnError}</p>
            {/if}
            <div class="v2-lane-add-actions">
              <button
                type="submit"
                class="v2-btn v2-btn-primary v2-btn-sm"
                disabled={addColumnBusy}
              >
                {addColumnBusy ? 'Adding…' : 'Add column'}
              </button>
              <button
                type="button"
                class="v2-btn v2-btn-sm"
                onclick={() => {
                  showAddColumn = false;
                  addColumnError = '';
                }}
                disabled={addColumnBusy}
              >
                Cancel
              </button>
            </div>
          </form>
        {:else}
          <button class="v2-lane-add v2-lane-add-lane" onclick={() => (showAddColumn = true)}>
            <Plus size={14} /> Add column
          </button>
        {/if}
      </section>
    {/if}
  </div>
{/if}

<!-- `tasks.Task` and `tasks.BoardTask` are separate tables. Nothing about the
     word "task" suggests that, and everyone assumes a card here is also a task
     there, so it is said once, in the open. -->
<p class="v2-sub v2-pad" style="font-size:11.5px;padding-bottom:14px;flex:none;margin:0">
  Cards on a board are separate records from the
  <a href={resolve('/tasks')} style="color:inherit">task list</a>. A card here does not appear
  there, and completing one does not complete the other.
</p>

<style>
  .v2-board-form {
    display: contents;
  }
  .v2-board-select {
    padding-right: 8px;
    cursor: pointer;
  }
  .v2-lane-over {
    display: flex;
    align-items: center;
    gap: 5px;
    font-size: 11px;
    color: var(--v2-clay);
    padding: 0 3px 8px;
    flex: none;
  }
  /* An empty lane still has to be a drop target, so give the body room even
     with no cards in it. */
  .v2-lane-body {
    min-height: 44px;
  }
  .v2-card-drag {
    cursor: grab;
  }
  .v2-card-drag:active {
    cursor: grabbing;
  }
  .v2-lane-empty {
    font-size: 12px;
    padding: 2px 3px 0;
    color: var(--v2-slate);
    flex: none;
  }
  .v2-move-error {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--v2-rust);
    background: color-mix(in srgb, var(--v2-rust) 8%, transparent);
    border: 1px solid color-mix(in srgb, var(--v2-rust) 24%, transparent);
    border-radius: 7px;
    padding: 7px 10px;
  }
  .v2-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 40px 0;
  }
  .v2-empty-title {
    font-weight: 600;
    letter-spacing: -0.01em;
    margin: 0;
  }
  .v2-card-flag {
    display: flex;
    align-items: flex-start;
    gap: 5px;
    margin-top: 8px;
    padding-top: 8px;
    border-top: 1px solid var(--v2-line-soft);
    font-size: 11px;
    color: var(--v2-clay);
    line-height: 1.4;
  }
  /* The quiet "Add card" affordance under each lane. Slate until hovered, so it
     reads as a place to add rather than a card in its own right. */
  .v2-lane-add {
    display: flex;
    align-items: center;
    gap: 5px;
    width: 100%;
    margin-top: 6px;
    padding: 7px 8px;
    border: 0;
    border-radius: 7px;
    background: none;
    color: var(--v2-slate);
    font: inherit;
    font-size: 12.5px;
    text-align: left;
    cursor: pointer;
    flex: none;
  }
  .v2-lane-add:hover {
    background: var(--v2-card);
    color: var(--v2-ink);
  }
  /* The whole "Add column" lane is the target, so it gets a dashed frame and
     centres its label. An empty column waiting to exist. */
  .v2-lane-add-column {
    background: none;
  }
  .v2-lane-add-lane {
    justify-content: center;
    min-height: 44px;
    border: 1px dashed var(--v2-line);
    color: var(--v2-slate);
  }
  .v2-lane-add-lane:hover {
    border-color: var(--v2-slate);
    background: var(--v2-card);
  }
  .v2-lane-add-form {
    display: flex;
    flex-direction: column;
    gap: 7px;
    margin-top: 6px;
    padding: 9px;
    background: var(--v2-card);
    border: 1px solid var(--v2-line);
    border-radius: 8px;
    flex: none;
  }
  .v2-lane-add-input {
    width: 100%;
    font-size: 13px;
  }
  textarea.v2-lane-add-input {
    resize: vertical;
    min-height: 40px;
  }
  .v2-lane-add-row {
    display: flex;
    gap: 7px;
    align-items: center;
  }
  .v2-lane-add-color {
    width: 34px;
    height: 34px;
    padding: 2px;
    border: 1px solid var(--v2-line);
    border-radius: 7px;
    background: var(--v2-card);
    cursor: pointer;
    flex: none;
  }
  .v2-lane-add-actions {
    display: flex;
    gap: 6px;
  }
  .v2-lane-add-error {
    margin: 0;
    font-size: 11.5px;
    color: var(--v2-rust);
  }
</style>
