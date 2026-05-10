<script>
  import { KanbanBoard } from '$lib/components/ui/kanban';
  import TicketCard from './TicketCard.svelte';

  /**
   * @typedef {Object} Column
   * @property {string} id
   * @property {string} name
   * @property {number} order
   * @property {string} color
   * @property {string} stage_type
   * @property {boolean} is_status_column
   * @property {number|null} wip_limit
   * @property {number} case_count
   * @property {Array<any>} cases
   */

  /**
   * @typedef {Object} KanbanData
   * @property {string} mode
   * @property {Object|null} pipeline
   * @property {Column[]} columns
   * @property {number} total_cases
   */

  /**
   * @type {{
   *   data: KanbanData | null,
   *   loading?: boolean,
   *   onStatusChange: (ticketId: string, newStatus: string, columnId: string) => Promise<void>,
   *   onCardClick: (ticketItem: any) => void
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
        items: col.cases || [],
        item_count: col.case_count || col.cases?.length || 0
      })),
      total_items: data.total_cases
    };
  });
</script>

<KanbanBoard
  data={transformedData()}
  {loading}
  itemName="ticket"
  itemNamePlural="cases"
  onItemMove={onStatusChange}
  {onCardClick}
  CardComponent={TicketCard}
  emptyMessage="No kanban data available"
/>
