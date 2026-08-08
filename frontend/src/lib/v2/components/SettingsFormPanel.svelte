<script>
  /**
   * The chrome around a settings form.
   *
   * Every settings page in v2 is a list with an "add" or "edit" control, and
   * every one of those forms needs the same four things: somewhere to put the
   * error, a submit that cannot be double-fired, a cancel, and the rule that
   * a failed submit leaves the form open so the error stays on screen. That
   * rule is the reason this exists as a component rather than as markup
   * copied eight times: getting it wrong closes the panel and takes the
   * message with it, and it is invisible until someone submits something
   * invalid.
   *
   * The fields are the caller's, passed as a snippet. This component holds no
   * opinion about what is being edited and no per-resource state.
   *
   * Visibility is the caller's too: render this inside an `{#if}`. A panel
   * that owned its own `open` flag would need the caller to reach in and set
   * it to switch between "add" and "edit this row", which is worse than an
   * `{#if}`.
   */
  import { enhance } from '$app/forms';

  /** @type {{
   *   title: string,
   *   action: string,
   *   error?: string | null,
   *   submitLabel?: string,
   *   oncancel: () => void,
   *   ondone?: () => void,
   *   fields: import('svelte').Snippet
   * }} */
  let { title, action, error = null, submitLabel = 'Save', oncancel, ondone, fields } = $props();

  // Disables submit while a request is in flight so a double-click cannot
  // fire two writes.
  let busy = $state(false);
</script>

<div class="v2-card v2-sfp">
  <form
    method="POST"
    {action}
    use:enhance={() => {
      busy = true;
      return async (/** @type {any} */ { result, update }) => {
        await update();
        busy = false;
        // Close only on success. A rejected submit has to leave the panel
        // open, or the error rendered above the fields is unmounted the
        // instant the action returns and nobody ever reads it.
        if (result.type === 'success') ondone?.();
      };
    }}
  >
    <div class="v2-sfp-head">{title}</div>

    {#if error}
      <p class="v2-error" style="margin:0 0 12px">{error}</p>
    {/if}

    <div class="v2-sfp-fields">
      {@render fields()}
    </div>

    <div class="v2-sfp-foot">
      <button class="v2-btn v2-btn-primary" type="submit" disabled={busy}>{submitLabel}</button>
      <button class="v2-btn" type="button" disabled={busy} onclick={oncancel}>Cancel</button>
    </div>
  </form>
</div>

<style>
  .v2-sfp {
    padding: 16px 17px;
    margin-bottom: 18px;
  }
  .v2-sfp-head {
    font-weight: 600;
    font-size: 13px;
    margin-bottom: 13px;
  }
  /* Two columns on a wide screen, one on a narrow one. A settings form is
     mostly short fields (a number, a select, a checkbox) and a single column
     of them wastes the width these pages have. A field that needs the full
     row opts in with `grid-column: 1 / -1` via the `v2-sfp-wide` class. */
  .v2-sfp-fields {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 13px 18px;
    align-items: start;
  }
  .v2-sfp-foot {
    display: flex;
    gap: 8px;
    margin-top: 16px;
  }

  @media (max-width: 768px) {
    .v2-sfp-fields {
      grid-template-columns: 1fr;
    }
  }
</style>
