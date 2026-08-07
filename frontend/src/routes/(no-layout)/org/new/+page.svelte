<script>
  import { resolve } from '$app/paths';
  import '../../../../app.css';
  import '$lib/v2/styles/v2.css';
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation';
  import imgLogo from '$lib/assets/images/logo.png';
  import { ArrowLeft, Check, AlertCircle } from '@lucide/svelte';

  let { data, form } = $props();

  let packs = $derived(data?.packs ?? []);
  let timezones = $derived(data?.timezones ?? [{ name: 'UTC', label: 'UTC' }]);

  let isSubmitting = $state(false);

  // Prefilled from the browser, then corrected against the server's list. The
  // two vocabularies differ on aliases, so a detected name that the list does
  // not carry has to fall back rather than be selected: a select whose value
  // matches no option submits its first entry, which would put a new org in
  // Africa/Abidjan without anyone choosing it.
  //
  // Starts at UTC so the server-rendered form is correct without JavaScript;
  // the effect below narrows it to the user's own zone once the browser runs.
  let timezone = $state('UTC');

  $effect(() => {
    const detected = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (detected && timezones.some((z) => z.name === detected)) timezone = detected;
  });

  // Handle form submission success - redirect after showing success message
  $effect(() => {
    if (form?.data) {
      const timer = setTimeout(() => {
        goto(resolve('/org'));
      }, 1500);
      return () => clearTimeout(timer);
    }
  });
</script>

<svelte:head>
  <title>Create organisation · BottleCRM</title>
</svelte:head>

<div class="v2-root v2-auth">
  <div class="v2-auth-box">
    <a href={resolve('/')} class="v2-auth-brand">
      <img src={imgLogo} alt="" />
      <b>BottleCRM</b>
    </a>

    <div class="v2-auth-card">
      <div class="v2-auth-head">
        <h1>Create organisation</h1>
        <p>Set up a new workspace for your team.</p>
      </div>

      <form
        action="/org/new"
        method="POST"
        use:enhance={() => {
          isSubmitting = true;
          return async ({ update }) => {
            await update();
            isSubmitting = false;
          };
        }}
      >
        <div class="v2-field">
          <label for="org_name">Organisation name</label>
          <input
            type="text"
            id="org_name"
            name="org_name"
            class="v2-input"
            placeholder="e.g. Acme Inc."
            required
            disabled={isSubmitting || !!form?.data}
          />
          <p class="v2-hint">This becomes your workspace name in BottleCRM.</p>
        </div>

        <div class="v2-field">
          <label for="timezone">Time zone</label>
          <select
            id="timezone"
            name="timezone"
            class="v2-input"
            bind:value={timezone}
            disabled={isSubmitting || !!form?.data}
          >
            {#each timezones as zone (zone.name)}
              <option value={zone.name}>{zone.label}</option>
            {/each}
          </select>
          <p class="v2-hint">
            Sets when a day starts here, so "due today" and "overdue" mean what your team expects.
            You can change it later in Settings.
          </p>
        </div>

        {#if packs.length > 0}
          <fieldset class="v2-field pack-choice">
            <legend>What kind of business is this?</legend>
            <p class="v2-hint" style="margin-top:0">
              Sets up a starter pipeline, tags and fields for your industry. You can change
              everything later.
            </p>

            <label class="pack-opt">
              <input
                type="radio"
                name="vertical"
                value=""
                checked
                disabled={isSubmitting || !!form?.data}
              />
              <span class="pack-opt-body">
                <b>Skip for now</b>
                <span class="v2-hint" style="margin:0">Start with a blank workspace.</span>
              </span>
            </label>

            {#each packs as pack (pack.id)}
              <label class="pack-opt">
                <input
                  type="radio"
                  name="vertical"
                  value={pack.id}
                  disabled={isSubmitting || !!form?.data}
                />
                <span class="pack-opt-body">
                  <b>{pack.name}</b>
                  {#if pack.description}
                    <span class="v2-hint" style="margin:0">{pack.description}</span>
                  {/if}
                </span>
              </label>
            {/each}
          </fieldset>
        {/if}

        {#if form?.error}
          <div class="v2-auth-note v2-auth-note-bad" style="margin-bottom:14px">
            <AlertCircle />
            <div>
              <b>Couldn't create organisation</b>
              <div style="font-weight:400;margin-top:2px">
                {form.error.name || 'Please try again.'}
              </div>
            </div>
          </div>
        {/if}

        {#if form?.data}
          <div class="v2-auth-note v2-auth-note-ok" style="margin-bottom:14px">
            <Check />
            <div>
              <b>Organisation created</b>
              <div style="font-weight:400;margin-top:2px">Taking you to your workspaces…</div>
            </div>
          </div>
        {/if}

        <button
          type="submit"
          class="v2-btn v2-btn-primary v2-btn-block"
          disabled={isSubmitting || !!form?.data}
        >
          {#if isSubmitting}
            <span class="v2-spin"></span>
            <span>Creating…</span>
          {:else if form?.data}
            <Check size={15} />
            <span>Created</span>
          {:else}
            <span>Create organisation</span>
          {/if}
        </button>
      </form>
    </div>

    <div class="v2-auth-foot">
      <a href={resolve('/org')} style="display:inline-flex;align-items:center;gap:5px">
        <ArrowLeft size={13} /> Back to organisations
      </a>
    </div>
  </div>
</div>

<style>
  .pack-choice {
    border: 1px solid var(--v2-line-soft);
    border-radius: 8px;
    padding: 14px 16px;
  }
  .pack-choice legend {
    font-weight: 600;
    padding: 0 6px;
  }
  .pack-opt {
    display: flex;
    align-items: flex-start;
    gap: 9px;
    padding: 9px 10px;
    border: 1px solid var(--v2-line);
    border-radius: 8px;
    cursor: pointer;
  }
  .pack-opt + .pack-opt {
    margin-top: 7px;
  }
  .pack-opt:has(input:checked) {
    border-color: var(--v2-ember);
    background: var(--v2-ember-soft);
  }
  .pack-opt:has(input:disabled) {
    cursor: not-allowed;
    opacity: 0.65;
  }
  .pack-opt input[type='radio'] {
    margin-top: 2px;
    accent-color: var(--v2-ember);
    flex: none;
  }
  .pack-opt-body {
    display: flex;
    flex-direction: column;
    gap: 2px;
    min-width: 0;
  }
</style>
