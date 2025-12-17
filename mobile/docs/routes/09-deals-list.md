# Deals List Screen

**Route:** `/deals`
**File:** `src/routes/(app)/deals/+page.svelte`
**Layout:** App layout (MobileShell + BottomNav)

---

## Overview

The deals list screen displays the sales pipeline using two view modes: a Kanban board (default) for visual pipeline management, and a list view for quick scanning. It provides search functionality and stage-based organization of all deals.

---

## Screen Purpose

- Visualize sales pipeline stages
- Enable drag-and-drop deal progression (Kanban)
- Quick deal search
- Access to deal details
- Toggle between view modes

---

## UI Structure

### App Bar
- **Component:** `AppBar`
- **Title:** "Deals"
- **Trailing actions:**
  - Search icon (toggles search bar)
  - View toggle icon (List/Kanban switch)
  - Plus icon (create new deal)

### Search Bar (Collapsible)
- **Position:** Below app bar when active
- **Input:** Search by deal title or company name
- **Clear button:** X icon when has value
- **Animation:** Slide down when shown

### View Toggle
- **Component:** Segmented control or icon toggle
- **Options:**
  - Kanban (LayoutGrid icon) - default
  - List (List icon)
- **Position:** In app bar trailing or below search

---

## Kanban View (Default)

### Pipeline Stage Columns

#### Container
- **Layout:** Horizontal scroll (`overflow-x-auto`)
- **Scroll snap:** `scroll-snap-x scroll-snap-mandatory`
- **Height:** Fill available (minus app bar and bottom nav)
- **Padding:** `px-4`

#### Stage Columns
- **Component:** `KanbanColumn`
- **Width:** `min-w-[300px]` (snaps to viewport width on mobile)
- **Gap:** `gap-3` between columns

### KanbanColumn Component

#### Column Header
- **Layout:** Row with color dot, title, count badge
- **Color dot:** 8px circle, stage-specific color
- **Title:** Stage name, `font-semibold`
- **Count badge:** Deal count, `bg-gray-100`, rounded pill
- **Total value:** Below title, `text-sm`, `text-gray-500`

#### Column Content
- **Layout:** Vertical scroll within column
- **Gap:** `gap-3` between cards
- **Padding:** `py-3`
- **Empty state:** "No deals" message

### Pipeline Stages

| Stage | Label | Color | Dot Color |
|-------|-------|-------|-----------|
| prospecting | Prospecting | gray | gray-400 |
| qualified | Qualified | blue | primary-500 |
| proposal | Proposal | purple | purple-500 |
| negotiation | Negotiation | warning | warning-500 |
| closed-won | Closed Won | success | success-500 |
| closed-lost | Closed Lost | danger | danger-500 |

---

## List View

### Grouped by Stage
- **Layout:** Vertical scroll
- **Grouping:** Deals grouped under stage headers

### Stage Group Header
- **Layout:** Sticky row
- **Content:** Stage name, deal count, total value
- **Style:** `bg-gray-50`, `py-3`, `px-4`
- **Color indicator:** Left border or dot

### Deal Cards in List
- Same `DealCard` component as Kanban
- Full-width layout
- Margin between cards

---

## DealCard Component

### Card Structure
- **Background:** White
- **Border radius:** `rounded-xl`
- **Padding:** `p-4`
- **Shadow:** `shadow-sm`
- **Draggable prop:** For Kanban mode

### Card Content

#### Row 1: Title + Priority
- **Title:** `font-semibold`, `text-gray-900`
- **Priority badge:** PriorityBadge component (right side)

#### Row 2: Company
- **Text:** Company name
- **Style:** `text-sm`, `text-gray-500`

#### Row 3: Labels
- **Component:** `LabelPill` (up to 3)
- **Layout:** `flex gap-1.5 flex-wrap`
- **Overflow:** "+N more" indicator

#### Row 4: Value + Close Date
- **Layout:** Row, space-between
- **Value:** Formatted currency, `font-semibold`
- **Close date:** Days until close indicator

**Close Date States:**
| Condition | Style | Example |
|-----------|-------|---------|
| > 7 days | `text-gray-500` | "15 days" |
| 1-7 days | `text-warning-600` | "5 days" (warning icon) |
| Today | `text-warning-600` | "Today" |
| Overdue | `text-danger-600` | "3 days overdue" |

#### Row 5: Probability + Assignee
- **Probability bar:**
  - Width: percentage of probability
  - Height: 4px
  - Color: primary-500
  - Background: gray-200
- **Assignee:** Avatar (xs) on right

#### Row 6: Products (optional)
- **Text:** Product count badge
- **Style:** `text-xs`, `bg-gray-100`

---

## State Management

