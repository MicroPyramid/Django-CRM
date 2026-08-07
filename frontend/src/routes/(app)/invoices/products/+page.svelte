<script>
  import { resolve } from '$app/paths';
  /**
   * The catalogue line items are picked from. Short, boring, and the only page
   * in Bill that is a settings screen wearing a list's clothes, so it is
   * grouped by category rather than paginated, because you come here to find
   * one thing and change its price.
   *
   * Retired products stay. A product that appears on eighteen historic
   * invoices cannot be deleted without rewriting what those invoices say was
   * sold, so `is_active=false` takes it out of the picker and leaves the
   * record intact. The row says which, and how many invoices it is on.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SectionTabs from '$lib/v2/components/SectionTabs.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import { money, count } from '$lib/v2/format.js';
  import { Plus, Package, Pencil } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let totals = $derived(data.totals);
  // The catalogue is org config: only an admin may add or change it. The API
  // enforces this. These gates just keep the page from offering a write it
  // would refuse. Reps still see every price, because they build line items.
  let canManage = $derived(data.can_manage);

  /**
   * Grouped for reading, not for counting. The totals still come from the API.
   * A plain object (not a Map) because this is a throwaway computation rebuilt
   * each render, never reactive state; string category keys keep first-seen
   * order, which is the order the list already arrives in.
   */
  let groups = $derived.by(() => {
    /** @type {Record<string, any[]>} */
    const byCategory = {};
    for (const p of data.products) {
      (byCategory[p.category] ??= []).push(p);
    }
    return Object.entries(byCategory).map(([category, items]) => ({ category, items }));
  });
</script>

<PageHeader title="Products">
  {#snippet sub()}
    <span class="v2-num">{count(totals.active)}</span> sellable ·
    <span class="v2-num">{count(totals.count - totals.active)}</span> retired
  {/snippet}
  {#snippet actions()}
    {#if canManage}
      <a class="v2-btn v2-btn-primary" href={resolve('/invoices/products/new')}
        ><Plus />New product</a
      >
    {/if}
  {/snippet}
</PageHeader>

<SectionTabs set="invoices" />

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    {#if data.products.length === 0}
      <EmptyState
        title="Nothing in the catalogue"
        body="Add the things you sell and their list prices. Line items on invoices and estimates pick from here, so the price is right without anyone remembering it."
      >
        {#snippet icon()}<Package size={21} />{/snippet}
        {#snippet actions()}
          {#if canManage}
            <a class="v2-btn v2-btn-primary" href={resolve('/invoices/products/new')}>New product</a
            >
          {:else}
            <span class="v2-sub" style="font-size:12px">Ask an admin to add products.</span>
          {/if}
        {/snippet}
      </EmptyState>
    {:else}
      {#each groups as group (group.category)}
        <div class="v2-label" style="margin-bottom:9px">{group.category}</div>
        <div class="v2-card" style="overflow:hidden;margin-bottom:20px">
          {#each group.items as p (p.id)}
            <div class="v2-setting" style={p.is_active ? '' : 'opacity:.62'}>
              <div class="v2-setting-body">
                <b>{p.name}</b>
                <span class="v2-sub" style="font-size:11.5px">
                  <span class="v2-num">{p.sku}</span>
                  · on <span class="v2-num">{p.used_on}</span>
                  {p.used_on === 1 ? 'invoice' : 'invoices'}
                </span>
              </div>
              {#if !p.is_active}
                <!-- Retired, not gone. Says why it is still listed. -->
                <Pill tone="slate">Retired</Pill>
              {/if}
              <span class="v2-num" style="font-weight:600;font-size:13px">
                {money(p.price, p.currency)}
              </span>
              {#if canManage}
                <a
                  class="prod-edit"
                  href={resolve(`/invoices/products/${p.id}/edit`)}
                  title="Edit {p.name}"
                >
                  <Pencil size={14} />
                </a>
              {/if}
            </div>
          {/each}
        </div>
      {/each}

      <p class="v2-sub" style="font-size:11.5px">
        Retired products stay listed because they appear on invoices already issued. Removing one
        would change what those invoices say was sold.
      </p>
    {/if}
  </div>
</div>

<style>
  /* Sits after the price on each catalogue row; only drawn for an admin. */
  .prod-edit {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px;
    height: 26px;
    margin-left: 2px;
    border-radius: 6px;
    color: var(--v2-slate);
    flex: none;
  }
  .prod-edit:hover {
    background: var(--v2-line-soft);
    color: var(--v2-ink);
  }
</style>
