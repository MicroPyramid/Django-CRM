<script>
  /**
   * The frame for the customer's side of the product, the invoice and estimate
   * links emailed to a customer, and the CSAT survey.
   *
   * These pages live under `(no-layout)`, which has no app chrome, so this is
   * the whole shell: it loads the v2 design system, roots it under `.v2-root`
   * (the tokens are scoped there so v2 cannot leak into the v1 app), centres one
   * capped column, and keeps the page out of search indexes. A person who
   * receives an invoice is not a user of the CRM and must never be shown its
   * furniture.
   *
   * `v2.css` is imported here rather than in a layout so the styles arrive with
   * the component and nowhere else, the sibling `(no-layout)` routes (login,
   * bounce) are untouched.
   */
  import '$lib/v2/styles/v2.css';

  /** @type {{ children: import('svelte').Snippet }} */
  let { children } = $props();
</script>

<svelte:head>
  <!-- A public portal URL is unguessable, not secret; it must never reach an index. -->
  <meta name="robots" content="noindex, nofollow" />
</svelte:head>

<div class="v2-root v2-public">
  <main class="v2-public-main">
    {@render children()}
  </main>
</div>

<style>
  .v2-public {
    min-height: 100vh;
    background: var(--v2-paper);
    color: var(--v2-ink);
    font-family: var(--v2-sans);
    font-size: var(--v2-fs);
  }
  .v2-public-main {
    /* A document, not an application: one column, capped, centred, and it
       does not grow to fill a 27-inch monitor. */
    max-width: 720px;
    margin: 0 auto;
    padding: 40px 20px 64px;
  }
  @media (max-width: 640px) {
    .v2-public-main {
      padding: 24px 16px 48px;
    }
  }
</style>
