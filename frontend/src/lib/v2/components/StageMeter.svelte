<script>
  import { OPEN_STAGES, STAGE_LABEL } from '$lib/v2/enums.js';

  /**
   * Four segments for the four open stages. A closed deal leaves the meter
   * entirely and becomes a pill. A won deal is not "100% through a funnel",
   * it is done.
   *
   * @type {{ stage: string, label?: boolean }}
   */
  let { stage, label = true } = $props();

  let closed = $derived(stage === 'CLOSED_WON' || stage === 'CLOSED_LOST');
  let index = $derived(OPEN_STAGES.indexOf(stage));
</script>

{#if !closed}
  <div class="v2-meter" role="img" aria-label="Stage: {STAGE_LABEL[stage]}">
    {#each OPEN_STAGES as stageKey, i (stageKey)}
      <i class={i <= index ? 'on' : ''}></i>
    {/each}
  </div>
  {#if label}
    <div class="v2-table-secondary" style="margin-top:4px">{STAGE_LABEL[stage]}</div>
  {/if}
{:else}
  <span class="v2-sub">{STAGE_LABEL[stage]}</span>
{/if}
