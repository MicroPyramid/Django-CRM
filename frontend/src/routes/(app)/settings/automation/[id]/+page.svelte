<script>
  import PageHeader from '#lib/v2/components/PageHeader.svelte';
  import AdminsOnly from '#lib/v2/components/automation/AdminsOnly.svelte';
  import AutomationCrumb from '#lib/v2/components/automation/AutomationCrumb.svelte';
  import RuleEditor from '#lib/v2/components/automation/RuleEditor.svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();
</script>

{#if data.forbidden}
  <PageHeader title="Automation rule">
    {#snippet crumb()}<AutomationCrumb />{/snippet}
  </PageHeader>
  <div class="v2-scroll">
    <div class="v2-pad" style="padding-top:16px">
      <AdminsOnly />
    </div>
  </div>
{:else}
  <!-- Keyed: moving between two rules reuses this page, and the draft is built once. -->
  {#key data.rule.id}
    <RuleEditor
      catalogue={data.catalogue}
      rule={data.rule}
      row={data.row}
      modules={data.modules}
      {form}
    />
  {/key}
{/if}
