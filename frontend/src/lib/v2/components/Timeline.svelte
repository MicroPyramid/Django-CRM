<script>
  import { relativeTime } from '#lib/v2/format.js';
  import ConfirmAction from '#lib/v2/components/ConfirmAction.svelte';

  /**
   * Newest first. The filled dot marks the latest event only. Everything
   * else is a hairline, so the eye lands on "what happened last".
   *
   * An event with `canDelete` is a logged interaction the caller may remove,
   * through the page's `?/deleteActivity`.
   *
   * @type {{ events: Array<{ id: string, body: string, at: string, by?: string|null, type?: string, detail?: string, canDelete?: boolean, interaction?: string }> }}
   */
  let { events = [] } = $props();
</script>

<div class="v2-timeline">
  {#each events as e, i (e.id)}
    <div class="v2-event" class:latest={i === 0}>
      <div style="font-weight:500">{e.body}</div>
      {#if e.detail}<div class="detail">{e.detail}</div>{/if}
      <div class="v2-event-meta">{relativeTime(e.at) + (e.by ? ` · ${e.by}` : '')}</div>
      {#if e.canDelete && e.interaction}
        <div style="margin-top:4px">
          <ConfirmAction
            action="?/deleteActivity"
            hidden={{ interaction: e.interaction }}
            label="Delete"
            confirmLabel="Delete for good"
            explain="Removes it from every timeline it is on."
          />
        </div>
      {/if}
    </div>
  {/each}
</div>

<style>
  .detail {
    font-size: 12.5px;
    line-height: 1.5;
    white-space: pre-wrap;
    overflow-wrap: anywhere;
    margin-top: 2px;
  }
</style>
