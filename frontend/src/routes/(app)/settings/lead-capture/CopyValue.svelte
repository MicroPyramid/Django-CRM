<script>
  /**
   * A value to paste somewhere else (a webhook URL, a key), with a copy button.
   *
   * @type {{ label: string, value: string, id: string }}
   */
  import { Copy, Check } from '@lucide/svelte';

  let { label, value, id } = $props();
  let copied = $state(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(value);
      copied = true;
      setTimeout(() => (copied = false), 1600);
    } catch {
      // Clipboard blocked (no https or no permission). The value is on screen
      // to select by hand.
    }
  }
</script>

<div class="cv">
  <span class="v2-label" {id}>{label}</span>
  <div class="cv-row">
    <code class="v2-num cv-value" aria-labelledby={id}>{value}</code>
    <button class="v2-btn cv-btn" type="button" onclick={copy} aria-label="Copy {label}">
      {#if copied}<Check size={13} />Copied{:else}<Copy size={13} />Copy{/if}
    </button>
  </div>
</div>

<style>
  .cv {
    display: flex;
    flex-direction: column;
    gap: 5px;
  }
  .cv-row {
    display: flex;
    gap: 8px;
    align-items: center;
    flex-wrap: wrap;
  }
  .cv-value {
    flex: 1;
    min-width: 0;
    background: var(--v2-bg-sunk);
    border: 1px solid var(--v2-line);
    border-radius: var(--v2-radius);
    padding: 9px 11px;
    font-size: 12.5px;
    word-break: break-all;
  }
  .cv-btn {
    min-height: 44px;
  }
</style>
