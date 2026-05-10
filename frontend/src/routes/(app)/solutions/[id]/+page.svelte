<script>
  import { goto, invalidateAll } from '$app/navigation';
  import { enhance } from '$app/forms';
  import { toast } from 'svelte-sonner';
  import {
    ChevronLeft,
    BookOpen,
    Eye,
    EyeOff,
    Trash2,
    Loader2,
    CheckCircle2,
    Briefcase
  } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';

  /** @type {{ data: any }} */
  let { data } = $props();

  const sol = $derived(data.solution);

  let title = $state(sol.title);
  let description = $state(sol.description || '');
  let statusVal = $state(sol.status);
  let saving = $state(false);

  // Re-seed local form state if the server-loaded solution changes (after a
  // status change via publish/unpublish actions, invalidateAll re-runs load
  // and we want the form to reflect the fresh values).
  $effect(() => {
    title = sol.title;
    description = sol.description || '';
    statusVal = sol.status;
  });

  const dirty = $derived(
    title !== sol.title ||
      (description || '') !== (sol.description || '') ||
      statusVal !== sol.status
  );

  /** @type {import('@sveltejs/kit').SubmitFunction} */
  function handleSave() {
    saving = true;
    return async ({ result, update }) => {
      saving = false;
      await update();
      if (result.type === 'success') {
        toast.success('Saved');
        await invalidateAll();
      } else if (result.type === 'failure') {
        toast.error(/** @type {any} */ (result.data)?.error || 'Save failed');
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

  /** @type {import('@sveltejs/kit').SubmitFunction} */
  function handleDelete({ cancel }) {
    if (
      !window.confirm(
        'Delete this solution? Linked tickets will lose their reference. This cannot be undone.'
      )
    ) {
      cancel();
      return;
    }
    return async ({ result }) => {
      if (result.type === 'redirect') {
        toast.success('Solution deleted');
      } else if (result.type === 'failure') {
        toast.error(/** @type {any} */ (result.data)?.error || 'Delete failed');
      }
    };
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

  /** @param {string | null | undefined} d */
  const formatDate = (d) => (d ? new Date(d).toLocaleString() : '—');
</script>

<svelte:head>
  <title>{sol.title} - Knowledge Base - BottleCRM</title>
</svelte:head>

<div class="flex flex-col gap-4 p-4">
  <div class="flex items-center gap-2 text-sm text-[var(--text-secondary)]">
    <button
      type="button"
      onclick={() => goto('/solutions')}
      class="inline-flex items-center gap-1 hover:text-[var(--text-primary)]"
    >
      <ChevronLeft class="h-4 w-4" />
      Knowledge Base
    </button>
    <span>/</span>
    <span class="truncate font-medium text-[var(--text-primary)]">{sol.title}</span>
  </div>

  <div class="flex flex-wrap items-start justify-between gap-3">
    <div class="flex items-center gap-2">
      <BookOpen class="h-5 w-5 text-[var(--text-secondary)]" />
      <h1 class="text-lg font-semibold">{sol.title}</h1>
      <span class={`rounded px-2 py-0.5 text-[10px] font-medium uppercase ${statusBadgeClass(sol.status)}`}>
        {sol.status}
      </span>
      {#if sol.is_published}
        <span class="inline-flex items-center gap-1 rounded bg-green-100 px-2 py-0.5 text-[10px] font-medium uppercase text-green-900 dark:bg-green-900/30 dark:text-green-200">
          <CheckCircle2 class="h-3 w-3" />
          Live
        </span>
      {/if}
    </div>

    <div class="flex items-center gap-2">
      {#if sol.is_published}
        <form method="POST" action="?/unpublish" use:enhance={handleUnpublish}>
          <Button type="submit" variant="outline" size="sm" class="gap-1">
            <EyeOff class="h-4 w-4" />
            Unpublish
          </Button>
        </form>
      {:else}
        <form method="POST" action="?/publish" use:enhance={handlePublish}>
          <Button
            type="submit"
            size="sm"
            class="gap-1"
            disabled={sol.status !== 'approved'}
            title={sol.status !== 'approved'
              ? 'Set status to Approved first'
              : 'Publish to the knowledge base'}
          >
            <Eye class="h-4 w-4" />
            Publish
          </Button>
        </form>
      {/if}
      <form method="POST" action="?/delete" use:enhance={handleDelete}>
        <Button type="submit" variant="ghost" size="sm" class="gap-1">
          <Trash2 class="h-4 w-4 text-red-600" />
          Delete
        </Button>
      </form>
    </div>
  </div>

  <div class="grid grid-cols-1 gap-4 lg:grid-cols-[1fr_320px]">
    <form
      method="POST"
      action="?/update"
      use:enhance={handleSave}
      class="flex flex-col gap-4 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
    >
      <label class="flex flex-col gap-1 text-sm">
        <span class="font-medium">Title</span>
        <input
          type="text"
          name="title"
          required
          maxlength="255"
          bind:value={title}
          class="rounded border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-1.5 text-sm"
        />
      </label>

      <label class="flex flex-col gap-1 text-sm">
        <span class="font-medium">Description</span>
        <textarea
          name="description"
          rows="14"
          bind:value={description}
          class="resize-y rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm font-mono"
        ></textarea>
      </label>

      <label class="flex max-w-xs flex-col gap-1 text-sm">
        <span class="font-medium">Status</span>
        <select
          name="status"
          bind:value={statusVal}
          class="rounded border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-1.5 text-sm"
        >
          <option value="draft">Draft</option>
          <option value="reviewed">Reviewed</option>
          <option value="approved">Approved</option>
        </select>
        {#if sol.is_published && statusVal !== 'approved'}
          <span class="text-xs text-amber-700 dark:text-amber-300">
            Saving will not auto-unpublish — use Unpublish above first.
          </span>
        {/if}
      </label>

      <div class="flex items-center justify-end gap-2">
        <Button
          type="button"
          variant="ghost"
          disabled={!dirty || saving}
          onclick={() => {
            title = sol.title;
            description = sol.description || '';
            statusVal = sol.status;
          }}
        >
          Reset
        </Button>
        <Button type="submit" disabled={!dirty || saving}>
          {#if saving}<Loader2 class="mr-1 h-3.5 w-3.5 animate-spin" />{/if}
          Save changes
        </Button>
      </div>
    </form>

    <aside class="flex flex-col gap-4">
      <section class="rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-3 text-sm">
        <h3 class="mb-2 text-xs font-medium uppercase tracking-wide text-[var(--text-secondary)]">
          Metadata
        </h3>
        <dl class="space-y-1 text-xs">
          <div class="flex justify-between gap-2">
            <dt class="text-[var(--text-secondary)]">Created</dt>
            <dd>{formatDate(sol.created_at)}</dd>
          </div>
          <div class="flex justify-between gap-2">
            <dt class="text-[var(--text-secondary)]">Updated</dt>
            <dd>{formatDate(sol.updated_at)}</dd>
          </div>
          <div class="flex justify-between gap-2">
            <dt class="text-[var(--text-secondary)]">Linked tickets</dt>
            <dd>{(sol.linked_cases || []).length}</dd>
          </div>
        </dl>
      </section>

      <section class="rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-3 text-sm">
        <h3 class="mb-2 flex items-center gap-1 text-xs font-medium uppercase tracking-wide text-[var(--text-secondary)]">
          <Briefcase class="h-3 w-3" />
          Linked tickets
        </h3>
        {#if !sol.linked_cases || sol.linked_cases.length === 0}
          <p class="text-xs text-[var(--text-secondary)]">No tickets reference this solution yet.</p>
        {:else}
          <ul class="space-y-1">
            {#each sol.linked_cases as c (c.id)}
              <li>
                <a
                  href={`/tickets/${c.id}`}
                  class="block truncate rounded px-1 py-0.5 text-xs hover:bg-[var(--surface-sunken)]"
                >
                  {c.name || c.subject || 'Untitled ticket'}
                </a>
              </li>
            {/each}
          </ul>
          <p class="mt-2 text-[10px] text-[var(--text-secondary)]">
            Showing up to 10. The status of this solution doesn't affect existing links.
          </p>
        {/if}
      </section>
    </aside>
  </div>
</div>
