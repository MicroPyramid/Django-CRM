/**
 * Drag and drop utilities for table row reordering
 * @module lib/utils/drag-drop
 */

/**
 * @typedef {'before' | 'after' | null} DropPosition
 */

/**
 * @typedef {Object} DragState
 * @property {string | null} draggedId - ID of the row being dragged
 * @property {string | null} dragOverId - ID of the row being dragged over
 * @property {DropPosition} dropPosition - Position relative to dragOverId
 */

/**
 * Create initial drag state
 * @returns {DragState}
 */
export function createDragState() {
  return {
    draggedId: null,
    dragOverId: null,
    dropPosition: null
  };
}

/**
 * Calculate drop position based on mouse position
 * @param {DragEvent} event - Drag event
 * @returns {DropPosition}
 */
export function calculateDropPosition(event) {
  const target = /** @type {HTMLElement} */ (event.currentTarget);
  const rect = target.getBoundingClientRect();
  const midpoint = rect.top + rect.height / 2;
  return event.clientY < midpoint ? 'before' : 'after';
}

/**
 * Reorder array items based on drag and drop
 * @template T
 * @param {T[]} items - Array of items
 * @param {string} draggedId - ID of dragged item
 * @param {string} targetId - ID of drop target
 * @param {DropPosition} position - Drop position
 * @param {(item: T) => string} getId - Function to get item ID
 * @returns {T[]} Reordered array
 */
export function reorderItems(items, draggedId, targetId, position, getId) {
  if (!draggedId || !targetId || draggedId === targetId || !position) {
    return items;
  }

  const draggedIndex = items.findIndex((item) => getId(item) === draggedId);
  const targetIndex = items.findIndex((item) => getId(item) === targetId);

  if (draggedIndex === -1 || targetIndex === -1) {
    return items;
  }

  const newItems = [...items];
  const [draggedItem] = newItems.splice(draggedIndex, 1);

  // Calculate insert position
  let insertIndex;
  if (position === 'after') {
    insertIndex = draggedIndex < targetIndex ? targetIndex : targetIndex + 1;
  } else {
    insertIndex = draggedIndex < targetIndex ? targetIndex - 1 : targetIndex;
  }

  newItems.splice(insertIndex, 0, draggedItem);
  return newItems;
}

/**
 * Handle drag start event
 * @param {DragEvent} event - Drag event
 * @param {string} itemId - ID of the item being dragged
 */
export function handleDragStart(event, itemId) {
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', itemId);
  }
}

/**
 * Drag handle styles that show on row hover
 */
export const dragHandleClasses =
  'flex items-center justify-center w-6 h-6 rounded opacity-0 group-hover:opacity-40 hover:!opacity-70 hover:bg-gray-200 transition-all cursor-grab active:cursor-grabbing';

/**
 * Expand button styles that show on row hover
 */
export const expandButtonClasses =
  'flex items-center justify-center w-6 h-6 rounded opacity-0 group-hover:opacity-100 hover:bg-gray-200 transition-all duration-75';

/**
 * Drop indicator line styles
 */
export const dropIndicatorClasses = 'h-0.5 bg-blue-400 rounded-full mx-4';

/**
 * Dragged row styles
 */
export const draggedRowClasses = 'opacity-40 bg-gray-100';
