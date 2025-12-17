# Dashboard Screen

**Route:** `/dashboard`
**File:** `src/routes/(app)/dashboard/+page.svelte`
**Layout:** App layout (MobileShell + BottomNav)

---

## Overview

The dashboard is the main hub of the CRM application, providing an at-a-glance view of key performance indicators, sales trends, pipeline status, upcoming tasks, and recent activity. It serves as the central navigation point after login.

---

## Screen Purpose

- Display critical business metrics (KPIs)
- Visualize sales trends and pipeline health
- Surface urgent items (tasks, deals closing soon)
- Provide quick actions via FAB
- Enable navigation to detailed sections

---

## UI Structure

### App Bar
- **Component:** `AppBar`
- **Title:** "Dashboard"
- **Leading:** Menu icon (hamburger)
- **Trailing:** Bell icon with notification badge
  - Badge shows unread count
  - Badge color: `bg-danger-500`
  - Navigate to `/more/notifications`

### Main Content (Scrollable)
Vertical scroll with multiple sections.

---

## Sections

### 1. KPI Cards Section

#### Container
- **Layout:** Horizontal scroll (`overflow-x-auto`)
- **Scroll snap:** `scroll-snap-x scroll-snap-mandatory`
- **Padding:** `px-4`, `py-2`
- **Gap:** `gap-3` between cards

#### KPI Card Component
Each card displays:
- **Icon:** In colored container (40px, rounded-xl)
- **Title:** Metric name (text-xs, text-gray-500)
- **Value:** Large number (text-2xl, font-bold)
- **Trend (optional):** Percentage with arrow
  - Up arrow: `text-success-600`
  - Down arrow: `text-danger-600`
- **Trend label:** Context (e.g., "vs last month")

#### KPI Data Points

| Metric | Icon | Icon BG | Sample Value | Trend |
|--------|------|---------|--------------|-------|
| Total Sales | DollarSign | success-100 | $284,500 | +12% |
| Open Deals | Briefcase | primary-100 | 24 | +4 |
| Pipeline Value | TrendingUp | warning-100 | $1.2M | +8% |
| Conversion Rate | Target | purple-100 | 32% | +2.5% |

#### Card Dimensions
- **Width:** `min-w-[160px]`
- **Height:** Auto (content-driven)
- **Padding:** `p-4`
- **Border radius:** `rounded-xl`
- **Background:** White with subtle shadow

---

### 2. Charts Section

#### Row Layout
- **Columns:** 2 (equal width)
- **Gap:** `gap-4`
- **Padding:** `px-4`, `mt-6`

#### Sales Trend Chart (Left)
- **Component:** `SalesChart`
- **Type:** Bar chart
- **Data:** 6 months of sales data
- **Features:**
  - Interactive hover tooltips
  - Shows value + deal count
  - Bars colored `primary-500`
  - Background grid lines
- **Height:** ~160px
- **Title:** "Sales Trend"

#### Task Completion Ring (Right)
- **Component:** `ProgressRing`
- **Type:** Circular progress indicator
- **Data:** Completed/Total tasks percentage
- **Features:**
  - SVG-based ring
  - Center shows percentage
  - Label below: "Tasks Done"
  - Color: `success-500`
- **Size:** 120px diameter
- **Title:** "Progress"

---

### 3. Pipeline Funnel Section

#### Header
- **Title:** "Pipeline"
- **Style:** `text-lg`, `font-semibold`
- **Padding:** `px-4`, `mt-6`, `mb-3`

#### Funnel Component
- **Component:** `PipelineFunnel`
- **Visualization:** Horizontal bars showing stage distribution
- **Stages displayed:**
  - Prospecting (count, value)
  - Qualified
  - Proposal
  - Negotiation
  - Closed Won
- **Each bar shows:**
  - Stage name
  - Deal count
  - Total value
  - Proportional width based on count
- **Colors:** Gradient from gray to primary to success

