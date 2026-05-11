<script>
  import { goto } from '$app/navigation';
  import {
    Pencil,
    Mail,
    Phone,
    MoreHorizontal,
    Paperclip,
    MessageSquare,
    Calendar
  } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { StageStepper } from '$lib/components/ui/stage-stepper';
  import { Timeline, TimelineItem } from '$lib/components/ui/timeline';
  import * as Card from '$lib/components/ui/card/index.js';
  import * as Tabs from '$lib/components/ui/tabs/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import { formatCurrency, formatDate, formatRelativeDate, getNameInitials } from '$lib/utils/formatting.js';
  import { OPPORTUNITY_STAGES } from '$lib/constants/filters.js';

  /** @type {{ data: { opportunity: any, comments: any[], attachments: any[], contacts: any[], users: any[], commentPermission: boolean } }} */
  let { data } = $props();

  const opp = $derived(data.opportunity || {});
  const comments = $derived(data.comments || []);
  const attachments = $derived(data.attachments || []);
  const contacts = $derived(data.contacts || []);

  let tab = $state('overview');

  // Build the 6 stepper cells from OPPORTUNITY_STAGES (skipping the 'ALL' filter sentinel)
  const stepperStages = $derived(
    OPPORTUNITY_STAGES.filter((s) => s.value !== 'ALL').map((s) => ({
      value: s.value,
      label: s.label
    }))
  );

  // Timeline items: comments + attachments + created event, sorted DESC by timestamp.
  const timelineItems = $derived.by(() => {
    /** @type {Array<{ id: string, ts: string, kind: 'comment' | 'attachment' | 'created', payload: any }>} */
    const items = [];
    for (const c of comments) {
      items.push({ id: `comment-${c.id}`, ts: c.commented_on || c.commented_on_arrow || '', kind: 'comment', payload: c });
    }
    for (const a of attachments) {
      items.push({ id: `attachment-${a.id}`, ts: a.created_on || a.created_at || '', kind: 'attachment', payload: a });
    }
    if (opp?.created_at || opp?.created_on) {
      items.push({ id: `created-${opp.id}`, ts: opp.created_at || opp.created_on, kind: 'created', payload: opp });
    }
    return items.sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime());
  });
</script>

<svelte:head>
  <title>{opp?.name || 'Opportunity'} · BottleCRM</title>
</svelte:head>

<PageHeader
  title={opp?.name || 'Opportunity'}
  breadcrumb={[
    { label: 'Opportunities', href: '/opportunities' },
    { label: opp?.name || '—' }
  ]}
