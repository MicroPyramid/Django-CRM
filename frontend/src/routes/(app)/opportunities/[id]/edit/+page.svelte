<script>
  import { goto } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Loader2 } from '@lucide/svelte';

  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import { FormShell } from '$lib/components/ui/form-shell/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { OPPORTUNITY_STAGES, OPPORTUNITY_SOURCES, CURRENCY_CODES } from '$lib/constants/filters.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const opp = $derived(data?.opportunity);
  const initial = $derived(form?.values || {});

  const stageChoices = OPPORTUNITY_STAGES.filter((s) => s.value !== 'ALL');
  const sourceChoices = OPPORTUNITY_SOURCES.filter((s) => s.value !== '');
  const currencyChoices = CURRENCY_CODES.filter((c) => c.value !== '');

  let submitting = $state(false);

  /** @type {import('@sveltejs/kit').SubmitFunction} */
  function handleSubmit() {
    submitting = true;
    return async ({ result, update }) => {
      submitting = false;
      if (result.type === 'redirect') {
        toast.success('Opportunity updated');
        await update();
      } else if (result.type === 'failure') {
        toast.error(/** @type {any} */ (result.data)?.error || 'Failed to update');
        await update({ reset: false });
      }
    };
  }

  function fv(/** @type {string} */ key, /** @type {any} */ fallback) {
    if (initial[key] !== undefined && initial[key] !== null) return initial[key];
    return fallback ?? '';
  }
</script>

<svelte:head>
  <title>{opp?.name ? `Edit ${opp.name}` : 'Edit opportunity'} - BottleCRM</title>
</svelte:head>

<PageHeader
  title={opp?.name ? `Edit ${opp.name}` : 'Edit opportunity'}
  breadcrumb={[
    { label: 'Opportunities', href: '/opportunities' },
    { label: opp?.name || 'Opportunity', href: opp?.id ? `/opportunities/${opp.id}` : '/opportunities' },
    { label: 'Edit' }
  ]}
/>

<FormShell errorMessage={form?.error || ''} useEnhance={handleSubmit}>
  {#snippet children()}
    <section class="flex flex-col gap-3">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--text-subtle)]">Basics</h3>

      <div class="flex flex-col gap-1.5">
        <Label for="opp-name">Name <span class="text-[color:var(--red)]">*</span></Label>
        <Input id="opp-name" name="name" required maxlength="64"
               value={fv('name', opp?.name)} placeholder="e.g. Acme Q3 expansion" />
      </div>

      <div class="flex flex-col gap-1.5">
        <Label for="opp-stage">Stage</Label>
        <select id="opp-stage" name="stage"
                class="flex h-9 w-full rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-input)] px-3 text-[13.5px] text-[color:var(--text)] outline-none hover:border-[color:var(--border-strong)] focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]">
          {#each stageChoices as opt (opt.value)}
            <option value={opt.value} selected={opt.value === fv('stage', opp?.stage)}>{opt.label}</option>
          {/each}
        </select>
      </div>
    </section>

    <section class="flex flex-col gap-3">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--text-subtle)]">Deal value</h3>

      <div class="grid grid-cols-[1fr_140px] gap-3">
        <div class="flex flex-col gap-1.5">
          <Label for="opp-amount">Amount</Label>
          <Input id="opp-amount" name="amount" type="number" min="0" step="0.01"
                 value={fv('amount', opp?.amount)} placeholder="0.00" />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="opp-currency">Currency</Label>
          <select id="opp-currency" name="currency"
                  class="flex h-9 w-full rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-input)] px-3 text-[13.5px] text-[color:var(--text)] outline-none hover:border-[color:var(--border-strong)] focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]">
            {#each currencyChoices as c (c.value)}
              <option value={c.value} selected={c.value === fv('currency', opp?.currency || 'USD')}>{c.value}</option>
            {/each}
          </select>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1.5">
          <Label for="opp-probability">Probability</Label>
          <Input id="opp-probability" name="probability" type="number" min="0" max="100" step="1"
                 value={fv('probability', opp?.probability)} placeholder="0–100" />
          <span class="text-[11.5px] text-[color:var(--text-subtle)]">Percent likelihood of closing.</span>
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="opp-close-date">Close date</Label>
          <Input id="opp-close-date" name="closeDate" type="date" value={fv('closeDate', opp?.close_date)} />
        </div>
      </div>
    </section>

    <section class="flex flex-col gap-3">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--text-subtle)]">Detail</h3>

      <div class="flex flex-col gap-1.5">
        <Label for="opp-source">Lead source</Label>
        <select id="opp-source" name="leadSource"
                class="flex h-9 w-full rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-input)] px-3 text-[13.5px] text-[color:var(--text)] outline-none hover:border-[color:var(--border-strong)] focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]">
          <option value="" selected={!fv('leadSource', opp?.lead_source)}>Not specified</option>
          {#each sourceChoices as opt (opt.value)}
            <option value={opt.value} selected={opt.value === fv('leadSource', opp?.lead_source)}>{opt.label}</option>
          {/each}
        </select>
      </div>

      <div class="flex flex-col gap-1.5">
        <Label for="opp-description">Description</Label>
        <textarea id="opp-description" name="description" rows="5"
                  placeholder="Notes about the deal, context for the team..."
                  class="flex w-full resize-y rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-input)] px-3 py-2 text-[13.5px] text-[color:var(--text)] outline-none hover:border-[color:var(--border-strong)] focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]">{fv('description', opp?.description)}</textarea>
      </div>
    </section>
  {/snippet}

  {#snippet actions()}
    <Button type="button" variant="ghost" onclick={() => goto(opp?.id ? `/opportunities/${opp.id}` : '/opportunities')}>
      Cancel
    </Button>
    <Button type="submit" disabled={submitting}>
      {#if submitting}<Loader2 class="mr-1 size-3.5 animate-spin" />{/if}
      Save changes
    </Button>
  {/snippet}
</FormShell>
