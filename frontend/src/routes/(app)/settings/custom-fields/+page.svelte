<script>
  /**
   * Fields this organisation added to records that shipped without them.
   *
   * Grouped by the record they extend, because that is how anyone looks for
   * one; "what do we collect on a ticket" is the question, not "show me all
   * 40 definitions sorted by created date".
   *
   * The number that earns its place here is `records_missing_value`. Marking a
   * field required only binds writes from that moment; records saved before it
   * existed keep their gap and nothing backfills them. So "Required" on a
   * field with 23 records missing a value is a promise the data does not keep,
   * and reporting on that field will quietly exclude or mis-bucket those 23.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import StatCard from '$lib/v2/components/StatCard.svelte';
  import { count } from '$lib/v2/format.js';
  import { FIELD_TYPE_LABEL, TARGET_MODEL_LABEL } from '$lib/v2/enums.js';
  import { Plus, TriangleAlert, Filter } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let totals = $derived(data.totals);

  /** One group per extended model, fields kept in display_order. */
  let groups = $derived.by(() => {
    /** @type {Map<string, any[]>} */
    const byModel = new Map();
    for (const f of data.fields) {
      byModel.set(f.target_model, [...(byModel.get(f.target_model) ?? []), f]);
    }
    return [...byModel.entries()].map(([model, fields]) => ({
      model,
      label: TARGET_MODEL_LABEL[model] ?? model,
      fields: [...fields].sort((a, b) => a.display_order - b.display_order)
    }));
  });

  let gaps = $derived(data.fields.filter((f) => f.is_required && f.records_missing_value > 0));
</script>

<PageHeader title="Custom fields">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(totals.active)}</span> fields across
    <span class="v2-num">{count(totals.models_extended)}</span> record types
  {/snippet}
  {#snippet actions()}
    <button class="v2-btn v2-btn-primary"><Plus />New field</button>
  {/snippet}
</PageHeader>

<div class="v2-pad" style="padding-top:16px;flex:none">
  <div class="v2-stats">
    <StatCard label="Active fields" value={count(totals.active)} tone="ink" />
    <StatCard label="Record types extended" value={count(totals.models_extended)} tone="slate" />
    <StatCard
      label="Required with gaps"
      value={count(totals.required_with_gaps)}
      tone={totals.required_with_gaps > 0 ? 'clay' : 'slate'}
      detail="Records that predate the rule"
    />
    <StatCard label="Turned off" value={count(totals.count - totals.active)} tone="slate" />
  </div>
</div>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-bottom:32px">
    {#if gaps.length}
      <div class="v2-cf-banner">
        <TriangleAlert size={16} style="color:var(--v2-clay);flex:none;margin-top:1px" />
        <div>
          <div style="font-weight:600;font-size:13px">
            Required does not mean every record has one
          </div>
          <p class="v2-sub" style="font-size:12px;margin:4px 0 0;line-height:1.5">
            {gaps
              .map(
                (f) =>
                  `${f.label} is missing on ${f.records_missing_value} ${(TARGET_MODEL_LABEL[f.target_model] ?? f.target_model).toLowerCase()}`
              )
              .join('; ')}. Marking a field required binds new writes only, nothing goes back and
            fills in what was saved before.
          </p>
        </div>
      </div>
    {/if}

    <div class="v2-cf-groups">
      {#each groups as g (g.model)}
        <div>
          <div class="v2-label" style="margin-bottom:10px">On {g.label.toLowerCase()}</div>
          <div class="v2-card" style="overflow:hidden">
            {#each g.fields as f (f.id)}
              <div class="v2-setting" style="opacity:{f.is_active ? 1 : 0.6}">
                <div class="v2-setting-body">
                  <div style="display:flex;gap:7px;align-items:baseline;flex-wrap:wrap">
                    <b>{f.label}</b>
                    <code class="v2-cf-key">{f.key}</code>
                  </div>
                  <span class="v2-sub" style="font-size:11.5px">
                    {FIELD_TYPE_LABEL[f.field_type]}{#if f.options}
                      · {f.options.map((o) => o.label).join(', ')}
                    {/if}
                    {#if f.is_required && f.records_missing_value > 0}
                      · <span style="color:var(--v2-clay)">
                        {count(f.records_missing_value)} without a value
                      </span>
                    {/if}
                  </span>
                </div>

                {#if f.is_filterable}
                  <!-- Filterable is the difference between a field you can
                       search a list by and one you can only read once you have
                       already opened the record. -->
                  <Filter size={13} style="color:var(--v2-slate);flex:none" />
                {/if}
                {#if !f.is_active}
                  <Pill tone="slate">Off</Pill>
                {:else if f.is_required}
                  <Pill tone="clay">Required</Pill>
                {/if}
              </div>
            {/each}
          </div>
        </div>
      {/each}
    </div>

    <p class="v2-sub" style="font-size:11.5px;margin-top:16px;max-width:66ch">
      A field marked with the filter icon can be used to narrow a list; the rest are readable only
      on the record itself. Turning a field off stops it being collected and hides it, and leaves
      the values already stored on each record untouched.
    </p>
  </div>
</div>

<style>
  .v2-cf-groups {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 20px 24px;
    align-items: start;
  }
  .v2-cf-key {
    font-family: var(--v2-mono);
    font-size: 11px;
    color: var(--v2-slate);
    background: var(--v2-hover);
    border-radius: 3px;
    padding: 1px 4px;
  }
  .v2-cf-banner {
    display: flex;
    gap: 11px;
    align-items: flex-start;
    padding: 14px 16px;
    margin-bottom: 18px;
    border: 1px solid var(--v2-line);
    border-radius: var(--v2-radius);
    background: var(--v2-card);
  }

  @media (max-width: 1000px) {
    .v2-cf-groups {
      grid-template-columns: 1fr;
    }
  }
</style>