```javascript
import { deals, getUserById, formatCurrency } from '$lib/stores/crmStore.svelte.js';

let searchQuery = $state('');
let viewMode = $state('kanban'); // 'kanban' | 'list'

// Filter deals by search
let filteredDeals = $derived(() => {
  if (!searchQuery) return deals;
  const query = searchQuery.toLowerCase();
  return deals.filter(deal =>
    deal.title.toLowerCase().includes(query) ||
    deal.companyName.toLowerCase().includes(query)
  );
});

// Group deals by stage for both views
let dealsByStage = $derived(() => {
  const stages = ['prospecting', 'qualified', 'proposal', 'negotiation', 'closed-won'];
  return stages.reduce((acc, stage) => {
    acc[stage] = filteredDeals.filter(d => d.stage === stage);
    return acc;
  }, {});
});

// Calculate stage totals
function getStageTotal(stage) {
  return dealsByStage[stage].reduce((sum, d) => sum + d.value, 0);
}
```

---

## Drag and Drop (Kanban)

### Implementation Approach
```javascript
let draggedDeal = $state(null);

function handleDragStart(deal) {
  draggedDeal = deal;
}

function handleDragOver(e, stage) {
  e.preventDefault();
  // Add visual indicator to column
}

function handleDrop(e, targetStage) {
  e.preventDefault();
  if (draggedDeal && draggedDeal.stage !== targetStage) {
    updateDealStage(draggedDeal.id, targetStage);
  }
  draggedDeal = null;
}
```

### Visual Feedback
- **Dragging card:** Slight opacity reduction, shadow increase
- **Target column:** Highlighted border, background tint
- **Drop zone:** Dashed border indicator

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Background | surface-dim | #f8fafc |
| Card background | surface | #ffffff |
| Column header bg | transparent | - |
| Stage dot (prospecting) | gray-400 | #9ca3af |
| Stage dot (qualified) | primary-500 | #3b82f6 |
| Stage dot (proposal) | purple-500 | #a855f7 |
| Stage dot (negotiation) | warning-500 | #f59e0b |
| Stage dot (closed-won) | success-500 | #22c55e |
| Probability bar bg | gray-200 | #e5e7eb |
| Probability bar fill | primary-500 | #3b82f6 |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| App bar height | 56px |
| Column min-width | 300px |
| Column gap | 12px (gap-3) |
| Card padding | 16px (p-4) |
| Card margin-bottom | 12px |
| Section padding horizontal | 16px |
| Bottom padding | 80px (BottomNav) |

---

## Interactions

### Search
- Tap search icon to show/hide search bar
- Real-time filtering as user types
- Clear button to reset

### View Toggle
- Tap to switch between Kanban/List
- Preserve search query between views
- Animate transition

### Deal Card Tap
- Navigate to `/deals/{id}`
- Preserve view state for back navigation

### Drag and Drop (Kanban)
- Long press to start drag (mobile)
- Drag to target column
- Release to drop
- Stage updates immediately

### Pull to Refresh
- Swipe down to refresh data
- Works in both view modes

### Horizontal Scroll (Kanban)
- Snap to column centers
- Show partial next column as hint
- Smooth scroll behavior

---

## Flutter Implementation Notes

### Screen Structure
```dart
class DealsListScreen extends StatefulWidget {
  @override
  State<DealsListScreen> createState() => _DealsListScreenState();
}

class _DealsListScreenState extends State<DealsListScreen> {
  bool _showSearch = false;
  String _searchQuery = '';
  ViewMode _viewMode = ViewMode.kanban;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Deals'),
        actions: [
          IconButton(
            icon: Icon(Icons.search),
            onPressed: () => setState(() => _showSearch = !_showSearch),
          ),
          IconButton(
            icon: Icon(_viewMode == ViewMode.kanban
              ? Icons.view_list
              : Icons.view_column),
            onPressed: () => setState(() {
              _viewMode = _viewMode == ViewMode.kanban
                ? ViewMode.list
                : ViewMode.kanban;
            }),
          ),
          IconButton(
            icon: Icon(Icons.add),
            onPressed: () => Navigator.pushNamed(context, '/deals/create'),
          ),
        ],
      ),
      body: Column(
        children: [
          if (_showSearch) _buildSearchBar(),
          Expanded(
            child: _viewMode == ViewMode.kanban
              ? _buildKanbanView()
              : _buildListView(),
          ),
        ],
      ),
      bottomNavigationBar: BottomNav(currentIndex: 2),
    );
  }
}
```

### Kanban View
```dart
Widget _buildKanbanView() {
  return SingleChildScrollView(
    scrollDirection: Axis.horizontal,
    physics: PageScrollPhysics(),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: stages.map((stage) => KanbanColumn(
        stage: stage,
        deals: dealsByStage[stage.id] ?? [],
        onDealTap: (deal) => Navigator.pushNamed(
          context,
          '/deals/${deal.id}',
        ),
        onDealMoved: (deal, newStage) => _handleDealMove(deal, newStage),
      )).toList(),
    ),
  );
}
```

