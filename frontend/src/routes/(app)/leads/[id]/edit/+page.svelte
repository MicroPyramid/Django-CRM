<script>
  import { goto } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Loader2 } from '@lucide/svelte';

  import PageHeader from '$lib/components/layout/PageHeader.svelte';
  import { FormShell } from '$lib/components/ui/form-shell/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { LEAD_STATUSES, LEAD_SOURCES, LEAD_RATINGS, CURRENCY_CODES } from '$lib/constants/filters.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const lead = $derived(data?.lead);
  const initial = $derived(form?.values || {});

  const displayName = $derived(
    [lead?.first_name, lead?.last_name].filter(Boolean).join(' ') ||
    lead?.email ||
    lead?.title ||
    'Lead'
  );

  const statusChoices = LEAD_STATUSES.filter((s) => s.value !== 'ALL');
  const sourceChoices = LEAD_SOURCES.filter((s) => s.value !== 'ALL');
  const ratingChoices = LEAD_RATINGS.filter((r) => r.value !== 'ALL');
  const currencyChoices = CURRENCY_CODES.filter((c) => c.value !== '');

  let submitting = $state(false);

  /** @type {import('@sveltejs/kit').SubmitFunction} */
  function handleSubmit() {
    submitting = true;
    return async ({ result, update }) => {
      submitting = false;
      if (result.type === 'redirect') {
        toast.success('Lead updated');
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

  /** Normalize status: backend stores "in process", constants use "IN_PROCESS" */
  function normalizeStatus(/** @type {any} */ value) {
    return (value || '').toString().toUpperCase().replace(/\s+/g, '_');
  }

  /** Normalize rating: backend stores lowercase */
  function normalizeRating(/** @type {any} */ value) {
    return (value || '').toString().toUpperCase();
  }
</script>

<svelte:head>
  <title>Edit {displayName} - BottleCRM</title>
</svelte:head>

<PageHeader
  title="Edit {displayName}"
  breadcrumb={[
    { label: 'Leads', href: '/leads' },
    { label: displayName, href: lead?.id ? `/leads/${lead.id}` : '/leads' },
    { label: 'Edit' }
  ]}
/>

<FormShell errorMessage={form?.error || ''} useEnhance={handleSubmit}>
  {#snippet children()}
    <!-- Section 1: Basics -->
    <section class="flex flex-col gap-3">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--text-subtle)]">Basics</h3>

      <div class="flex flex-col gap-1.5">
        <Label for="lead-title">Title <span class="text-[color:var(--red)]">*</span></Label>
        <Input id="lead-title" name="title" required maxlength="200"
               value={fv('title', lead?.title)} placeholder="Lead title" />
      </div>

      <div class="grid grid-cols-[100px_1fr_1fr] gap-3">
        <div class="flex flex-col gap-1.5">
          <Label for="lead-salutation">Salutation</Label>
          <select id="lead-salutation" name="salutation"
                  class="flex h-9 w-full rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-input)] px-3 text-[13px] text-[color:var(--text)] outline-none hover:border-[color:var(--border-strong)] focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]">
            <option value="" selected={!fv('salutation', lead?.salutation)}></option>
            {#each ['Mr.', 'Mrs.', 'Ms.', 'Dr.'] as sal (sal)}
              <option value={sal} selected={sal === fv('salutation', lead?.salutation)}>{sal}</option>
            {/each}
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-first-name">First name</Label>
          <Input id="lead-first-name" name="firstName" maxlength="50"
                 value={fv('firstName', lead?.first_name)} />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-last-name">Last name</Label>
          <Input id="lead-last-name" name="lastName" maxlength="50"
                 value={fv('lastName', lead?.last_name)} />
        </div>
      </div>
    </section>

    <!-- Section 2: Contact -->
    <section class="flex flex-col gap-3">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--text-subtle)]">Contact</h3>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1.5">
          <Label for="lead-email">Email</Label>
          <Input id="lead-email" name="email" type="email" maxlength="254"
                 value={fv('email', lead?.email)} />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-phone">Phone</Label>
          <Input id="lead-phone" name="phone" type="tel" maxlength="20"
                 value={fv('phone', lead?.phone)} />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <Label for="lead-job-title">Job title</Label>
        <Input id="lead-job-title" name="jobTitle" maxlength="100"
               value={fv('jobTitle', lead?.job_title)} />
      </div>
    </section>

    <!-- Section 3: Company -->
    <section class="flex flex-col gap-3">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--text-subtle)]">Company</h3>

      <div class="flex flex-col gap-1.5">
        <Label for="lead-company">Company</Label>
        <Input id="lead-company" name="company" maxlength="255"
               value={fv('company', lead?.company_name)} />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1.5">
          <Label for="lead-website">Website</Label>
          <Input id="lead-website" name="website" type="url" maxlength="255" placeholder="https://"
                 value={fv('website', lead?.website)} />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-linkedin">LinkedIn</Label>
          <Input id="lead-linkedin" name="linkedinUrl" type="url" maxlength="255" placeholder="https://linkedin.com/in/..."
                 value={fv('linkedinUrl', lead?.linkedin_url)} />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <Label for="lead-industry">Industry</Label>
        <Input id="lead-industry" name="industry" maxlength="100" placeholder="e.g. Software, Healthcare"
               value={fv('industry', lead?.industry)} />
      </div>
    </section>

    <!-- Section 4: Classification -->
    <section class="flex flex-col gap-3">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--text-subtle)]">Classification</h3>

      <div class="grid grid-cols-3 gap-3">
        <div class="flex flex-col gap-1.5">
          <Label for="lead-status">Status</Label>
          <select id="lead-status" name="status"
                  class="flex h-9 w-full rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-input)] px-3 text-[13px] text-[color:var(--text)] outline-none hover:border-[color:var(--border-strong)] focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]">
            {#each statusChoices as opt (opt.value)}
              <option value={opt.value} selected={opt.value === normalizeStatus(fv('status', lead?.status))}>{opt.label}</option>
            {/each}
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-source">Source</Label>
          <select id="lead-source" name="source"
                  class="flex h-9 w-full rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-input)] px-3 text-[13px] text-[color:var(--text)] outline-none hover:border-[color:var(--border-strong)] focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]">
            <option value="">—</option>
            {#each sourceChoices as opt (opt.value)}
              <option value={opt.value} selected={opt.value === fv('source', lead?.source)}>{opt.label}</option>
            {/each}
          </select>
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-rating">Rating</Label>
          <select id="lead-rating" name="rating"
                  class="flex h-9 w-full rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-input)] px-3 text-[13px] text-[color:var(--text)] outline-none hover:border-[color:var(--border-strong)] focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]">
            <option value="">—</option>
            {#each ratingChoices as opt (opt.value)}
              <option value={opt.value} selected={opt.value === normalizeRating(fv('rating', lead?.rating))}>{opt.label}</option>
            {/each}
          </select>
        </div>
      </div>
    </section>

    <!-- Section 5: Opportunity -->
    <section class="flex flex-col gap-3">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--text-subtle)]">Opportunity</h3>

      <div class="grid grid-cols-[1fr_140px] gap-3">
        <div class="flex flex-col gap-1.5">
          <Label for="lead-opp-amount">Estimated value</Label>
          <Input id="lead-opp-amount" name="opportunityAmount" type="number" min="0" step="0.01"
                 value={fv('opportunityAmount', lead?.opportunity_amount)} placeholder="0.00" />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-currency">Currency</Label>
          <select id="lead-currency" name="currency"
                  class="flex h-9 w-full rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-input)] px-3 text-[13px] text-[color:var(--text)] outline-none hover:border-[color:var(--border-strong)] focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]">
            {#each currencyChoices as c (c.value)}
              <option value={c.value} selected={c.value === fv('currency', lead?.currency || 'USD')}>{c.value}</option>
            {/each}
          </select>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1.5">
          <Label for="lead-probability">Probability</Label>
          <Input id="lead-probability" name="probability" type="number" min="0" max="100" step="1"
                 value={fv('probability', lead?.probability)} placeholder="0–100" />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-close-date">Close date</Label>
          <Input id="lead-close-date" name="closeDate" type="date"
                 value={fv('closeDate', lead?.close_date)} />
        </div>
      </div>
    </section>

    <!-- Section 6: Address -->
    <section class="flex flex-col gap-3">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--text-subtle)]">Address</h3>

      <div class="flex flex-col gap-1.5">
        <Label for="lead-address-line">Street</Label>
        <Input id="lead-address-line" name="addressLine" maxlength="255"
               value={fv('addressLine', lead?.address_line)} />
      </div>

      <div class="grid grid-cols-[1fr_120px_140px] gap-3">
        <div class="flex flex-col gap-1.5">
          <Label for="lead-city">City</Label>
          <Input id="lead-city" name="city" maxlength="100"
                 value={fv('city', lead?.city)} />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-state">State</Label>
          <Input id="lead-state" name="state" maxlength="100"
                 value={fv('state', lead?.state)} />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-postcode">Postcode</Label>
          <Input id="lead-postcode" name="postcode" maxlength="20"
                 value={fv('postcode', lead?.postcode)} />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <Label for="lead-country">Country</Label>
        <Input id="lead-country" name="country" maxlength="100"
               value={fv('country', lead?.country)} />
      </div>
    </section>

    <!-- Section 7: Activity -->
    <section class="flex flex-col gap-3">
      <h3 class="text-[11px] font-semibold uppercase tracking-wider text-[color:var(--text-subtle)]">Activity</h3>

      <div class="grid grid-cols-2 gap-3">
        <div class="flex flex-col gap-1.5">
          <Label for="lead-last-contacted">Last contacted</Label>
          <Input id="lead-last-contacted" name="lastContacted" type="date"
                 value={fv('lastContacted', lead?.last_contacted)} />
        </div>
        <div class="flex flex-col gap-1.5">
          <Label for="lead-next-follow-up">Next follow-up</Label>
          <Input id="lead-next-follow-up" name="nextFollowUp" type="date"
                 value={fv('nextFollowUp', lead?.next_follow_up)} />
        </div>
      </div>

      <div class="flex flex-col gap-1.5">
        <Label for="lead-description">Description</Label>
        <textarea id="lead-description" name="description" rows="5"
                  class="flex w-full resize-y rounded-[var(--r-md)] border border-[color:var(--border)] bg-[color:var(--bg-input)] px-3 py-2 text-[13px] text-[color:var(--text)] outline-none hover:border-[color:var(--border-strong)] focus-visible:border-[color:var(--text)] focus-visible:shadow-[0_0_0_3px_var(--focus-ring)]">{fv('description', lead?.description)}</textarea>
      </div>
    </section>
  {/snippet}

  {#snippet actions()}
    <Button type="button" variant="ghost" onclick={() => goto(lead?.id ? `/leads/${lead.id}` : '/leads')}>
      Cancel
    </Button>
    <Button type="submit" disabled={submitting}>
      {#if submitting}<Loader2 class="mr-1 size-3.5 animate-spin" />{/if}
      Save changes
    </Button>
  {/snippet}
</FormShell>
