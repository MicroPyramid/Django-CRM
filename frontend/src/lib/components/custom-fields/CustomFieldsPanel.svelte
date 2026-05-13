<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Sliders, Loader2, Check } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';

  /**
   * @typedef {Object} CustomFieldDef
   * @property {string} id
   * @property {string} key
   * @property {string} label
   * @property {string} field_type
   * @property {Array<{value: string, label: string}>=} options
   * @property {boolean=} is_required
   * @property {number=} display_order
   * @property {boolean=} is_active
   *
   * @typedef {{
   *   target: string,
   *   definitions: CustomFieldDef[],
   *   values: Record<string, unknown>,
   *   formAction?: string,
   *   title?: string,
   *   extraFields?: Record<string, string>,
   * }} Props
   */

  /** @type {Props} */
  let {
    target,
    definitions,
    values = {},
    formAction = '?/updateCustomFields',
    title = 'Details',
    extraFields = /** @type {Record<string, string>} */ ({})
  } = $props();

  // Local editable copy of values, keyed by definition key.
  /** @type {Record<string, any>} */
  let draft = $state({});
  let saving = $state(false);

  $effect(() => {
    // Reseed when the upstream values change (load() invalidation).
    draft = { ...values };
    for (const defn of definitions) {
      if (!(defn.key in draft)) draft[defn.key] = defaultFor(defn);
    }
  });

  /** @param {CustomFieldDef} defn */
  function defaultFor(defn) {
    if (defn.field_type === 'checkbox') return false;
    if (defn.field_type === 'number') return '';
    return '';
  }

  const activeDefs = $derived(
    (definitions || [])
      .filter((d) => d.is_active !== false)
      .slice()
      .sort((a, b) => (a.display_order ?? 0) - (b.display_order ?? 0))
  );

  const isEmpty = $derived(activeDefs.length === 0);
</script>

<section
  class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
>
  <header class="mb-3 flex items-center gap-2">
    <Sliders class="h-4 w-4 text-[var(--text-secondary)]" />
    <h3 class="text-sm font-medium text-[var(--text-secondary)]">
      {title}
    </h3>
  </header>

  {#if isEmpty}
    <p class="text-sm text-[var(--text-secondary)]">
      No custom fields configured for {target.toLowerCase()}.
      <a class="underline" href="/settings/custom-fields?target={target}">Manage</a>
    </p>
  {:else}
    <form
      method="POST"
      action={formAction}
      use:enhance={() => {
        saving = true;
        return async ({ result, update }) => {
          await update();
          saving = false;
          if (result.type === 'success') {
            toast.success(`${title} saved`);
            await invalidateAll();
          } else if (result.type === 'failure') {
            toast.error(String(result.data?.error || 'Failed to save'));
          }
        };
      }}
      class="space-y-4"
    >
      <input
        type="hidden"
        name="custom_fields"
        value={JSON.stringify(draft || {})}
      />
      {#each Object.entries(extraFields) as [extraKey, extraValue] (extraKey)}
        <input type="hidden" name={extraKey} value={extraValue} />
      {/each}

      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {#each activeDefs as defn (defn.id)}
          <div class="space-y-1.5">
            <Label for={`cf_${defn.key}`} class="text-xs">
              {defn.label}
              {#if defn.is_required}
                <span class="text-[var(--color-danger-default)]">*</span>
              {/if}
            </Label>

            {#if defn.field_type === 'text'}
              <Input
                id={`cf_${defn.key}`}
                bind:value={draft[defn.key]}
                required={!!defn.is_required}
              />
            {:else if defn.field_type === 'textarea'}
              <textarea
                id={`cf_${defn.key}`}
                rows={3}
                required={!!defn.is_required}
                bind:value={draft[defn.key]}
                class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary-default)]"
              ></textarea>
            {:else if defn.field_type === 'number'}
              <Input
                id={`cf_${defn.key}`}
                type="number"
                step="any"
                required={!!defn.is_required}
                bind:value={draft[defn.key]}
              />
            {:else if defn.field_type === 'date'}
              <Input
                id={`cf_${defn.key}`}
                type="date"
                required={!!defn.is_required}
                bind:value={draft[defn.key]}
              />
            {:else if defn.field_type === 'checkbox'}
              <label class="flex items-center gap-2 text-sm">
                <input
                  id={`cf_${defn.key}`}
                  type="checkbox"
                  bind:checked={draft[defn.key]}
                />
                <span class="text-[var(--text-secondary)]">{defn.label}</span>
              </label>
            {:else if defn.field_type === 'dropdown'}
              <select
                id={`cf_${defn.key}`}
                required={!!defn.is_required}
                bind:value={draft[defn.key]}
                class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm focus:ring-2 focus:ring-[var(--color-primary-default)]"
              >
                <option value="">— None —</option>
                {#each defn.options || [] as opt (opt.value)}
                  <option value={opt.value}>{opt.label}</option>
                {/each}
              </select>
            {:else}
              <Input
                id={`cf_${defn.key}`}
                bind:value={draft[defn.key]}
              />
            {/if}
          </div>
        {/each}
      </div>

      <div class="flex justify-end">
        <Button type="submit" size="sm" disabled={saving} class="gap-1">
          {#if saving}
            <Loader2 class="h-3.5 w-3.5 animate-spin" />
          {:else}
            <Check class="h-3.5 w-3.5" />
          {/if}
          Save
        </Button>
      </div>
    </form>
  {/if}
</section>
