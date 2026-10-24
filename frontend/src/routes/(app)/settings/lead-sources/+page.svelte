<script>
  /**
   * Settings › Lead sources: the list every source picker, filter, import and
   * webhook reads. Any member sees it; admins add, rename, retire and order.
   * There is no delete, so an old record always says where it came from.
   */
  import { enhance } from '$app/forms';
  import { ArrowDown, ArrowUp, Plus } from '@lucide/svelte';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '#lib/v2/components/SettingsCrumb.svelte';
  import Pill from '#lib/v2/components/Pill.svelte';
  import NextAction from '#lib/v2/components/NextAction.svelte';
  import { count } from '#lib/v2/format.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let sources = $derived(/** @type {any[]} */ (data.sources));
  let active = $derived(sources.filter((s) => s.is_active).length);
  let renaming = $state(/** @type {string | null} */ (null));
  let busy = $state(false);

  /** The refusal for a row, whichever action it came from. */
  let rowError = $derived(form?.rename ?? form?.retire ?? form?.move ?? /** @type {any} */ (null));

  /** @param {{ reset?: boolean }} [opts] */
  const working = (opts = {}) => {
    busy = true;
    return async (/** @type {any} */ { update, result }) => {
      await update({ reset: opts.reset ?? false });
      busy = false;
      if (result?.type === 'success') renaming = null;
    };
  };
</script>

<PageHeader title="Lead sources">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(active)}</span> in use of
    <span class="v2-num">{count(sources.length)}</span>
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    {#if data.canEdit}
      <form
        method="POST"
        action="?/add"
        use:enhance={() => working({ reset: true })}
        class="v2-card ls-add"
      >
        <div class="ls-add-field">
          <label class="v2-label" for="ls-label">New source</label>
          <input
            id="ls-label"
            name="label"
            class="v2-input"
            maxlength="64"
            required
            placeholder="e.g. Spring fair"
            value={form?.add?.label ?? ''}
          />
        </div>
        <button class="v2-btn v2-btn-primary ls-tap" disabled={busy}><Plus />Add</button>
      </form>
      {#if form?.add?.error}
        <p class="v2-error" style="margin:-8px 0 14px">{form.add.error}</p>
      {/if}
    {:else}
      <div style="margin-bottom:16px">
        <NextAction
          label="Admins change this list"
          text="Every member picks from these sources. Ask an admin to add one, rename one or retire one."
        />
      </div>
    {/if}

    {#if rowError?.error && !sources.some((s) => s.id === rowError.id || s.key === rowError.id)}
      <p class="v2-error" style="margin-bottom:12px">{rowError.error}</p>
    {/if}

    <div class="v2-card" style="overflow:hidden">
      {#each sources as s, i (s.key)}
        <div class="ls-row" class:ls-retired={!s.is_active}>
          {#if renaming === s.id}
            <form method="POST" action="?/rename" use:enhance={() => working()} class="ls-rename">
              <input type="hidden" name="id" value={s.id} />
              <label class="v2-label" for="ls-rename-{s.id}">Name</label>
              <input
                id="ls-rename-{s.id}"
                name="label"
                class="v2-input"
                maxlength="64"
                required
                value={s.label}
              />
              <div class="ls-actions">
                <button class="v2-btn v2-btn-primary v2-btn-sm ls-tap" disabled={busy}>Save</button>
                <button
                  type="button"
                  class="v2-btn v2-btn-sm ls-tap"
                  disabled={busy}
                  onclick={() => (renaming = null)}
                >
                  Cancel
                </button>
              </div>
            </form>
          {:else}
            <div class="ls-body">
              <div class="ls-title">
                <b>{s.label}</b>
                {#if !s.is_active}<Pill tone="slate">Retired</Pill>{/if}
              </div>
              <span class="v2-sub ls-key">{s.key}</span>
            </div>
            {#if data.canEdit}
              <div class="ls-actions">
                <button
                  type="button"
                  class="v2-btn v2-btn-sm ls-tap"
                  disabled={busy}
                  onclick={() => (renaming = s.id)}
                >
                  Rename
                </button>
                <form method="POST" action="?/retire" use:enhance={() => working()}>
                  <input type="hidden" name="id" value={s.id} />
                  <input type="hidden" name="is_active" value={s.is_active ? 'false' : 'true'} />
                  <button class="v2-btn v2-btn-sm ls-tap" disabled={busy}>
                    {s.is_active ? 'Retire' : 'Bring back'}
                  </button>
                </form>
                <div class="ls-order">
                  {#each ['up', 'down'] as direction (direction)}
                    <form method="POST" action="?/move" use:enhance={() => working()}>
                      <input type="hidden" name="key" value={s.key} />
                      <input type="hidden" name="direction" value={direction} />
                      <button
                        class="v2-btn v2-btn-sm ls-icon"
                        aria-label="Move {s.label} {direction}"
                        disabled={busy || (direction === 'up' ? i === 0 : i === sources.length - 1)}
                      >
                        {#if direction === 'up'}<ArrowUp size={14} />{:else}<ArrowDown
                            size={14}
                          />{/if}
                      </button>
                    </form>
                  {/each}
                </div>
              </div>
            {/if}
          {/if}
          {#if rowError?.error && (rowError.id === s.id || rowError.id === s.key)}
            <p class="v2-error ls-row-error">{rowError.error}</p>
          {/if}
        </div>
      {:else}
        <p class="v2-sub" style="padding:14px 16px;margin:0">No sources yet.</p>
      {/each}
    </div>

    <p class="v2-sub" style="font-size:12px;margin:16px 0 0;max-width:68ch;line-height:1.5">
      A retired source stays on every lead, contact and deal that has it, and can no longer be
      picked for new ones. Spreadsheet imports match a source by its name or by the key under it,
      and lead webhooks and lead addresses record one of these.
    </p>
  </div>
</div>

<style>
  .ls-add {
    display: flex;
    gap: 10px;
    align-items: flex-end;
    flex-wrap: wrap;
    padding: 14px 15px;
    margin-bottom: 18px;
  }
  .ls-add-field {
    flex: 1 1 220px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .ls-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 14px;
    padding: 12px 16px;
    border-top: 1px solid var(--v2-line);
  }
  .ls-row:first-child {
    border-top: 0;
  }
  .ls-retired .ls-body {
    opacity: 0.68;
  }
  .ls-body {
    flex: 1 1 220px;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .ls-title {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }
  .ls-key {
    font-size: 11.5px;
    overflow-wrap: anywhere;
  }
  .ls-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-left: auto;
  }
  .ls-order {
    display: flex;
    gap: 6px;
  }
  .ls-rename {
    flex: 1 1 100%;
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 8px;
  }
  .ls-rename .v2-input {
    flex: 1 1 200px;
  }
  .ls-row-error {
    flex: 1 1 100%;
    margin: 0;
  }
  .ls-tap {
    min-height: 44px;
  }
  .ls-icon {
    min-width: 44px;
    min-height: 44px;
    justify-content: center;
  }
  @media (max-width: 768px) {
    .ls-actions {
      margin-left: 0;
      width: 100%;
    }
    .ls-order {
      margin-left: auto;
    }
  }
</style>
