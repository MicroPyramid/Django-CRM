<script>
  /**
   * Canned replies.
   *
   * The body is the whole point of a macro, so it is on the page. V1 hides it
   * behind an edit dialog and lists titles, which means you cannot tell two
   * similarly-named macros apart without opening both.
   *
   * Placeholders are marked inline. `%customer_name%` is substituted by the
   * server; anything outside its seven supported tokens is left literal and
   * goes to the customer exactly as typed. That is the failure this page
   * exists to make visible: `%custmer_name%` has shipped twelve times.
   *
   * The body is org-authored text and is rendered as TEXT, split into
   * segments and placed in elements, never through {@html}. A canned reply is
   * a string a colleague wrote; putting it in the DOM as markup would make the
   * macro editor a stored-XSS form.
   */
  import PageHeader from '$lib/v2/components/PageHeader.svelte';
  import SettingsCrumb from '$lib/v2/components/SettingsCrumb.svelte';
  import Pill from '$lib/v2/components/Pill.svelte';
  import StatCard from '$lib/v2/components/StatCard.svelte';
  import { count, relativeDays } from '$lib/v2/format.js';
  import { MACRO_SCOPE_LABEL } from '$lib/v2/enums.js';
  import { Plus, TriangleAlert } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let totals = $derived(data.totals);
  let byUse = $derived([...data.macros].sort((a, b) => b.usage_count - a.usage_count));
  let orgMacros = $derived(byUse.filter((m) => m.scope === 'org'));
  let personalMacros = $derived(byUse.filter((m) => m.scope === 'personal'));

  /**
   * Split a body into text and placeholder segments for rendering.
   *
   * Whether a token is real is decided by the server's `unknown_placeholders`,
   * not by matching against a list kept here. The supported set lives in
   * `macros/render.py` precisely so clients cannot drift from it. A copy in
   * this file would eventually mark a working macro as broken.
   */
  function segments(macro) {
    const re = /%[a-zA-Z_][a-zA-Z0-9_]*%/g;
    const out = [];
    let last = 0;
    let m;
    while ((m = re.exec(macro.body)) !== null) {
      if (m.index > last) out.push({ text: macro.body.slice(last, m.index), token: false });
      out.push({
        text: m[0],
        token: true,
        known: !macro.unknown_placeholders.includes(m[0])
      });
      last = m.index + m[0].length;
    }
    if (last < macro.body.length) out.push({ text: macro.body.slice(last), token: false });
    return out;
  }
</script>

