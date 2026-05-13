<script>
  import { Bell as BellIcon } from '@lucide/svelte';
  import * as Popover from '$lib/components/ui/popover/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { notifications } from '$lib/stores/notifications.svelte.js';
  import NotificationPanel from './NotificationPanel.svelte';

  let open = $state(false);

  $effect(() => {
    notifications.startStream();
    return () => notifications.stopStream();
  });

  // Refresh on first open in case the stream missed any messages while
  // we were initialising.
  $effect(() => {
    if (open) notifications.fetch();
  });

  /** @param {number} n */
  const fmt = (n) => (n > 99 ? '99+' : String(n));
</script>

<Popover.Root bind:open>
  <Popover.Trigger asChild class="">
    {#snippet child({ props })}
      <Button
        {...props}
        variant="ghost"
        size="icon"
        class="relative h-9 w-9 rounded-full"
        aria-label={notifications.unread_count > 0
          ? `Notifications (${notifications.unread_count} unread)`
          : 'Notifications'}
      >
        <BellIcon class="h-5 w-5" />
        {#if notifications.unread_count > 0}
          <span
            class="absolute -top-0.5 -right-0.5 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-[var(--color-primary-default)] px-1 text-[10px] font-semibold leading-none text-white"
          >
            {fmt(notifications.unread_count)}
          </span>
        {/if}
      </Button>
    {/snippet}
  </Popover.Trigger>
  <Popover.Content align="end" class="w-auto p-0">
    <NotificationPanel onClose={() => (open = false)} />
  </Popover.Content>
</Popover.Root>
