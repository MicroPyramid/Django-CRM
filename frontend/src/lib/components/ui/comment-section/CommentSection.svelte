<script>
  import { toast } from 'svelte-sonner';
  import { MessageSquare, Send, Trash2, Loader2, ChevronDown, ChevronUp } from '@lucide/svelte';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Textarea } from '$lib/components/ui/textarea/index.js';
  import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
  import { Separator } from '$lib/components/ui/separator/index.js';
  import { formatRelativeDate, getInitials } from '$lib/utils/formatting.js';
  import * as api from '$lib/api.js';

  /**
   * @type {{
   *   entityId: string,
   *   entityType: 'leads' | 'accounts' | 'contacts' | 'opportunity' | 'cases' | 'tasks',
   *   initialComments?: Array<{
   *     id: string,
   *     comment: string,
   *     commented_on: string,
   *     commented_by?: {
   *       id: string,
   *       user_details?: { email?: string }
   *     }
   *   }>,
   *   currentUserEmail?: string,
   *   isAdmin?: boolean,
   *   initialDisplayCount?: number,
   *   showAddComment?: boolean
   * }}
   */
  let {
    entityId,
    entityType,
    initialComments = [],
    currentUserEmail = '',
    isAdmin = false,
    initialDisplayCount = 5,
    showAddComment = true
  } = $props();

  // State
  let comments = $state([]);
  let showAllComments = $state(false);

  // Sync with initialComments prop changes
  $effect(() => {
    comments = initialComments;
  });
  let newComment = $state('');
  let isSubmitting = $state(false);
  let deletingCommentId = $state(null);
  let deleteDialogOpen = $state(false);
  let commentToDelete = $state(null);

  // Derived
  const displayedComments = $derived(
    showAllComments ? comments : comments.slice(0, initialDisplayCount)
  );
  const hasMoreComments = $derived(comments.length > initialDisplayCount);
  const hiddenCount = $derived(comments.length - initialDisplayCount);

  // Get API module based on entity type
  function getApiModule() {
    const modules = {
      leads: api.leads,
      accounts: api.accounts,
      contacts: api.contacts,
      opportunity: api.opportunities,
      cases: api.cases,
      tasks: api.tasks
    };
    return modules[entityType];
  }

  // Check if user can delete a comment (by email match)
  function canDeleteComment(comment) {
    if (isAdmin) return true;
    const commentEmail = comment.commented_by?.user_details?.email;
    return commentEmail && currentUserEmail && commentEmail === currentUserEmail;
  }

  // Get commenter display name from email
  function getCommenterName(comment) {
    const email = comment.commented_by?.user_details?.email;
    if (!email) return 'Unknown';
    // Extract name from email (before @)
    return email.split('@')[0].replace(/[._]/g, ' ');
  }

  // Get commenter initials
  function getCommenterInitials(comment) {
    const name = getCommenterName(comment);
    return getInitials(name);
  }

  // Get avatar background color based on user id
  function getAvatarColor(comment) {
    const colors = [
      'bg-blue-100 text-blue-700 dark:bg-blue-900/50 dark:text-blue-300',
      'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300',
      'bg-amber-100 text-amber-700 dark:bg-amber-900/50 dark:text-amber-300',
      'bg-purple-100 text-purple-700 dark:bg-purple-900/50 dark:text-purple-300',
      'bg-rose-100 text-rose-700 dark:bg-rose-900/50 dark:text-rose-300',
      'bg-cyan-100 text-cyan-700 dark:bg-cyan-900/50 dark:text-cyan-300'
    ];
    const id = comment.commented_by?.id || '';
    const hash = id.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
    return colors[hash % colors.length];
  }

  // Add comment handler
  async function handleAddComment() {
    if (!newComment.trim() || isSubmitting) return;

    const commentText = newComment.trim();
    isSubmitting = true;

    // Create optimistic comment
    const tempId = `temp-${Date.now()}`;
    const optimisticComment = {
      id: tempId,
      comment: commentText,
      commented_on: new Date().toISOString(),
      commented_by: {
        id: tempId,
        user_details: { email: currentUserEmail || 'You' }
      }
    };

    // Optimistic update - prepend new comment
    comments = [optimisticComment, ...comments];
    newComment = '';

    try {
      const apiModule = getApiModule();
      const result = await apiModule.addComment(entityId, commentText);

      // Replace temp comment with real one if response contains it
      if (result?.id) {
        comments = comments.map(c =>
          c.id === tempId ? { ...result, comment: commentText } : c
        );
      }

      toast.success('Comment added');
    } catch (err) {
      // Revert on error
      comments = comments.filter(c => c.id !== tempId);
      newComment = commentText; // Restore the text
      console.error('Failed to add comment:', err);
      toast.error(err?.message || 'Failed to add comment');
    } finally {
      isSubmitting = false;
    }
  }

  // Delete confirmation
  function confirmDelete(comment) {
    commentToDelete = comment;
    deleteDialogOpen = true;
  }

  // Delete comment handler
  async function handleDeleteComment() {
    if (!commentToDelete || deletingCommentId) return;

    const commentId = commentToDelete.id;
    deletingCommentId = commentId;
    deleteDialogOpen = false;

    // Store for rollback
    const originalComments = [...comments];

    // Optimistic remove
    comments = comments.filter(c => c.id !== commentId);

    try {
      const apiModule = getApiModule();
      await apiModule.deleteComment(commentId);
      toast.success('Comment deleted');
    } catch (err) {
      // Revert on error
      comments = originalComments;
      console.error('Failed to delete comment:', err);
      toast.error(err?.message || 'Failed to delete comment');
    } finally {
      deletingCommentId = null;
      commentToDelete = null;
    }
  }

  // Handle keyboard submit
  function handleKeyDown(event) {
    if (event.key === 'Enter' && (event.metaKey || event.ctrlKey)) {
      event.preventDefault();
      handleAddComment();
    }
  }
