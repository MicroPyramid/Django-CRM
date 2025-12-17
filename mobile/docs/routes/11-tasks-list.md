# Tasks List Screen

**Route:** `/tasks`
**File:** `src/routes/(app)/tasks/+page.svelte`
**Layout:** App layout (MobileShell + BottomNav)

---

## Overview

The tasks list screen provides two view modes: a Calendar view for date-based task visualization, and a List view grouped by due date status (Overdue, Today, Upcoming). It supports task completion, filtering, and quick task management.

---

## Screen Purpose

- Display all tasks in organized views
- Enable date-based task navigation (Calendar)
- Group tasks by urgency (List)
- Toggle task completion
- Create and manage tasks

---

## UI Structure

### App Bar
- **Component:** `AppBar`
- **Title:** "Tasks"
- **Trailing actions:**
  - View toggle icon (Calendar/List)
  - Plus icon (create new task)

### View Toggle
- **Component:** Icon toggle or segmented control
- **Options:**
  - Calendar (CalendarDays icon) - default
  - List (List icon)
- **Position:** App bar trailing

---

## Calendar View (Default)

### Calendar Component
- **Component:** `Calendar`
- **Position:** Top portion of screen
- **Height:** ~350px (fixed)

#### Calendar Header
- **Month/Year:** "December 2024"
- **Style:** `text-lg`, `font-semibold`, centered
- **Navigation:** Left/Right chevron buttons

#### Weekday Headers
- **Layout:** 7 columns
- **Labels:** S, M, T, W, T, F, S
- **Style:** `text-xs`, `text-gray-500`, `uppercase`

#### Date Grid
- **Layout:** 6 rows × 7 columns
- **Cell size:** Equal width, ~48px height
- **Tap action:** Select date

#### Date Cell States

| State | Style |
|-------|-------|
| Default | `text-gray-900` |
| Today | `bg-primary-100`, `text-primary-700`, `font-semibold` |
| Selected | `bg-primary-600`, `text-white`, `rounded-full` |
| Has tasks | Small dot indicator below number |
| Other month | `text-gray-300` |

#### Task Indicator Dots
- **Position:** Below date number
- **Size:** 4px circles
- **Max shown:** 3 dots
- **Color:** Based on task priority or count

### Tasks for Selected Date

#### Section Header
- **Text:** "Tasks for {Selected Date}"
- **Format:** "December 15" or "Today" or "Tomorrow"
- **Style:** `text-sm`, `text-gray-500`
- **Margin:** `mt-4`, `px-4`

#### Task List
- **Component:** `TaskRow` for each task
- **Layout:** Vertical list
- **Empty state:** "No tasks for this date"

---

## List View

### Grouped Task List
Tasks grouped into sections by due date status.

#### Group: Overdue
- **Component:** `TaskGroup`
- **Title:** "Overdue"
- **Variant:** `danger` (red accent)
- **Count badge:** Number of overdue tasks
- **Collapsed by default:** No (always visible if has tasks)

#### Group: Today
- **Component:** `TaskGroup`
- **Title:** "Today"
- **Variant:** `warning` (yellow accent)
- **Count badge:** Number of tasks due today

#### Group: Upcoming
- **Component:** `TaskGroup`
- **Title:** "Upcoming"
- **Variant:** `default` (gray accent)
- **Count badge:** Number of upcoming tasks
- **Sub-groups (optional):** Tomorrow, This Week, Later

---

## TaskRow Component

### Row Structure
- **Component:** `TaskRow`
- **Background:** White
- **Padding:** `py-3`, `px-4`
- **Border:** Bottom border `border-gray-100`

### Row Content

#### Left: Checkbox
- **Size:** 24px
- **Style:** Rounded checkbox
- **Unchecked:** `border-gray-300`
- **Checked:** `bg-primary-600`, checkmark icon
- **Action:** Toggle task completion