### Kanban Column Widget
```dart
class KanbanColumn extends StatelessWidget {
  final PipelineStage stage;
  final List<Deal> deals;
  final Function(Deal) onDealTap;
  final Function(Deal, String) onDealMoved;

  @override
  Widget build(BuildContext context) {
    final totalValue = deals.fold<int>(0, (sum, d) => sum + d.value);

    return Container(
      width: MediaQuery.of(context).size.width - 32,
      margin: EdgeInsets.symmetric(horizontal: 8),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Padding(
            padding: EdgeInsets.all(12),
            child: Row(
              children: [
                Container(
                  width: 8,
                  height: 8,
                  decoration: BoxDecoration(
                    color: stage.color,
                    shape: BoxShape.circle,
                  ),
                ),
                SizedBox(width: 8),
                Text(stage.label, style: TextStyle(fontWeight: FontWeight.w600)),
                SizedBox(width: 8),
                Container(
                  padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                  decoration: BoxDecoration(
                    color: Colors.grey[100],
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text('${deals.length}', style: TextStyle(fontSize: 12)),
                ),
                Spacer(),
                Text(
                  formatCurrency(totalValue),
                  style: TextStyle(color: Colors.grey[500], fontSize: 12),
                ),
              ],
            ),
          ),
          // Deals list
          Expanded(
            child: DragTarget<Deal>(
              onAccept: (deal) => onDealMoved(deal, stage.id),
              builder: (context, candidateData, rejectedData) {
                return ListView.builder(
                  padding: EdgeInsets.all(8),
                  itemCount: deals.length,
                  itemBuilder: (context, index) => Draggable<Deal>(
                    data: deals[index],
                    feedback: Material(
                      elevation: 4,
                      child: DealCard(deal: deals[index]),
                    ),
                    childWhenDragging: Opacity(
                      opacity: 0.3,
                      child: DealCard(deal: deals[index]),
                    ),
                    child: DealCard(
                      deal: deals[index],
                      onTap: () => onDealTap(deals[index]),
                    ),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
```

### Deal Card Widget
```dart
class DealCard extends StatelessWidget {
  final Deal deal;
  final VoidCallback? onTap;

  int get daysUntilClose {
    return deal.closeDate.difference(DateTime.now()).inDays;
  }

  Color get closeDateColor {
    if (daysUntilClose < 0) return AppColors.danger600;
    if (daysUntilClose <= 7) return AppColors.warning600;
    return AppColors.gray500;
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Row 1: Title + Priority
              Row(
                children: [
                  Expanded(
                    child: Text(
                      deal.title,
                      style: TextStyle(fontWeight: FontWeight.w600),
                    ),
                  ),
                  PriorityBadge(priority: deal.priority),
                ],
              ),
              SizedBox(height: 4),
              // Row 2: Company
              Text(
                deal.companyName,
                style: TextStyle(color: Colors.grey[500], fontSize: 14),
              ),
              SizedBox(height: 8),
              // Row 3: Labels
              Wrap(
                spacing: 6,
                runSpacing: 6,
                children: deal.labels.take(3).map((label) =>
                  LabelPill(label: label)
                ).toList(),
              ),
              SizedBox(height: 12),
              // Row 4: Value + Close Date
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    formatCurrency(deal.value),
                    style: TextStyle(fontWeight: FontWeight.w600),
                  ),
                  Row(
                    children: [
                      if (daysUntilClose <= 7 && daysUntilClose >= 0)
                        Icon(Icons.warning_amber, size: 14, color: closeDateColor),
                      SizedBox(width: 4),
                      Text(
                        _formatCloseDate(),
                        style: TextStyle(color: closeDateColor, fontSize: 12),
                      ),
                    ],
                  ),
                ],
              ),
              SizedBox(height: 8),
              // Row 5: Probability bar
              LinearProgressIndicator(
                value: deal.probability / 100,
                backgroundColor: AppColors.gray200,
                valueColor: AlwaysStoppedAnimation(AppColors.primary500),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

---

## Accessibility

- **View mode:** Announce current view (Kanban/List)
- **Columns:** Announce stage name and deal count
- **Deal cards:** Full deal info announced
- **Drag/drop:** Provide alternative (menu-based) stage change
- **Search:** Label and clear button accessible

---

## Empty States

### No Deals
- **Kanban:** Empty columns with "No deals" message
- **List:** Full-screen empty state
- **CTA:** "Add your first deal" button

### No Search Results
- **Message:** "No deals match your search"
- **CTA:** "Clear search" button

---

## Performance Considerations

- Lazy load deal cards in columns
- Cache column calculations
- Debounce search input
- Optimize drag preview rendering
- Consider virtualization for large datasets