</script>

<div class="space-y-4">
  <!-- Header -->
  <div class="flex items-center justify-between">
    <div class="flex items-center gap-2 text-sm font-medium text-gray-600 dark:text-gray-400">
      <MessageSquare class="h-4 w-4" />
      <span>Comments</span>
      {#if comments.length > 0}
        <span class="rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600 dark:bg-gray-800 dark:text-gray-400">
          {comments.length}
        </span>
      {/if}
    </div>
  </div>

  <!-- Add Comment Form -->
  {#if showAddComment}
    <div class="space-y-3">
      <div class="relative">
        <Textarea
          bind:value={newComment}
          placeholder="Write a comment..."
          onkeydown={handleKeyDown}
          class="min-h-[80px] resize-none pr-4 pb-8"
          disabled={isSubmitting}
        />
        <div class="absolute bottom-2 left-3 right-3 flex items-center justify-between">
          <span class="text-[10px] text-gray-400 dark:text-gray-500">
            {#if newComment.trim()}
              Press <kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 text-[10px] font-medium dark:border-gray-700 dark:bg-gray-800">Ctrl</kbd>+<kbd class="rounded border border-gray-200 bg-gray-50 px-1 py-0.5 text-[10px] font-medium dark:border-gray-700 dark:bg-gray-800">Enter</kbd> to send
            {/if}
          </span>
          <Button
            size="sm"
            onclick={handleAddComment}
            disabled={!newComment.trim() || isSubmitting}
            class="h-7 gap-1.5 px-3 text-xs"
          >
            {#if isSubmitting}
              <Loader2 class="h-3 w-3 animate-spin" />
            {:else}
              <Send class="h-3 w-3" />
            {/if}
            Send
          </Button>
        </div>
      </div>
    </div>
  {/if}

  <!-- Comments List -->
  {#if comments.length === 0}
    <div class="flex flex-col items-center justify-center rounded-lg border border-dashed border-gray-200 py-8 dark:border-gray-800">
      <div class="flex h-12 w-12 items-center justify-center rounded-full bg-gray-50 dark:bg-gray-900">
        <MessageSquare class="h-5 w-5 text-gray-400 dark:text-gray-600" />
      </div>
      <p class="mt-3 text-sm font-medium text-gray-500 dark:text-gray-400">No comments yet</p>
      <p class="mt-1 text-xs text-gray-400 dark:text-gray-500">Be the first to comment</p>
    </div>
  {:else}
    <div class="space-y-1">
      {#each displayedComments as comment (comment.id)}
        <div
          class="group relative rounded-lg border border-transparent px-3 py-3 transition-colors hover:border-gray-100 hover:bg-gray-50/50 dark:hover:border-gray-800 dark:hover:bg-gray-900/30"
        >
          <div class="flex gap-3">
            <!-- Avatar -->
            <div
              class="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-xs font-semibold uppercase {getAvatarColor(comment)}"
            >
              {getCommenterInitials(comment)}
            </div>

            <!-- Content -->
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-2">
                <span class="text-sm font-medium text-gray-900 dark:text-gray-100">
                  {getCommenterName(comment)}
                </span>
                <span class="text-xs text-gray-400 dark:text-gray-500">
                  {formatRelativeDate(comment.commented_on)}
                </span>
              </div>

              <p class="mt-1 whitespace-pre-wrap text-sm text-gray-600 dark:text-gray-400">
                {comment.comment}
              </p>
            </div>

            <!-- Delete button -->
            {#if canDeleteComment(comment)}
              <button
                type="button"
                onclick={() => confirmDelete(comment)}
                class="absolute right-2 top-2 rounded-md p-1.5 text-gray-400 opacity-0 transition-all hover:bg-red-50 hover:text-red-500 group-hover:opacity-100 dark:hover:bg-red-950/50 dark:hover:text-red-400"
                disabled={deletingCommentId === comment.id}
                title="Delete comment"
              >
                {#if deletingCommentId === comment.id}
                  <Loader2 class="h-4 w-4 animate-spin" />
                {:else}
                  <Trash2 class="h-4 w-4" />
                {/if}
              </button>
            {/if}
          </div>
        </div>
      {/each}
    </div>

    <!-- Show More/Less Toggle -->
    {#if hasMoreComments}
      <button
        type="button"
        onclick={() => showAllComments = !showAllComments}
        class="flex w-full items-center justify-center gap-2 rounded-lg border border-gray-200 py-2 text-sm font-medium text-gray-600 transition-colors hover:border-gray-300 hover:bg-gray-50 hover:text-gray-900 dark:border-gray-800 dark:text-gray-400 dark:hover:border-gray-700 dark:hover:bg-gray-900 dark:hover:text-gray-200"
      >
        {#if showAllComments}
          <ChevronUp class="h-4 w-4" />
          Show less
        {:else}
          <ChevronDown class="h-4 w-4" />
          View all {comments.length} comments
        {/if}
      </button>
    {/if}
  {/if}
</div>

<!-- Delete Confirmation Dialog -->
<AlertDialog.Root bind:open={deleteDialogOpen}>
  <AlertDialog.Content>
    <AlertDialog.Header>
      <AlertDialog.Title>Delete comment</AlertDialog.Title>
      <AlertDialog.Description>
        Are you sure you want to delete this comment? This action cannot be undone.
      </AlertDialog.Description>
    </AlertDialog.Header>
    <AlertDialog.Footer>
      <AlertDialog.Cancel>Cancel</AlertDialog.Cancel>
      <AlertDialog.Action
        onclick={handleDeleteComment}
        class="bg-red-600 text-white hover:bg-red-700 dark:bg-red-600 dark:hover:bg-red-700"
      >
        Delete
      </AlertDialog.Action>
    </AlertDialog.Footer>
  </AlertDialog.Content>
</AlertDialog.Root>
