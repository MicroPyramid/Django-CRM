<script>
  /**
   * A record's custom fields on its detail page, every active one filled or
   * not, from `fieldsForDetail` (`#lib/server/v2/record-custom-fields.js`).
   * Renders nothing when the org has no active fields for the record type.
   * `flush` drops the space above, for a page that spaces its own sections.
   */

  /**
   * @type {{
   *   fields: { key: string, label: string, value: string, filled: boolean }[],
   *   label?: string,
   *   flush?: boolean
   * }}
   */
  let { fields, label = 'Details', flush = false } = $props();
</script>

{#if fields.length > 0}
  <div class="v2-label cf-head" class:flush>{label}</div>
  <div class="v2-card cf">
    {#each fields as f (f.key)}
      <div class="cf-row">
        <span class="cf-label">{f.label}</span>
        <span class="cf-value" class:v2-muted={!f.filled}>{f.filled ? f.value : 'Not set'}</span>
      </div>
    {/each}
  </div>
{/if}

<style>
  .cf-head {
    margin: 22px 0 10px;
  }
  .cf-head.flush {
    margin-top: 0;
  }
  .cf {
    padding: 4px 16px;
    font-size: 13px;
  }
  .cf-row {
    display: flex;
    gap: 16px;
    align-items: baseline;
    padding: 9px 0;
    border-bottom: 1px solid var(--v2-line);
  }
  .cf-row:last-child {
    border-bottom: 0;
  }
  .cf-label {
    flex: 0 0 40%;
    color: var(--v2-ink-soft);
  }
  .cf-value {
    flex: 1 1 auto;
    min-width: 0;
    overflow-wrap: anywhere;
    white-space: pre-wrap;
  }
  @media (max-width: 768px) {
    .cf-row {
      display: block;
    }
    .cf-label {
      display: block;
      margin-bottom: 2px;
    }
  }
</style>