#### Center: Task Info
- **Title:** Task title
  - Style: `font-medium`, `text-gray-900`
  - Completed: `line-through`, `text-gray-400`
- **Subtitle Row:**
  - Due time: "2:30 PM" or "Dec 15"
  - Related entity: "Lead: John Doe" or "Deal: Enterprise Plan"
  - Style: `text-sm`, `text-gray-500`

#### Right: Priority + Assignee
- **Priority badge:** `PriorityBadge` component
- **Assignee avatar:** Small avatar (xs)

### Swipe Actions
- **Swipe left:** Delete button revealed
- **Delete button:** Red background, trash icon
- **Confirm:** Immediate delete or confirmation dialog

### Due Time Color Coding

| Condition | Color |
|-----------|-------|
| Overdue | `text-danger-600` |
| Due within 2 hours | `text-warning-600` |
| Due today | `text-gray-700` |
| Future | `text-gray-500` |

---

## TaskGroup Component

### Group Header
- **Layout:** Row with expand/collapse chevron
- **Content:**
  - Title (Overdue, Today, Upcoming)
  - Count badge
  - Chevron icon (rotates)

### Header Variants

| Variant | Left Border | Title Color |
|---------|-------------|-------------|
| danger | danger-500 | danger-600 |
| warning | warning-500 | warning-600 |
| default | gray-300 | gray-600 |

### Group Content
- **Layout:** Collapsible section
- **Children:** List of `TaskRow` components
- **Animation:** Height transition

---

## State Management

```javascript
import { tasks, toggleTaskComplete } from '$lib/stores/crmStore.svelte.js';

let viewMode = $state('calendar'); // 'calendar' | 'list'
let selectedDate = $state(new Date());

// For Calendar view
let tasksForSelectedDate = $derived(
  tasks.filter(t => isSameDay(new Date(t.dueDate), selectedDate))
);

// For List view
let overdueTasks = $derived(
  tasks.filter(t => !t.completed && isPast(new Date(t.dueDate)) && !isToday(new Date(t.dueDate)))
);

let todayTasks = $derived(
  tasks.filter(t => !t.completed && isToday(new Date(t.dueDate)))
);

let upcomingTasks = $derived(
  tasks.filter(t => !t.completed && isFuture(new Date(t.dueDate)))
);

// Dates that have tasks (for calendar dots)
let taskDates = $derived(
  [...new Set(tasks.map(t => formatDateKey(t.dueDate)))]
);
```

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Background | surface-dim | #f8fafc |
| Calendar bg | surface | #ffffff |
| Today bg | primary-100 | #dbeafe |
| Today text | primary-700 | #1d4ed8 |
| Selected bg | primary-600 | #2563eb |
| Selected text | white | #ffffff |
| Task dot | primary-500 | #3b82f6 |
| Overdue text | danger-600 | #dc2626 |
| Warning text | warning-600 | #d97706 |
| Checkbox checked | primary-600 | #2563eb |
| Completed text | gray-400 | #9ca3af |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| Calendar height | ~350px |
| Calendar padding | 16px |
| Date cell height | 48px |
| Task list padding | 16px horizontal |
| TaskRow padding | 12px vertical, 16px horizontal |
| Group header height | 48px |
| Bottom padding | 80px (BottomNav) |

---

## Interactions

### Calendar Navigation
- **Prev/Next month:** Tap chevron buttons
- **Date selection:** Tap date cell
- **Swipe (optional):** Horizontal swipe to change month

### Task Checkbox
- **Tap:** Toggle completion state
- **Animation:** Checkmark appears/disappears
- **Completed task:** Strikethrough animation

### Task Row Tap
- Navigate to `/tasks/{id}`
- Or open task detail modal

### Swipe to Delete
- Swipe left reveals delete button
- Tap delete or swipe fully to confirm
- Undo toast appears

### View Mode Toggle
- Instant switch between Calendar/List
- Preserve task data
- Reset scroll position

### Pull to Refresh
- Refresh task data
- Show loading indicator

---

