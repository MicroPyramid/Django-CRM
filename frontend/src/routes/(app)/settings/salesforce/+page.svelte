<script>
  import { enhance } from '$app/forms';
  import { toast } from 'svelte-sonner';
  import { Button } from '$lib/components/ui/button/index.js';
  import * as Card from '$lib/components/ui/card/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';
  import * as Dialog from '$lib/components/ui/dialog/index.js';
  import { Input } from '$lib/components/ui/input/index.js';
  import { Label } from '$lib/components/ui/label/index.js';
  import { Separator } from '$lib/components/ui/separator/index.js';
  import { PageHeader } from '$lib/components/layout';
  import { Cloud, ExternalLink, Trash2, Download, Key } from '@lucide/svelte';

  /** @type {{ data: any, form: any }} */
  let { data, form } = $props();

  let sfStatus = $derived(data.sfStatus || { connected: false });
  let isConnecting = $state(false);
  let isDisconnecting = $state(false);
  let disconnectDialogOpen = $state(false);

  // Show toast for form results
  $effect(() => {
    if (form?.connected) toast.success('Salesforce connected successfully');
    if (form?.disconnected) toast.success('Salesforce disconnected');
    if (form?.credentialError) toast.error(form.credentialError);
  });

  /**
   * Format a date string for display
   * @param {string} dateStr
   */
  function formatDate(dateStr) {
    if (!dateStr) return 'Unknown';
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  }
</script>

<svelte:head>
  <title>Salesforce Integration - BottleCRM</title>
</svelte:head>

<PageHeader title="Salesforce Integration" subtitle="Connect and import data from Salesforce" />

