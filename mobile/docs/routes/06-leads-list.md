# Leads List Screen

**Route:** `/leads`
**File:** `src/routes/(app)/leads/+page.svelte`
**Layout:** App layout (MobileShell + BottomNav)

---

## Overview

The leads list screen displays all sales leads in a searchable, filterable, and sortable list. It provides quick access to lead details and supports multiple view/filter configurations to help sales reps manage their pipeline efficiently.

---

## Screen Purpose

- Display all leads in organized list
- Enable search by name, company, email
- Filter by status and source
- Sort by various criteria
- Quick navigation to lead details
- Access lead creation

---

## UI Structure

### App Bar
- **Component:** `AppBar`
- **Title:** "Leads"
- **Leading:** None (default)
- **Trailing:** Plus icon button
  - Action: Navigate to `/leads/create`

### Search Bar
- **Position:** Below app bar, sticky
- **Background:** `bg-surface-dim`
- **Padding:** `px-4 py-3`

#### Search Input
- **Component:** `InputFloatingLabel` or custom search
- **Placeholder:** "Search leads..."
- **Icon:** Search (lucide) on left
- **Type:** `search`
- **Behavior:** Real-time filtering as user types
- **Clear button:** X icon when has value

### Filter Bar
- **Position:** Below search, horizontal scroll
- **Layout:** `flex overflow-x-auto gap-2`
- **Padding:** `px-4 py-2`
- **Background:** `bg-surface`

#### Filter Chips

**Status Filter (Dropdown)**
- **Label:** "Status" or selected value
- **Icon:** ChevronDown
- **Options:**
  - All Statuses (default)
  - New
  - Contacted
  - Qualified
  - Lost
- **Selected style:** `bg-primary-100`, `text-primary-700`, `border-primary-300`
- **Default style:** `bg-gray-100`, `text-gray-700`

**Source Filter (Dropdown)**
- **Label:** "Source" or selected value
- **Options:**
  - All Sources (default)
  - Website
  - Referral
  - LinkedIn
  - Cold Call
  - Trade Show

**Sort Control (Dropdown)**
- **Label:** "Sort: {current}"
- **Icon:** ArrowUpDown
- **Options:**
  - Newest First (default)
  - Oldest First
  - Name (A-Z)
  - Name (Z-A)
  - Hot Leads First

### Results Count
- **Position:** Below filters
- **Text:** "{count} leads"
- **Style:** `text-sm`, `text-gray-500`
- **Padding:** `px-4 py-2`

### Leads List
- **Layout:** Vertical scroll
- **Gap:** None (cards have bottom border or margin)
- **Padding:** `px-4`

---

## Lead Card Component

### Card Structure
- **Component:** `LeadCard`
- **Background:** White
- **Border radius:** `rounded-xl`
- **Margin bottom:** `mb-3`
- **Padding:** `p-4`
- **Shadow:** Subtle (`shadow-sm`)

### Card Content

#### Row 1: Avatar + Basic Info
- **Avatar:**
  - Component: `Avatar`
  - Size: `md` (40px)
  - Source: `lead.avatar` or initials
  - Colors: Deterministic from name

- **Info Column:**
  - **Name:** `text-base`, `font-semibold`, `text-gray-900`
  - **Company:** `text-sm`, `text-gray-500`

- **Right side:**
  - Priority badge (if high)
  - "Hot" badge (if hot lead)
  - Time indicator (`text-xs`, `text-gray-400`)

#### Row 2: Tags
- **Component:** `LabelPill` (up to 2 shown)
- **Layout:** `flex gap-1.5`
- **Overflow:** Hidden with "+N more" indicator

#### Row 3: Status + Assignment
- **Left:** Status badge (New, Contacted, Qualified, Lost)
- **Right:** Assigned user avatar + name

### Card Interactions
- **Tap:** Navigate to `/leads/{id}`
- **Long press (optional):** Quick actions menu
- **Swipe (optional):** Quick call/email

---

## State Management

```javascript
import { leads, getUserById } from '$lib/stores/crmStore.svelte.js';

let searchQuery = $state('');
let statusFilter = $state('all');
let sourceFilter = $state('all');
let sortBy = $state('newest');

let filteredLeads = $derived(() => {
  let result = [...leads];

  // Search filter
  if (searchQuery) {
    const query = searchQuery.toLowerCase();
    result = result.filter(lead =>
      lead.name.toLowerCase().includes(query) ||
      lead.company.toLowerCase().includes(query) ||
      lead.email.toLowerCase().includes(query)
    );
  }

  // Status filter
  if (statusFilter !== 'all') {
    result = result.filter(lead => lead.status === statusFilter);
  }

  // Source filter
  if (sourceFilter !== 'all') {
    result = result.filter(lead => lead.source === sourceFilter);
  }

  // Sorting
  switch (sortBy) {
    case 'newest':
      result.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
      break;
    case 'oldest':
      result.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
      break;
    case 'name-asc':
      result.sort((a, b) => a.name.localeCompare(b.name));
      break;
    case 'name-desc':
      result.sort((a, b) => b.name.localeCompare(a.name));
      break;
    case 'hot':
      result.sort((a, b) => {
        if (a.priority === 'high' && b.priority !== 'high') return -1;
        if (b.priority === 'high' && a.priority !== 'high') return 1;
        return 0;
      });
      break;
  }

  return result;
});
```

---

## Filter/Sort Options

### Status Values
| Value | Label | Badge Color |
|-------|-------|-------------|
| new | New | primary-100/600 |
| contacted | Contacted | warning-50/600 |
| qualified | Qualified | success-50/600 |
| lost | Lost | danger-50/600 |

