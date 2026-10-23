<script>
  import { onDestroy } from 'svelte';
  import { goto } from '$app/navigation';
  import { resolve } from '$app/paths';
  import ImportFlow from '#lib/components/import/ImportFlow.svelte';
  import { IMPORT_ENTITIES } from '#lib/import/entities.js';
  import { asInternalPath } from '#lib/utils/paths.js';
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import { isOn } from '#lib/v2/modules.js';

  /** @type {{ data: any }} */
  let { data } = $props();

  /** @type {'contacts' | 'leads'} */
  let chosen = $state('contacts');

  let leadsOn = $derived(isOn(data.modules, 'leads'));

  // `ImportFlow` calls `onDone` even after this page is gone, so someone who
  // left mid-import is not pulled back to the list.
  let destroyed = false;
  onDestroy(() => (destroyed = true));

  const CHOICES = [
    {
      entity: /** @type {const} */ ('contacts'),
      title: 'Customers and people you work with',
      line: 'Import them as contacts.'
    },
    {
      entity: /** @type {const} */ ('leads'),
      title: 'People you’re trying to sell to',
      line: 'Import them as leads to follow up.'
    }
  ];
</script>

<svelte:head>
  <title>Bring in your contacts · BottleCRM</title>
</svelte:head>

<PageHeader title="Bring in your contacts" center width="720px">
  {#snippet sub()}Upload a spreadsheet and we will match its columns for you.{/snippet}
  {#snippet actions()}
    <a class="v2-btn v2-btn-quiet" href={resolve('')} style="min-height:44px">Skip for now</a>
  {/snippet}
</PageHeader>

<div class="v2-scroll">
  <div class="v2-pad" style="max-width:720px;margin:0 auto;padding-top:14px;padding-bottom:26px">
    <div class="welcome-choices" role="group" aria-label="What are you importing?">
      {#each leadsOn ? CHOICES : CHOICES.filter((c) => c.entity !== 'leads') as c (c.entity)}
        <button
          type="button"
          class="v2-card welcome-choice"
          aria-pressed={chosen === c.entity}
          onclick={() => (chosen = c.entity)}
        >
          <span style="font-weight:640;letter-spacing:-0.012em">{c.title}</span>
          <span class="v2-sub">{c.line}</span>
        </button>
      {/each}
    </div>

    <ImportFlow
      entity={chosen}
      onUseLeads={leadsOn ? () => (chosen = 'leads') : undefined}
      onDone={() => {
        if (!destroyed) goto(resolve(asInternalPath(IMPORT_ENTITIES[chosen].listHref)));
      }}
    />
  </div>
</div>

<style>
  .welcome-choices {
    display: grid;
    grid-template-columns: 1fr;
    gap: 10px;
    margin-bottom: 18px;
  }
  .welcome-choice {
    display: flex;
    flex-direction: column;
    gap: 3px;
    min-height: 64px;
    padding: 14px 16px;
    text-align: left;
    font-family: inherit;
    color: var(--v2-ink);
    cursor: pointer;
  }
  .welcome-choice[aria-pressed='true'] {
    border-color: var(--v2-ink);
    box-shadow: inset 0 0 0 1px var(--v2-ink);
  }
  @media (min-width: 768px) {
    .welcome-choices {
      grid-template-columns: 1fr 1fr;
    }
  }
</style>
