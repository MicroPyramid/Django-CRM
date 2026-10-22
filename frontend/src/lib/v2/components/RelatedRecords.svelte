<script>
  /**
   * Custom records that link to the built-in record on this page, with add and
   * remove for someone who may edit it. The server decides what is offered;
   * the page passes `relatedView(data.related)` and its form error.
   */
  import { enhance } from '$app/forms';
  import { page } from '$app/state';
  import { resolve } from '$app/paths';
  import { asInternalPath } from '#lib/utils/paths.js';
  import { recordHref } from '#lib/v2/custom-objects.js';
  import RecordPicker from '#lib/v2/components/RecordPicker.svelte';
  import { X } from '@lucide/svelte';

  /** @type {{ related: { groups: any[], addTargets: any[] } | null, error?: string | null, flush?: boolean }} */
  let { related, error = null, flush = false } = $props();

  let chosen = $state('');
  /** Bumped after an add so the picker forgets the record just linked. */
  let added = $state(0);
  let picked = $state(0);
  let targets = $derived(related?.addTargets ?? []);
  let current = $derived(
    targets.find((t) => `${t.object.key}:${t.field.key}` === chosen) ?? targets[0] ?? null
  );
  let selectedKey = $derived(current ? `${current.object.key}:${current.field.key}` : '');
  const uid = $props.id();
</script>

{#if related}
  <section class="rel" aria-label="Related">
    <div class="v2-label" style="margin:{flush ? '0' : '22px'} 0 10px">Related</div>
    <div class="v2-card rel-card">
      {#if error}
        <p class="v2-error" role="alert" style="margin:0 0 12px">{error}</p>
      {/if}

      {#each related.groups as g (`${g.object.key}:${g.field.key}`)}
        <div class="rel-group">
          <div class="rel-head">{g.object.label}: {g.field.label}</div>
          <ul class="rel-list">
            {#each g.records as r (r.id)}
              <li class="rel-row">
                <a href={resolve(asInternalPath(recordHref(`obj:${g.object.key}`, r.id) ?? '/'))}>
                  {r.name}
                </a>
                {#if g.removable}
                  <form method="POST" action="?/relatedRemove" use:enhance>
                    <input type="hidden" name="record" value={r.id} />
                    <input type="hidden" name="field" value={g.field.key} />
                    <button
                      type="submit"
                      class="v2-btn rel-x"
                      aria-label="Remove {r.name} from {g.object.label}: {g.field.label}"
                    >
                      <X />
                    </button>
                  </form>
                {/if}
              </li>
            {/each}
          </ul>
        </div>
      {/each}

      {#if targets.length > 0 && current}
        {#key page.params.id}
          <form
            method="POST"
            action="?/relatedAdd"
            class="rel-add"
            use:enhance={() =>
              async ({ result, update }) => {
                await update({ reset: false });
                if (result.type === 'success') added++;
              }}
          >
            <label class="v2-label" for="{uid}-to">Add to</label>
            <select
              id="{uid}-to"
              class="v2-input"
              name="field"
              value={selectedKey}
              onchange={(e) => (chosen = e.currentTarget.value)}
            >
              {#each targets as t (`${t.object.key}:${t.field.key}`)}
                <option value="{t.object.key}:{t.field.key}">
                  {t.object.label}: {t.field.label}
                </option>
              {/each}
            </select>
            {#key `${current.object.key}:${added}`}
              <RecordPicker
                name="record"
                target="obj:{current.object.key}"
                label="Record to add"
                bind:picked
              />
            {/key}
            <button type="submit" class="v2-btn" disabled={picked === 0}>Add</button>
          </form>
        {/key}
      {/if}
    </div>
  </section>
{/if}

<style>
  .rel-card {
    padding: 12px 16px;
  }
  .rel-group + .rel-group {
    margin-top: 14px;
  }
  .rel-head {
    font-weight: 600;
    font-size: 13px;
    margin-bottom: 6px;
  }
  .rel-list {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .rel-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    min-height: 44px;
  }
  .rel-x {
    min-width: 44px;
    min-height: 44px;
    justify-content: center;
  }
  .rel-add {
    display: grid;
    gap: 8px;
  }
  .rel-group + .rel-add {
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid var(--v2-line, rgba(0, 0, 0, 0.08));
  }
  .rel-add :global(.v2-btn) {
    justify-self: start;
    min-height: 44px;
  }
</style>
