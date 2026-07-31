<script>
  import '../../../../app.css';
  import '$lib/v2/styles/v2.css';
  import { enhance } from '$app/forms';
  import { goto } from '$app/navigation';
  import imgLogo from '$lib/assets/images/logo.png';
  import { ArrowLeft, Check, AlertCircle } from '@lucide/svelte';

  let { form } = $props();

  let isSubmitting = $state(false);

  // Handle form submission success - redirect after showing success message
  $effect(() => {
    if (form?.data) {
      const timer = setTimeout(() => {
        goto('/org');
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
    <a href="/" class="v2-auth-brand">
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
      <a href="/org" style="display:inline-flex;align-items:center;gap:5px">
        <ArrowLeft size={13} /> Back to organisations
      </a>
    </div>
  </div>
</div>
