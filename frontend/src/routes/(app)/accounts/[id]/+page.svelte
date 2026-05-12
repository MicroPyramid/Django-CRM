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
    Globe,
    Briefcase,
    Building2,
    DollarSign,
    MapPin,
    Users,
    UserCheck,
    FileText,
    ExternalLink,
    Contact as ContactIcon,
    Banknote,
    CheckSquare,
    Ticket,
    Receipt,
    Target,
    Lock,
    Hash
  } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Timeline, TimelineItem } from '$lib/components/ui/timeline';
  import { SectionCard } from '$lib/components/ui/section-card/index.js';
  import * as Tabs from '$lib/components/ui/tabs/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import {
    formatRelativeDate,
    formatDate,
    formatCurrency,
    getNameInitials
  } from '$lib/utils/formatting.js';
  import {
    opportunityStageOptions,
    taskStatusOptions,
    getOptionLabel,
    getOptionStyle
  } from '$lib/utils/table-helpers.js';
  import { getCountryName } from '$lib/constants/countries.js';

  /** @type {{ data: {
   *   account: any,
   *   comments: any[],
   *   attachments: any[],
   *   contacts: any[],
   *   opportunities: any[],
   *   cases: any[],
   *   tasks: any[],
   *   invoices: any[],
   *   emails: any[],
   *   tags: any[],
   *   teams: any[],
   *   assignedTo: any[],
   *   commentPermission: boolean
   * } }} */
  let { data } = $props();

  const account = $derived(data.account || {});
  const comments = $derived(data.comments || []);
  const attachments = $derived(data.attachments || []);
  const contacts = $derived(data.contacts || []);
  const opportunities = $derived(data.opportunities || []);
  const cases = $derived(data.cases || []);
  const tasksList = $derived(data.tasks || []);
  const invoices = $derived(data.invoices || []);
  const emails = $derived(data.emails || []);
  const tags = $derived(data.tags || []);
  const teams = $derived(data.teams || []);
  const assignedRaw = $derived(data.assignedTo || []);

  let tab = $state('overview');

  const isActive = $derived(account?.is_active !== false);
  const accountName = $derived(account?.name || 'Account');

  const industryLabel = $derived(
    account?.industry
      ? account.industry.replace(/\b\w+/g, (/** @type {string} */ w) =>
          w.charAt(0) + w.slice(1).toLowerCase()
        )
      : ''
  );

  /** @typedef {{ id: string, email: string, photo?: string }} AssignedUser */
  /** @type {AssignedUser[]} */
  const assignedUsers = $derived(
    Array.isArray(assignedRaw)
      ? assignedRaw
          .map((/** @type {any} */ p) => ({
            id: p?.id,
            email: p?.user_details?.email || p?.user?.email || '',
            photo: p?.user_details?.profile_pic
          }))
          .filter((/** @type {AssignedUser} */ u) => u.email)
      : []
  );

  /** @type {{ id: string, name: string }[]} */
  const teamItems = $derived(
    Array.isArray(teams)
      ? teams.map((/** @type {any} */ t) => ({ id: t?.id, name: t?.name || '' }))
      : []
  );

  const hasContactInfo = $derived(
    !!(account?.email || account?.phone || account?.website)
  );

  const hasBusinessInfo = $derived(
    account?.industry || account?.number_of_employees != null || account?.annual_revenue != null
  );

  const hasAddress = $derived(
    !!(account?.address_line || account?.city || account?.state || account?.postcode || account?.country)
  );

  const addressLines = $derived(
    [
      account?.address_line,
      [account?.city, account?.state, account?.postcode].filter(Boolean).join(', '),
      account?.country_display || getCountryName(account?.country)
    ].filter(Boolean)
  );

  function normalizeUrl(/** @type {string} */ raw) {
    if (!raw) return '';
    return /^https?:\/\//i.test(raw) ? raw : `https://${raw}`;
  }

  function fullContactName(/** @type {any} */ c) {
    const parts = [c?.salutation, c?.first_name, c?.last_name].filter(Boolean);
    return parts.join(' ') || c?.email || c?.primary_email || 'Contact';
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
    if (account?.created_at) {
      items.push({
        id: `created-${account.id}`,
        ts: account.created_at,
        kind: 'created',
        payload: account
      });
    }
    return items.sort((a, b) => new Date(b.ts).getTime() - new Date(a.ts).getTime());
  });

  const totalOpportunityValue = $derived(
    opportunities.reduce(
      (/** @type {number} */ sum, /** @type {any} */ o) => sum + (parseFloat(o?.amount) || 0),
      0
    )
  );

  const openOpportunities = $derived(
    opportunities.filter(
      (/** @type {any} */ o) => !['CLOSED_WON', 'CLOSED_LOST'].includes(o?.stage)
    ).length
  );

  const openCases = $derived(
    cases.filter((/** @type {any} */ c) => (c?.status || '').toLowerCase() !== 'closed').length
  );

  const openTasks = $derived(
    tasksList.filter(
      (/** @type {any} */ t) => (t?.status || '').toUpperCase() !== 'COMPLETED'
    ).length
  );

  const outstandingInvoiceAmount = $derived(
    invoices.reduce(
      (/** @type {number} */ sum, /** @type {any} */ inv) => sum + (parseFloat(inv?.amount_due) || 0),
      0
    )
  );

  const accountCurrency = $derived(account?.currency || 'USD');