## Flutter Implementation Notes

### Screen Structure
```dart
class TasksListScreen extends StatefulWidget {
  @override
  State<TasksListScreen> createState() => _TasksListScreenState();
}

class _TasksListScreenState extends State<TasksListScreen> {
  ViewMode _viewMode = ViewMode.calendar;
  DateTime _selectedDate = DateTime.now();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Tasks'),
        actions: [
          IconButton(
            icon: Icon(_viewMode == ViewMode.calendar
              ? Icons.list
              : Icons.calendar_month),
            onPressed: () => setState(() {
              _viewMode = _viewMode == ViewMode.calendar
                ? ViewMode.list
                : ViewMode.calendar;
            }),
          ),
          IconButton(
            icon: Icon(Icons.add),
            onPressed: () => Navigator.pushNamed(context, '/tasks/create'),
          ),
        ],
      ),
      body: _viewMode == ViewMode.calendar
        ? _buildCalendarView()
        : _buildListView(),
      bottomNavigationBar: BottomNav(currentIndex: 3),
    );
  }
}
```

### Calendar View
```dart
Widget _buildCalendarView() {
  return Column(
    children: [
      CalendarWidget(
        selectedDate: _selectedDate,
        onDateSelected: (date) => setState(() => _selectedDate = date),
        taskDates: _getTaskDates(),
      ),
      Padding(
        padding: EdgeInsets.all(16),
        child: Text(
          'Tasks for ${formatDate(_selectedDate)}',
          style: TextStyle(color: Colors.grey[500], fontSize: 14),
        ),
      ),
      Expanded(
        child: ListView.builder(
          itemCount: _getTasksForDate(_selectedDate).length,
          itemBuilder: (context, index) {
            final task = _getTasksForDate(_selectedDate)[index];
            return TaskRow(
              task: task,
              onToggle: () => _toggleTask(task.id),
              onTap: () => Navigator.pushNamed(context, '/tasks/${task.id}'),
            );
          },
        ),
      ),
    ],
  );
}
```

### Calendar Widget
```dart
class CalendarWidget extends StatelessWidget {
  final DateTime selectedDate;
  final Function(DateTime) onDateSelected;
  final Set<String> taskDates;

  @override
  Widget build(BuildContext context) {
    return TableCalendar(
      firstDay: DateTime.utc(2020, 1, 1),
      lastDay: DateTime.utc(2030, 12, 31),
      focusedDay: selectedDate,
      selectedDayPredicate: (day) => isSameDay(selectedDate, day),
      onDaySelected: (selectedDay, focusedDay) {
        onDateSelected(selectedDay);
      },
      calendarBuilders: CalendarBuilders(
        markerBuilder: (context, date, events) {
          if (taskDates.contains(_formatDateKey(date))) {
            return Positioned(
              bottom: 4,
              child: Container(
                width: 6,
                height: 6,
                decoration: BoxDecoration(
                  color: AppColors.primary500,
                  shape: BoxShape.circle,
                ),
              ),
            );
          }
          return null;
        },
      ),
    );
  }
}
```