---

### 4. Deals Closing This Week Section

#### Header Row
- **Title:** "Closing This Week"
- **Style:** `text-lg`, `font-semibold`
- **Action:** "See All" link (text-primary-600)
- **Navigate to:** `/deals`
- **Padding:** `px-4`, `mt-6`, `mb-3`

#### Deal Cards
- **Component:** Mini deal cards (not full DealCard)
- **Display:** Top 3 deals closing within 7 days
- **Card content:**
  - Company name
  - Deal value
  - Days until close (color-coded)
  - Priority indicator
- **Empty state:** "No deals closing this week"

---

### 5. Today's Tasks Section

#### Header Row
- **Title:** "Today's Tasks"
- **Style:** `text-lg`, `font-semibold`
- **Action:** "See All" link
- **Navigate to:** `/tasks`
- **Padding:** `px-4`, `mt-6`, `mb-3`

#### Task Items
- **Component:** `TaskItem`
- **Display:** Tasks due today (up to 3)
- **Each item shows:**
  - Checkbox (toggle completion)
  - Task title
  - Due time
  - Related entity badge
- **Empty state:** "No tasks for today"

---

### 6. Recent Activity Section

#### Header Row
- **Title:** "Recent Activity"
- **Style:** `text-lg`, `font-semibold`
- **Padding:** `px-4`, `mt-6`, `mb-3`

#### Activity Feed
- **Component:** `ActivityItem`
- **Display:** Last 4 activities
- **Each item shows:**
  - Icon (based on activity type)
  - Title (action performed)
  - Description (details)
  - Relative timestamp
- **Activity types:**
  - Call (Phone icon, primary)
  - Email (Mail icon, primary)
  - Note (FileText icon, gray)
  - Meeting (Calendar icon, warning)
  - Stage change (ArrowRight icon, success)
  - Deal won (Trophy icon, success)
  - Deal lost (XCircle icon, danger)

---

### 7. Floating Action Button

- **Component:** `FAB`
- **Position:** Bottom-right, above BottomNav
- **Default state:** Plus icon
- **Expanded state:** 3 action buttons
  - Add Lead (User icon)
  - Add Deal (Briefcase icon)
  - Add Task (CheckSquare icon)
- **Backdrop:** Semi-transparent overlay when expanded
- **Actions:**
  - Lead: Navigate to `/leads/create`
  - Deal: Navigate to `/deals/create`
  - Task: Navigate to `/tasks/create`

---

## Data Flow

### KPI Computation
```javascript
import { getKpis } from '$lib/stores/crmStore.svelte.js';

let kpis = $derived(getKpis());
// Returns: { totalSales, openDeals, pipelineValue, leadsConverted, tasksToday, overdueTasksCount }
```

### Pipeline Stats
```javascript
import { getPipelineStats } from '$lib/stores/crmStore.svelte.js';

let pipelineStats = $derived(getPipelineStats());
// Returns: [{ stage, label, count, value }, ...]
```

### Deals Closing Soon
```javascript
import { getDealsClosingThisWeek } from '$lib/stores/crmStore.svelte.js';

let urgentDeals = $derived(getDealsClosingThisWeek());
```

### Today's Tasks
```javascript
let todaysTasks = $derived(
  tasks.filter(t => !t.completed && isToday(t.dueDate)).slice(0, 3)
);
```

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Background | surface-dim | #f8fafc |
| Card background | surface | #ffffff |
| Title text | gray-900 | #0f172a |
| Subtitle text | gray-500 | #6b7280 |
| Link text | primary-600 | #2563eb |
| Trend positive | success-600 | #16a34a |
| Trend negative | danger-600 | #dc2626 |
| FAB | primary-600 | #2563eb |
| Notification badge | danger-500 | #ef4444 |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| Screen padding (horizontal) | 16px (px-4) |
| Section gap | 24px (mt-6) |
| Section title margin-bottom | 12px (mb-3) |
| KPI cards gap | 12px (gap-3) |
| Chart columns gap | 16px (gap-4) |
| Card padding | 16px (p-4) |
| Bottom padding (for BottomNav) | 80px (pb-20) |