<div class="mx-auto max-w-3xl space-y-6 p-6 md:p-8">
  {#if sfStatus.connected}
    <!-- ============================================================ -->
    <!-- CONNECTED -->
    <!-- ============================================================ -->
    <Card.Root>
      <Card.Header>
        <div class="flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div
              class="flex size-10 items-center justify-center rounded-lg bg-blue-100 dark:bg-blue-950"
            >
              <Cloud class="size-5 text-blue-600 dark:text-blue-400" />
            </div>
            <div>
              <Card.Title>Salesforce Connection</Card.Title>
              <Card.Description>Your Salesforce org is connected</Card.Description>
            </div>
          </div>
          <Badge
            class="border-emerald-200 bg-emerald-100 text-emerald-700 dark:border-emerald-800 dark:bg-emerald-950 dark:text-emerald-400"
          >
            Connected
          </Badge>
        </div>
      </Card.Header>
      <Card.Content>
        <div class="space-y-4">
          <div class="bg-muted/50 rounded-lg p-4">
            <dl class="grid gap-3 sm:grid-cols-2">
              {#if sfStatus.connection?.instance_url}
                <div>
                  <dt class="text-muted-foreground text-sm font-medium">Instance URL</dt>
                  <dd class="text-foreground mt-1 text-sm">
                    <a
                      href={sfStatus.connection.instance_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      class="inline-flex items-center gap-1 text-blue-600 hover:underline dark:text-blue-400"
                    >
                      {sfStatus.connection.instance_url}
                      <ExternalLink class="size-3" />
                    </a>
                  </dd>
                </div>
              {/if}
              {#if sfStatus.connection?.connected_by_email}
                <div>
                  <dt class="text-muted-foreground text-sm font-medium">Connected By</dt>
                  <dd class="text-foreground mt-1 text-sm">{sfStatus.connection.connected_by_email}</dd>
                </div>
              {/if}
              {#if sfStatus.connection?.created_at}
                <div>
                  <dt class="text-muted-foreground text-sm font-medium">Connected On</dt>
                  <dd class="text-foreground mt-1 text-sm">{formatDate(sfStatus.connection.created_at)}</dd>
                </div>
              {/if}
            </dl>
          </div>

          <Separator />

          <div class="flex items-center justify-between">
            <Button variant="outline" href="/settings/salesforce/import" class="gap-2">
              <Download class="size-4" />
              Import Data
            </Button>
            <Button
              variant="outline"
              class="text-destructive hover:bg-destructive/10 gap-2"
              onclick={() => (disconnectDialogOpen = true)}
              type="button"
            >
              <Trash2 class="size-4" />
              Disconnect
            </Button>
          </div>
        </div>
      </Card.Content>
    </Card.Root>
  {:else}
    <!-- ============================================================ -->
    <!-- NOT CONNECTED - Setup + Credential Form -->
    <!-- ============================================================ -->
    <Card.Root>
      <Card.Header class="text-center">
        <div
          class="mx-auto mb-4 flex size-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-950"
        >
          <Key class="size-8 text-blue-600 dark:text-blue-400" />
        </div>
        <Card.Title class="text-xl">Connect to Salesforce</Card.Title>
        <Card.Description class="mx-auto max-w-md">
          Create a Connected App in your Salesforce org and enter the credentials below to connect.
        </Card.Description>
      </Card.Header>
      <Card.Content>
        <div class="space-y-6">
          <!-- Setup instructions -->
          <div class="bg-muted/50 rounded-lg p-4">
            <h4 class="text-foreground mb-3 text-sm font-medium">How to create a Connected App:</h4>
            <ol class="text-muted-foreground space-y-2 text-sm">
              <li class="flex gap-2">
                <span class="text-foreground shrink-0 font-medium">1.</span>
                <span>Log in to <strong class="text-foreground">Salesforce Setup</strong></span>
              </li>
              <li class="flex gap-2">
                <span class="text-foreground shrink-0 font-medium">2.</span>
                <span>Go to <strong class="text-foreground">App Manager</strong> &rarr; <strong class="text-foreground">New Connected App</strong></span>
              </li>
              <li class="flex gap-2">
                <span class="text-foreground shrink-0 font-medium">3.</span>
                <span>Enable <strong class="text-foreground">OAuth Settings</strong> and set Callback URL to <code class="bg-muted rounded px-1 text-xs">https://login.salesforce.com/services/oauth2/success</code></span>
              </li>
              <li class="flex gap-2">
                <span class="text-foreground shrink-0 font-medium">4.</span>
                <span>Add OAuth scopes: <code class="bg-muted rounded px-1 text-xs">api</code>, <code class="bg-muted rounded px-1 text-xs">refresh_token</code></span>
              </li>
              <li class="flex gap-2">
                <span class="text-foreground shrink-0 font-medium">5.</span>
                <span>Check <strong class="text-foreground">Enable Client Credentials Flow</strong></span>
              </li>
              <li class="flex gap-2">
                <span class="text-foreground shrink-0 font-medium">6.</span>
                <span>Assign a <strong class="text-foreground">Run As</strong> user to the Connected App (required for Client Credentials)</span>
              </li>
              <li class="flex gap-2">
                <span class="text-foreground shrink-0 font-medium">7.</span>
                <span>Copy the <strong class="text-foreground">Consumer Key</strong> (Client ID) and <strong class="text-foreground">Consumer Secret</strong> (Client Secret) below</span>
              </li>
            </ol>
          </div>

          <Separator />

          <!-- Credential form - saves + connects in one step -->
          <form method="POST" action="?/saveCredentials" use:enhance={() => {
            isConnecting = true;
            return async ({ update }) => {
              isConnecting = false;
              await update();
            };
          }}>
            <div class="space-y-4">
              <div class="space-y-2">
                <Label for="login_url">Salesforce My Domain URL</Label>
                <Input
                  id="login_url"
                  name="login_url"
                  type="url"
                  placeholder="https://yourcompany.my.salesforce.com"
                  required
                  autocomplete="off"
                />
                <p class="text-muted-foreground text-xs">
                  Find this in Salesforce Setup &rarr; My Domain. Use <code class="bg-muted rounded px-1">https://yourcompany.my.salesforce.com</code>
                </p>
              </div>
              <div class="space-y-2">
                <Label for="client_id">Client ID (Consumer Key)</Label>
                <Input
                  id="client_id"
                  name="client_id"
                  type="text"
                  placeholder="3MVG9..."
                  required
                  autocomplete="off"
                />
              </div>
              <div class="space-y-2">
                <Label for="client_secret">Client Secret (Consumer Secret)</Label>
                <Input
                  id="client_secret"
                  name="client_secret"
                  type="password"
                  placeholder="Enter your client secret"
                  required
                  autocomplete="off"
                />
              </div>
              <Button
                type="submit"
                disabled={isConnecting}
                class="w-full gap-2 border-0 bg-[var(--color-primary-default)] text-white hover:bg-[var(--color-primary-hover)]"
              >
                <Cloud class="size-4" />
                {isConnecting ? 'Connecting to Salesforce...' : 'Connect to Salesforce'}
              </Button>
            </div>
          </form>
        </div>
      </Card.Content>
    </Card.Root>

    <Card.Root>
      <Card.Header>
        <Card.Title class="text-base">What gets imported?</Card.Title>
      </Card.Header>
      <Card.Content>
        <ul class="text-muted-foreground space-y-2 text-sm">
          <li class="flex items-start gap-2">
            <span class="mt-1.5 size-1.5 shrink-0 rounded-full bg-blue-500"></span>
            <span
              ><strong class="text-foreground">Accounts</strong> - Companies and organizations</span
            >
          </li>
          <li class="flex items-start gap-2">
            <span class="mt-1.5 size-1.5 shrink-0 rounded-full bg-blue-500"></span>
            <span
              ><strong class="text-foreground">Contacts</strong> - People associated with accounts</span
            >
          </li>
          <li class="flex items-start gap-2">
            <span class="mt-1.5 size-1.5 shrink-0 rounded-full bg-blue-500"></span>
            <span
              ><strong class="text-foreground">Opportunities</strong> - Sales deals and pipeline</span
            >
          </li>
          <li class="flex items-start gap-2">
            <span class="mt-1.5 size-1.5 shrink-0 rounded-full bg-blue-500"></span>
            <span><strong class="text-foreground">Products</strong> - Product catalog</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="mt-1.5 size-1.5 shrink-0 rounded-full bg-blue-500"></span>
            <span><strong class="text-foreground">Orders</strong> - Sales orders</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="mt-1.5 size-1.5 shrink-0 rounded-full bg-blue-500"></span>
            <span><strong class="text-foreground">Quotes</strong> - Price quotes and estimates</span
            >
          </li>
        </ul>
      </Card.Content>
    </Card.Root>
  {/if}
</div>

<!-- Disconnect Confirmation Dialog -->
<Dialog.Root bind:open={disconnectDialogOpen}>
  <Dialog.Content class="sm:max-w-md">
    <Dialog.Header>
      <Dialog.Title>Disconnect Salesforce</Dialog.Title>
      <Dialog.Description>
        Are you sure you want to disconnect from Salesforce? Previously imported data will not be deleted.
      </Dialog.Description>
    </Dialog.Header>
    <form method="POST" action="?/disconnect" use:enhance={() => {
      isDisconnecting = true;
      return async ({ update }) => {
        isDisconnecting = false;
        disconnectDialogOpen = false;
        await update();
      };
    }}>
      <div class="flex justify-end gap-2 pt-4">
        <Button variant="outline" type="button" onclick={() => (disconnectDialogOpen = false)}>Cancel</Button>
        <Button variant="destructive" type="submit" disabled={isDisconnecting}>
          {isDisconnecting ? 'Disconnecting...' : 'Disconnect'}
        </Button>
      </div>
    </form>
  </Dialog.Content>
</Dialog.Root>
