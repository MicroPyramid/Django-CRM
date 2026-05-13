<script>
  import { goto, invalidateAll } from '$app/navigation';
  import { page } from '$app/state';
  import { enhance } from '$app/forms';
  import { untrack } from 'svelte';
  import { toast } from 'svelte-sonner';
  import {
    BookOpen,
    Plus,
    Search,
    Eye,
    EyeOff,
    Trash2,
    Pencil,
    CheckCircle2
  } from '@lucide/svelte';
  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import { Button } from '$lib/components/ui/button/index.js';

  /** @type {{ data: any }} */
  let { data } = $props();

  const solutions = $derived(data.solutions || []);
  const total = $derived(data.total || 0);
  const pageNum = $derived(data.pageNum || 1);
  const pageSize = $derived(data.pageSize || 20);
  const totalPages = $derived(Math.max(1, Math.ceil(total / pageSize)));

  let search = $state(untrack(() => data.filters?.search || ''));
  let statusFilter = $state(untrack(() => data.filters?.status || ''));
  let publishedFilter = $state(untrack(() => data.filters?.published || ''));

  /** @param {Record<string, string | null | undefined>} updates */
  function pushQuery(updates) {
    const url = new URL(page.url);
    for (const [k, v] of Object.entries(updates)) {
      if (v === null || v === undefined || v === '') url.searchParams.delete(k);
      else url.searchParams.set(k, v);
    }
    if (!('page' in updates)) url.searchParams.delete('page');
    goto(url.pathname + (url.search ? url.search : ''));
  }

  /** @param {SubmitEvent} ev */
  function applySearch(ev) {
    ev.preventDefault();
    pushQuery({ q: search });
  }

  function clearFilters() {
    search = '';
    statusFilter = '';
    publishedFilter = '';
    pushQuery({ q: '', status: '', published: '' });
  }

  /** @param {string} state */
  function statusBadgeClass(state) {
    switch (state) {
      case 'draft':
        return 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200';
      case 'reviewed':
        return 'bg-blue-100 text-blue-900 dark:bg-blue-900/30 dark:text-blue-200';
      case 'approved':
        return 'bg-emerald-100 text-emerald-900 dark:bg-emerald-900/30 dark:text-emerald-200';
      default:
        return 'bg-[var(--surface-muted)] text-[var(--text-secondary)]';
    }
  }

  /** @type {import('@sveltejs/kit').SubmitFunction} */
  function handleDelete({ cancel }) {
    if (!window.confirm('Delete this solution? This cannot be undone.')) {
      cancel();
      return;
    }
    return async ({ result, update }) => {
      await update();
      if (result.type === 'success') {
        toast.success('Solution deleted');
        await invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {any} */ (result.data)?.error || 'Delete failed');
      }
    };
  }

  /** @type {import('@sveltejs/kit').SubmitFunction} */
  function handlePublish() {
    return async ({ result, update }) => {
      await update();
      if (result.type === 'success') {
        toast.success('Published');
        await invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {any} */ (result.data)?.error || 'Publish failed');
      }
    };
  }

  /** @type {import('@sveltejs/kit').SubmitFunction} */
  function handleUnpublish() {
    return async ({ result, update }) => {
      await update();
      if (result.type === 'success') {
        toast.success('Unpublished');
        await invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {any} */ (result.data)?.error || 'Unpublish failed');
      }
    };
  }

  /** @param {string | null | undefined} d */
  const formatDate = (d) => (d ? new Date(d).toLocaleDateString() : '—');
</script>

<svelte:head>
  <title>Knowledge Base - BottleCRM</title>
</svelte:head>

