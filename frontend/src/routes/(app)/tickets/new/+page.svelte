<script>
  import { resolve } from '$app/paths';
  /**
   * Raising a ticket.
   *
   * Deliberately short. A ticket that has just been raised has no history, no
   * closing date and nothing linked to it, so the only questions are what
   * happened, how bad it is, and who it is for.
   *
   * `?account=<id>` preselects the company, so "raise a ticket for this
   * account" arrives with the account already chosen.
   */
  import { tick, untrack } from 'svelte';
  import { enhance } from '$app/forms';
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import { ChevronRight, TriangleAlert } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form: result } = $props();

  // `untrack` so a re-render after a failed save does not throw away what the
  // person typed; `result.values` is the server's echo of the same fields.
  let form = $state(
    untrack(() => ({
      name: '',
      status: data.defaults.status,
      priority: data.defaults.priority,
      case_type: data.defaults.case_type,
      description: '',
      account: data.defaults.account ?? '',
      assigned_to: '',
      ...(result?.values ?? {})
    }))
  );
  let touched = $state(/** @type {Record<string, boolean>} */ ({}));
  let submitted = $state(false);

  let errors = $derived.by(() => {
    /** @type {Record<string, string>} */
    const e = {};
    const name = form.name.trim();
    if (!name) e.name = 'A ticket needs a subject.';
    // `Case.name` is max_length=64, short for a subject line, but it is the
    // column, and a 65th character is a 400 from the serializer.
    else if (name.length > 64)
      e.name = `Subjects are capped at 64 characters (this is ${name.length}).`;
    return e;
  });

  let valid = $derived(Object.keys(errors).length === 0);
  const show = (/** @type {string} */ field) => (touched[field] || submitted) && errors[field];

  /** @type {import('./$types').SubmitFunction} */
  const check = async ({ cancel }) => {
    submitted = true;
    if (!valid) {
      cancel();
      await tick();
      /** @type {HTMLElement | null} */
      const first = document.querySelector('[aria-invalid="true"]');
      first?.focus();
    }
  };
</script>

<PageHeader title="New ticket" center>
  {#snippet crumb()}
    <a href={resolve('/tickets')}>Tickets</a>
    <ChevronRight size={12} />
    <span>New</span>
  {/snippet}
  {#snippet sub()}
    What happened, how urgent it is, and who it is for.
  {/snippet}
</PageHeader>

<div class="v2-scroll v2-pad" style="padding-top:18px">
  <form class="v2-form" method="POST" action="?/create" use:enhance={check} novalidate>
    {#if result?.error}
      <div
        class="v2-next"
        style="background:color-mix(in srgb, var(--v2-rust) 9%, transparent);border-color:color-mix(in srgb, var(--v2-rust) 28%, transparent);margin-bottom:18px"
        role="alert"
      >
        <TriangleAlert size={17} style="color:var(--v2-rust);flex:none" />
        <div class="v2-next-body">
          <div style="font-weight:600">The server refused this ticket</div>
          <div class="v2-sub" style="margin-top:2px">{result.error}</div>
        </div>
      </div>
    {/if}

    <div class="v2-field">
      <label for="f-name">Subject</label>
      <input
        id="f-name"
        name="name"
        class="v2-input"
        bind:value={form.name}
        onblur={() => (touched.name = true)}
        aria-invalid={show('name') ? 'true' : undefined}
      />
      {#if show('name')}
        <p class="v2-error">{errors.name}</p>
      {:else}
        <!-- Worth saying up front, because it is an unusual rule for a
             helpdesk and the refusal is otherwise baffling: two tickets in one
             organisation cannot share a subject, ignoring capitals. -->
        <p class="v2-hint">Has to be unique in this organisation, ignoring capitals.</p>
      {/if}
    </div>

    <div class="triple">
      <div class="v2-field">
        <label for="f-priority">Priority</label>
        <select id="f-priority" name="priority" class="v2-input" bind:value={form.priority}>
          {#each data.priorities as p (p.value)}
            <option value={p.value}>{p.label}</option>
          {/each}
        </select>
        <p class="v2-hint">Sets the first-reply target.</p>
      </div>
      <div class="v2-field">
        <label for="f-type">Type</label>
        <select id="f-type" name="case_type" class="v2-input" bind:value={form.case_type}>
          <option value="">Not set</option>
          {#each data.caseTypes as t (t.value)}
            <option value={t.value}>{t.label}</option>
          {/each}
        </select>
      </div>
      <div class="v2-field">
        <label for="f-status">Status</label>
        <select id="f-status" name="status" class="v2-input" bind:value={form.status}>
          {#each data.statuses as s (s.value)}
            <option value={s.value}>{s.label}</option>
          {/each}
        </select>
      </div>
    </div>

    <div class="pair">
      <div class="v2-field">
        <label for="f-account">Account</label>
        <select id="f-account" name="account" class="v2-input" bind:value={form.account}>
          <option value="">Not linked</option>
          {#each data.accounts as a (a.id)}
            <option value={a.id}>{a.name}</option>
          {/each}
        </select>
        <p class="v2-hint">Cannot be changed later. The API makes it read-only after creation.</p>
      </div>
      <div class="v2-field">
        <label for="f-owner">Assignee</label>
        <select id="f-owner" name="assigned_to" class="v2-input" bind:value={form.assigned_to}>
          <option value="">Nobody</option>
          {#each data.owners as o (o.id)}
            <option value={o.id}>{o.name}</option>
          {/each}
        </select>
        <p class="v2-hint">Unassigned tickets still count against the clock.</p>
      </div>
    </div>

    <div class="v2-field">
      <label for="f-contacts">People affected</label>
      <select id="f-contacts" name="contacts" class="v2-input" multiple size="4">
        {#each data.contacts as c (c.id)}
          <option value={c.id}>{c.name}</option>
        {/each}
      </select>
      <p class="v2-hint">Optional. Hold ctrl or cmd to pick more than one.</p>
    </div>

    <div class="v2-field">
      <label for="f-desc">What happened</label>
      <textarea
        id="f-desc"
        name="description"
        class="v2-input"
        rows="4"
        bind:value={form.description}></textarea>
    </div>

    <div class="actions">
      <button class="v2-btn v2-btn-primary" type="submit">Raise ticket</button>
      <a class="v2-btn" href={resolve('/tickets')}>Cancel</a>
    </div>
  </form>
</div>

<style>
  .pair {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 14px;
  }
  .triple {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 14px;
  }
  .actions {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-top: 22px;
    padding-bottom: 40px;
  }
  @media (max-width: 720px) {
    .pair,
    .triple {
      grid-template-columns: 1fr;
    }
  }
</style>