### Source Values
| Value | Label |
|-------|-------|
| website | Website |
| referral | Referral |
| linkedin | LinkedIn |
| cold-call | Cold Call |
| trade-show | Trade Show |

### Sort Options
| Value | Label | Logic |
|-------|-------|-------|
| newest | Newest First | createdAt DESC |
| oldest | Oldest First | createdAt ASC |
| name-asc | Name (A-Z) | name ASC |
| name-desc | Name (Z-A) | name DESC |
| hot | Hot Leads | priority high first |

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Background | surface-dim | #f8fafc |
| Card background | surface | #ffffff |
| Search input bg | gray-100 | #f3f4f6 |
| Filter chip default | gray-100 | #f3f4f6 |
| Filter chip active bg | primary-100 | #dbeafe |
| Filter chip active text | primary-700 | #1d4ed8 |
| Title text | gray-900 | #0f172a |
| Secondary text | gray-500 | #6b7280 |
| Count text | gray-500 | #6b7280 |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| Search bar padding | 16px horizontal, 12px vertical |
| Filter bar padding | 16px horizontal, 8px vertical |
| Filter chip gap | 8px (gap-2) |
| List padding | 16px horizontal |
| Card margin-bottom | 12px (mb-3) |
| Card padding | 16px (p-4) |
| Bottom padding | 80px (for BottomNav) |

---

## Interactions

### Search
- Debounced input (300ms)
- Clear button appears when has value
- Results update in real-time

### Filter Dropdowns
- Tap chip to open dropdown
- Select option to apply filter
- Multiple filters combine with AND logic
- Clear individual filter by selecting "All"

### Sort Dropdown
- Single selection
- Applies immediately

### Lead Card Tap
- Navigate to `/leads/{id}`
- Preserve filter/search state for back navigation

### Pull to Refresh
- Swipe down to refresh data
- Show loading indicator

### Infinite Scroll (if paginated)
- Load more as user scrolls near bottom
- Show loading spinner at bottom

---

## Flutter Implementation Notes

### Screen Structure
```dart
class LeadsListScreen extends StatefulWidget {
  @override
  State<LeadsListScreen> createState() => _LeadsListScreenState();
}

class _LeadsListScreenState extends State<LeadsListScreen> {
  final TextEditingController _searchController = TextEditingController();
  String _statusFilter = 'all';
  String _sourceFilter = 'all';
  String _sortBy = 'newest';

  List<Lead> get filteredLeads {
    // Apply filters and sorting
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Leads'),
        actions: [
          IconButton(
            icon: Icon(Icons.add),
            onPressed: () => Navigator.pushNamed(context, '/leads/create'),
          ),
        ],
      ),
      body: Column(
        children: [
          _buildSearchBar(),
          _buildFilterBar(),
          _buildResultsCount(),
          Expanded(
            child: RefreshIndicator(
              onRefresh: _handleRefresh,
              child: ListView.builder(
                padding: EdgeInsets.all(16),
                itemCount: filteredLeads.length,
                itemBuilder: (context, index) => LeadCard(
                  lead: filteredLeads[index],
                  onTap: () => Navigator.pushNamed(
                    context,
                    '/leads/${filteredLeads[index].id}',
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: BottomNav(currentIndex: 1),
    );
  }
}
```

### Search Bar Widget
```dart
Widget _buildSearchBar() {
  return Container(
    color: AppColors.surfaceDim,
    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 12),
    child: TextField(
      controller: _searchController,
      decoration: InputDecoration(
        hintText: 'Search leads...',
        prefixIcon: Icon(Icons.search),
        suffixIcon: _searchController.text.isNotEmpty
          ? IconButton(
              icon: Icon(Icons.clear),
              onPressed: () {
                _searchController.clear();
                setState(() {});
              },
            )
          : null,
        filled: true,
        fillColor: AppColors.gray100,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide.none,
        ),
      ),
      onChanged: (value) => setState(() {}),
    ),
  );
}
```

### Filter Chip
```dart
class FilterChip extends StatelessWidget {
  final String label;
  final bool isActive;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        decoration: BoxDecoration(
          color: isActive ? AppColors.primary100 : AppColors.gray100,
          borderRadius: BorderRadius.circular(20),
          border: isActive
            ? Border.all(color: AppColors.primary300)
            : null,
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              label,
              style: TextStyle(
                color: isActive ? AppColors.primary700 : AppColors.gray700,
                fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
              ),
            ),
            SizedBox(width: 4),
            Icon(
              Icons.keyboard_arrow_down,
              size: 18,
              color: isActive ? AppColors.primary700 : AppColors.gray700,
            ),
          ],
        ),
      ),
    );
  }
}
```

---

## Accessibility

- **Search:** Label "Search leads"
- **Filter chips:** Announce selected state
- **Lead cards:** Announce lead name, company, status
- **List:** Announce result count on filter change
- **Empty state:** Announce "No leads found"

---

## Empty States

### No Leads
- **Icon:** Users (gray)
- **Title:** "No leads yet"
- **Description:** "Start by adding your first lead"
- **CTA:** "Add Lead" button

### No Search Results
- **Icon:** Search (gray)
- **Title:** "No results found"
- **Description:** "Try adjusting your search or filters"
- **CTA:** "Clear filters" button

---

## Performance Considerations

- Virtualize long lists (`ListView.builder`)
- Debounce search input
- Cache filter results
- Lazy load avatars
- Consider pagination for large datasets
