<script>
  import { KanbanBoard } from '$lib/components/ui/kanban';
  import LeadCard from './LeadCard.svelte';

  /**
   * @typedef {Object} Column
   * @property {string} id
   * @property {string} name
   * @property {number} order
   * @property {string} color
   * @property {string} stage_type
   * @property {boolean} is_status_column
   * @property {number|null} wip_limit
   * @property {number} lead_count
   * @property {Array<any>} leads
   */

  /**
   * @typedef {Object} KanbanData
   * @property {string} mode
   * @property {Object|null} pipeline
   * @property {Column[]} columns
   * @property {number} total_leads
   */

  /**
   * @type {{
   *   data: KanbanData | null,
   *   loading?: boolean,
   *   onStatusChange: (leadId: string, newStatus: string, columnId: string) => Promise<void>,
   *   onCardClick: (lead: any) => void
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
        items: col.leads || [],
        item_count: col.lead_count || col.leads?.length || 0
      })),
      total_items: data.total_leads
    };
  });
</script>

<KanbanBoard
  data={transformedData()}
  {loading}
  itemName="lead"
  itemNamePlural="leads"
  onItemMove={onStatusChange}
  {onCardClick}
  CardComponent={LeadCard}
  emptyMessage="No kanban data available"
/>
