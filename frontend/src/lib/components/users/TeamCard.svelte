<script>
  import { Users, Pencil, Trash2 } from '@lucide/svelte';
  import * as Card from '$lib/components/ui/card/index.js';
  import * as Avatar from '$lib/components/ui/avatar/index.js';
  import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { getInitials } from '$lib/utils/formatting.js';

  /**
   * @typedef {Object} TeamMember
   * @property {string} id
   * @property {Object} [user_details]
   * @property {string} [user_details.email]
   * @property {string} [user_details.profile_pic]
   */

  /**
   * @typedef {Object} Team
   * @property {string} id
   * @property {string} name
   * @property {string} [description]
   * @property {TeamMember[]} [users]
   * @property {string} [created_at]
   */

  /**
   * @type {{
   *   team: Team,
   *   onEdit?: (team: Team) => void,
   *   onDelete?: (teamId: string) => void,
   *   maxAvatars?: number
   * }}
   */
  let { team, onEdit, onDelete, maxAvatars = 4 } = $props();

  const members = $derived(team.users || []);
  const displayMembers = $derived(members.slice(0, maxAvatars));
  const remainingCount = $derived(members.length > maxAvatars ? members.length - maxAvatars : 0);

  /**
   * Get member name from user details
   * @param {TeamMember} member
   */
  function getMemberName(member) {
    return member.user_details?.email?.split('@')[0] || 'User';
  }

  /**
   * Get member avatar URL
   * @param {TeamMember} member
   */
  function getMemberAvatar(member) {
    return member.user_details?.profile_pic || '';
  }
</script>

<Card.Root class="group transition-shadow hover:shadow-md">
  <Card.Header class="pb-3">
    <div class="flex items-start justify-between">
      <div class="flex items-center gap-3">
        <div
          class="flex h-10 w-10 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30"
        >
          <Users class="h-5 w-5 text-purple-600 dark:text-purple-400" />
        </div>
        <div>
          <Card.Title class="text-base">{team.name}</Card.Title>
          <p class="text-muted-foreground text-sm">
            {members.length} member{members.length !== 1 ? 's' : ''}
          </p>
        </div>
      </div>
      <div class="flex gap-1 opacity-0 transition-opacity group-hover:opacity-100">
        <Button variant="ghost" size="icon" class="h-8 w-8" onclick={() => onEdit?.(team)}>
          <Pencil class="h-4 w-4" />
        </Button>
        <AlertDialog.Root>
          <AlertDialog.Trigger
            class="text-destructive hover:bg-destructive/10 inline-flex h-8 w-8 items-center justify-center rounded-md"
          >
            <Trash2 class="h-4 w-4" />
          </AlertDialog.Trigger>
          <AlertDialog.Content>
            <AlertDialog.Header>
              <AlertDialog.Title>Delete Team</AlertDialog.Title>
              <AlertDialog.Description>
                Are you sure you want to delete <strong>{team.name}</strong>? This will remove the
                team from all assigned records. This action cannot be undone.
              </AlertDialog.Description>
            </AlertDialog.Header>
            <AlertDialog.Footer>
              <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
              <Button variant="destructive" onclick={() => onDelete?.(team.id)}>Delete</Button>
            </AlertDialog.Footer>
          </AlertDialog.Content>
        </AlertDialog.Root>
      </div>
    </div>
  </Card.Header>

  {#if team.description}
    <Card.Content class="pt-0 pb-3">
      <p class="text-muted-foreground line-clamp-2 text-sm">{team.description}</p>
    </Card.Content>
  {/if}

  <Card.Content class="pt-0">
    <div class="flex items-center">
      <div class="flex -space-x-2">
        {#each displayMembers as member (member.id)}
          <Avatar.Root class="border-background h-8 w-8 border-2">
            {#if getMemberAvatar(member)}
              <Avatar.Image class="" src={getMemberAvatar(member)} alt={getMemberName(member)} />
            {/if}
            <Avatar.Fallback
              class="bg-gradient-to-br from-blue-500 to-purple-600 text-xs text-white"
            >
              {getInitials(getMemberName(member))}
            </Avatar.Fallback>
          </Avatar.Root>
        {/each}
        {#if remainingCount > 0}
          <div
            class="bg-muted text-muted-foreground border-background flex h-8 w-8 items-center justify-center rounded-full border-2 text-xs font-medium"
          >
            +{remainingCount}
          </div>
        {/if}
      </div>
      {#if members.length === 0}
        <span class="text-muted-foreground text-sm italic">No members assigned</span>
      {/if}
    </div>
  </Card.Content>
</Card.Root>
