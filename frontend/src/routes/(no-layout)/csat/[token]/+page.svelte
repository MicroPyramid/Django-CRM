<script>
  import { enhance } from '$app/forms';
  import { Star, CheckCircle2 } from '@lucide/svelte';

  /** @type {{ data: import('./$types').PageData, form: import('./$types').ActionData }} */
  let { data, form } = $props();

  // Local rating state, seeded from the loader if the customer already
  // submitted within the edit window.
  let rating = $state(data.survey?.rating ?? 0);
  let comment = $state(data.survey?.comment ?? '');
  let hover = $state(0);
  let submitting = $state(false);
</script>

<svelte:head>
  <title>How did we do? — {data.survey?.orgName ?? 'CSAT survey'}</title>
  <meta name="robots" content="noindex" />
</svelte:head>

<main class="mx-auto flex min-h-screen max-w-md flex-col justify-center px-4 py-10">
  {#if data.gone}
    <section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-6 text-center">
      <h1 class="text-lg font-semibold">This survey link has expired</h1>
      <p class="mt-2 text-sm text-[var(--text-secondary)]">
        Survey links are valid for a limited time after a ticket is closed. If
        you'd still like to share feedback, please reply to the agent's email
        directly.
      </p>
    </section>
  {:else if data.invalid}
    <section class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-6 text-center">
      <h1 class="text-lg font-semibold">Invalid survey link</h1>
      <p class="mt-2 text-sm text-[var(--text-secondary)]">
        We couldn't verify this link. Please use the most recent link from
        your email.
      </p>
    </section>
  {:else if data.error}
    <section class="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
      <h1 class="text-lg font-semibold text-red-700">Something went wrong</h1>
      <p class="mt-2 text-sm text-red-700/80">{data.error}</p>
    </section>
  {:else if form?.success}
    <section
      class="flex flex-col items-center gap-3 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-8 text-center"
    >
      <CheckCircle2 class="size-10 text-green-600" />
      <h1 class="text-lg font-semibold">Thanks for your feedback</h1>
      <p class="text-sm text-[var(--text-secondary)]">
        Your rating of <strong>{form.rating}/5</strong> has been recorded.
        You can update it for the next 24 hours by re-opening this link.
      </p>
    </section>
  {:else if data.survey}
    <header class="mb-4 text-center">
      <h1 class="text-lg font-semibold">How did we do?</h1>
      <p class="mt-1 text-sm text-[var(--text-secondary)]">
        {data.survey.orgName} · ticket "{data.survey.ticketSubject}"
      </p>
      <p class="mt-1 text-xs text-[var(--text-secondary)]">
        Agent: {data.survey.agentName}
      </p>
    </header>

    <form
      method="POST"
      action="?/submit"
      use:enhance={() => {
        submitting = true;
        return async ({ result, update }) => {
          submitting = false;
          await update();
        };
      }}
      class="space-y-4 rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-6"
    >
      <input type="hidden" name="rating" value={rating} />

      <div class="flex justify-center gap-1" aria-label="Rate 1 to 5 stars">
        {#each [1, 2, 3, 4, 5] as n (n)}
          <button
            type="button"
            class="rounded p-1 transition focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-primary-default)]"
            aria-label="Rate {n} star{n === 1 ? '' : 's'}"
            onclick={() => (rating = n)}
            onmouseenter={() => (hover = n)}
            onmouseleave={() => (hover = 0)}
          >
            <Star
              class="size-9 transition-colors {(hover || rating) >= n
                ? 'fill-amber-400 text-amber-400'
                : 'text-[var(--text-secondary)]'}"
            />
          </button>
        {/each}
      </div>

      <div>
        <label for="comment" class="text-xs font-medium text-[var(--text-secondary)]">
          Comments (optional)
        </label>
        <textarea
          id="comment"
          name="comment"
          rows="3"
          bind:value={comment}
          placeholder="What worked well, or what could we improve?"
          class="mt-1 w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] p-2 text-sm focus:border-[var(--color-primary-default)] focus:outline-none"
        ></textarea>
      </div>

      {#if form?.error}
        <div class="rounded border border-red-200 bg-red-50 p-2 text-xs text-red-700">
          {form.error}
        </div>
      {/if}

      <button
        type="submit"
        disabled={!rating || submitting}
        class="w-full rounded-md bg-[var(--color-primary-default)] px-3 py-2 text-sm font-medium text-white transition hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {submitting ? 'Submitting…' : 'Submit feedback'}
      </button>

      <p class="text-center text-[10px] text-[var(--text-secondary)]">
        Powered by BottleCRM. Your response is shared only with the support team.
      </p>
    </form>
  {/if}
</main>
