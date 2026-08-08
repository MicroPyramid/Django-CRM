<script>
  /**
   * A destructive action that takes two clicks.
   *
   * The first click swaps the button for a confirm and a cancel; the second
   * submits. No `window.confirm`: a native dialog blocks the page, cannot be
   * styled or explained, and is a dead end for anything driving the browser.
   *
   * `explain` is the one line of consequence shown while armed. Say what the
   * action actually does. "Turn off" and "Delete permanently" are different
   * promises and this codebase has both, sometimes behind the same verb on
   * the backend.
   */
  import { enhance } from '$app/forms';

  /** @type {{
   *   action: string,
   *   label?: string,
   *   confirmLabel?: string,
   *   explain?: string,
   *   hidden?: Record<string, string>
   * }} */
  let { action, label = 'Delete', confirmLabel = 'Confirm', explain = '', hidden = {} } = $props();

  let armed = $state(false);
  let busy = $state(false);
</script>

{#if armed}
  <form
    class="v2-confirm"
    method="POST"
    {action}
    use:enhance={() => {
      busy = true;
      return async (/** @type {any} */ { update }) => {
        await update();
        busy = false;
        // Disarm either way. On success the row is gone; on failure the page
        // error is what the user needs to read, not a still-armed button.
        armed = false;
      };
    }}
  >
    {#each Object.entries(hidden) as [name, value] (name)}
      <input type="hidden" {name} {value} />
    {/each}
    {#if explain}
      <span class="v2-sub" style="font-size:11.5px">{explain}</span>
    {/if}
    <button class="v2-btn v2-btn-sm" type="submit" disabled={busy}>{confirmLabel}</button>
    <button class="v2-btn v2-btn-sm" type="button" disabled={busy} onclick={() => (armed = false)}>
      Cancel
    </button>
  </form>
{:else}
  <button class="v2-btn v2-btn-sm" type="button" onclick={() => (armed = true)}>{label}</button>
{/if}

<style>
  .v2-confirm {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    flex-wrap: wrap;
    justify-content: flex-end;
  }
</style>
