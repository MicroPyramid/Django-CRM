<script>
  /**
   * Your own API tokens.
   *
   * THE PAGE THAT WAS MISSING
   * `/api/profile/tokens/` has always been self-scoped and open to any member,
   * and until now nothing in either client called it. The only token page
   * either app had was the org-wide oversight list, which 403s a member on the
   * read, so a rep who wanted to script against their own CRM had to be handed
   * a token by an admin or reach for curl.
   *
   * WHAT IS DELIBERATELY ABSENT
   * No owner column, because every row is yours. No org totals, because you
   * cannot see anybody else's rows to count. No "revoke them all", because that
   * is an offboarding action and offboarding is the admin's page. Copying the
   * oversight layout here would draw an org-wide surface out of a self-scoped
   * one, and the first person to notice would be whoever tried it.
   *
   * A TOKEN VALUE IS SHOWN ONCE
   * The server keeps a SHA-256 hash and a 13-character prefix, so there is
   * nothing to re-display later even if somebody asks. The reveal below is the
   * only place a full value appears, and it is gone on the next load.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import NextAction from '$lib/v2/components/NextAction.svelte';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import { count, relativeDays, shortDate } from '$lib/v2/format.js';
  import { resolve } from '$app/paths';
  import { enhance } from '$app/forms';
  import { Plus, KeyRound, ShieldAlert, Copy, Check } from '@lucide/svelte';
  import { tokenStatus, staleness, scopeSummary, EXPIRY_CHOICES } from '$lib/v2/token-rules.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let creating = $state(false);
  let busy = $state(false);
  let copied = $state(false);

  const working = () => {
    busy = true;
    return async (/** @type {any} */ { update }) => {
      await update();
      busy = false;
    };
  };

  const createSubmit = () => {
    busy = true;
    return async (/** @type {any} */ { update, result }) => {
      await update();
      busy = false;
      if (result?.type === 'success' && result?.data?.created) creating = false;
    };
  };

  /** @param {string} value */
  async function copyToken(value) {
    try {
      await navigator.clipboard.writeText(value);
      copied = true;
      setTimeout(() => (copied = false), 1600);
    } catch {
      // Clipboard blocked (no https / no permission). The value is on screen to
      // select by hand, and there is nothing worth alarming over.
    }
  }
</script>

