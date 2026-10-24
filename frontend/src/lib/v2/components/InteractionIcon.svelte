<script>
  import {
    Inbox,
    Mail,
    MessageCircle,
    MessageSquareText,
    PhoneIncoming,
    PhoneOutgoing,
    Users
  } from '@lucide/svelte';

  /** @type {{ kind: string, direction?: string, size?: number }} */
  let { kind, direction = 'outbound', size = 13 } = $props();
</script>

{#if kind === 'call'}
  {#if direction === 'inbound'}<PhoneIncoming {size} />{:else}<PhoneOutgoing {size} />{/if}
{:else if kind === 'meeting'}<Users {size} />
{:else if kind === 'email'}<Mail {size} />
{:else if kind === 'whatsapp'}<MessageCircle {size} />
{:else if kind === 'sms'}<MessageSquareText {size} />
{:else}<Inbox {size} />{/if}