</script>

<svelte:head>
  <title>{accountName} · BottleCRM</title>
</svelte:head>

<PageHeader
  title={accountName}
  subtitle={industryLabel}
  breadcrumb={[{ label: 'Accounts', href: '/accounts' }, { label: accountName }]}
>
  {#snippet meta()}
    <div
      class="flex flex-wrap items-center gap-3 text-[12px] leading-none text-[color:var(--text-subtle)]"
    >
      {#if account?.created_at}
        <span>Created {formatRelativeDate(account.created_at)}</span>
      {/if}
      {#if !isActive}
        <span>·</span>
        <Badge
          variant="secondary"
          class="bg-[var(--color-negative-light)] text-[var(--color-negative-default)]"
        >
          <Lock class="mr-1 size-3" /> Closed
        </Badge>
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
      {#if account?.email}
        <Button variant="ghost" size="icon" aria-label="Email" href="mailto:{account.email}">
          <Mail class="size-4" />
        </Button>
      {/if}
      {#if account?.phone}
        <Button variant="ghost" size="icon" aria-label="Call" href="tel:{account.phone}">
          <Phone class="size-4" />
        </Button>
      {/if}
      <Button variant="ghost" size="icon" aria-label="More">
        <MoreHorizontal class="size-4" />
      </Button>
      <Button
        variant="outline"
        size="sm"
        onclick={() => account?.id && goto(`/accounts?view=${account.id}`)}
      >
        <Pencil class="mr-1.5 size-3.5" /> Edit
      </Button>
    </div>
  {/snippet}
</PageHeader>

<!-- KPI strip -->
<div class="grid grid-cols-2 gap-3 px-7 pb-3 md:grid-cols-4 md:px-8">
  <SectionCard class="px-4 py-3" padded={false}>
    <div class="flex items-center gap-2 text-[11px] text-[color:var(--text-subtle)]">
      <Target class="size-3" /> Open Opportunities
    </div>
    <div class="mt-1 text-[18px] font-medium tabular-nums">{openOpportunities}</div>
    <div class="text-[11px] text-[color:var(--text-subtle)]">
      {opportunities.length} total · {formatCurrency(totalOpportunityValue, accountCurrency)}
    </div>
  </SectionCard>
  <SectionCard class="px-4 py-3" padded={false}>
    <div class="flex items-center gap-2 text-[11px] text-[color:var(--text-subtle)]">
      <ContactIcon class="size-3" /> Contacts
    </div>
    <div class="mt-1 text-[18px] font-medium tabular-nums">{contacts.length}</div>
  </SectionCard>
  <SectionCard class="px-4 py-3" padded={false}>
    <div class="flex items-center gap-2 text-[11px] text-[color:var(--text-subtle)]">
      <Ticket class="size-3" /> Open Cases
    </div>
    <div class="mt-1 text-[18px] font-medium tabular-nums">{openCases}</div>
    <div class="text-[11px] text-[color:var(--text-subtle)]">{cases.length} total</div>
  </SectionCard>
  <SectionCard class="px-4 py-3" padded={false}>
    <div class="flex items-center gap-2 text-[11px] text-[color:var(--text-subtle)]">
      <Receipt class="size-3" /> Outstanding
    </div>
    <div class="mt-1 text-[18px] font-medium tabular-nums">
      {formatCurrency(outstandingInvoiceAmount, accountCurrency)}
    </div>
    <div class="text-[11px] text-[color:var(--text-subtle)]">{invoices.length} invoices</div>
  </SectionCard>
</div>

<!-- Tabs -->
<Tabs.Root bind:value={tab} class="px-7 md:px-8">
  <Tabs.List class="">
    <Tabs.Trigger class="" value="overview">Overview</Tabs.Trigger>
    <Tabs.Trigger class="" value="contacts">
      Contacts
      <span
        class="ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[color:var(--bg-elevated)] px-1 text-[10px] tabular-nums text-[color:var(--text-subtle)]"
      >
        {contacts.length}
      </span>
    </Tabs.Trigger>
    <Tabs.Trigger class="" value="opportunities">
      Opportunities
      <span
        class="ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[color:var(--bg-elevated)] px-1 text-[10px] tabular-nums text-[color:var(--text-subtle)]"
      >
        {opportunities.length}
      </span>
    </Tabs.Trigger>
    <Tabs.Trigger class="" value="cases">
      Cases
      <span
        class="ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[color:var(--bg-elevated)] px-1 text-[10px] tabular-nums text-[color:var(--text-subtle)]"
      >
        {cases.length}
      </span>
    </Tabs.Trigger>
    <Tabs.Trigger class="" value="tasks">
      Tasks
      <span
        class="ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[color:var(--bg-elevated)] px-1 text-[10px] tabular-nums text-[color:var(--text-subtle)]"
      >
        {tasksList.length}
      </span>
    </Tabs.Trigger>
    <Tabs.Trigger class="" value="invoices">
      Invoices
      <span
        class="ml-1.5 inline-flex h-4 min-w-[16px] items-center justify-center rounded-full bg-[color:var(--bg-elevated)] px-1 text-[10px] tabular-nums text-[color:var(--text-subtle)]"
      >
        {invoices.length}
      </span>
    </Tabs.Trigger>
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

  <!-- OVERVIEW -->
  <Tabs.Content class="" value="overview">
    <div class="grid grid-cols-1 gap-6 pt-4 pb-8 lg:grid-cols-[1fr_320px]">
      <!-- Main column -->
      <div class="flex flex-col gap-6">
        <!-- About card -->
        <SectionCard title="About">
          {#if account?.description}
            <p class="text-[13px] leading-[1.6] whitespace-pre-wrap text-[color:var(--text-muted)]">
              {account.description}
            </p>
          {:else}
            <p class="text-[12px] italic text-[color:var(--text-subtle)]">No description.</p>
          {/if}
        </SectionCard>

        <!-- Business info card -->
        {#if hasBusinessInfo}
          <SectionCard title="Business">
            <dl class="grid grid-cols-2 gap-x-6 gap-y-3 text-[12px] sm:grid-cols-3">
                {#if account?.industry}
                  <div class="flex flex-col gap-1">
                    <dt class="flex items-center gap-1 text-[11px] text-[color:var(--text-subtle)]">
                      <Briefcase class="size-3" /> Industry
                    </dt>
                    <dd class="text-[13px] text-[color:var(--text)]">{industryLabel}</dd>
                  </div>
                {/if}
                {#if account?.number_of_employees != null}
                  <div class="flex flex-col gap-1">
                    <dt class="flex items-center gap-1 text-[11px] text-[color:var(--text-subtle)]">
                      <Users class="size-3" /> Employees
                    </dt>
                    <dd class="text-[13px] tabular-nums text-[color:var(--text)]">
                      {account.number_of_employees}
                    </dd>
                  </div>
                {/if}
                {#if account?.annual_revenue != null}
                  <div class="flex flex-col gap-1">
                    <dt class="flex items-center gap-1 text-[11px] text-[color:var(--text-subtle)]">
                      <DollarSign class="size-3" /> Annual Revenue
                    </dt>
                    <dd class="text-[15px] font-medium tabular-nums text-[color:var(--text)]">
                      {formatCurrency(parseFloat(account.annual_revenue), accountCurrency)}
                    </dd>
                  </div>
                {/if}
              </dl>
          </SectionCard>
        {/if}

        <!-- Contact info card -->
        {#if hasContactInfo}
          <SectionCard title="Contact">
            <dl class="grid grid-cols-1 gap-y-3 text-[12px] sm:grid-cols-2">
                {#if account?.email}
                  <div class="flex items-start gap-2">
                    <Mail
                      class="mt-0.5 size-3.5 shrink-0 text-[color:var(--text-subtle)]"
                      aria-hidden="true"
                    />
                    <div class="flex min-w-0 flex-col">
                      <dt class="text-[11px] text-[color:var(--text-subtle)]">Email</dt>
                      <dd>
                        <a
                          href="mailto:{account.email}"
                          class="truncate text-[color:var(--color-primary-default)] hover:underline"
                        >
                          {account.email}
                        </a>
                      </dd>
                    </div>
                  </div>
                {/if}
                {#if account?.phone}
                  <div class="flex items-start gap-2">
                    <Phone
                      class="mt-0.5 size-3.5 shrink-0 text-[color:var(--text-subtle)]"
                      aria-hidden="true"
                    />
                    <div class="flex min-w-0 flex-col">
                      <dt class="text-[11px] text-[color:var(--text-subtle)]">Phone</dt>
                      <dd>
                        <a
                          href="tel:{account.phone}"
                          class="truncate text-[color:var(--color-primary-default)] hover:underline"
                        >
                          {account.phone}
                        </a>
                      </dd>
                    </div>
                  </div>
                {/if}
                {#if account?.website}
                  <div class="flex items-start gap-2">
                    <Globe
                      class="mt-0.5 size-3.5 shrink-0 text-[color:var(--text-subtle)]"
                      aria-hidden="true"
                    />
                    <div class="flex min-w-0 flex-col">
                      <dt class="text-[11px] text-[color:var(--text-subtle)]">Website</dt>
                      <dd>
                        <a
                          href={normalizeUrl(account.website)}
                          target="_blank"
                          rel="noopener noreferrer"
                          class="inline-flex items-center gap-1 truncate text-[color:var(--color-primary-default)] hover:underline"
                        >
                          {account.website}
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

        <!-- Activity preview card -->
        <SectionCard title="Activity">
            <Timeline isEmpty={timelineItems.length === 0}>
              {#each timelineItems.slice(0, 5) as item (item.id)}
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
                    {#snippet text()}Account created{/snippet}
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
                  <Badge
                    variant="secondary"
                    class={isActive
                      ? 'bg-[var(--color-success-light)] text-[var(--color-success-default)]'
                      : 'bg-[var(--color-negative-light)] text-[var(--color-negative-default)]'}
                  >
                    {isActive ? 'Active' : 'Closed'}
                  </Badge>
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Industry</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">
                  {industryLabel || '—'}
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Currency</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">
                  {account?.currency || '—'}
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Created by</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">
                  {account?.created_by?.email || '—'}
                </dd>
              </div>
              <div class="flex items-baseline justify-between gap-3">
                <dt class="text-[color:var(--text-subtle)]">Created</dt>
                <dd class="truncate text-right text-[color:var(--text-muted)]">
                  {account?.created_at ? formatRelativeDate(account.created_at) : '—'}
                </dd>
              </div>
          </dl>
        </SectionCard>

        <!-- People -->
        <SectionCard title="People">
          <div class="flex flex-col gap-3 text-[12px]">
              <div>
                <div
                  class="mb-1.5 flex items-center gap-1 text-[11px] text-[color:var(--text-subtle)]"
                >
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
              {#if teamItems.length > 0}
                <div>
                  <div
                    class="mb-1.5 flex items-center gap-1 text-[11px] text-[color:var(--text-subtle)]"
                  >
                    <Users class="size-3" /> Teams
                  </div>
                  <div class="flex flex-wrap gap-1.5">
                    {#each teamItems as team (team.id)}
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

  <!-- CONTACTS -->
  <Tabs.Content class="" value="contacts">
    <div class="pt-4 pb-8">
      <SectionCard title="Contacts">
          {#if contacts.length === 0}
            <p class="text-[12px] italic text-[color:var(--text-subtle)]">
              No contacts linked to this account.
            </p>
          {:else}
            <ul class="flex flex-col divide-y divide-[color:var(--border-faint)]">
              {#each contacts as c (c.id)}
                <li class="flex items-center gap-3 py-2.5 text-[12px]">
                  <span
                    class="flex size-7 shrink-0 items-center justify-center rounded-full bg-[color:var(--color-primary-light)] text-[10px] font-semibold text-[color:var(--color-primary-default)]"
                  >
                    {getNameInitials(fullContactName(c), '')}
                  </span>
                  <div class="flex min-w-0 flex-1 flex-col">
                    <span class="truncate font-medium text-[color:var(--text)]">
                      {fullContactName(c)}
                    </span>
                    {#if c.email || c.primary_email}
                      <a
                        href="mailto:{c.email || c.primary_email}"
                        class="truncate text-[11px] text-[color:var(--color-primary-default)] hover:underline"
                      >
                        {c.email || c.primary_email}
                      </a>
                    {/if}
                  </div>
                  {#if c.phone || c.mobile_number}
                    <a
                      href="tel:{c.phone || c.mobile_number}"
                      class="text-[11px] text-[color:var(--text-muted)] hover:underline"
                    >
                      {c.phone || c.mobile_number}
                    </a>
                  {/if}
                </li>
              {/each}
          </ul>
        {/if}
      </SectionCard>
    </div>
  </Tabs.Content>

  <!-- OPPORTUNITIES -->
  <Tabs.Content class="" value="opportunities">
    <div class="pt-4 pb-8">
      <SectionCard title="Opportunities">
          {#if opportunities.length === 0}
            <p class="text-[12px] italic text-[color:var(--text-subtle)]">
              No opportunities linked.
            </p>
          {:else}
            <ul class="flex flex-col divide-y divide-[color:var(--border-faint)]">
              {#each opportunities as o (o.id)}
                <li class="flex items-center gap-3 py-2.5 text-[12px]">
                  <Target class="size-3.5 shrink-0 text-[color:var(--text-subtle)]" />
                  <a
                    href="/opportunities/{o.id}"
                    class="flex-1 truncate text-[color:var(--color-primary-default)] hover:underline"
                  >
                    {o.name}
                  </a>
                  {#if o.stage}
                    <Badge
                      variant="secondary"
                      class={getOptionStyle(o.stage, opportunityStageOptions)}
                    >
                      {getOptionLabel(o.stage, opportunityStageOptions) || o.stage}
                    </Badge>
                  {/if}
                  <span class="w-24 text-right tabular-nums text-[color:var(--text-muted)]">
                    {formatCurrency(parseFloat(o.amount) || 0, o.currency || accountCurrency)}
                  </span>
                </li>
              {/each}
          </ul>
        {/if}
      </SectionCard>
    </div>
  </Tabs.Content>

  <!-- CASES -->
  <Tabs.Content class="" value="cases">
    <div class="pt-4 pb-8">
      <SectionCard title="Cases">
          {#if cases.length === 0}
            <p class="text-[12px] italic text-[color:var(--text-subtle)]">No cases.</p>
          {:else}
            <ul class="flex flex-col divide-y divide-[color:var(--border-faint)]">
              {#each cases as c (c.id)}
                <li class="flex items-center gap-3 py-2.5 text-[12px]">
                  <Ticket class="size-3.5 shrink-0 text-[color:var(--text-subtle)]" />
                  <a
                    href="/tickets/{c.id}"
                    class="flex-1 truncate text-[color:var(--color-primary-default)] hover:underline"
                  >
                    {c.name}
                  </a>
                  {#if c.priority}
                    <Badge
                      variant="secondary"
                      class="bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)]"
                    >
                      {c.priority}
                    </Badge>
                  {/if}
                  {#if c.status}
                    <Badge
                      variant="secondary"
                      class="bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)]"
                    >
                      {c.status}
                    </Badge>
                  {/if}
                </li>
              {/each}
          </ul>
        {/if}
      </SectionCard>
    </div>
  </Tabs.Content>

  <!-- TASKS -->
  <Tabs.Content class="" value="tasks">
    <div class="pt-4 pb-8">
      <SectionCard title="Tasks">
          {#if tasksList.length === 0}
            <p class="text-[12px] italic text-[color:var(--text-subtle)]">No tasks.</p>
          {:else}
            <ul class="flex flex-col divide-y divide-[color:var(--border-faint)]">
              {#each tasksList as t (t.id)}
                <li class="flex items-center gap-3 py-2.5 text-[12px]">
                  <CheckSquare class="size-3.5 shrink-0 text-[color:var(--text-subtle)]" />
                  <span class="flex-1 truncate text-[color:var(--text)]">
                    {t.title}
                  </span>
                  {#if t.priority}
                    <Badge
                      variant="secondary"
                      class="bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)]"
                    >
                      {t.priority}
                    </Badge>
                  {/if}
                  {#if t.status}
                    <Badge
                      variant="secondary"
                      class={getOptionStyle(t.status, taskStatusOptions)}
                    >
                      {getOptionLabel(t.status, taskStatusOptions) || t.status}
                    </Badge>
                  {/if}
                  {#if t.due_date}
                    <span class="w-24 text-right text-[11px] text-[color:var(--text-subtle)]">
                      {formatDate(t.due_date)}
                    </span>
                  {/if}
                </li>
              {/each}
          </ul>
        {/if}
      </SectionCard>
    </div>
  </Tabs.Content>

  <!-- INVOICES -->
  <Tabs.Content class="" value="invoices">
    <div class="pt-4 pb-8">
      <SectionCard title="Invoices">
          {#if invoices.length === 0}
            <p class="text-[12px] italic text-[color:var(--text-subtle)]">No invoices.</p>
          {:else}
            <ul class="flex flex-col divide-y divide-[color:var(--border-faint)]">
              {#each invoices as inv (inv.id)}
                <li class="flex items-center gap-3 py-2.5 text-[12px]">
                  <Hash class="size-3.5 shrink-0 text-[color:var(--text-subtle)]" />
                  <a
                    href="/invoices/{inv.id}"
                    class="w-28 shrink-0 truncate text-[color:var(--color-primary-default)] hover:underline"
                  >
                    {inv.invoice_number || '—'}
                  </a>
                  <span class="flex-1 truncate text-[color:var(--text)]">
                    {inv.invoice_title || inv.client_name || ''}
                  </span>
                  {#if inv.status}
                    <Badge
                      variant="secondary"
                      class="bg-[color:var(--bg-elevated)] text-[color:var(--text-muted)]"
                    >
                      {inv.status}
                    </Badge>
                  {/if}
                  <span class="w-24 text-right tabular-nums text-[color:var(--text)]">
                    {formatCurrency(parseFloat(inv.total_amount) || 0, inv.currency || accountCurrency)}
                  </span>
                  {#if parseFloat(inv.amount_due) > 0}
                    <span
                      class="w-24 text-right tabular-nums text-[11px] text-[color:var(--color-negative-default)]"
                    >
                      due {formatCurrency(parseFloat(inv.amount_due) || 0, inv.currency || accountCurrency)}
                    </span>
                  {/if}
                </li>
              {/each}
            </ul>
          {/if}
      </SectionCard>
    </div>
  </Tabs.Content>

  <!-- ACTIVITY -->
  <Tabs.Content class="" value="activity">
    <div class="pt-4 pb-8">
      <SectionCard title="All activity">
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
                  {#snippet text()}Account created{/snippet}
                </TimelineItem>
              {/if}
            {/each}
          </Timeline>
      </SectionCard>
    </div>
  </Tabs.Content>

  <!-- FILES -->
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
