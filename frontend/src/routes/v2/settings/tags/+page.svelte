<script>
  /**
   * The labels shared across accounts, leads, deals and tickets.
   *
   * A tag list without usage counts is a list of words. The two questions an
   * admin actually has are "which of these is nobody using" and "have we ended
   * up with two tags for one idea", and both need the counts to answer.
   *
   * `slug` is unique per org and derived from `name`, so two tags can never
   * collide on the slug — but "Renewal" and "Renewals" slug differently while
   * meaning the same thing, and the work splits silently across them.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import StatCard from '$lib/v2/components/StatCard.svelte';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import { count } from '$lib/v2/format.js';
  import { Plus, Merge, Tags as TagsIcon } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let totals = $derived(data.totals);

  const used = (t) => t.usage.accounts + t.usage.leads + t.usage.opportunities + t.usage.cases;

  let tags = $derived(
    [...data.tags].sort((a, b) => used(b) - used(a) || a.name.localeCompare(b.name))
  );

  /**
   * Tags that probably mean the same thing.
   *
   * A suggestion, computed over the complete list — settings lists are not
   * paginated, so this is not an aggregate over rows we cannot see. It is
   * deliberately crude (case, spacing, punctuation and a trailing plural) and
   * it never merges anything: it puts two names next to each other and lets a
   * person decide, because "Invoice" and "Invoices" might genuinely be two
   * ideas in some org.
   */
  const normalise = (name) =>
    name
      .toLowerCase()
      .replace(/[^a-z0-9]/g, '')
      .replace(/s$/, '');

  let duplicateGroups = $derived.by(() => {
    /** @type {Map<string, any[]>} */
    const groups = new Map();
    for (const t of data.tags) {
      const key = normalise(t.name);
      groups.set(key, [...(groups.get(key) ?? []), t]);
    }
    return [...groups.values()].filter((g) => g.length > 1);
  });
</script>

<PageHeader title="Tags">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(totals.active)}</span> in use across accounts, leads, deals and tickets
  {/snippet}
  {#snippet actions()}
    <button class="v2-btn v2-btn-primary"><Plus />New tag</button>
  {/snippet}
</PageHeader>

<div class="v2-pad" style="padding-top:16px;flex:none">
  <div class="v2-stats">
    <StatCard label="Active" value={count(totals.active)} tone="ink" />
    <StatCard
      label="Applied to nothing"
      value={count(totals.unused)}
      tone={totals.unused > 0 ? 'clay' : 'slate'}
      detail="Safe to delete"
    />
    <StatCard label="Turned off" value={count(totals.count - totals.active)} tone="slate" />
  </div>
</div>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-bottom:32px">
    {#each duplicateGroups as group (group[0].id)}
      <div class="v2-tag-banner">
        <Merge size={16} style="color:var(--v2-clay);flex:none;margin-top:1px" />
        <div>
          <div style="font-weight:600;font-size:13px">
            {group.map((t) => t.name).join(' and ')} look like the same tag
          </div>
          <p class="v2-sub" style="font-size:12px;margin:4px 0 0;line-height:1.5">
            {group.map((t) => `${t.name} is on ${used(t)} records`).join('; ')}. Anyone filtering by
            one of them misses the other.
          </p>
        </div>
        <button class="v2-btn v2-btn-sm" style="flex:none;align-self:center">Merge</button>
      </div>
    {/each}

    <div class="v2-label" style="margin-bottom:10px">All tags</div>
    <div class="v2-table-wrap">
      <table class="v2-table">
        <thead>
          <tr>
            <th>Tag</th>
            <th style="text-align:right">Accounts</th>
            <th style="text-align:right">Leads</th>
            <th style="text-align:right">Deals</th>
            <th style="text-align:right">Tickets</th>
            <th style="text-align:right">Total</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each tags as t (t.id)}
            <tr style="opacity:{t.is_active ? 1 : 0.62}">
              <td class="v2-table-primary">
                {t.name}
                <!-- The stored colour, named rather than painted. The model
                     offers eighteen named hues; v2's palette has six tones and
                     renders every tag in them, so a swatch here would be the
                     only place in the product those eighteen exist. -->
                <span class="v2-sub" style="font-size:11px;margin-left:7px">{t.color}</span>
              </td>
              <td class="v2-num" style="text-align:right">{t.usage.accounts || '—'}</td>
              <td class="v2-num" style="text-align:right">{t.usage.leads || '—'}</td>
              <td class="v2-num" style="text-align:right">{t.usage.opportunities || '—'}</td>
              <td class="v2-num" style="text-align:right">{t.usage.cases || '—'}</td>
              <td class="v2-num" style="text-align:right;font-weight:600">{used(t) || '—'}</td>
              <td style="text-align:right">
                {#if !t.is_active}
                  <Pill tone="slate">Off</Pill>
                {:else if used(t) === 0}
                  <Pill tone="clay">Unused</Pill>
                {/if}
              </td>
            </tr>
          {:else}
            <tr>
              <td colspan="7">
                <EmptyState
                  title="No tags yet"
                  body="Tags are shared across every record type, so the first one is worth naming carefully."
                >
                  {#snippet icon()}<TagsIcon size={21} />{/snippet}
                </EmptyState>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>

    <p class="v2-sub" style="font-size:11.5px;margin-top:14px;max-width:64ch">
      Turning a tag off hides it from the pickers and leaves it on the records that already carry
      it. Deleting removes it everywhere, which is why the unused ones are the only safe ones to
      delete.
    </p>
  </div>
</div>

<style>
  .v2-tag-banner {
    display: flex;
    gap: 11px;
    align-items: flex-start;
    padding: 14px 16px;
    margin-bottom: 16px;
    border: 1px solid var(--v2-line);
    border-radius: var(--v2-radius);
    background: var(--v2-card);
  }
</style>
