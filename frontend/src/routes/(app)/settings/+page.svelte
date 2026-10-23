<script>
  import { resolve } from '$app/paths';
  import { asInternalPath } from '#lib/utils/paths.js';
  /**
   * The settings hub.
   *
   * v1 has thirteen settings routes reachable only from a dropdown, so nobody
   * could tell what was configurable without opening each one. This lists them
   * with the current value beside each. A settings index that does not tell
   * you the current state is a table of contents, not a screen.
   *
   * Grouped by what a setting decides, not by which Django app owns it:
   * "who a ticket lands on" and "what closes it" belong together whether or
   * not they live in the same models file.
   *
   * `warn` is the second reason this page exists. Each destination reports
   * whether something there needs attention, so the hub is worth opening even
   * when you did not come to change anything. A warning here always has a
   * matching explanation on the page it points to, never a badge that leads
   * to a screen with nothing on it.
   *
   * Destinations v2 has not built are listed anyway and link to v1, marked as
   * such. An index that quietly omits settings is worse than one that admits
   * where they live: people go looking, find nothing, and conclude the feature
   * does not exist.
   */
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import { count, shortDate } from '#lib/v2/format.js';
  import { hubGroups } from '#lib/v2/settings-hub.js';
  import { ChevronRight, ShieldAlert } from '@lucide/svelte';

  /** @type {{ data: any }} */
  let { data } = $props();

  let org = $derived(data.org);
  let groups = $derived(hubGroups(data));

  let warnings = $derived(groups.flatMap((g) => g.items).filter((i) => i.warn).length);
</script>

<PageHeader title="Settings">
  {#snippet sub()}
    {org.name} · <span class="v2-num">{count(org.member_count)}</span> members · since
    {shortDate(org.created_at)}
    {#if warnings}
      · <span class="v2-num">{count(warnings)}</span> need a look
    {/if}
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="padding-top:18px;padding-bottom:32px">
    {#each groups as g (g.label)}
      <div class="v2-label" style="margin-bottom:10px">{g.label}</div>
      <div class="v2-card" style="overflow:hidden;margin-bottom:22px">
        {#each g.items as s (s.href)}
          <a class="v2-setting" href={resolve(asInternalPath(s.href))}>
            <div class="v2-setting-body">
              <b>{s.title}</b>
              <span class="v2-sub" style="font-size:11.5px">{s.body}</span>
            </div>
            {#if s.warn}
              <ShieldAlert size={15} style="color:var(--v2-clay);flex:none" />
            {/if}
            {#if s.value}
              <span class="v2-sub v2-setting-value">{s.value}</span>
            {/if}
            <ChevronRight size={15} style="color:var(--v2-slate);flex:none" />
          </a>
        {/each}
      </div>
    {/each}

    <!--
      The org API key is deliberately absent from this page. It is a
      credential, it was once exposed through nested serializers, and a
      settings screen that renders it is how the next leak happens. Rotating
      or revealing it belongs behind an explicit, audited action, not on an
      index anyone with the URL can load.
    -->
    <p class="v2-sub" style="font-size:11.5px;margin-top:18px;max-width:64ch">
      The organisation API key is not shown here. Credentials are never rendered on a page you can
      arrive at by browsing. See
      <a href={resolve('settings/api-tokens')} style="color:inherit">API tokens</a> for how token values
      are handled.
    </p>
  </div>
</div>

<style>
  .v2-setting-value {
    font-size: 12px;
    text-align: right;
  }

  /* At 414px the value column squeezes the title to a couple of words per
     line. Drop it. The destination and what it does are what you navigate
     by, and every value is repeated on the page it points to. */
  @media (max-width: 640px) {
    .v2-setting-value {
      display: none;
    }
  }
</style>