---

## Interactions

### Pull to Refresh (optional)
- Swipe down to refresh all data
- Loading indicator while fetching

### KPI Card Tap
- Navigate to relevant detail section
- Sales → Analytics
- Deals → Deals list
- Tasks → Tasks list

### Task Checkbox
- Toggle task completion
- Optimistic UI update
- Sync with store

### "See All" Links
- Navigate to respective list views
- Preserve any context/filters

### FAB Expansion
- Tap to expand
- Tap backdrop to collapse
- Tap action to navigate

### Notification Bell
- Shows unread badge count
- Navigate to notifications screen
- Badge disappears when all read

---

## Flutter Implementation Notes

### Screen Structure
```dart
class DashboardScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Dashboard'),
        leading: IconButton(
          icon: Icon(Icons.menu),
          onPressed: () => Scaffold.of(context).openDrawer(),
        ),
        actions: [
          Stack(
            children: [
              IconButton(
                icon: Icon(Icons.notifications_outlined),
                onPressed: () => Navigator.pushNamed(context, '/notifications'),
              ),
              if (unreadCount > 0)
                Positioned(
                  right: 8,
                  top: 8,
                  child: Badge(count: unreadCount),
                ),
            ],
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _handleRefresh,
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildKPISection(),
              _buildChartsSection(),
              _buildPipelineSection(),
              _buildDealsClosingSection(),
              _buildTasksSection(),
              _buildActivitySection(),
              SizedBox(height: 80), // Space for BottomNav
            ],
          ),
        ),
      ),
      floatingActionButton: ExpandableFAB(
        onLeadTap: () => Navigator.pushNamed(context, '/leads/create'),
        onDealTap: () => Navigator.pushNamed(context, '/deals/create'),
        onTaskTap: () => Navigator.pushNamed(context, '/tasks/create'),
      ),
      bottomNavigationBar: BottomNav(currentIndex: 0),
    );
  }
}
```

### KPI Card Widget
```dart
class KPICard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color iconBgColor;
  final double? trend;
  final String? trendLabel;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: 160,
      padding: EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 10,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding: EdgeInsets.all(10),
            decoration: BoxDecoration(
              color: iconBgColor,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon, size: 20),
          ),
          SizedBox(height: 12),
          Text(title, style: TextStyle(color: Colors.grey[500], fontSize: 12)),
          SizedBox(height: 4),
          Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
          if (trend != null) ...[
            SizedBox(height: 4),
            Row(
              children: [
                Icon(
                  trend! >= 0 ? Icons.arrow_upward : Icons.arrow_downward,
                  size: 14,
                  color: trend! >= 0 ? Colors.green : Colors.red,
                ),
                Text(
                  '${trend!.abs()}%',
                  style: TextStyle(
                    fontSize: 12,
                    color: trend! >= 0 ? Colors.green : Colors.red,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
```

### Charts
- Use `fl_chart` package for bar chart and progress ring
- Or `syncfusion_flutter_charts` for more options
- Custom painter for simple progress ring

---

## Accessibility

- **KPI cards:** Announce full value and trend
- **Charts:** Provide text alternatives
- **Activity feed:** Time announced in accessible format
- **FAB:** Expanded options have labels
- **Notification badge:** Announce count

---

## Performance Considerations

- Lazy load chart data
- Cache KPI computations
- Debounce scroll events
- Optimize list rendering
- Consider skeleton loading states

---

## Empty States

### No Deals
- Message: "No deals in pipeline yet"
- CTA: "Add your first deal"

### No Tasks
- Message: "No tasks for today"
- CTA: "Create a task"

### No Activity
- Message: "No recent activity"
- CTA: "Start tracking your work"
