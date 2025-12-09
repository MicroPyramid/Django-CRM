<script>
  import { KanbanBoard } from '$lib/components/ui/kanban';
  import TaskCard from './TaskCard.svelte';

  /**
   * @typedef {Object} Column
   * @property {string} id
   * @property {string} name
   * @property {number} order
   * @property {string} color
   * @property {string} stage_type
   * @property {boolean} is_status_column
   * @property {number|null} wip_limit
   * @property {number} task_count
   * @property {Array<any>} tasks
   */

  /**
   * @typedef {Object} KanbanData
   * @property {string} mode
   * @property {Object|null} pipeline
   * @property {Column[]} columns
   * @property {number} total_tasks
   */

  /**
   * @type {{
   *   data: KanbanData | null,
   *   loading?: boolean,
   *   onStatusChange: (taskId: string, newStatus: string, columnId: string) => Promise<void>,
   *   onCardClick: (task: any) => void
   * }}
   */
  let { data = null, loading = false, onStatusChange, onCardClick } = $props();

  // Transform data to use generic field names
  const transformedData = $derived(() => {
    if (!data) return null;

    return {
      mode: data.mode,
      pipeline: data.pipeline,
      columns: data.columns.map((col) => ({
        ...col,
        items: col.tasks || [],
        item_count: col.task_count || col.tasks?.length || 0
      })),
      total_items: data.total_tasks
    };
  });
</script>

<KanbanBoard
  data={transformedData()}
  {loading}
  itemName="task"
  itemNamePlural="tasks"
  onItemMove={onStatusChange}
  {onCardClick}
  CardComponent={TaskCard}
  emptyMessage="No kanban data available"
/>
