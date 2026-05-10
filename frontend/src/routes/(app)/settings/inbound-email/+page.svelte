<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';
  import { toast } from 'svelte-sonner';
  import { Plus, Mail, Trash2, Copy, Save, AlertTriangle } from '@lucide/svelte';
  import { PageHeader } from '$lib/components/layout';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  const priorities = $derived(data.priorities || []);
  const ticketTypes = $derived(data.ticketTypes || []);
  const mailboxes = $derived(data.mailboxes || []);
  const profiles = $derived(data.profiles || []);
  const origin = $derived(data.origin || '');

  let dialogOpen = $state(false);
  let dialogAddress = $state('');
  let dialogPriority = $state('Normal');
  let dialogTicketType = $state('');
  let dialogAssigneeId = $state('');

  function openCreate() {
    dialogAddress = '';
    dialogPriority = 'Normal';
    dialogTicketType = '';
    dialogAssigneeId = '';
    dialogOpen = true;
  }

  /** @param {string} mailboxId */
  function webhookUrl(mailboxId) {
    return `${origin}/api/cases/inbound/${mailboxId}/`;
  }

  /** @param {string} value */
  async function copyToClipboard(value) {
    try {
      await navigator.clipboard.writeText(value);
      toast.success('Copied');
    } catch {
      toast.error('Copy failed');
    }
  }

  $effect(() => {
    if (form?.success) {
      toast.success('Mailbox saved');
      dialogOpen = false;
      invalidateAll();
    } else if (form?.error) {
      const msg = typeof form.error === 'string' ? form.error : JSON.stringify(form.error);
      toast.error(msg);
    }
  });
</script>

<svelte:head>
  <title>Inbound Email - Settings - BottleCRM</title>
</svelte:head>

<PageHeader
  title="Inbound Email"
  subtitle="Customers email these addresses; replies thread back to the same ticket automatically"
