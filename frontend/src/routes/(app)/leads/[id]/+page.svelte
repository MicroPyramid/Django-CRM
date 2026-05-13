<script>
  import { goto } from '$app/navigation';
  import {
    Pencil,
    Mail,
    Phone,
    MoreHorizontal,
    Paperclip,
    MessageSquare,
    Calendar,
    ArrowRightCircle,
    Globe,
    Briefcase,
    Building2,
    DollarSign,
    Target,
    Star,
    MapPin,
    Users,
    UserCheck,
    FileText,
    ExternalLink
  } from '@lucide/svelte';
  import { LinkedinIcon as Linkedin } from '$lib/components/icons';
  import { PageHeader } from '$lib/components/layout';
  import { StageStepper } from '$lib/components/ui/stage-stepper';
  import { Timeline, TimelineItem } from '$lib/components/ui/timeline';
  import { SectionCard } from '$lib/components/ui/section-card/index.js';
  import * as Tabs from '$lib/components/ui/tabs/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import CustomFieldsPanel from '$lib/components/custom-fields/CustomFieldsPanel.svelte';
  import {
    formatRelativeDate,
    formatDate,
    formatCurrency,
    getNameInitials
  } from '$lib/utils/formatting.js';
  import {
    leadStatusOptions,
    leadRatingOptions,
    getOptionLabel,
    getOptionStyle
  } from '$lib/utils/table-helpers.js';
  import { INDUSTRIES } from '$lib/constants/lead-choices.js';
  import { getCountryName } from '$lib/constants/countries.js';

  /** @type {{ data: { lead: any, comments: any[], attachments: any[], tags: any[], users: any[], commentPermission: boolean, customFieldDefinitions: any[], customFieldValues: Record<string, unknown> } }} */
  let { data } = $props();

  const lead = $derived(data.lead || {});
  const comments = $derived(data.comments || []);
  const attachments = $derived(data.attachments || []);
  const tags = $derived(data.tags || []);
  const customFieldDefinitions = $derived(data.customFieldDefinitions || []);
  const customFieldValues = $derived(data.customFieldValues || {});

  let tab = $state('overview');

  // Normalize backend status ("in process", "assigned") to leadStatusOptions value format ("IN_PROCESS")
  const normalizedStatus = $derived(
    (lead?.status || '').toString().toUpperCase().replace(/\s+/g, '_')
  );
  const normalizedRating = $derived((lead?.rating || '').toString().toUpperCase());

  const stepperStages = $derived(
    leadStatusOptions.map((s) => ({ value: s.value, label: s.label }))
  );

  const fullName = $derived(
    [lead?.salutation, lead?.first_name, lead?.last_name]
      .filter(Boolean)
      .join(' ')
      .trim() ||
      lead?.email ||
      'Lead'
  );

  const sourceLabel = $derived(
    lead?.source
      ? lead.source.replace(/\b\w/g, (/** @type {string} */ c) => c.toUpperCase())
      : ''
  );

  const industryLabel = $derived(
    INDUSTRIES.find((i) => i.value === lead?.industry)?.label || lead?.industry || ''
  );

  /** @typedef {{ id: string, email: string }} AssignedUser */
  /** @type {AssignedUser[]} */
  const assignedUsers = $derived(
    Array.isArray(lead?.assigned_to)
      ? lead.assigned_to
          .map((/** @type {any} */ p) => ({
            id: p?.id,
            email: p?.user_details?.email || p?.user?.email || ''
          }))
          .filter((/** @type {AssignedUser} */ u) => u.email)
      : []
  );

  /** @type {{ id: string, name: string }[]} */
  const teams = $derived(
    Array.isArray(lead?.teams)
      ? lead.teams.map((/** @type {any} */ t) => ({ id: t?.id, name: t?.name || '' }))
      : []
  );

  const probability = $derived(
    typeof lead?.probability === 'number' ? Math.max(0, Math.min(100, lead.probability)) : null
  );

  const hasDeal = $derived(
    lead?.opportunity_amount != null || probability !== null || !!lead?.close_date
  );

  const hasContactLinks = $derived(
    !!(lead?.email || lead?.phone || lead?.website || lead?.linkedin_url || lead?.job_title)
  );

  const hasAddress = $derived(
    !!(lead?.address_line || lead?.city || lead?.state || lead?.postcode || lead?.country)
  );

  const addressLines = $derived(
    [
      lead?.address_line,
      [lead?.city, lead?.state, lead?.postcode].filter(Boolean).join(', '),
      getCountryName(lead?.country)
    ].filter(Boolean)
  );

  function normalizeUrl(/** @type {string} */ raw) {
    if (!raw) return '';
    return /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
  }

  // Timeline items: comments + attachments + created event, sorted DESC by timestamp.
  const timelineItems = $derived.by(() => {
    /** @type {Array<{ id: string, ts: string, kind: 'comment' | 'attachment' | 'created', payload: any }>} */
    const items = [];
    for (const c of comments) {
      items.push({ id: `comment-${c.id}`, ts: c.commented_on || '', kind: 'comment', payload: c });
    }
    for (const a of attachments) {
      items.push({
        id: `attachment-${a.id}`,
        ts: a.created_on || a.created_at || '',
        kind: 'attachment',
        payload: a
      });
    }
    if (lead?.created_at || lead?.created_on) {
      items.push({
        id: `created-${lead.id}`,
        ts: lead.created_at || lead.created_on,
        kind: 'created',
        payload: lead
      });
    }
    return items.sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime());
  });