<PageHeader title="Knowledge Base">
  {#snippet titleIcon()}
    <BookOpen class="size-4" />
  {/snippet}
  {#snippet meta()}
    <span class="text-xs text-[var(--text-secondary)]">
      {total} {total === 1 ? 'article' : 'articles'}
    </span>
  {/snippet}
  {#snippet actions()}
    <Button onclick={() => goto('/solutions/new')} size="sm" class="gap-1">
      <Plus class="h-4 w-4" />
      New solution
    </Button>
  {/snippet}
</PageHeader>

<div class="flex flex-col gap-4 p-4">
  <section
    class="flex flex-wrap items-end gap-2 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-3"
  >
    <form class="flex flex-1 items-center gap-2" onsubmit={applySearch}>
      <div class="relative flex-1 min-w-[200px]">
        <Search
          class="pointer-events-none absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--text-secondary)]"
        />
        <input
          type="text"
          bind:value={search}
          placeholder="Search title or description..."
          class="w-full rounded border border-[var(--border-default)] bg-[var(--surface-default)] py-1.5 pl-8 pr-2 text-sm"
        />
      </div>
      <Button type="submit" size="sm" variant="outline">Search</Button>
    </form>

    <div class="flex items-center gap-2">
      <label class="flex items-center gap-1 text-xs text-[var(--text-secondary)]">
        Status
        <select
          bind:value={statusFilter}
          onchange={() => pushQuery({ status: statusFilter })}
          class="rounded border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-1 text-sm"
        >
          <option value="">All</option>
          <option value="draft">Draft</option>
          <option value="reviewed">Reviewed</option>
          <option value="approved">Approved</option>
        </select>
      </label>
      <label class="flex items-center gap-1 text-xs text-[var(--text-secondary)]">
        Published
        <select
          bind:value={publishedFilter}
          onchange={() => pushQuery({ published: publishedFilter })}
          class="rounded border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-1 text-sm"
        >
          <option value="">All</option>
          <option value="yes">Published</option>
          <option value="no">Not published</option>
        </select>
      </label>
      {#if search || statusFilter || publishedFilter}
        <Button size="sm" variant="ghost" onclick={clearFilters}>Clear</Button>
      {/if}
    </div>
  </section>

  {#if data.loadError}
    <div class="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-900 dark:border-red-900/50 dark:bg-red-900/20 dark:text-red-200">
      {data.loadError}
    </div>
  {/if}

  <section class="overflow-hidden rounded-md border border-[var(--border-default)] bg-[var(--surface-default)]">
    {#if solutions.length === 0}
      <div class="flex flex-col items-center gap-2 p-12 text-center">
        <BookOpen class="h-8 w-8 text-[var(--text-tertiary)]" />
        <p class="text-sm text-[var(--text-secondary)]">
          {search || statusFilter || publishedFilter
            ? 'No solutions match your filters.'
            : 'No solutions yet. Create one to start building your knowledge base.'}
        </p>
        {#if !(search || statusFilter || publishedFilter)}
          <Button onclick={() => goto('/solutions/new')} size="sm" variant="outline" class="mt-2 gap-1">
            <Plus class="h-4 w-4" />
            Create first solution
          </Button>
        {/if}
      </div>
    {:else}
      <table class="w-full text-sm">
        <thead class="border-b border-[var(--border-default)] bg-[var(--surface-sunken)] text-left text-xs uppercase tracking-wide text-[var(--text-secondary)]">
          <tr>
            <th class="px-3 py-2 font-medium">Title</th>
            <th class="px-3 py-2 font-medium">Status</th>
            <th class="px-3 py-2 font-medium">Published</th>
            <th class="px-3 py-2 text-right font-medium">Tickets</th>
            <th class="px-3 py-2 font-medium">Updated</th>
            <th class="px-3 py-2 font-medium"></th>
          </tr>
        </thead>
        <tbody>
          {#each solutions as sol (sol.id)}
            <tr class="border-b border-[var(--border-default)] last:border-0 hover:bg-[var(--surface-sunken)]">
              <td class="px-3 py-2">
                <a
                  href={`/solutions/${sol.id}`}
                  class="font-medium text-[var(--text-primary)] hover:underline"
                >
                  {sol.title}
                </a>
                {#if sol.description}
                  <p class="mt-0.5 line-clamp-1 max-w-[480px] text-xs text-[var(--text-secondary)]">
                    {sol.description}
                  </p>
                {/if}
              </td>
              <td class="px-3 py-2">
                <span class={`rounded px-2 py-0.5 text-[10px] font-medium uppercase ${statusBadgeClass(sol.status)}`}>
                  {sol.status}
                </span>
              </td>
              <td class="px-3 py-2">
                {#if sol.is_published}
                  <span class="inline-flex items-center gap-1 rounded bg-green-100 px-2 py-0.5 text-[10px] font-medium uppercase text-green-900 dark:bg-green-900/30 dark:text-green-200">
                    <CheckCircle2 class="h-3 w-3" />
                    Live
                  </span>
                {:else}
                  <span class="text-xs text-[var(--text-secondary)]">—</span>
                {/if}
              </td>
              <td class="px-3 py-2 text-right text-xs text-[var(--text-secondary)]">
                {sol.case_count ?? 0}
              </td>
              <td class="px-3 py-2 text-xs text-[var(--text-secondary)]">
                {formatDate(sol.updated_at)}
              </td>
              <td class="px-3 py-2">
                <div class="flex items-center justify-end gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    onclick={() => goto(`/solutions/${sol.id}`)}
                    aria-label="Edit"
                  >
                    <Pencil class="h-3.5 w-3.5" />
                  </Button>
                  {#if sol.is_published}
                    <form method="POST" action="?/unpublish" use:enhance={handleUnpublish}>
                      <input type="hidden" name="id" value={sol.id} />
                      <Button type="submit" size="sm" variant="ghost" aria-label="Unpublish" title="Unpublish">
                        <EyeOff class="h-3.5 w-3.5" />
                      </Button>
                    </form>
                  {:else if sol.status === 'approved'}
                    <form method="POST" action="?/publish" use:enhance={handlePublish}>
                      <input type="hidden" name="id" value={sol.id} />
                      <Button type="submit" size="sm" variant="ghost" aria-label="Publish" title="Publish">
                        <Eye class="h-3.5 w-3.5" />
                      </Button>
                    </form>
                  {/if}
                  <form method="POST" action="?/delete" use:enhance={handleDelete}>
                    <input type="hidden" name="id" value={sol.id} />
                    <Button type="submit" size="sm" variant="ghost" aria-label="Delete" title="Delete">
                      <Trash2 class="h-3.5 w-3.5 text-red-600" />
                    </Button>
                  </form>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </section>

  {#if totalPages > 1}
    <div class="flex items-center justify-between text-xs text-[var(--text-secondary)]">
      <span>
        Page {pageNum} of {totalPages}
      </span>
      <div class="flex items-center gap-2">
        <Button
          size="sm"
          variant="outline"
          disabled={pageNum <= 1}
          onclick={() => pushQuery({ page: String(pageNum - 1) })}
        >
          Previous
        </Button>
        <Button
          size="sm"
          variant="outline"
          disabled={pageNum >= totalPages}
          onclick={() => pushQuery({ page: String(pageNum + 1) })}
        >
          Next
        </Button>
      </div>
    </div>
  {/if}
</div>
