<script>
  import { resolve } from '$app/paths';
  import { page } from '$app/state';
  import EmptyState from '$lib/v2/components/EmptyState.svelte';
  import { FileQuestion, Lock, TriangleAlert } from '@lucide/svelte';

  /**
   * Every failed load in /v2 lands here. Three cases, three different things
   * to do next, which is the point: "Something went wrong" tells you nothing
   * and leaves you on a dead page.
   *
   * 403 deliberately does not say whether the record exists. Confirming that
   * an id is real to somebody who cannot open it is an information leak, so
   * the copy talks about access, never about the record.
   */
  let status = $derived(page.status);

  let shape = $derived(
    status === 404
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
      {#if status >= 500}
        <button class="v2-btn v2-btn-primary" onclick={() => location.reload()}>Try again</button>
      {/if}
      <a class="v2-btn" href={resolve('/')}>Back to Today</a>
    {/snippet}
  </EmptyState>

  <p class="v2-sub" style="text-align:center;font-size:11.5px">
    <span class="v2-num">{status}</span>
    · {page.url.pathname}
  </p>
</div>