<PageHeader title="Macros">
  {#snippet crumb()}<SettingsCrumb />{/snippet}
  {#snippet sub()}
    <span class="v2-num">{count(totals.org)}</span> shared ·
    <span class="v2-num">{count(totals.personal)}</span> yours
  {/snippet}
  {#snippet actions()}
    <button class="v2-btn v2-btn-primary"><Plus />New macro</button>
  {/snippet}
</PageHeader>

<div class="v2-pad" style="padding-top:16px;flex:none">
  <div class="v2-stats">
    <StatCard label="Shared with everyone" value={count(totals.org)} tone="ink" />
    <StatCard label="Only yours" value={count(totals.personal)} tone="slate" />
    <StatCard
      label="Broken placeholders"
      value={count(totals.with_unknown_placeholders)}
      tone={totals.with_unknown_placeholders > 0 ? 'rust' : 'slate'}
      detail="Sent to customers as typed"
    />
    <StatCard label="Turned off" value={count(totals.inactive)} tone="slate" />
  </div>
</div>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-bottom:32px">
    <div class="v2-split-wide">
      <div>
        <div class="v2-label" style="margin-bottom:10px">Shared with everyone</div>
        <div style="display:flex;flex-direction:column;gap:9px;margin-bottom:24px">
          {#each orgMacros as m (m.id)}
            {@render macro(m)}
          {/each}
        </div>

        <div class="v2-label" style="margin-bottom:10px">Only yours</div>
        <div style="display:flex;flex-direction:column;gap:9px">
          {#each personalMacros as m (m.id)}
            {@render macro(m)}
          {/each}
        </div>
        <p class="v2-sub" style="font-size:11.5px;margin-top:11px">
          Personal macros are visible only to you. Nobody else in the organisation, admins included,
          sees this list.
        </p>
      </div>

      <div>
        <div class="v2-label" style="margin-bottom:10px">Placeholders that work</div>
        <div class="v2-card" style="overflow:hidden">
          {#each data.placeholders as p (p.token)}
            <div class="v2-setting" style="padding:10px 15px">
              <div class="v2-setting-body">
                <code class="v2-token">{p.token}</code>
              </div>
              <span class="v2-sub" style="font-size:11.5px;text-align:right">{p.resolves}</span>
            </div>
          {/each}
        </div>
        <p class="v2-sub" style="font-size:11.5px;margin-top:11px;line-height:1.5">
          These seven are the whole set. Anything else between percent signs is left exactly as
          written and goes out that way. The server does not guess, on purpose, so a typo is
          visible in the composer rather than a blank in the customer's inbox.
        </p>
      </div>
    </div>
  </div>
</div>

{#snippet macro(m)}
  <div class="v2-card" style="padding:14px 16px;opacity:{m.is_active ? 1 : 0.62}">
    <div style="display:flex;gap:10px;align-items:baseline;flex-wrap:wrap">
      <b style="font-size:13.5px">{m.title}</b>
      {#if !m.is_active}<Pill tone="slate">Off</Pill>{/if}
      {#if m.unknown_placeholders.length}<Pill tone="rust">Broken placeholder</Pill>{/if}
      <span class="v2-sub" style="font-size:11.5px;margin-left:auto">
        used <span class="v2-num">{count(m.usage_count)}</span> times · {relativeDays(m.updated_at)}
      </span>
    </div>

    <!--
      Text nodes and spans, never {@html}.

      Written on one line and held there by prettier-ignore. Svelte collapses
      the newline and indentation between two inline children into a single
      space, so a formatted version of this block renders "%customer_name% ,".
      A space the macro does not contain, in a preview whose whole job is to
      show exactly what the customer receives.
    -->
    <!-- prettier-ignore -->
    <p class="v2-macro-body">{#each segments(m) as seg, i (i)}{#if seg.token}<span class="v2-token" class:v2-token-bad={!seg.known}>{seg.text}</span>{:else}{seg.text}{/if}{/each}</p>

    {#if m.unknown_placeholders.length}
      <div class="v2-macro-flag">
        <TriangleAlert size={14} style="color:var(--v2-rust);flex:none" />
        <span>
          {m.unknown_placeholders.join(' and ')}
          {m.unknown_placeholders.length === 1 ? 'is not a placeholder' : 'are not placeholders'},
          {m.unknown_placeholders.length === 1 ? 'it goes' : 'they go'} to the customer exactly as written.
          {#if m.usage_count > 0}
            This macro has been sent
            <span class="v2-num">{count(m.usage_count)}</span> times.
          {/if}
        </span>
      </div>
    {/if}

    {#if m.owner}
      <div class="v2-sub" style="font-size:11px;margin-top:8px">
        {MACRO_SCOPE_LABEL[m.scope]} · {m.owner.name}
      </div>
    {/if}
  </div>
{/snippet}

<style>
  .v2-macro-body {
    font-size: 12.5px;
    color: var(--v2-slate);
    line-height: 1.55;
    white-space: pre-wrap;
    margin: 9px 0 0;
  }
  .v2-token {
    font-family: var(--v2-mono);
    font-size: 11.5px;
    background: var(--v2-hover);
    border-radius: 3px;
    padding: 1px 4px;
    color: var(--v2-ink);
  }
  /* No side padding inside a body preview. Four pixels either side renders
     "%customer_name% ,". A space the macro does not contain, on a screen
     whose only job is to show exactly what the customer will receive. The
     background alone is enough to mark it. */
  .v2-macro-body .v2-token {
    padding: 1px 0;
  }
  /* Rust, not ember: a broken placeholder is a fact about the macro, not a
     button. Ember stays reserved for things you act on. */
  .v2-token-bad {
    color: var(--v2-rust);
    text-decoration: underline wavy;
    text-underline-offset: 2px;
  }
  .v2-macro-flag {
    display: flex;
    gap: 7px;
    align-items: flex-start;
    margin-top: 10px;
    font-size: 12px;
    color: var(--v2-slate);
    line-height: 1.45;
  }
</style>
