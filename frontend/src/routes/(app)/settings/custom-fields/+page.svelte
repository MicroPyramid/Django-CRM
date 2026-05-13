<script>
  import { enhance } from '$app/forms';
  import { goto, invalidateAll } from '$app/navigation';
  import { page } from '$app/stores';
  import { toast } from 'svelte-sonner';
  import { Plus, Pencil, Archive, RotateCcw, Sliders, Check, X } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const target = $derived(data.target || 'Case');
  const targets = $derived(data.targets || []);
  const definitions = $derived(data.definitions || []);

  const FIELD_TYPES = [
    { value: 'text', label: 'Text' },
    { value: 'textarea', label: 'Textarea' },
    { value: 'number', label: 'Number' },
    { value: 'dropdown', label: 'Dropdown' },
    { value: 'date', label: 'Date' },
    { value: 'checkbox', label: 'Checkbox' }
  ];

  let dialogOpen = $state(false);
  /** @type {any} */
  let editing = $state(null);

  // Form fields
  let formKey = $state('');
  let formLabel = $state('');
  let formFieldType = $state('text');
  let formOptionsText = $state('');
  let formIsRequired = $state(false);
  let formIsFilterable = $state(false);
  let formDisplayOrder = $state(0);
  let formIsActive = $state(true);

  function slugify(value) {
    return String(value || '')
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 64);
  }

  function openCreate() {
    editing = null;
    formKey = '';
    formLabel = '';
    formFieldType = 'text';
    formOptionsText = '';
    formIsRequired = false;
    formIsFilterable = false;
    formDisplayOrder = 0;
    formIsActive = true;
    dialogOpen = true;
  }

  /** @param {any} defn */
  function openEdit(defn) {
    editing = defn;
    formKey = defn.key;
    formLabel = defn.label;
    formFieldType = defn.field_type;
    formOptionsText = Array.isArray(defn.options)
      ? JSON.stringify(defn.options, null, 2)
      : '';
    formIsRequired = !!defn.is_required;
    formIsFilterable = !!defn.is_filterable;
    formDisplayOrder = defn.display_order ?? 0;
    formIsActive = defn.is_active !== false;
    dialogOpen = true;
  }

  function closeDialog() {
    dialogOpen = false;
    editing = null;
  }

  /** @param {string} value */
  function selectTarget(value) {
    const params = new URLSearchParams($page.url.search);
    params.set('target', value);
    goto(`?${params.toString()}`, { keepFocus: true, noScroll: true });
  }

  $effect(() => {
    if (form?.success) {
      toast.success(editing ? 'Custom field updated' : 'Custom field saved');
      closeDialog();
      invalidateAll();
    } else if (form?.error) {
      const message =
        typeof form.error === 'string' ? form.error : JSON.stringify(form.error);
      toast.error(message);
    }
  });

  /** @param {string} type */
  function describeType(type) {
    return FIELD_TYPES.find((t) => t.value === type)?.label || type;
  }
</script>

<svelte:head>
  <title>Custom Fields - Settings - BottleCRM</title>
</svelte:head>

<PageHeader
  title="Custom Fields"
  subtitle="Per-org schema extensions for tickets, leads, contacts, accounts, opportunities, tasks, invoices, estimates, and recurring invoices"