>
  {#snippet actions()}
    <Button onclick={openCreate} class="gap-2">
      <Plus class="h-4 w-4" />
      New mailbox
    </Button>
  {/snippet}
</PageHeader>

<div class="flex-1 p-4 md:p-6 lg:p-8">
  <div class="mx-auto max-w-4xl space-y-6">
    <section
      class="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm text-amber-900 dark:border-amber-900/40 dark:bg-amber-900/20 dark:text-amber-200"
    >
      <div class="flex gap-2">
        <AlertTriangle class="h-4 w-4 flex-shrink-0" />
        <div>
          <p class="font-medium">AWS SES setup required.</p>
          <p>
            Create an SES Receipt Rule on a verified domain that publishes to an
            SNS Topic with action <strong>"SNS Notification with full content"</strong>.
            Subscribe the topic to the webhook URL shown below for each mailbox.
            The first POST will be a <code>SubscriptionConfirmation</code> — we
            confirm it automatically. Other providers (Mailgun, Postmark, IMAP)
            will be enabled in a follow-up.
          </p>
        </div>
      </div>
    </section>

    {#if mailboxes.length === 0}
      <section
        class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-8 text-center text-sm text-[var(--text-secondary)]"
      >
        <Mail class="mx-auto mb-3 h-10 w-10 text-[var(--text-tertiary)]" />
        <p>No inbound mailboxes yet.</p>
        <p class="mt-1">Click <strong>New mailbox</strong> to add one.</p>
      </section>
    {:else}
      <ul class="space-y-3">
        {#each mailboxes as mailbox (mailbox.id)}
          <li
            class="rounded-lg border border-[var(--border-default)] bg-[var(--surface-default)] p-4"
          >
            <form
              method="POST"
              action="?/update"
              use:enhance={() => async ({ update }) => {
                await update();
              }}
              class="space-y-3"
            >
              <input type="hidden" name="id" value={mailbox.id} />

              <header class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <Mail class="h-4 w-4 text-[var(--text-secondary)]" />
                  <span class="font-medium text-[var(--text-primary)]">
                    {mailbox.address}
                  </span>
                  <span
                    class="rounded-full bg-[var(--surface-muted)] px-2 py-0.5 text-xs uppercase text-[var(--text-secondary)]"
                  >
                    {mailbox.provider}
                  </span>
                  {#if !mailbox.is_active}
                    <span class="rounded-full bg-slate-200 px-2 py-0.5 text-xs text-slate-700 dark:bg-slate-700 dark:text-slate-200">
                      Inactive
                    </span>
                  {/if}
                </div>
                <div class="flex items-center gap-1">
                  <Button type="submit" size="sm" class="gap-1">
                    <Save class="h-3.5 w-3.5" />
                    Save
                  </Button>
                </div>
              </header>

              <div class="grid grid-cols-1 gap-3 text-xs sm:grid-cols-2">
                <div class="space-y-1">
                  <Label class="text-xs">Webhook URL</Label>
                  <div class="flex items-center gap-1">
                    <code class="flex-1 truncate rounded bg-[var(--surface-muted)] px-2 py-1 text-[11px]">
                      {webhookUrl(mailbox.id)}
                    </code>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onclick={() => copyToClipboard(webhookUrl(mailbox.id))}
                      title="Copy URL"
                    >
                      <Copy class="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
                <div class="space-y-1">
                  <Label class="text-xs">Webhook secret</Label>
                  <div class="flex items-center gap-1">
                    <code class="flex-1 truncate rounded bg-[var(--surface-muted)] px-2 py-1 text-[11px]">
                      {mailbox.webhook_secret}
                    </code>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      onclick={() => copyToClipboard(mailbox.webhook_secret)}
                      title="Copy secret"
                    >
                      <Copy class="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>

                <div class="space-y-1">
                  <Label class="text-xs">Default priority</Label>
                  <select
                    name="default_priority"
                    value={mailbox.default_priority}
                    class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
                  >
                    {#each priorities as p (p)}
                      <option value={p}>{p}</option>
                    {/each}
                  </select>
                </div>

                <div class="space-y-1">
                  <Label class="text-xs">Default ticket type</Label>
                  <select
                    name="default_case_type"
                    value={mailbox.default_case_type || ''}
                    class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
                  >
                    {#each ticketTypes as t (t)}
                      <option value={t}>{t || '— None —'}</option>
                    {/each}
                  </select>
                </div>

                <div class="space-y-1 sm:col-span-2">
                  <Label class="text-xs">Default assignee</Label>
                  <select
                    name="default_assignee_id"
                    value={mailbox.default_assignee?.id || ''}
                    class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
                  >
                    <option value="">— Unassigned —</option>
                    {#each profiles as p (p.id)}
                      <option value={p.id}>{p.name}</option>
                    {/each}
                  </select>
                </div>

                <input
                  type="hidden"
                  name="address"
                  value={mailbox.address}
                />
                <input type="hidden" name="provider" value={mailbox.provider} />
                <input
                  type="hidden"
                  name="is_active"
                  value={mailbox.is_active === false ? 'false' : 'true'}
                />
              </div>
            </form>

            <div class="mt-3 flex justify-end border-t border-[var(--border-default)] pt-3">
              <form method="POST" action="?/delete" use:enhance class="inline">
                <input type="hidden" name="id" value={mailbox.id} />
                <Button
                  type="submit"
                  variant="outline"
                  size="sm"
                  class="gap-1 text-[var(--color-danger-default)]"
                >
                  <Trash2 class="h-3.5 w-3.5" />
                  Delete mailbox
                </Button>
              </form>
            </div>
          </li>
        {/each}
      </ul>
    {/if}
  </div>
</div>

<Dialog.Root bind:open={dialogOpen}>
  <Dialog.Content class="sm:max-w-md">
    <Dialog.Header>
      <Dialog.Title>New inbound mailbox</Dialog.Title>
      <Dialog.Description>
        Configure an address customers can email to open tickets.
      </Dialog.Description>
    </Dialog.Header>

    <form
      method="POST"
      action="?/create"
      use:enhance={() => async ({ update }) => {
        await update();
      }}
      class="space-y-4"
    >
      <input type="hidden" name="provider" value="ses" />
      <input type="hidden" name="is_active" value="true" />

      <div class="space-y-1.5">
        <Label for="address">Email address *</Label>
        <Input
          id="address"
          name="address"
          type="email"
          required
          placeholder="support@your-domain.com"
          bind:value={dialogAddress}
        />
        <p class="text-xs text-[var(--text-secondary)]">
          Must match the domain configured in your SES Receipt Rule.
        </p>
      </div>

      <div class="space-y-1.5">
        <Label for="default_priority">Default priority</Label>
        <select
          id="default_priority"
          name="default_priority"
          bind:value={dialogPriority}
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
        >
          {#each priorities as p (p)}
            <option value={p}>{p}</option>
          {/each}
        </select>
      </div>

      <div class="space-y-1.5">
        <Label for="default_case_type">Default ticket type</Label>
        <select
          id="default_case_type"
          name="default_case_type"
          bind:value={dialogTicketType}
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
        >
          {#each ticketTypes as t (t)}
            <option value={t}>{t || '— None —'}</option>
          {/each}
        </select>
      </div>

      <div class="space-y-1.5">
        <Label for="default_assignee_id">Default assignee</Label>
        <select
          id="default_assignee_id"
          name="default_assignee_id"
          bind:value={dialogAssigneeId}
          class="w-full rounded-md border border-[var(--border-default)] bg-[var(--surface-default)] px-3 py-2 text-sm"
        >
          <option value="">— Unassigned —</option>
          {#each profiles as p (p.id)}
            <option value={p.id}>{p.name}</option>
          {/each}
        </select>
      </div>

      <Dialog.Footer>
        <Button type="button" variant="outline" onclick={() => (dialogOpen = false)}>
          Cancel
        </Button>
        <Button type="submit">Create</Button>
      </Dialog.Footer>
    </form>
  </Dialog.Content>
</Dialog.Root>
