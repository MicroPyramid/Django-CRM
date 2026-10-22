<script>
  import { resolve } from '$app/paths';
  import { asInternalPath } from '#lib/utils/paths.js';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import EmptyState from '#lib/v2/components/EmptyState.svelte';
  import { count } from '#lib/v2/format.js';
  import { Boxes, Plus } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let def = $derived(data.definition);
  let rows = $derived(data.page.results);
  let canCreate = $derived(data.customObjects?.has_custom_objects === true);
  let hasNext = $derived(data.pageNumber * 20 < data.page.count);

  /** @param {number} n */
  function pageQuery(n) {
    const parts = [];
    if (data.q) parts.push(`q=${encodeURIComponent(data.q)}`);
    if (n > 1) parts.push(`page=${n}`);
    return `/objects/${def.key}${parts.length ? `?${parts.join('&')}` : ''}`;
  }
</script>

<PageHeader title={def.label_plural}>
  {#snippet sub()}
    {#if def.description}{def.description}{:else}<span class="v2-num">{count(data.page.count)}</span
      >
      {data.page.count === 1 ? def.label.toLowerCase() : def.label_plural.toLowerCase()}{/if}
  {/snippet}
  {#snippet actions()}
    {#if canCreate}
      <a class="v2-btn v2-btn-primary" href={resolve(asInternalPath(`/objects/${def.key}/new`))}
        ><Plus />New {def.label}</a
      >
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <form class="ol-search" method="GET" role="search">
    <input
      class="v2-input"
      type="search"
      name="q"
      value={data.q}
      maxlength="100"
      placeholder="Search by {def.name_label.toLowerCase()}"
      aria-label="Search {def.label_plural}"
    />
    <button class="v2-btn" type="submit">Search</button>
  </form>

  {#if rows.length === 0}
    <EmptyState
      title={data.q ? 'No matches' : `No ${def.label_plural.toLowerCase()} yet`}
      body={data.q
        ? `Nothing matches "${data.q}". Try a shorter search.`
        : `Records of this kind will be listed here.`}
    >
      {#snippet icon()}<Boxes size={21} />{/snippet}
      {#snippet actions()}
        {#if canCreate && !data.q}
          <a class="v2-btn v2-btn-primary" href={resolve(asInternalPath(`/objects/${def.key}/new`))}
            >New {def.label}</a
          >
        {/if}
      {/snippet}
    </EmptyState>
  {:else}
    <div class="v2-table-wrap">
      <table class="v2-table">
        <thead>
          <tr>
            <th>{def.name_label}</th>
            {#each data.columns as c (c.key)}<th>{c.label}</th>{/each}
            <th>Assigned to</th>
          </tr>
        </thead>
        <tbody>
          {#each rows as r (r.id)}
            <tr>
              <td data-m="title">
                <a
                  class="v2-row-link"
                  href={resolve(asInternalPath(`/objects/${def.key}/${r.id}`))}
                >
                  <div class="v2-table-primary">{r.name}</div>
                </a>
              </td>
              {#each r.cells as cell, i (data.columns[i].key)}
                <td data-m="meta" data-l={data.columns[i].label}>{cell}</td>
              {/each}
              <td class="v2-muted" data-m="hide">{r.assignees.join(', ')}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="v2-sub v2-pad ol-foot">
      Showing <span class="v2-num">{rows.length}</span> of
      <span class="v2-num">{count(data.page.count)}</span>
    </p>
    {#if data.pageNumber > 1 || hasNext}
      <nav class="v2-pad ol-pager" aria-label="Pages">
        {#if data.pageNumber > 1}
          <a class="v2-btn" href={resolve(asInternalPath(pageQuery(data.pageNumber - 1)))}
            >Previous</a
          >
        {/if}
        {#if hasNext}
          <a class="v2-btn" href={resolve(asInternalPath(pageQuery(data.pageNumber + 1)))}>Next</a>
        {/if}
      </nav>
    {/if}
  {/if}
</div>

<style>
  .ol-search {
    display: flex;
    gap: 8px;
    padding: 12px var(--v2-pad, 24px) 4px;
  }
  .ol-search .v2-input {
    flex: 1;
    min-width: 0;
    min-height: 44px;
  }
  .ol-search .v2-btn {
    min-height: 44px;
  }
  .ol-foot {
    font-size: 12px;
    padding-bottom: 12px;
  }
  .ol-pager {
    display: flex;
    gap: 9px;
    padding-bottom: 24px;
  }
</style>