>
  {#snippet actions()}
    <Button onclick={openCreate} class="gap-2">
      <Plus class="h-4 w-4" />
      New field
    </Button>
  {/snippet}
</PageHeader>

<div class="flex-1 p-4 md:p-6 lg:p-8">
  <div class="mx-auto max-w-4xl space-y-6">
    <section
      class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
    >
      <div class="flex flex-wrap items-center gap-2">
        <Sliders class="h-4 w-4 text-[var(--text-secondary)]" />
        <span class="text-sm text-[var(--text-secondary)]">Entity:</span>
        {#each targets as t (t.value)}
          {@const isCurrent = t.value === target}
          <button
            type="button"
            onclick={() => t.enabled && selectTarget(t.value)}
            disabled={!t.enabled}
            class={[
              'rounded-md border px-3 py-1 text-xs transition-colors',
              isCurrent
                ? 'border-[var(--color-primary-default)] bg-[var(--color-primary-light)] text-[var(--color-primary-default)]'
                : 'border-[var(--border-default)] text-[var(--text-secondary)] hover:bg-[var(--surface-muted)]',
              !t.enabled && 'cursor-not-allowed opacity-50'
            ]}
            title={t.enabled ? '' : 'Coming soon — entity needs a custom_fields column first'}
          >
            {t.label}
          </button>
        {/each}
      </div>
    </section>

    <section
      class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)]"
    >
      <header class="border-b border-[var(--border-default)] p-4">
        <h2 class="text-base font-medium text-[var(--text-primary)]">
          {target} fields
        </h2>
        <p class="text-sm text-[var(--text-secondary)]">
          Active fields render on the {target.toLowerCase()} detail form. Inactive
          fields stay archived but their values remain readable on existing records.
        </p>
      </header>

      {#if definitions.length === 0}
        <div class="p-6 text-center text-sm text-[var(--text-secondary)]">
          No custom fields yet. Click <strong>New field</strong> to define one.
        </div>
      {:else}
        <ul class="divide-y divide-[var(--border-default)]">
          {#each definitions as defn (defn.id)}
            <li class="flex items-center gap-3 p-4">
              <div class="min-w-0 flex-1">
                <div class="flex flex-wrap items-baseline gap-2">
                  <span class="text-sm font-medium text-[var(--text-primary)]">
                    {defn.label}
                  </span>
                  <code class="text-xs text-[var(--text-secondary)]">{defn.key}</code>
                  <span
                    class="rounded-full bg-[var(--surface-muted)] px-2 py-0.5 text-xs text-[var(--text-secondary)]"
                  >
                    {describeType(defn.field_type)}
                  </span>
                  {#if defn.is_required}
                    <span class="rounded-full bg-amber-100 px-2 py-0.5 text-xs text-amber-700 dark:bg-amber-900/40 dark:text-amber-300">
                      Required
                    </span>
                  {/if}
                  {#if !defn.is_active}
                    <span class="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-700 dark:bg-slate-700 dark:text-slate-200">
                      Inactive
                    </span>
                  {/if}
                </div>
                {#if defn.field_type === 'dropdown' && defn.options?.length}
                  <p class="mt-1 text-xs text-[var(--text-secondary)]">
                    {defn.options.length} options:
                    {defn.options.map((/** @type {any} */ o) => o.label).join(', ')}
                  </p>
                {/if}
              </div>
              <div class="flex items-center gap-1">
                <Button variant="ghost" size="sm" onclick={() => openEdit(defn)} class="gap-1">
                  <Pencil class="h-3.5 w-3.5" />
                </Button>
                {#if defn.is_active}
                  <form method="POST" action="?/delete" use:enhance class="inline">
                    <input type="hidden" name="id" value={defn.id} />
                    <Button
                      type="submit"
                      variant="ghost"
                      size="sm"
                      class="gap-1 text-[var(--color-danger-default)]"
                    >
                      <Archive class="h-3.5 w-3.5" />
                    </Button>
                  </form>
                {:else}
                  <form
                    method="POST"
                    action="?/update"
                    use:enhance
                    class="inline"
                  >
                    <input type="hidden" name="id" value={defn.id} />
                    <input type="hidden" name="label" value={defn.label} />
                    <input type="hidden" name="display_order" value={defn.display_order ?? 0} />
                    <input type="hidden" name="is_required" value={defn.is_required ? 'true' : 'false'} />
                    <input type="hidden" name="is_filterable" value={defn.is_filterable ? 'true' : 'false'} />
                    <input type="hidden" name="is_active" value="true" />
                    <input
                      type="hidden"
                      name="options"
                      value={defn.options ? JSON.stringify(defn.options) : ''}
                    />
                    <Button type="submit" variant="ghost" size="sm" class="gap-1">
                      <RotateCcw class="h-3.5 w-3.5" />
                    </Button>
                  </form>
                {/if}
              </div>
            </li>
          {/each}
        </ul>
      {/if}
    </section>
  </div>
</div>

<Dialog.Root bind:open={dialogOpen}>
  <Dialog.Content class="sm:max-w-lg">
    <Dialog.Header>
      <Dialog.Title>{editing ? 'Edit field' : 'New field'}</Dialog.Title>
      <Dialog.Description>
        {editing
          ? 'Key, target entity, and type are immutable; create a new field if you need to change shape.'
          : 'Define a custom field for ' + target + '.'}
      </Dialog.Description>
    </Dialog.Header>

    <form
      method="POST"
      action={editing ? '?/update' : '?/create'}
      use:enhance={() => {
        return async ({ update }) => {
          await update();
        };
      }}
      class="space-y-4"
    >
      {#if editing}
        <input type="hidden" name="id" value={editing.id} />
      {/if}
      <input type="hidden" name="target_model" value={target} />

      <div class="space-y-1.5">
        <Label for="label">Label *</Label>
        <Input
          id="label"
          name="label"
          required
          bind:value={formLabel}
          oninput={() => {
            if (!editing && !formKey) formKey = slugify(formLabel);
          }}
        />
      </div>

      <div class="space-y-1.5">
        <Label for="key">Key *</Label>
        <Input
          id="key"
          name="key"
          required
          bind:value={formKey}
          disabled={!!editing}
          placeholder="severity"
        />
        <p class="text-xs text-[var(--text-secondary)]">
          Lowercase slug (a-z, 0-9, _). Stored as the JSON key on the entity.
          Immutable once saved.
        </p>
      </div>

      <div class="space-y-1.5">
        <Label for="field_type">Type *</Label>
        <select
          id="field_type"
          name="field_type"
          bind:value={formFieldType}
          disabled={!!editing}
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary-default)] disabled:opacity-50"
        >
          {#each FIELD_TYPES as opt (opt.value)}
            <option value={opt.value}>{opt.label}</option>
          {/each}
        </select>
      </div>

      {#if formFieldType === 'dropdown'}
        <div class="space-y-1.5">
          <Label for="options">Dropdown options (JSON)</Label>
          <textarea
            id="options"
            name="options"
            bind:value={formOptionsText}
            rows={5}
            placeholder={`[
  { "value": "S1", "label": "S1" },
  { "value": "S2", "label": "S2" }
]`}
            class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 font-mono text-xs focus:ring-2 focus:ring-[var(--color-primary-default)]"
          ></textarea>
          <p class="text-xs text-[var(--text-secondary)]">
            JSON array of {'{ value, label }'} objects. Values must be unique.
          </p>
        </div>
      {/if}

      <div class="grid grid-cols-2 gap-3">
        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" bind:checked={formIsRequired} />
          Required
        </label>
        <input
          type="hidden"
          name="is_required"
          value={formIsRequired ? 'true' : 'false'}
        />

        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" bind:checked={formIsFilterable} />
          Filterable
        </label>
        <input
          type="hidden"
          name="is_filterable"
          value={formIsFilterable ? 'true' : 'false'}
        />

        <div class="space-y-1.5">
          <Label for="display_order" class="text-xs">Display order</Label>
          <Input
            id="display_order"
            name="display_order"
            type="number"
            min="0"
            bind:value={formDisplayOrder}
          />
        </div>

        <label class="flex items-center gap-2 text-sm">
          <input type="checkbox" bind:checked={formIsActive} />
          Active
        </label>
        <input
          type="hidden"
          name="is_active"
          value={formIsActive ? 'true' : 'false'}
        />
      </div>

      <Dialog.Footer>
        <Button type="button" variant="outline" onclick={closeDialog} class="gap-1">
          <X class="h-4 w-4" />
          Cancel
        </Button>
        <Button type="submit" class="gap-1">
          <Check class="h-4 w-4" />
          {editing ? 'Save changes' : 'Create field'}
        </Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
