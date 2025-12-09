<script>
  import { enhance } from '$app/forms';
  import { invalidateAll } from '$app/navigation';

  export let data;

  let showAddColumn = false;
  let newColumnName = '';
  let newColumnColor = '#6B7280';

  // Track which column is showing the add task form
  let addingTaskToColumn = null;
  let newTaskTitle = '';
  let newTaskDescription = '';
  let newTaskPriority = 'medium';

  // Drag and drop state
  let draggedTask = null;
  let dragOverColumn = null;

  const priorityColors = {
    low: '#10B981',
    medium: '#F59E0B',
    high: '#EF4444',
    urgent: '#7C3AED'
  };

  function handleDragStart(event, task, columnId) {
    draggedTask = { ...task, sourceColumnId: columnId };
    event.dataTransfer.effectAllowed = 'move';
    event.dataTransfer.setData('text/plain', task.id);
  }

  function handleDragOver(event, columnId) {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
    dragOverColumn = columnId;
  }

  function handleDragLeave() {
    dragOverColumn = null;
  }

  async function handleDrop(event, targetColumnId) {
    event.preventDefault();
    dragOverColumn = null;

    if (!draggedTask) return;

    // Don't do anything if dropped in same column
    if (draggedTask.sourceColumnId === targetColumnId) {
      draggedTask = null;
      return;
    }

    // Submit the move via form action
    const formData = new FormData();
    formData.append('taskId', draggedTask.id);
    formData.append('columnId', targetColumnId);
    formData.append('order', '0'); // Add to top of column

    try {
      const response = await fetch('?/moveTask', {
        method: 'POST',
        body: formData
      });

      if (response.ok) {
        await invalidateAll();
      }
    } catch (err) {
      console.error('Failed to move task:', err);
    }

    draggedTask = null;
  }

  function handleDragEnd() {
    draggedTask = null;
    dragOverColumn = null;
  }

  function startAddingTask(columnId) {
    addingTaskToColumn = columnId;
    newTaskTitle = '';
    newTaskDescription = '';
    newTaskPriority = 'medium';
  }

  function cancelAddingTask() {
    addingTaskToColumn = null;
  }

  function formatDate(date) {
    if (!date) return '';
    return new Date(date).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  }
</script>