<PageHeader title="Your API tokens">
  {#snippet crumb()}<a href={resolve('/profile')}>Profile</a> ›{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(data.live)}</span>
    live of <span class="v2-num">{count(data.tokens.length)}</span> you have issued
  {/snippet}
  {#snippet actions()}
    <button class="v2-btn v2-btn-primary" onclick={() => (creating = !creating)}>
      <Plus />New token
    </button>
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    {#if form?.created?.token}
      <!-- The one and only time this value is shown. -->
      <div
        class="v2-card"
        style="padding:15px 16px;margin-bottom:18px;border-color:color-mix(in srgb, var(--v2-moss) 40%, var(--v2-line))"
      >
        <div style="font-weight:650;font-size:13px">
          “{form.created.name}” created, copy it now
        </div>
        <p class="v2-sub" style="font-size:12px;margin:4px 0 10px">
          This is the only time the full token is shown. Store it somewhere safe; it cannot be
          retrieved again.
        </p>
        <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
          <code
            class="v2-num"
            style="flex:1;min-width:200px;background:var(--v2-bg-sunk);border:1px solid var(--v2-line);border-radius:var(--v2-radius);padding:9px 11px;font-size:12.5px;word-break:break-all"
          >
            {form.created.token}
          </code>
          <button class="v2-btn v2-btn-sm" onclick={() => copyToken(form.created.token)}>
            {#if copied}<Check size={13} />Copied{:else}<Copy size={13} />Copy{/if}
          </button>
        </div>
      </div>
    {/if}

    {#if form?.error}
      <div style="margin-bottom:16px">
        <NextAction label="That did not work" text={form.error} tone="rust" />
      </div>
    {/if}

    {#if creating}
      <form
        method="POST"
        action="?/create"
        use:enhance={createSubmit}
        class="v2-card"
        style="padding:14px 15px;margin-bottom:18px;display:flex;gap:10px;align-items:flex-end;flex-wrap:wrap"
      >
        <div style="flex:1;min-width:200px">
          <label class="v2-label" for="token-name" style="display:block;margin-bottom:4px">
            What is this token for?
          </label>
          <input
            id="token-name"
            name="name"
            required
            maxlength="255"
            class="v2-input"
            style="width:100%"
            placeholder="e.g. My export script"
          />
        </div>
        <div style="flex:1;min-width:160px">
          <label class="v2-label" for="token-access" style="display:block;margin-bottom:4px">
            Access
          </label>
          <select id="token-access" name="access" class="v2-input" style="width:100%">
            <option value="read" selected>Read only</option>
            <!-- "Everything you can", not "everything": a token acts as you and
                 inherits your role, so it can never reach past what you can. -->
            <option value="full">Everything you can</option>
          </select>
        </div>
        <div style="flex:1;min-width:140px">
          <label class="v2-label" for="token-expiry" style="display:block;margin-bottom:4px">
            Expires
          </label>
          <select id="token-expiry" name="expiry" class="v2-input" style="width:100%">
            {#each EXPIRY_CHOICES as choice (choice.value)}
              <option value={choice.value}>{choice.label}</option>
            {/each}
          </select>
        </div>
        <button class="v2-btn v2-btn-primary" disabled={busy}>Create token</button>
        <button type="button" class="v2-btn" disabled={busy} onclick={() => (creating = false)}>
          Cancel
        </button>
        {#if form?.create?.error}
          <p
            class="v2-sub"
            style="color:var(--v2-rust);font-size:12px;flex-basis:100%;margin:2px 0 0"
          >
            {form.create.error}
          </p>
        {/if}
      </form>
    {/if}

    {#if data.tokens.length === 0}
      <EmptyState
        title="No tokens yet"
        body="A token lets a script, an integration or an agent call the API as you, with your role and your org. Create one when you need it, and revoke it the moment you do not."
      >
        {#snippet icon()}<KeyRound size={21} />{/snippet}
        {#snippet actions()}
          <button class="v2-btn v2-btn-primary" onclick={() => (creating = true)}>
            Create your first token
          </button>
        {/snippet}
      </EmptyState>
    {:else}
      <div class="v2-table-wrap">
        <table class="v2-table">
          <thead>
            <tr>
              <th>Token</th>
              <th data-m="hide">Can do</th>
              <th data-m="hide">Last used</th>
              <th data-m="hide">Expires</th>
              <th class="v2-r">State</th>
            </tr>
          </thead>
          <tbody>
            {#each data.tokens as t (t.id)}
              {@const s = tokenStatus(t)}
              {@const stale = staleness(t)}
              <tr style={t.is_live ? '' : 'opacity:.55'}>
                <td data-m="title">
                  <span class="v2-table-primary">{t.name}</span>
                  <!-- The prefix, and only the prefix. The server keeps a hash. -->
                  <span class="v2-table-secondary v2-num" style="display:block">
                    {t.token_prefix}…
                  </span>
                </td>
                <td data-m="meta">
                  <span class="v2-sub" style="font-size:12px">
                    {scopeSummary(t, { ownerLabel: 'you' })}
                  </span>
                </td>
                <td data-m="meta">
                  {#if t.last_used_at}
                    {relativeDays(t.last_used_at)}
                  {:else}
                    <span class="v2-muted">never used</span>
                  {/if}
                  {#if stale}
                    <span
                      class="v2-table-secondary"
                      style="display:block;color:var(--v2-clay);font-weight:600"
                    >
                      {stale}
                    </span>
                  {/if}
                </td>
                <td data-m="hide">
                  {#if t.expires_at}
                    {shortDate(t.expires_at)}
                  {:else}
                    <span class="v2-sub">never expires</span>
                  {/if}
                </td>
                <td class="v2-r" data-m="tag">
                  <span style="display:inline-flex;gap:7px;align-items:center">
                    <Pill tone={s.tone}>{s.label}</Pill>
                    {#if t.is_live}
                      <form method="POST" action="?/revoke" use:enhance={working}>
                        <input type="hidden" name="id" value={t.id} />
                        <button class="v2-btn v2-btn-sm" disabled={busy}>Revoke</button>
                      </form>
                    {/if}
                  </span>
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}

    <div
      style="display:flex;gap:10px;align-items:flex-start;margin-top:20px;padding:14px 16px;border:1px solid var(--v2-line);border-radius:var(--v2-radius)"
    >
      <ShieldAlert size={16} style="color:var(--v2-clay);flex:none;margin-top:1px" />
      <div>
        <div style="font-weight:600;font-size:13px">A token is you</div>
        <p class="v2-sub" style="font-size:12px;margin:4px 0 0">
          It authenticates as your profile and inherits your role and your org, so anyone holding it
          can do what you can. Keep it out of shared repositories and screenshots, and revoke it
          here the moment it is not needed. An admin can see and revoke it too.
        </p>
      </div>
    </div>
  </div>
</div>
