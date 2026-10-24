<script>
  import { resolve } from '$app/paths';
  import { page } from '$app/state';
  import EmptyState from '#lib/v2/components/EmptyState.svelte';
  import { isOrgAdmin } from '#lib/admin.js';
  import { labelOf } from '#lib/v2/modules.js';
  import { asInternalPath } from '#lib/utils/paths.js';
  import { FileQuestion, Lock, ToggleLeft, TriangleAlert } from '@lucide/svelte';

  /**
   * Every failed load in /v2 lands here. Four cases, four different things
   * to do next, which is the point: "Something went wrong" tells you nothing
   * and leaves you on a dead page.
   *
   * 403 deliberately does not say whether the record exists. Confirming that
   * an id is real to somebody who cannot open it is an information leak, so
   * the copy talks about access, never about the record.
   */
  let status = $derived(page.status);
  let moduleOff = $derived(page.error?.code === 'module_off');
  // The API's refusal names the module but not its label, which follows terminology.
  let moduleLabel = $derived(
    page.error?.label || (page.error?.module ? labelOf(page.data.modules, page.error.module) : '')
  );

  let shape = $derived(
    moduleOff
      ? {
          icon: ToggleLeft,
          title: moduleLabel ? `${moduleLabel} is switched off` : 'This is switched off',
          body: page.error?.message ?? ''
        }
      : status === 404
        ? {
            icon: FileQuestion,
            title: 'That record is not here',
            body:
              page.error?.message ||
              'It may have been deleted, or it belongs to a team you are not part of.'
          }
        : status === 403
          ? {
              icon: Lock,
              title: 'You do not have access to this',
              body: 'Ask an admin in your organisation to give you access, or head back to Today.'
            }
          : {
              icon: TriangleAlert,
              title: 'That did not load',
              body:
                page.error?.message ||
                'The server did not answer. Nothing you did caused this, and nothing was saved or lost.'
            }
  );
</script>

<div class="v2-scroll">
  <EmptyState title={shape.title} body={shape.body}>
    {#snippet icon()}
      <shape.icon size={21} />
    {/snippet}
    {#snippet actions()}
      {#if status >= 500 && !moduleOff}
        <button class="v2-btn v2-btn-primary" onclick={() => location.reload()}>Try again</button>
      {/if}
      <a class="v2-btn" href={resolve('')}>Back to Today</a>
      {#if moduleOff && isOrgAdmin(page.data)}
        <a class="v2-btn" href={resolve(asInternalPath('/settings/apps'))}>Open Settings › Apps</a>
      {/if}
    {/snippet}
  </EmptyState>

  <p class="v2-sub" style="text-align:center;font-size:11.5px">
    <span class="v2-num">{status}</span>
    · {page.url.pathname}
  </p>
</div>