</script>

<svelte:head>
  <title>{fullName} · BottleCRM</title>
</svelte:head>

<PageHeader
  title={fullName}
  subtitle={lead?.title || ''}
  breadcrumb={[{ label: 'Leads', href: '/leads' }, { label: fullName }]}
>
  {#snippet meta()}
    <div
      class="flex flex-wrap items-center gap-3 text-[12px] leading-none text-[color:var(--text-subtle)]"
    >
      {#if lead?.created_at || lead?.created_on}
        <span>Created {formatRelativeDate(lead.created_at || lead.created_on)}</span>
      {/if}
      {#if lead?.company_name}
        <span>·</span>
        <span class="flex items-center gap-1">
          <Building2 class="size-3" />
          {lead.company_name}
        </span>
      {/if}
      {#if assignedUsers.length > 0}
        <span>·</span>
        <span class="flex items-center gap-1.5">
          <span
            class="flex size-4 items-center justify-center rounded-full bg-[color:var(--bg-elevated)] text-[9px] font-medium text-[color:var(--text-muted)]"
          >
            {getNameInitials(assignedUsers[0].email, '')}
          </span>
          {assignedUsers[0].email}{#if assignedUsers.length > 1}
            <span class="text-[color:var(--text-subtle)]">+{assignedUsers.length - 1}</span>
          {/if}
        </span>
      {/if}
    </div>
  {/snippet}

  {#snippet actions()}
    <div class="flex items-center gap-1.5">
      {#if lead?.email}
        <Button variant="ghost" size="icon" aria-label="Email" href="mailto:{lead.email}">
          <Mail class="size-4" />
        </Button>
      {/if}
      {#if lead?.phone}
        <Button variant="ghost" size="icon" aria-label="Call" href="tel:{lead.phone}">
          <Phone class="size-4" />
        </Button>
      {/if}
      <Button variant="ghost" size="icon" aria-label="More"><MoreHorizontal class="size-4" /></Button>
      <Button
        variant="outline"
        size="sm"
        onclick={() => lead?.id && goto(`/leads/${lead.id}/edit`)}
      >
        <Pencil class="mr-1.5 size-3.5" /> Edit
      </Button>
      <Button variant="default" size="sm">
        <ArrowRightCircle class="mr-1.5 size-3.5" /> Convert
      </Button>
    </div>
  {/snippet}
</PageHeader>

<!-- Stage stepper -->
<div class="px-7 pb-3 md:px-8">
  <StageStepper stages={stepperStages} current={normalizedStatus} />
</div>

<!-- Tabs -->
<Tabs.Root bind:value={tab} class="px-7 md:px-8">
  <Tabs.List class="">
    <Tabs.Trigger class="" value="overview">Overview</Tabs.Trigger>
    <Tabs.Trigger class="" value="activity">
      Activity
      <span
        class="ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[color:var(--bg-elevated)] px-1 text-[10px] tabular-nums text-[color:var(--text-subtle)]"
      >
        {timelineItems.length}
      </span>
    </Tabs.Trigger>
    <Tabs.Trigger class="" value="files">
      Files
      <span
        class="ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[color:var(--bg-elevated)] px-1 text-[10px] tabular-nums text-[color:var(--text-subtle)]"
      >
        {attachments.length}
      </span>
    </Tabs.Trigger>
  </Tabs.List>

  <Tabs.Content class="" value="overview">
    <div class="grid grid-cols-1 gap-6 pt-4 pb-8 lg:grid-cols-[1fr_320px]">
      <!-- Main column -->
      <div class="flex flex-col gap-6">
        <!-- About card -->
        <SectionCard title="About">
            {#if lead?.description}
              <p class="text-[13px] leading-[1.6] whitespace-pre-wrap text-[color:var(--text-muted)]">
                {lead.description}
              </p>
            {:else}
              <p class="text-[12px] italic text-[color:var(--text-subtle)]">No description.</p>
            {/if}
          </SectionCard>

        <!-- Custom fields -->
        {#if customFieldDefinitions.length > 0}
          <CustomFieldsPanel
            target="Lead"
            definitions={customFieldDefinitions}
            values={customFieldValues}
            title="Custom Fields"
          />
        {/if}

        <!-- Deal card -->
        {#if hasDeal}
          <SectionCard title="Deal">
              <dl class="grid grid-cols-2 gap-x-6 gap-y-3 text-[12px] sm:grid-cols-3">
                <div class="flex flex-col gap-1">
                  <dt class="flex items-center gap-1 text-[11px] text-[color:var(--text-subtle)]">
                    <DollarSign class="size-3" /> Deal Value
                  </dt>
                  <dd class="text-[15px] font-medium tabular-nums text-[color:var(--text)]">
                    {lead?.opportunity_amount != null
                      ? formatCurrency(lead.opportunity_amount, lead?.currency || 'USD')
                      : '—'}
                  </dd>
                </div>
                <div class="flex flex-col gap-1">
                  <dt class="flex items-center gap-1 text-[11px] text-[color:var(--text-subtle)]">
                    <Target class="size-3" /> Probability
                  </dt>
                  <dd class="text-[color:var(--text)]">
                    {#if probability !== null}
                      <div class="flex items-center gap-2">
                        <span class="text-[13px] tabular-nums">{probability}%</span>
                        <div
                          class="h-1.5 flex-1 overflow-hidden rounded-full bg-[color:var(--bg-elevated)]"
                        >
                          <div
                            class="h-full rounded-full bg-[color:var(--color-primary-default)]"
                            style="width: {probability}%"
                          ></div>
                        </div>
                      </div>
                    {:else}
                      <span class="text-[color:var(--text-muted)]">—</span>
                    {/if}
                  </dd>
                </div>
                <div class="flex flex-col gap-1">
                  <dt class="flex items-center gap-1 text-[11px] text-[color:var(--text-subtle)]">
                    <Calendar class="size-3" /> Close Date
                  </dt>
                  <dd class="text-[13px] text-[color:var(--text)]">
                    {lead?.close_date ? formatDate(lead.close_date) : '—'}
                  </dd>
                </div>
              </dl>
            </SectionCard>
        {/if}

        <!-- Contact info card -->
        {#if hasContactLinks}
          <SectionCard title="Contact">
              <dl class="grid grid-cols-1 gap-y-3 text-[12px] sm:grid-cols-2">
                {#if lead?.email}
                  <div class="flex items-start gap-2">
                    <Mail
                      class="mt-0.5 size-3.5 shrink-0 text-[color:var(--text-subtle)]"
                      aria-hidden="true"
                    />
                    <div class="flex min-w-0 flex-col">
                      <dt class="text-[11px] text-[color:var(--text-subtle)]">Email</dt>
                      <dd>
                        <a
                          href="mailto:{lead.email}"
                          class="truncate text-[color:var(--color-primary-default)] hover:underline"
                        >
                          {lead.email}
                        </a>
                      </dd>
                    </div>
                  </div>
                {/if}
                {#if lead?.phone}
                  <div class="flex items-start gap-2">
                    <Phone
                      class="mt-0.5 size-3.5 shrink-0 text-[color:var(--text-subtle)]"
                      aria-hidden="true"
                    />
                    <div class="flex min-w-0 flex-col">
                      <dt class="text-[11px] text-[color:var(--text-subtle)]">Phone</dt>
                      <dd>
                        <a
                          href="tel:{lead.phone}"
                          class="truncate text-[color:var(--color-primary-default)] hover:underline"
                        >
                          {lead.phone}
                        </a>
                      </dd>
                    </div>
                  </div>
                {/if}
                {#if lead?.job_title}
                  <div class="flex items-start gap-2">
                    <Briefcase
                      class="mt-0.5 size-3.5 shrink-0 text-[color:var(--text-subtle)]"
                      aria-hidden="true"
                    />
                    <div class="flex min-w-0 flex-col">
                      <dt class="text-[11px] text-[color:var(--text-subtle)]">Job Title</dt>
                      <dd class="truncate text-[color:var(--text)]">{lead.job_title}</dd>
                    </div>
                  </div>
                {/if}
                {#if lead?.website}
                  <div class="flex items-start gap-2">
                    <Globe
                      class="mt-0.5 size-3.5 shrink-0 text-[color:var(--text-subtle)]"
                      aria-hidden="true"
                    />
                    <div class="flex min-w-0 flex-col">
                      <dt class="text-[11px] text-[color:var(--text-subtle)]">Website</dt>
                      <dd>
                        <a
                          href={normalizeUrl(lead.website)}
                          target="_blank"
                          rel="noopener noreferrer"
                          class="inline-flex items-center gap-1 truncate text-[color:var(--color-primary-default)] hover:underline"
                        >
                          {lead.website}
                          <ExternalLink class="size-3 shrink-0" aria-hidden="true" />
                        </a>
                      </dd>
                    </div>
                  </div>
                {/if}
                {#if lead?.linkedin_url}
                  <div class="flex items-start gap-2">
                    <Linkedin
                      class="mt-0.5 size-3.5 shrink-0 text-[color:var(--text-subtle)]"
                      aria-hidden="true"
                    />
                    <div class="flex min-w-0 flex-col">
                      <dt class="text-[11px] text-[color:var(--text-subtle)]">LinkedIn</dt>
                      <dd>
                        <a
                          href={normalizeUrl(lead.linkedin_url)}
                          target="_blank"
                          rel="noopener noreferrer"
                          class="inline-flex items-center gap-1 truncate text-[color:var(--color-primary-default)] hover:underline"
                        >
                          {lead.linkedin_url}
                          <ExternalLink class="size-3 shrink-0" aria-hidden="true" />
                        </a>
                      </dd>
                    </div>
                  </div>
                {/if}
              </dl>
            </SectionCard>
        {/if}

        <!-- Address card -->
        {#if hasAddress}
          <SectionCard title="Address">
              <div class="flex items-start gap-2 text-[12px]">
                <MapPin
                  class="mt-0.5 size-3.5 shrink-0 text-[color:var(--text-subtle)]"
                  aria-hidden="true"
                />
                <address class="flex flex-col gap-0.5 not-italic text-[color:var(--text-muted)]">
                  {#each addressLines as line}
                    <span>{line}</span>
                  {/each}
                </address>
              </div>
            </SectionCard>
        {/if}

        <!-- Activity timeline card -->
        <SectionCard title="Activity" class="px-4 py-2">
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
                  <TimelineItem time={item.ts ? formatRelativeDate(item.ts) : ''}>
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
                    {#snippet text()}Lead created{/snippet}
                  </TimelineItem>
                {/if}
              {/each}
            </Timeline>
          </SectionCard>
      </div>

      <!-- Right rail -->
      <div class="flex flex-col gap-6">
        <SectionCard title="Details">
            <dl class="grid grid-cols-1 gap-y-3 text-[12px]">
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Status</dt>
                <dd>
                  {#if normalizedStatus}
                    <Badge
                      variant="secondary"
                      class={getOptionStyle(normalizedStatus, leadStatusOptions)}
                    >
                      {getOptionLabel(normalizedStatus, leadStatusOptions)}
                    </Badge>
                  {:else}
                    <span class="text-[color:var(--text-muted)]">—</span>
                  {/if}
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Rating</dt>
                <dd>
                  {#if normalizedRating}
                    <Badge
                      variant="secondary"
                      class={getOptionStyle(normalizedRating, leadRatingOptions)}
                    >
                      <Star class="mr-1 size-3" />
                      {getOptionLabel(normalizedRating, leadRatingOptions)}
                    </Badge>
                  {:else}
                    <span class="text-[color:var(--text-muted)]">—</span>
                  {/if}
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Source</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">
                  {sourceLabel || '—'}
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Industry</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">
                  {industryLabel || '—'}
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Company</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">
                  {lead?.company_name || '—'}
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Created by</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">
                  {lead?.created_by?.email || '—'}
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Updated</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">
                  {lead?.updated_at ? formatRelativeDate(lead.updated_at) : '—'}
                </dd>
              </div>
            </dl>
          </SectionCard>

        <!-- People -->
        <SectionCard title="People">
            <div class="flex flex-col gap-3 text-[12px]">
              <div>
                <div class="mb-1.5 flex items-center gap-1 text-[11px] text-[color:var(--text-subtle)]">
                  <UserCheck class="size-3" /> Assigned to
                </div>
                {#if assignedUsers.length === 0}
                  <p class="italic text-[color:var(--text-subtle)]">Unassigned</p>
                {:else}
                  <ul class="flex flex-col gap-1.5">
                    {#each assignedUsers as user (user.id)}
                      <li class="flex items-center gap-2">
                        <span
                          class="flex size-5 items-center justify-center rounded-full bg-[color:var(--color-primary-light)] text-[9px] font-semibold text-[color:var(--color-primary-default)]"
                        >
                          {getNameInitials(user.email, '')}
                        </span>
                        <span class="truncate text-[color:var(--text-muted)]">{user.email}</span>
                      </li>
                    {/each}
                  </ul>
                {/if}
              </div>
              {#if teams.length > 0}
                <div>
                  <div
                    class="mb-1.5 flex items-center gap-1 text-[11px] text-[color:var(--text-subtle)]"
                  >
                    <Users class="size-3" /> Teams
                  </div>
                  <div class="flex flex-wrap gap-1.5">
                    {#each teams as team (team.id)}
                      <Badge
                        variant="secondary"
                        class="bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)]"
                      >
                        {team.name}
                      </Badge>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          </SectionCard>

        <!-- Dates -->
        {#if lead?.last_contacted || lead?.next_follow_up}
          <SectionCard title="Dates">
              <dl class="grid grid-cols-1 gap-y-3 text-[12px]">
                {#if lead?.last_contacted}
                  <div class="flex items-baseline justify-between gap-3">
                    <dt class="text-[color:var(--text-subtle)]">Last contact</dt>
                    <dd
                      class="truncate text-right text-[color:var(--text-muted)]"
                      title={formatDate(lead.last_contacted)}
                    >
                      {formatRelativeDate(lead.last_contacted)}
                    </dd>
                  </div>
                {/if}
                {#if lead?.next_follow_up}
                  <div class="flex items-baseline justify-between gap-3">
                    <dt class="text-[color:var(--text-subtle)]">Next follow-up</dt>
                    <dd
                      class="truncate text-right text-[color:var(--text-muted)]"
                      title={formatDate(lead.next_follow_up)}
                    >
                      {formatDate(lead.next_follow_up)}
                    </dd>
                  </div>
                {/if}
              </dl>
            </SectionCard>
        {/if}

        <SectionCard title="Tags">
            {#if tags.length === 0}
              <p class="text-[12px] italic text-[color:var(--text-subtle)]">No tags.</p>
            {:else}
              <div class="flex flex-wrap gap-1.5">
                {#each tags as tag, i (tag.id ?? tag.slug ?? tag.name ?? i)}
                  <Badge
                    variant="secondary"
                    class="bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)]"
                  >
                    {tag.name}
                  </Badge>
                {/each}
              </div>
            {/if}
          </SectionCard>
      </div>
    </div>
  </Tabs.Content>

  <Tabs.Content class="" value="activity">
    <div class="pt-4 pb-8">
      <SectionCard title="All activity" class="px-4 py-2">
          <Timeline isEmpty={timelineItems.length === 0}>
            {#each timelineItems as item (item.id)}
              {#if item.kind === 'comment'}
                <TimelineItem
                  variant="violet"
                  time={item.ts ? formatRelativeDate(item.ts) : ''}
                  quote={item.payload.comment || ''}
                >
                  {#snippet icon()}<MessageSquare class="size-3.5" />{/snippet}
                  {#snippet text()}<strong
                      >{item.payload.commented_by_user || 'Someone'}</strong
                    > commented{/snippet}
                </TimelineItem>
              {:else if item.kind === 'attachment'}
                <TimelineItem time={item.ts ? formatRelativeDate(item.ts) : ''}>
                  {#snippet icon()}<Paperclip class="size-3.5" />{/snippet}
                  {#snippet text()}<strong>{item.payload.created_by_user || 'Someone'}</strong>
                    uploaded <strong>{item.payload.file_name || 'a file'}</strong>{/snippet}
                </TimelineItem>
              {:else}
                <TimelineItem variant="success" time={item.ts ? formatRelativeDate(item.ts) : ''}>
                  {#snippet icon()}<Calendar class="size-3.5" />{/snippet}
                  {#snippet text()}Lead created{/snippet}
                </TimelineItem>
              {/if}
            {/each}
          </Timeline>
        </SectionCard>
    </div>
  </Tabs.Content>

  <Tabs.Content class="" value="files">
    <div class="pt-4 pb-8">
      <SectionCard title="Files">
          {#if attachments.length === 0}
            <p class="text-[12px] italic text-[color:var(--text-subtle)]">No files uploaded.</p>
          {:else}
            <ul class="flex flex-col divide-y divide-[color:var(--border-faint)]">
              {#each attachments as a (a.id)}
                <li class="flex items-center gap-3 py-2.5 text-[12px]">
                  <Paperclip class="size-3.5 shrink-0 text-[color:var(--text-subtle)]" />
                  <span class="flex-1 truncate text-[color:var(--text)]">
                    {a.file_name || 'File'}
                  </span>
                  <span class="text-[11px] text-[color:var(--text-subtle)]">
                    {a.created_on ? formatRelativeDate(a.created_on) : ''}
                  </span>
                </li>
              {/each}
            </ul>
          {/if}
        </SectionCard>
    </div>
  </Tabs.Content>
</Tabs.Root>
