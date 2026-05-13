<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import {
    Loader2,
    MessageSquareQuote,
    Plus,
    Trash2,
    Pencil,
    Power,
    AlertTriangle
  } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import { Textarea } from '$lib/components/ui/textarea/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const macros = $derived(/** @type {any[]} */ (data.macros || []));
  const isAdmin = $derived(data.isAdmin === true);
  const currentProfileId = $derived(data.currentProfileId);

  const orgMacros = $derived(macros.filter((m) => m.scope === 'org'));
  const personalMacros = $derived(macros.filter((m) => m.scope === 'personal'));

  // Create-form state
  let creating = $state(false);
  let newTitle = $state('');
  let newBody = $state('');
  let newScope = $state('personal');

  // Edit-dialog state
  let editOpen = $state(false);
  /** @type {any} */
  let editing = $state(null);
  let editTitle = $state('');
  let editBody = $state('');
  let editIsActive = $state(true);
  let saving = $state(false);

  /** @param {any} macro */
  function openEdit(macro) {
    editing = macro;
    editTitle = macro.title;
    editBody = macro.body;
    editIsActive = macro.is_active;
    editOpen = true;
  }

  /** @param {any} macro */
  function canEdit(macro) {
    if (macro.scope === 'org') return isAdmin;
    return macro.owner === currentProfileId;
  }

  const PLACEHOLDERS = [
    '%customer_name%',
    '%customer_email%',
    '%case_id%',
    '%case_subject%',
    '%agent_name%',
    '%agent_email%',
    '%org_name%'
  ];

  // Mirror of backend SUPPORTED_TOKENS in macros/render.py — unknown tokens
  // render literally on the ticket, so we surface them at edit-time before
  // they ship in a customer-facing reply.
  const SUPPORTED_TOKENS = new Set([
    'customer_name',
    'customer_email',
    'case_id',
    'case_subject',
    'agent_name',
    'agent_email',
    'org_name'
  ]);

  /** @param {string | undefined | null} body */
  function findUnknownPlaceholders(body) {
    if (!body) return [];
    const re = /%([a-zA-Z_][a-zA-Z0-9_]*)%/g;
    /** @type {Set<string>} */
    const found = new Set();
    for (const m of body.matchAll(re)) {
      if (!SUPPORTED_TOKENS.has(m[1])) found.add(`%${m[1]}%`);
    }
    return Array.from(found);
  }

  const unknownInNew = $derived(findUnknownPlaceholders(newBody));
  const unknownInEdit = $derived(findUnknownPlaceholders(editBody));
</script>

<svelte:head>
  <title>Macros - Settings - BottleCRM</title>
</svelte:head>

<PageHeader
  title="Macros"
  subtitle="Reusable canned responses agents apply to a ticket comment in one click"
/>

