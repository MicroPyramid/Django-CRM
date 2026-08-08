<script>
  import { resolve } from '$app/paths';
  /**
   * The way back up from a settings page.
   *
   * Settings has no tab strip (see the note in `tabs.js`): you arrive at one
   * page, change one thing, and leave. What that needs is a way back to the
   * index, not twelve siblings competing for the same row.
   *
   * Rendered inside PageHeader's `crumb` snippet so it sits above the title in
   * the same place a record's account name does. One convention for "the
   * thing this belongs to", whether that thing is an account or a section.
   */
  import { ChevronLeft } from '@lucide/svelte';
</script>

<a href={resolve('/settings')}><ChevronLeft size={13} />Settings</a>

<style>
  a {
    display: inline-flex;
    align-items: center;
    gap: 2px;
    color: inherit;
    text-decoration: none;
  }
  a:hover {
    color: var(--v2-ink);
    text-decoration: underline;
  }
</style>
