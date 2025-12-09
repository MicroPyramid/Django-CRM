/**
 * Board Detail Page - Server-side Loader
 *
 * Fetches board data including columns and tasks from Django API.
 *
 * Django Endpoints:
 * - GET  /api/boards/{id}/                    - Get board with columns
 * - GET  /api/boards/{id}/columns/            - List columns with tasks
 * - POST /api/boards/{id}/columns/            - Create column
 * - POST /api/boards/columns/{id}/tasks/      - Create task in column
 * - PUT  /api/boards/tasks/{id}/              - Update task
 * - DELETE /api/boards/tasks/{id}/            - Delete task
 */

import { fail, error } from '@sveltejs/kit';
import { apiRequest } from '$lib/api-helpers.js';

/** @type {import('./$types').PageServerLoad} */
export async function load({ params, locals, cookies }) {
  const { boardId } = params;
  const user = locals.user;
  const org = locals.org;

  try {
    // Fetch board details with columns
    const board = await apiRequest(`/boards/${boardId}/`, {}, { cookies, org });

    // Fetch columns with tasks
    const columns = await apiRequest(`/boards/${boardId}/columns/`, {}, { cookies, org });

    return {
      board: {
        id: board.id,
        name: board.name,
        description: board.description,
        isArchived: board.is_archived,
        owner: board.owner,
        createdAt: new Date(board.created_at),
        updatedAt: new Date(board.updated_at)
      },
      columns: columns.map((col) => ({
        id: col.id,
        name: col.name,
        order: col.order,
        color: col.color,
        limit: col.limit,
        taskCount: col.task_count,
        tasks: (col.tasks || []).map((task) => ({
          id: task.id,
          title: task.title,
          description: task.description,
          order: task.order,
          priority: task.priority,
          dueDate: task.due_date ? new Date(task.due_date) : null,
          completedAt: task.completed_at ? new Date(task.completed_at) : null,
          isCompleted: task.is_completed,
          isOverdue: task.is_overdue,
          assignedTo: task.assigned_to || [],
          accountId: task.account,
          contactId: task.contact,
          opportunityId: task.opportunity
        }))
      })),
      user
    };
  } catch (err) {
    console.error('Error loading board:', err);

    if (err.message.includes('404') || err.message.includes('not found')) {
      throw error(404, 'Board not found');
    }

    throw error(500, err.message || 'Failed to load board');
  }
}

/** @type {import('./$types').Actions} */
export const actions = {
  /**
   * Create a new column
   */
  createColumn: async ({ params, request, locals, cookies }) => {
    const { boardId } = params;
    const org = locals.org;

    try {
      const formData = await request.formData();
      const name = formData.get('name')?.toString();
      const color = formData.get('color')?.toString() || '#6B7280';

      if (!name) {
        return fail(400, { error: 'Column name is required' });
      }

      await apiRequest(
        `/boards/${boardId}/columns/`,
        {
          method: 'POST',
          body: { name, color }
        },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error creating column:', err);
      return fail(500, { error: err.message || 'Failed to create column' });
    }
  },

  /**
   * Create a new task in a column
   */
  createTask: async ({ params, request, locals, cookies }) => {
    const { boardId } = params;
    const org = locals.org;

    try {
      const formData = await request.formData();
      const columnId = formData.get('columnId')?.toString();
      const title = formData.get('title')?.toString();
      const description = formData.get('description')?.toString() || '';
      const priority = formData.get('priority')?.toString() || 'medium';

      if (!columnId || !title) {
        return fail(400, { error: 'Column ID and title are required' });
      }

      await apiRequest(
        `/boards/columns/${columnId}/tasks/`,
        {
          method: 'POST',
          body: {
            title,
            description,
            priority,
            column: columnId
          }
        },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error creating task:', err);
      return fail(500, { error: err.message || 'Failed to create task' });
    }
  },

  /**
   * Update a task (move to different column, update details)
   */
  updateTask: async ({ request, locals, cookies }) => {
    const org = locals.org;

    try {
      const formData = await request.formData();
      const taskId = formData.get('taskId')?.toString();
      const title = formData.get('title')?.toString();
      const description = formData.get('description')?.toString();
      const columnId = formData.get('columnId')?.toString();
      const order = formData.get('order')?.toString();
      const priority = formData.get('priority')?.toString();

      if (!taskId) {
        return fail(400, { error: 'Task ID is required' });
      }

      /** @type {Record<string, unknown>} */
      const updateData = {};
      if (title) updateData.title = title;
      if (description !== undefined) updateData.description = description;
      if (columnId) updateData.column = columnId;
      if (order) updateData.order = parseInt(order);
      if (priority) updateData.priority = priority;

      await apiRequest(
        `/boards/tasks/${taskId}/`,
        {
          method: 'PATCH',
          body: updateData
        },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error updating task:', err);
      return fail(500, { error: err.message || 'Failed to update task' });
    }
  },

  /**
   * Delete a task
   */
  deleteTask: async ({ request, locals, cookies }) => {
    const org = locals.org;

    try {
      const formData = await request.formData();
      const taskId = formData.get('taskId')?.toString();

      if (!taskId) {
        return fail(400, { error: 'Task ID is required' });
      }

      await apiRequest(
        `/boards/tasks/${taskId}/`,
        {
          method: 'DELETE'
        },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error deleting task:', err);
      return fail(500, { error: err.message || 'Failed to delete task' });
    }
  },

  /**
   * Move task to a different column (drag and drop)
   */
  moveTask: async ({ request, locals, cookies }) => {
    const org = locals.org;

    try {
      const formData = await request.formData();
      const taskId = formData.get('taskId')?.toString();
      const columnId = formData.get('columnId')?.toString();
      const order = parseInt(formData.get('order')?.toString() || '0');

      if (!taskId || !columnId) {
        return fail(400, { error: 'Task ID and column ID are required' });
      }

      await apiRequest(
        `/boards/tasks/${taskId}/`,
        {
          method: 'PATCH',
          body: {
            column: columnId,
            order
          }
        },
        { cookies, org }
      );

      return { success: true };
    } catch (err) {
      console.error('Error moving task:', err);
      return fail(500, { error: err.message || 'Failed to move task' });
    }
  }
};
