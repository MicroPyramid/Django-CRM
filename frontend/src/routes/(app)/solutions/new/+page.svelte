<script>
  import { goto } from '$app/navigation';
  import { enhance } from '$app/forms';
  import { toast } from 'svelte-sonner';
  import { ChevronLeft, BookOpen, Loader2 } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let submitting = $state(false);

  /** @type {import('@sveltejs/kit').SubmitFunction} */
  function handleSubmit() {
    submitting = true;
    return async ({ result, update }) => {
      submitting = false;
      if (result.type === 'redirect') {
        toast.success('Solution created');
        await update();
      } else if (result.type === 'failure') {
        toast.error(/** @type {any} */ (result.data)?.error || 'Failed to create');
        await update({ reset: false });
      }
    };
  }
</script>

<svelte:head>
  <title>New Solution - BottleCRM</title>
</svelte:head>

<div class="mx-auto flex max-w-2xl flex-col gap-4 p-4">
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
    <span class="font-medium text-[var(--text-primary)]">New solution</span>
  </div>

  <div class="flex items-center gap-2">
    <BookOpen class="h-5 w-5 text-[var(--text-secondary)]" />
    <h1 class="text-lg font-semibold">New solution</h1>
  </div>

  <form method="POST" use:enhance={handleSubmit} class="flex flex-col gap-4 rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-4">
    <label class="flex flex-col gap-1 text-sm">
      <span class="font-medium">Title <span class="text-red-600">*</span></span>
      <input
        type="text"
        name="title"
        required
        maxlength="255"
        placeholder="e.g. How to reset a customer's MFA"
        value={form?.title ?? ''}
        class="rounded border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-1.5 text-sm"
      />
    </label>

    <label class="flex flex-col gap-1 text-sm">
      <span class="font-medium">Description</span>
      <textarea
        name="description"
        rows="10"
        placeholder="Steps, root cause, workaround..."
        class="resize-y rounded border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm font-mono"
      >{form?.description ?? ''}</textarea>
      <span class="text-xs text-[var(--text-secondary)]">
        Markdown is fine — agents will see this when linking to a ticket.
      </span>
    </label>

    <label class="flex flex-col gap-1 text-sm">
      <span class="font-medium">Status</span>
      <select
        name="status"
        value={form?.status ?? 'draft'}
        class="rounded border border-[var(--border-default)] bg-[var(--surface-default)] px-2 py-1.5 text-sm"
      >
        <option value="draft">Draft</option>
        <option value="reviewed">Reviewed</option>
        <option value="approved">Approved</option>
      </select>
      <span class="text-xs text-[var(--text-secondary)]">
        Only "Approved" articles can be published. You can change this later.
      </span>
    </label>

    {#if form?.error}
      <p class="rounded bg-red-50 p-2 text-sm text-red-900 dark:bg-red-900/30 dark:text-red-200">
        {form.error}
      </p>
    {/if}

    <div class="flex items-center justify-end gap-2">
      <Button type="button" variant="ghost" onclick={() => goto('/solutions')}>Cancel</Button>
      <Button type="submit" disabled={submitting}>
        {#if submitting}<Loader2 class="mr-1 h-3.5 w-3.5 animate-spin" />{/if}
        Create solution
      </Button>
    </div>
  </form>
</div>