<div class="board-container">
  <header class="board-header">
    <a href="/tasks" class="back-link">Back to Boards</a>
    <h1>{data.board.name}</h1>
    {#if data.board.description}
      <p class="board-description">{data.board.description}</p>
    {/if}
  </header>

  <div class="kanban-board">
    {#each data.columns as column (column.id)}
      <div
        class="kanban-column"
        class:drag-over={dragOverColumn === column.id}
        role="region"
        aria-label="{column.name} column"
        on:dragover={(e) => handleDragOver(e, column.id)}
        on:dragleave={handleDragLeave}
        on:drop={(e) => handleDrop(e, column.id)}
      >
        <div class="column-header" style="border-top-color: {column.color}">
          <h3>{column.name}</h3>
          <span class="task-count">{column.tasks.length}</span>
        </div>

        <div class="column-tasks">
          {#each column.tasks as task (task.id)}
            <div
              class="task-card"
              class:completed={task.isCompleted}
              class:overdue={task.isOverdue}
              role="listitem"
              aria-label="Task: {task.title}"
              draggable="true"
              on:dragstart={(e) => handleDragStart(e, task, column.id)}
              on:dragend={handleDragEnd}
            >
              <div class="task-title">{task.title}</div>
              {#if task.description}
                <div class="task-description">{task.description}</div>
              {/if}
              <div class="task-meta">
                <span
                  class="priority-badge"
                  style="background-color: {priorityColors[task.priority]}"
                >
                  {task.priority}
                </span>
                {#if task.dueDate}
                  <span class="due-date" class:overdue={task.isOverdue}>
                    {formatDate(task.dueDate)}
                  </span>
                {/if}
              </div>
              {#if task.assignedTo && task.assignedTo.length > 0}
                <div class="task-assignees">
                  {#each task.assignedTo.slice(0, 3) as assignee}
                    <span class="assignee-avatar" title={assignee.user?.email}>
                      {assignee.user?.email?.charAt(0).toUpperCase() || '?'}
                    </span>
                  {/each}
                  {#if task.assignedTo.length > 3}
                    <span class="assignee-more">+{task.assignedTo.length - 3}</span>
                  {/if}
                </div>
              {/if}
            </div>
          {/each}

          {#if addingTaskToColumn === column.id}
            <form
              class="add-task-form"
              method="POST"
              action="?/createTask"
              use:enhance={() => {
                return async ({ result }) => {
                  if (result.type === 'success') {
                    cancelAddingTask();
                    await invalidateAll();
                  }
                };
              }}
            >
              <input type="hidden" name="columnId" value={column.id} />
              <input
                type="text"
                name="title"
                bind:value={newTaskTitle}
                placeholder="Task title"
                required
              />
              <textarea
                name="description"
                bind:value={newTaskDescription}
                placeholder="Description (optional)"
                rows="2"
              ></textarea>
              <select name="priority" bind:value={newTaskPriority}>
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
              <div class="form-actions">
                <button type="submit" class="btn-primary">Add Task</button>
                <button type="button" class="btn-secondary" on:click={cancelAddingTask}
                  >Cancel</button
                >
              </div>
            </form>
          {:else}
            <button class="add-task-btn" on:click={() => startAddingTask(column.id)}>
              + Add Task
            </button>
          {/if}
        </div>
      </div>
    {/each}

    <!-- Add Column -->
    <div class="kanban-column add-column-wrapper">
      {#if showAddColumn}
        <form
          class="add-column-form"
          method="POST"
          action="?/createColumn"
          use:enhance={() => {
            return async ({ result }) => {
              if (result.type === 'success') {
                showAddColumn = false;
                newColumnName = '';
                await invalidateAll();
              }
            };
          }}
        >
          <input
            type="text"
            name="name"
            bind:value={newColumnName}
            placeholder="Column name"
            required
          />
          <input type="color" name="color" bind:value={newColumnColor} />
          <div class="form-actions">
            <button type="submit" class="btn-primary">Add</button>
            <button type="button" class="btn-secondary" on:click={() => (showAddColumn = false)}
              >Cancel</button
            >
          </div>
        </form>
      {:else}
        <button class="add-column-btn" on:click={() => (showAddColumn = true)}>
          + Add Column
        </button>
      {/if}
    </div>
  </div>
</div>

<style>
  .board-container {
    padding: 1.5rem;
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: #f4f5f7;
  }

  .board-header {
    margin-bottom: 1.5rem;
  }

  .back-link {
    color: #5e6c84;
    text-decoration: none;
    font-size: 0.9rem;
    display: inline-block;
    margin-bottom: 0.5rem;
  }

  .back-link:hover {
    color: #0079bf;
  }

  .board-header h1 {
    font-size: 1.8rem;
    font-weight: 700;
    color: #172b4d;
    margin: 0;
  }

  .board-description {
    color: #5e6c84;
    margin-top: 0.5rem;
    font-size: 0.95rem;
  }

  .kanban-board {
    display: flex;
    gap: 1rem;
    flex: 1;
    overflow-x: auto;
    padding-bottom: 1rem;
  }

  .kanban-column {
    flex: 0 0 300px;
    background: #ebecf0;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    max-height: calc(100vh - 180px);
  }

  .kanban-column.drag-over {
    background: #deebff;
  }

  .column-header {
    padding: 0.75rem 1rem;
    border-top: 3px solid #6b7280;
    border-radius: 8px 8px 0 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .column-header h3 {
    margin: 0;
    font-size: 1rem;
    font-weight: 600;
    color: #172b4d;
  }

  .task-count {
    background: #dfe1e6;
    color: #5e6c84;
    padding: 0.15rem 0.5rem;
    border-radius: 10px;
    font-size: 0.8rem;
    font-weight: 600;
  }

  .column-tasks {
    padding: 0.5rem;
    overflow-y: auto;
    flex: 1;
  }

  .task-card {
    background: #fff;
    border-radius: 6px;
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 3px rgba(9, 30, 66, 0.13);
    cursor: grab;
    transition:
      box-shadow 0.15s,
      transform 0.1s;
  }

  .task-card:hover {
    box-shadow: 0 4px 8px rgba(9, 30, 66, 0.2);
  }

  .task-card:active {
    cursor: grabbing;
    transform: rotate(2deg);
  }

  .task-card.completed {
    opacity: 0.7;
  }

  .task-card.overdue {
    border-left: 3px solid #ef4444;
  }

  .task-title {
    font-size: 0.95rem;
    font-weight: 500;
    color: #172b4d;
    margin-bottom: 0.5rem;
  }

  .task-description {
    font-size: 0.85rem;
    color: #5e6c84;
    margin-bottom: 0.5rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .task-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  .priority-badge {
    font-size: 0.7rem;
    padding: 0.15rem 0.4rem;
    border-radius: 3px;
    color: #fff;
    font-weight: 600;
    text-transform: uppercase;
  }

  .due-date {
    font-size: 0.8rem;
    color: #5e6c84;
  }

  .due-date.overdue {
    color: #ef4444;
    font-weight: 600;
  }

  .task-assignees {
    display: flex;
    gap: 0.25rem;
  }

  .assignee-avatar {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    background: #0079bf;
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.7rem;
    font-weight: 600;
  }

  .assignee-more {
    font-size: 0.75rem;
    color: #5e6c84;
    display: flex;
    align-items: center;
  }

  .add-task-btn,
  .add-column-btn {
    width: 100%;
    padding: 0.75rem;
    background: transparent;
    border: none;
    color: #5e6c84;
    font-size: 0.9rem;
    cursor: pointer;
    text-align: left;
    border-radius: 4px;
    transition:
      background 0.15s,
      color 0.15s;
  }

  .add-task-btn:hover,
  .add-column-btn:hover {
    background: #dfe1e6;
    color: #172b4d;
  }

  .add-task-form,
  .add-column-form {
    background: #fff;
    border-radius: 6px;
    padding: 0.75rem;
    box-shadow: 0 1px 3px rgba(9, 30, 66, 0.13);
  }

  .add-task-form input[type='text'],
  .add-task-form textarea,
  .add-task-form select,
  .add-column-form input[type='text'] {
    width: 100%;
    padding: 0.5rem;
    border: 2px solid #dfe1e6;
    border-radius: 4px;
    font-size: 0.9rem;
    margin-bottom: 0.5rem;
    box-sizing: border-box;
  }

  .add-task-form input:focus,
  .add-task-form textarea:focus,
  .add-task-form select:focus,
  .add-column-form input:focus {
    outline: none;
    border-color: #0079bf;
  }

  .add-column-form input[type='color'] {
    width: 40px;
    height: 32px;
    border: none;
    cursor: pointer;
    margin-bottom: 0.5rem;
  }

  .form-actions {
    display: flex;
    gap: 0.5rem;
  }

  .btn-primary {
    background: #0079bf;
    color: #fff;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 4px;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s;
  }

  .btn-primary:hover {
    background: #026aa7;
  }

  .btn-secondary {
    background: transparent;
    color: #5e6c84;
    border: none;
    padding: 0.5rem 1rem;
    font-size: 0.85rem;
    cursor: pointer;
    transition: background 0.15s;
  }

  .btn-secondary:hover {
    background: #dfe1e6;
  }

  .add-column-wrapper {
    background: transparent;
    flex: 0 0 280px;
  }
</style>