>
  {#snippet meta()}
    <div class="flex flex-wrap items-center gap-3 text-[12px] leading-none text-[color:var(--text-subtle)]">
      {#if opp?.created_at || opp?.created_on}
        <span>Created {formatRelativeDate(opp.created_at || opp.created_on)}</span>
      {/if}
      {#if opp?.account?.name}
        <span>·</span>
        <a href={`/accounts`} class="hover:text-[color:var(--text-muted)]">{opp.account.name}</a>
      {/if}
      {#if opp?.assigned_to?.[0]}
        <span>·</span>
        <span class="flex items-center gap-1.5">
          <span class="flex size-4 items-center justify-center rounded-full bg-[color:var(--bg-elevated)] text-[9px] font-medium text-[color:var(--text-muted)]">
            {getNameInitials(opp.assigned_to[0].user_details?.email || '?', '')}
          </span>
          {opp.assigned_to[0].user_details?.email || 'Unassigned'}
        </span>
      {/if}
    </div>
  {/snippet}

  {#snippet amount()}
    {#if opp?.amount != null}
      <span class="text-[28px] font-bold leading-none tabular-nums text-[color:var(--text)]">
        {formatCurrency(opp.amount, opp.currency || 'USD')}
      </span>
      {#if opp?.probability != null}
        <span class="text-[11px] leading-none text-[color:var(--text-subtle)]">
          {opp.probability}% probability
        </span>
      {/if}
    {/if}
  {/snippet}

  {#snippet actions()}
    <div class="flex items-center gap-1.5">
      <Button variant="ghost" size="icon" aria-label="Email"><Mail class="size-4" /></Button>
      <Button variant="ghost" size="icon" aria-label="Call"><Phone class="size-4" /></Button>
      <Button variant="ghost" size="icon" aria-label="More"><MoreHorizontal class="size-4" /></Button>
      <Button variant="outline" size="sm" onclick={() => opp?.id && goto(`/opportunities/${opp.id}/edit`)}>
        <Pencil class="mr-1.5 size-3.5" /> Edit
      </Button>
    </div>
  {/snippet}
</PageHeader>

<!-- Stage stepper -->
<div class="px-7 pb-3 md:px-8">
  <StageStepper stages={stepperStages} current={opp?.stage || ''} />
</div>

<!-- Tabs -->
<Tabs.Root bind:value={tab} class="px-7 md:px-8">
  <Tabs.List class="">
    <Tabs.Trigger class="" value="overview">Overview</Tabs.Trigger>
    <Tabs.Trigger class="" value="activity">
      Activity
      <span class="ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[color:var(--bg-elevated)] px-1 text-[10px] tabular-nums text-[color:var(--text-subtle)]">
        {timelineItems.length}
      </span>
    </Tabs.Trigger>
    <Tabs.Trigger class="" value="files">
      Files
      <span class="ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[color:var(--bg-elevated)] px-1 text-[10px] tabular-nums text-[color:var(--text-subtle)]">
        {attachments.length}
      </span>
    </Tabs.Trigger>
  </Tabs.List>

  <Tabs.Content class="" value="overview">
    <div class="grid grid-cols-1 gap-6 pt-4 pb-8 lg:grid-cols-[1fr_320px]">
      <!-- Main column -->
      <div class="flex flex-col gap-6">
        <!-- About card -->
        <Card.Root>
          <Card.Header>
            <Card.Title>About</Card.Title>
          </Card.Header>
          <Card.Content>
            {#if opp?.description}
              <p class="text-[13px] leading-[1.6] text-[color:var(--text-muted)]">{opp.description}</p>
            {:else}
              <p class="text-[12.5px] italic text-[color:var(--text-subtle)]">No description.</p>
            {/if}
          </Card.Content>
        </Card.Root>

        <!-- Activity timeline card -->
        <Card.Root>
          <Card.Header>
            <Card.Title>Activity</Card.Title>
          </Card.Header>
          <Card.Content class="px-4 py-2">
            <Timeline isEmpty={timelineItems.length === 0}>
              {#each timelineItems as item (item.id)}
                {#if item.kind === 'comment'}
                  <TimelineItem
                    variant="violet"
                    time={item.ts ? formatRelativeDate(item.ts) : ''}
                    quote={item.payload.comment || ''}
                  >
                    {#snippet icon()}<MessageSquare class="size-3.5" />{/snippet}
                    {#snippet text()}
                      <strong>{item.payload.commented_by_user || 'Someone'}</strong> commented
                    {/snippet}
                  </TimelineItem>
                {:else if item.kind === 'attachment'}
                  <TimelineItem
                    time={item.ts ? formatRelativeDate(item.ts) : ''}
                  >
                    {#snippet icon()}<Paperclip class="size-3.5" />{/snippet}
                    {#snippet text()}
                      <strong>{item.payload.created_by_user || 'Someone'}</strong> uploaded
                      <strong>{item.payload.file_name || 'a file'}</strong>
                    {/snippet}
                  </TimelineItem>
                {:else}
                  <TimelineItem
                    variant="success"
                    time={item.ts ? formatRelativeDate(item.ts) : ''}
                  >
                    {#snippet icon()}<Calendar class="size-3.5" />{/snippet}
                    {#snippet text()}
                      Opportunity created
                    {/snippet}
                  </TimelineItem>
                {/if}
              {/each}
            </Timeline>
          </Card.Content>
        </Card.Root>
      </div>

      <!-- Right rail -->
      <div class="flex flex-col gap-6">
        <Card.Root>
          <Card.Header><Card.Title>Details</Card.Title></Card.Header>
          <Card.Content>
            <dl class="grid grid-cols-1 gap-y-3 text-[12.5px]">
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Account</dt>
                <dd class="truncate text-right font-medium text-[color:var(--text)]">{opp?.account?.name || '—'}</dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Stage</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">
                  {OPPORTUNITY_STAGES.find((s) => s.value === opp?.stage)?.label || opp?.stage || '—'}
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Close date</dt>
                <dd class="text-right text-[color:var(--text-muted)]">{opp?.closed_on ? formatDate(opp.closed_on) : '—'}</dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Probability</dt>
                <dd class="text-right tabular-nums text-[color:var(--text-muted)]">{opp?.probability != null ? `${opp.probability}%` : '—'}</dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Source</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">{opp?.lead_source || '—'}</dd>
              </div>
            </dl>
          </Card.Content>
        </Card.Root>

        <Card.Root>
          <Card.Header><Card.Title>Contacts</Card.Title></Card.Header>
          <Card.Content>
            {#if contacts.length === 0}
              <p class="text-[12.5px] italic text-[color:var(--text-subtle)]">No contacts linked.</p>
            {:else}
              <ul class="flex flex-col gap-2">
                {#each contacts as ct (ct.id)}
                  <li class="flex items-center gap-2 text-[12.5px]">
                    <span class="flex size-6 items-center justify-center rounded-full bg-[color:var(--bg-elevated)] text-[10px] font-medium text-[color:var(--text-muted)]">
                      {getNameInitials(ct.first_name || ct.email || '?', ct.last_name || '')}
                    </span>
                    <span class="truncate text-[color:var(--text)]">{`${ct.first_name || ''} ${ct.last_name || ''}`.trim() || ct.email || 'Contact'}</span>
                  </li>
                {/each}
              </ul>
            {/if}
          </Card.Content>
        </Card.Root>

        <Card.Root>
          <Card.Header><Card.Title>Tags</Card.Title></Card.Header>
          <Card.Content>
            {#if (opp?.tags || []).length === 0}
              <p class="text-[12.5px] italic text-[color:var(--text-subtle)]">No tags.</p>
            {:else}
              <div class="flex flex-wrap gap-1.5">
                {#each opp.tags as tag, i (tag.id ?? tag.slug ?? tag.name ?? i)}
                  <Badge variant="secondary" class="bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)]">
                    {tag.name}
                  </Badge>
                {/each}
              </div>
            {/if}
          </Card.Content>
        </Card.Root>
      </div>
    </div>
  </Tabs.Content>

  <Tabs.Content class="" value="activity">
    <div class="pt-4 pb-8">
      <Card.Root>
        <Card.Header><Card.Title>All activity</Card.Title></Card.Header>
        <Card.Content class="px-4 py-2">
          <Timeline isEmpty={timelineItems.length === 0}>
            {#each timelineItems as item (item.id)}
              {#if item.kind === 'comment'}
                <TimelineItem variant="violet" time={item.ts ? formatRelativeDate(item.ts) : ''} quote={item.payload.comment || ''}>
                  {#snippet icon()}<MessageSquare class="size-3.5" />{/snippet}
                  {#snippet text()}<strong>{item.payload.commented_by_user || 'Someone'}</strong> commented{/snippet}
                </TimelineItem>
              {:else if item.kind === 'attachment'}
                <TimelineItem time={item.ts ? formatRelativeDate(item.ts) : ''}>
                  {#snippet icon()}<Paperclip class="size-3.5" />{/snippet}
                  {#snippet text()}<strong>{item.payload.created_by_user || 'Someone'}</strong> uploaded <strong>{item.payload.file_name || 'a file'}</strong>{/snippet}
                </TimelineItem>
              {:else}
                <TimelineItem variant="success" time={item.ts ? formatRelativeDate(item.ts) : ''}>
                  {#snippet icon()}<Calendar class="size-3.5" />{/snippet}
                  {#snippet text()}Opportunity created{/snippet}
                </TimelineItem>
              {/if}
            {/each}
          </Timeline>
        </Card.Content>
      </Card.Root>
    </div>
  </Tabs.Content>

  <Tabs.Content class="" value="files">
    <div class="pt-4 pb-8">
      <Card.Root>
        <Card.Header><Card.Title>Files</Card.Title></Card.Header>
        <Card.Content>
          {#if attachments.length === 0}
            <p class="text-[12.5px] italic text-[color:var(--text-subtle)]">No files uploaded.</p>
          {:else}
            <ul class="flex flex-col divide-y divide-[color:var(--border-faint)]">
              {#each attachments as a (a.id)}
                <li class="flex items-center gap-3 py-2.5 text-[12.5px]">
                  <Paperclip class="size-3.5 shrink-0 text-[color:var(--text-subtle)]" />
                  <span class="flex-1 truncate text-[color:var(--text)]">{a.file_name || 'File'}</span>
                  <span class="text-[11px] text-[color:var(--text-subtle)]">{a.created_on ? formatRelativeDate(a.created_on) : ''}</span>
                </li>
              {/each}
            </ul>
          {/if}
        </Card.Content>
      </Card.Root>
    </div>
  </Tabs.Content>
</Tabs.Root>
