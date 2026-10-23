<script>
  /**
   * Settings › Modules: switch the parts of BottleCRM an organization does
   * not use off and on, and order them within their group. Switching off
   * deletes nothing. Forms use plain `use:enhance`, so the shell reloads and
   * the menus change at once.
   */
  import { enhance } from '$app/forms';
  import { resolve } from '$app/paths';
  import { ArrowDown, ArrowUp, Boxes } from '@lucide/svelte';
  import ConfirmAction from '#lib/v2/components/ConfirmAction.svelte';
  import EmptyState from '#lib/v2/components/EmptyState.svelte';
  import NextAction from '#lib/v2/components/NextAction.svelte';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import Pill from '#lib/v2/components/Pill.svelte';
  import SettingsCrumb from '#lib/v2/components/SettingsCrumb.svelte';
  import { labelOf } from '#lib/v2/modules.js';
  import { asInternalPath } from '#lib/utils/paths.js';

  /** @type {{ data: any, form?: any }} */
  let { data, form } = $props();

  const GROUPS = [
    { key: 'sell', label: 'Sell' },
    { key: 'serve', label: 'Serve' },
    { key: 'bill', label: 'Bill' }
  ];

  /** @type {import('#lib/v2/modules.js').ModuleRow[]} */
  let rows = $derived(data.modules ?? []);

  let groups = $derived(
    GROUPS.map((g) => ({ ...g, rows: rows.filter((r) => r.group === g.key) })).filter(
      (g) => g.rows.length
    )
  );

  let errors = $derived(Array.isArray(form?.errors) ? form.errors : []);
  let formsLink = $derived(form?.key === 'leads' || form?.key === 'tickets');
  let mailboxLink = $derived(form?.key === 'tickets');
  // Shown under the row it is about, so a phone user sees it where they tapped.
  let refusedKey = $derived(rows.some((r) => r.key === form?.key) ? form.key : null);

  /** @param {import('#lib/v2/modules.js').ModuleRow} row */
  function needOff(row) {
    const need = row.needs ? rows.find((r) => r.key === row.needs) : null;
    return need ? !need.available : false;
  }
</script>

<PageHeader title="Modules">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    Switch off what this organization does not use. Nothing is deleted: switching a module back on
    brings everything back as it was.
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    {#if data.failed}
      <EmptyState title="Modules could not be loaded." body="Reload the page to try again.">
        {#snippet icon()}<Boxes size={21} />{/snippet}
      </EmptyState>
    {:else if data.forbidden}
      <NextAction
        label="Admins only"
        text="Only an organization admin can switch modules on or off."
      />
    {:else}
      {#snippet refusal()}
        <div class="mod-errors" role="alert">
          <ul>
            {#each errors as message, n (n)}
              <li>{message}</li>
            {/each}
          </ul>
          {#if formsLink || mailboxLink}
            <p>
              {#if formsLink}<a href={resolve(asInternalPath('/settings/web-forms'))}
                  >Open web forms</a
                >{/if}
              {#if mailboxLink}<a href={resolve(asInternalPath('/settings/inbound-email'))}
                  >Open inbound email</a
                >{/if}
            </p>
          {/if}
        </div>
      {/snippet}

      {#if errors.length && !refusedKey}
        {@render refusal()}
      {/if}

      {#each groups as g (g.key)}
        <div class="v2-label" style="margin-bottom:10px">{g.label}</div>
        <div class="v2-card" style="overflow:hidden;margin-bottom:22px">
          {#each g.rows as row, i (row.key)}
            {@const blocked = needOff(row)}
            <div class="mod-item">
              <div class="mod-row">
                <div class="mod-body">
                  <div class="mod-title">
                    <b>{row.label}</b>
                    <Pill tone={row.available ? 'moss' : 'slate'}
                      >{row.available ? 'On' : 'Off'}</Pill
                    >
                  </div>
                  <span class="v2-sub" style="font-size:11.5px">{row.covers}</span>
                  {#if blocked && row.needs}
                    <span class="v2-sub" style="font-size:11.5px">
                      Needs {labelOf(data.modules, row.needs)}.{row.enabled
                        ? ` It comes back when ${labelOf(data.modules, row.needs)} is switched on.`
                        : ''}
                    </span>
                  {/if}
                </div>
                <div class="mod-actions">
                  {#if row.available}
                    <ConfirmAction
                      action="?/switch"
                      label="Switch off"
                      confirmLabel="Switch off"
                      explain={row.stops}
                      hidden={{ key: row.key, on: 'false' }}
                    />
                  {:else if !blocked}
                    <form method="POST" action="?/switch" use:enhance>
                      <input type="hidden" name="key" value={row.key} />
                      <input type="hidden" name="on" value="true" />
                      <button class="v2-btn v2-btn-sm" type="submit">Switch on</button>
                    </form>
                  {/if}
                  <div class="mod-order">
                    {#each ['up', 'down'] as direction (direction)}
                      <form method="POST" action="?/move" use:enhance>
                        <input type="hidden" name="key" value={row.key} />
                        <input type="hidden" name="direction" value={direction} />
                        <button
                          class="v2-btn v2-btn-sm mod-icon"
                          type="submit"
                          aria-label="Move {row.label} {direction}"
                          disabled={direction === 'up' ? i === 0 : i === g.rows.length - 1}
                        >
                          {#if direction === 'up'}<ArrowUp size={14} />{:else}<ArrowDown
                              size={14}
                            />{/if}
                        </button>
                      </form>
                    {/each}
                  </div>
                </div>
              </div>
              {#if errors.length && refusedKey === row.key}
                {@render refusal()}
              {/if}
            </div>
          {/each}
        </div>
      {/each}
    {/if}
  </div>
</div>

<style>
  .mod-errors {
    border: 1px solid color-mix(in srgb, var(--v2-rust) 28%, transparent);
    background: color-mix(in srgb, var(--v2-rust) 9%, transparent);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 18px;
    font-size: 13px;
  }
  .mod-errors ul {
    margin: 0;
    padding-left: 18px;
  }
  .mod-errors p {
    margin: 8px 0 0;
    display: flex;
    gap: 14px;
    flex-wrap: wrap;
  }
  /* Inside a row, the refusal sits under the row it is about. */
  .mod-item .mod-errors {
    margin: 0 16px 12px;
  }
  .mod-item {
    border-top: 1px solid var(--v2-line);
  }
  .mod-item:first-child {
    border-top: 0;
  }
  /* Wraps, so an armed Switch off, whose sentence can run longer than the
     card is wide, drops under the name instead of pushing past the edge. */
  .mod-row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 10px 14px;
    padding: 12px 16px;
  }
  .mod-body {
    flex: 1 1 260px;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 3px;
  }
  .mod-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .mod-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 0 1 auto;
    min-width: 0;
    margin-left: auto;
  }
  .mod-order {
    display: flex;
    gap: 6px;
  }
  .mod-icon {
    min-width: 44px;
    min-height: 44px;
    justify-content: center;
  }
  @media (max-width: 768px) {
    .mod-row {
      flex-direction: column;
      align-items: stretch;
    }
    .mod-body {
      flex-basis: auto;
    }
    .mod-actions {
      justify-content: space-between;
      flex-wrap: wrap;
      margin-left: 0;
    }
  }
</style>