<div class="flex-1 p-4 md:p-6 lg:p-8">
  <div class="mx-auto max-w-4xl space-y-6">
    <section
      class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-6 space-y-4"
    >
      <header class="flex items-start gap-3">
        <div
          class="flex h-9 w-9 items-center justify-center rounded-full bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300"
        >
          <MessageSquareQuote class="h-4 w-4" />
        </div>
        <div>
          <h2 class="text-base font-medium text-[var(--text-primary)]">
            New macro
          </h2>
          <p class="text-sm text-[var(--text-secondary)]">
            Use placeholders like
            {#each PLACEHOLDERS as p, i (p)}
              <code class="rounded bg-[var(--surface-sunken)] px-1 text-xs"
                >{p}</code
              >{i < PLACEHOLDERS.length - 1 ? ', ' : ''}
            {/each}
            — they expand at apply-time.
          </p>
        </div>
      </header>

      <form
        method="POST"
        action="?/create"
        use:enhance={() => {
          creating = true;
          return async ({ result, update }) => {
            await update();
            creating = false;
            if (result.type === 'success') {
              newTitle = '';
              newBody = '';
              toast.success('Macro created');
              await invalidateAll();
            } else if (result.type === 'failure') {
              toast.error(/** @type {any} */ (result.data)?.error || 'Failed to create');
            }
          };
        }}
        class="space-y-3"
      >
        <div class="grid grid-cols-1 gap-3 md:grid-cols-2">
          <div class="space-y-1">
            <Label for="m-title" class="text-sm">Title</Label>
            <Input
              id="m-title"
              name="title"
              type="text"
              maxlength="255"
              bind:value={newTitle}
              required
              placeholder="e.g. Greeting"
            />
          </div>
          <div class="space-y-1">
            <Label for="m-scope" class="text-sm">Scope</Label>
            <select
              id="m-scope"
              name="scope"
              bind:value={newScope}
              class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary-default)]"
            >
              <option value="personal">Personal (only you)</option>
              {#if isAdmin}
                <option value="org">Org (all agents)</option>
              {/if}
            </select>
          </div>
        </div>
        <div class="space-y-1">
          <Label for="m-body" class="text-sm">Body</Label>
          <Textarea
            id="m-body"
            name="body"
            rows={5}
            bind:value={newBody}
            required
            placeholder="Hi %customer_name%, this is %agent_name%..."
          />
          {#if unknownInNew.length > 0}
            <div
              class="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50/70 p-2 text-xs text-amber-900 dark:border-amber-900/40 dark:bg-amber-900/15 dark:text-amber-200"
              role="alert"
            >
              <AlertTriangle class="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>
                Unknown placeholder{unknownInNew.length > 1 ? 's' : ''}:
                {#each unknownInNew as token, i (token)}
                  <code class="rounded bg-amber-100 px-1 dark:bg-amber-900/40"
                    >{token}</code
                  >{i < unknownInNew.length - 1 ? ', ' : ''}
                {/each}
                — these will render literally on the ticket. Check spelling
                against the supported list above.
              </span>
            </div>
          {/if}
        </div>
        <div class="flex justify-end">
          <Button type="submit" disabled={creating} class="gap-2">
            {#if creating}
              <Loader2 class="h-4 w-4 animate-spin" />
              Creating…
            {:else}
              <Plus class="h-4 w-4" />
              Create macro
            {/if}
          </Button>
        </div>
        {#if form?.error}
          <p class="text-sm text-[var(--color-danger-default)]">{form.error}</p>
        {/if}
      </form>
    </section>

    <section
      class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-6 space-y-3"
    >
      <header>
        <h2 class="text-base font-medium text-[var(--text-primary)]">
          Org macros
        </h2>
        <p class="text-sm text-[var(--text-secondary)]">
          Visible to every agent in the org. {isAdmin
            ? 'You can edit and deactivate.'
            : 'Only admins can edit.'}
        </p>
      </header>
      {#if orgMacros.length === 0}
        <p class="text-sm text-[var(--text-secondary)]">
          No org macros yet.{isAdmin ? ' Create one above.' : ''}
        </p>
      {:else}
        <ul
          class="divide-y divide-[var(--border-default)] rounded-md border border-[var(--border-default)]"
        >
          {#each orgMacros as m (m.id)}
            {@const unknown = findUnknownPlaceholders(m.body)}
            <li class="flex items-start justify-between gap-3 px-3 py-2 text-sm">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-medium">{m.title}</span>
                  {#if !m.is_active}
                    <span
                      class="rounded bg-[var(--surface-sunken)] px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-[var(--text-secondary)]"
                    >
                      Inactive
                    </span>
                  {/if}
                  {#if unknown.length > 0}
                    <span
                      class="inline-flex items-center gap-1 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-900 dark:bg-amber-900/40 dark:text-amber-200"
                      title={`Unknown placeholder${unknown.length > 1 ? 's' : ''}: ${unknown.join(', ')}`}
                    >
                      <AlertTriangle class="h-3 w-3" />
                      Unknown placeholder{unknown.length > 1 ? 's' : ''}
                    </span>
                  {/if}
                </div>
                <p
                  class="mt-0.5 line-clamp-2 whitespace-pre-wrap text-xs text-[var(--text-secondary)]"
                >
                  {m.body}
                </p>
              </div>
              {#if canEdit(m)}
                <div class="flex shrink-0 items-center gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onclick={() => openEdit(m)}
                    aria-label="Edit macro"
                    title="Edit"
                    class="h-7 w-7 p-0"
                  >
                    <Pencil class="h-4 w-4" />
                  </Button>
                  <form
                    method="POST"
                    action="?/remove"
                    use:enhance={() => async ({ result, update }) => {
                      await update();
                      if (result.type === 'success') {
                        toast.success('Macro deactivated');
                        await invalidateAll();
                      } else if (result.type === 'failure') {
                        toast.error(/** @type {any} */ (result.data)?.error || 'Failed to deactivate');
                      }
                    }}
                  >
                    <input type="hidden" name="id" value={m.id} />
                    <Button
                      type="submit"
                      variant="ghost"
                      size="sm"
                      aria-label="Deactivate macro"
                      title="Deactivate"
                      class="h-7 w-7 p-0 text-[var(--text-secondary)] hover:text-[var(--color-danger-default)]"
                    >
                      <Power class="h-4 w-4" />
                    </Button>
                  </form>
                </div>
              {/if}
            </li>
          {/each}
        </ul>
      {/if}
    </section>

    <section
      class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-6 space-y-3"
    >
      <header>
        <h2 class="text-base font-medium text-[var(--text-primary)]">
          My macros
        </h2>
        <p class="text-sm text-[var(--text-secondary)]">
          Only you can see and use these.
        </p>
      </header>
      {#if personalMacros.length === 0}
        <p class="text-sm text-[var(--text-secondary)]">No personal macros yet.</p>
      {:else}
        <ul
          class="divide-y divide-[var(--border-default)] rounded-md border border-[var(--border-default)]"
        >
          {#each personalMacros as m (m.id)}
            {@const unknown = findUnknownPlaceholders(m.body)}
            <li class="flex items-start justify-between gap-3 px-3 py-2 text-sm">
              <div class="min-w-0 flex-1">
                <div class="flex items-center gap-2">
                  <span class="font-medium">{m.title}</span>
                  {#if unknown.length > 0}
                    <span
                      class="inline-flex items-center gap-1 rounded bg-amber-100 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-amber-900 dark:bg-amber-900/40 dark:text-amber-200"
                      title={`Unknown placeholder${unknown.length > 1 ? 's' : ''}: ${unknown.join(', ')}`}
                    >
                      <AlertTriangle class="h-3 w-3" />
                      Unknown placeholder{unknown.length > 1 ? 's' : ''}
                    </span>
                  {/if}
                </div>
                <p
                  class="mt-0.5 line-clamp-2 whitespace-pre-wrap text-xs text-[var(--text-secondary)]"
                >
                  {m.body}
                </p>
              </div>
              <div class="flex shrink-0 items-center gap-1">
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onclick={() => openEdit(m)}
                  aria-label="Edit macro"
                  title="Edit"
                  class="h-7 w-7 p-0"
                >
                  <Pencil class="h-4 w-4" />
                </Button>
                <form
                  method="POST"
                  action="?/remove"
                  use:enhance={() => async ({ result, update }) => {
                    await update();
                    if (result.type === 'success') {
                      toast.success('Macro deleted');
                      await invalidateAll();
                    } else if (result.type === 'failure') {
                      toast.error(/** @type {any} */ (result.data)?.error || 'Failed to delete');
                    }
                  }}
                >
                  <input type="hidden" name="id" value={m.id} />
                  <Button
                    type="submit"
                    variant="ghost"
                    size="sm"
                    aria-label="Delete macro"
                    title="Delete"
                    class="h-7 w-7 p-0 text-[var(--text-secondary)] hover:text-[var(--color-danger-default)]"
                  >
                    <Trash2 class="h-4 w-4" />
                  </Button>
                </form>
              </div>
            </li>
          {/each}
        </ul>
      {/if}
    </section>
  </div>
</div>

<Dialog.Root bind:open={editOpen}>
  <Dialog.Content class="max-w-xl">
    <Dialog.Header>
      <Dialog.Title>Edit macro</Dialog.Title>
      <Dialog.Description>
        Changes apply the next time someone inserts this macro.
      </Dialog.Description>
    </Dialog.Header>
    {#if editing}
      <form
        method="POST"
        action="?/update"
        use:enhance={() => {
          saving = true;
          return async ({ result, update }) => {
            await update();
            saving = false;
            if (result.type === 'success') {
              editOpen = false;
              toast.success('Macro saved');
              await invalidateAll();
            } else if (result.type === 'failure') {
              toast.error(/** @type {any} */ (result.data)?.error || 'Failed to save');
            }
          };
        }}
        class="space-y-3"
      >
        <input type="hidden" name="id" value={editing.id} />
        <div class="space-y-1">
          <Label for="edit-title" class="text-sm">Title</Label>
          <Input
            id="edit-title"
            name="title"
            type="text"
            maxlength="255"
            bind:value={editTitle}
            required
          />
        </div>
        <div class="space-y-1">
          <Label for="edit-body" class="text-sm">Body</Label>
          <Textarea
            id="edit-body"
            name="body"
            rows={6}
            bind:value={editBody}
            required
          />
          {#if unknownInEdit.length > 0}
            <div
              class="flex items-start gap-2 rounded-md border border-amber-200 bg-amber-50/70 p-2 text-xs text-amber-900 dark:border-amber-900/40 dark:bg-amber-900/15 dark:text-amber-200"
              role="alert"
            >
              <AlertTriangle class="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>
                Unknown placeholder{unknownInEdit.length > 1 ? 's' : ''}:
                {#each unknownInEdit as token, i (token)}
                  <code class="rounded bg-amber-100 px-1 dark:bg-amber-900/40"
                    >{token}</code
                  >{i < unknownInEdit.length - 1 ? ', ' : ''}
                {/each}
                — these will render literally on the ticket.
              </span>
            </div>
          {/if}
        </div>
        {#if editing.scope === 'org'}
          <div class="flex items-center gap-2">
            <input
              id="edit-active"
              type="checkbox"
              bind:checked={editIsActive}
              class="h-4 w-4"
            />
            <Label for="edit-active" class="text-sm">Active</Label>
            <input
              type="hidden"
              name="is_active"
              value={editIsActive ? 'true' : 'false'}
            />
          </div>
        {/if}
        <Dialog.Footer>
          <Button
            type="button"
            variant="outline"
            onclick={() => (editOpen = false)}
          >
            Cancel
          </Button>
          <Button type="submit" disabled={saving} class="gap-2">
            {#if saving}
              <Loader2 class="h-4 w-4 animate-spin" />
              Saving…
            {:else}
              Save
            {/if}
          </Button>
        </Dialog.Footer>
      </form>
    {/if}
  </Dialog.Content>
</Dialog.Root>