### Task Row Widget
```dart
class TaskRow extends StatelessWidget {
  final Task task;
  final VoidCallback onToggle;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return Dismissible(
      key: Key(task.id),
      direction: DismissDirection.endToStart,
      background: Container(
        color: AppColors.danger500,
        alignment: Alignment.centerRight,
        padding: EdgeInsets.only(right: 16),
        child: Icon(Icons.delete, color: Colors.white),
      ),
      onDismissed: (_) => _deleteTask(task.id),
      child: InkWell(
        onTap: onTap,
        child: Container(
          padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            border: Border(
              bottom: BorderSide(color: AppColors.gray100),
            ),
          ),
          child: Row(
            children: [
              // Checkbox
              GestureDetector(
                onTap: onToggle,
                child: Container(
                  width: 24,
                  height: 24,
                  decoration: BoxDecoration(
                    color: task.completed ? AppColors.primary600 : null,
                    border: Border.all(
                      color: task.completed
                        ? AppColors.primary600
                        : AppColors.gray300,
                      width: 2,
                    ),
                    borderRadius: BorderRadius.circular(6),
                  ),
                  child: task.completed
                    ? Icon(Icons.check, size: 16, color: Colors.white)
                    : null,
                ),
              ),
              SizedBox(width: 12),
              // Task info
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      task.title,
                      style: TextStyle(
                        fontWeight: FontWeight.w500,
                        decoration: task.completed
                          ? TextDecoration.lineThrough
                          : null,
                        color: task.completed
                          ? AppColors.gray400
                          : AppColors.gray900,
                      ),
                    ),
                    SizedBox(height: 2),
                    Row(
                      children: [
                        Text(
                          _formatDueTime(task.dueDate),
                          style: TextStyle(
                            fontSize: 12,
                            color: _getDueTimeColor(task.dueDate),
                          ),
                        ),
                        if (task.relatedTo != null) ...[
                          Text(' • ', style: TextStyle(color: AppColors.gray400)),
                          Text(
                            task.relatedTo!.title,
                            style: TextStyle(
                              fontSize: 12,
                              color: AppColors.gray500,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ),
              ),
              // Priority + Avatar
              PriorityBadge(priority: task.priority, size: 'sm'),
              SizedBox(width: 8),
              Avatar(size: 'xs', userId: task.assignedTo),
            ],
          ),
        ),
      ),
    );
  }
}
```

### Task Group Widget
```dart
class TaskGroup extends StatefulWidget {
  final String title;
  final String variant; // 'danger', 'warning', 'default'
  final List<Task> tasks;

  @override
  State<TaskGroup> createState() => _TaskGroupState();
}

class _TaskGroupState extends State<TaskGroup> {
  bool _expanded = true;

  Color get _accentColor {
    switch (widget.variant) {
      case 'danger': return AppColors.danger500;
      case 'warning': return AppColors.warning500;
      default: return AppColors.gray300;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        InkWell(
          onTap: () => setState(() => _expanded = !_expanded),
          child: Container(
            padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              border: Border(
                left: BorderSide(color: _accentColor, width: 3),
              ),
            ),
            child: Row(
              children: [
                Text(
                  widget.title,
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: _accentColor,
                  ),
                ),
                SizedBox(width: 8),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: _accentColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${widget.tasks.length}',
                    style: TextStyle(
                      fontSize: 12,
                      color: _accentColor,
                    ),
                  ),
                ),
                Spacer(),
                Icon(
                  _expanded ? Icons.expand_less : Icons.expand_more,
                  color: AppColors.gray400,
                ),
              ],
            ),
          ),
        ),
        AnimatedCrossFade(
          firstChild: Column(
            children: widget.tasks.map((task) => TaskRow(task: task)).toList(),
          ),
          secondChild: SizedBox.shrink(),
          crossFadeState: _expanded
            ? CrossFadeState.showFirst
            : CrossFadeState.showSecond,
          duration: Duration(milliseconds: 200),
        ),
      ],
    );
  }
}
```

---

## Accessibility

- **Calendar:** Announce date and task count
- **Date selection:** Confirm selected date
- **Task checkbox:** Announce completion state
- **Groups:** Announce group name and task count
- **Swipe actions:** Provide alternative delete button

---

## Empty States

### No Tasks (Overall)
- **Icon:** CheckSquare
- **Title:** "All caught up!"
- **Description:** "No tasks to show. Create a new task to get started."
- **CTA:** "Add Task" button

### No Tasks for Date (Calendar)
- **Message:** "No tasks for {date}"
- **Style:** Centered, gray text

### No Overdue Tasks
- Hide the Overdue section entirely

---

## Performance Considerations

- Virtualize long task lists
- Cache date calculations
- Lazy load calendar months
- Debounce checkbox toggles
- Optimize swipe gesture handling
