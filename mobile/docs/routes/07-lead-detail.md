# Lead Detail Screen

**Route:** `/leads/[id]`
**File:** `src/routes/(app)/leads/[id]/+page.svelte`
**Layout:** App layout (MobileShell + BottomNav)

---

## Overview

The lead detail screen provides comprehensive information about a single lead, organized into tabs for Overview, Timeline, and Notes. It enables quick actions (call, email, message) and displays the complete interaction history.

---

## Screen Purpose

- Display complete lead information
- Enable quick communication actions
- Show interaction timeline/history
- Manage lead notes
- Update lead status

---

## UI Structure

### App Bar
- **Component:** `AppBar`
- **Props:** `showBack={true}`, `transparent={true}`
- **Trailing actions:**
  - Edit icon (navigate to edit screen)
  - More/menu icon (dropdown with actions)

### Header Section
- **Component:** `LeadDetailHeader`
- **Position:** Below app bar
- **Background:** Gradient or solid primary-50

#### Header Content

**Avatar**
- **Component:** `Avatar`
- **Size:** `xl` (64px)
- **Position:** Centered
- **Source:** Lead avatar or initials

**Name**
- **Text:** Lead full name
- **Style:** `text-2xl`, `font-bold`, `text-gray-900`
- **Margin:** `mt-4`

**Company**
- **Text:** Company name
- **Style:** `text-base`, `text-gray-500`
- **Margin:** `mt-1`

**Status Badges Row**
- **Layout:** `flex gap-2 justify-center`
- **Items:**
  - Status badge (New/Contacted/Qualified/Lost)
  - Priority badge (if high)
  - Tags (first 2)
- **Margin:** `mt-3`

**Quick Action Buttons**
- **Layout:** `flex gap-4 justify-center`
- **Margin:** `mt-4`

| Action | Icon | Color | Behavior |
|--------|------|-------|----------|
| Call | Phone | primary | Opens `tel:` link |
| Email | Mail | primary | Opens `mailto:` link |
| Message | MessageSquare | primary | Opens SMS/chat |

**Button Style:**
- Container: `w-12 h-12`, `rounded-full`, `bg-primary-100`
- Icon: `text-primary-600`, 24px
- Hover: `bg-primary-200`

---

### Tab Section

#### Tab Bar
- **Component:** `TabBar`
- **Tabs:**
  - Overview
  - Timeline
  - Notes
- **Style:** Full width, underline indicator
- **Active indicator:** Primary-600, 2px height

---

## Tab Content

### Overview Tab

#### Contact Information Card
- **Title:** "Contact Information"
- **Style:** Card with `p-4`, `rounded-xl`

| Field | Icon | Value |
|-------|------|-------|
| Email | Mail | lead.email (tappable, opens mailto) |
| Phone | Phone | lead.phone (tappable, opens tel) |
| Source | Globe/Link | lead.source |
| Created | Calendar | Formatted date |

**Field Layout:**
- Icon: 20px, `text-gray-400`
- Label: `text-xs`, `text-gray-500`, `uppercase`
- Value: `text-sm`, `text-gray-900`
- Spacing: `gap-4` between fields

#### Assigned To Card
- **Title:** "Assigned To"
- **Content:**
  - User avatar (md)
  - User name (`font-medium`)
  - User role (`text-sm`, `text-gray-500`)

#### Tags Section
- **Title:** "Tags"
- **Layout:** `flex flex-wrap gap-2`
- **Component:** `LabelPill` for each tag

#### Notes Preview
- **Title:** "Notes"
- **Content:** First 200 chars of notes
- **Action:** "See all notes" link (switches to Notes tab)

---

### Timeline Tab

#### Timeline Container
- **Layout:** Vertical list with connecting line
- **Line:** 2px width, `bg-gray-200`, left offset

#### Timeline Items
- **Component:** `TimelineItem`
- **Props:** `type`, `title`, `description`, `timestamp`, `isLast`

**Item Structure:**
```
[Icon Circle]----[Title]
     |          [Description]
     |          [Timestamp]
     |
[Icon Circle]----[Next Item...]
```

**Icon Circle:**
- Size: 32px
- Background: Type-specific color
- Icon: Type-specific icon, 16px, white

**Timeline Event Types:**

| Type | Icon | Color | Example Title |
|------|------|-------|---------------|
| call | Phone | primary-500 | "Phone call" |
| email | Mail | primary-500 | "Email sent" |
| note | FileText | gray-400 | "Note added" |
| meeting | Calendar | warning-500 | "Meeting scheduled" |
| stage_change | ArrowRight | success-500 | "Status changed to Qualified" |

**Content:**
- Title: `font-medium`, `text-gray-900`
- Description: `text-sm`, `text-gray-500`
- Timestamp: `text-xs`, `text-gray-400`

#### Empty State
- Message: "No activity yet"
- Description: "Start by making a call or sending an email"

---

### Notes Tab

#### Notes List
- **Layout:** Vertical list of note cards
- **Sorted:** Most recent first

#### Note Card
- **Background:** `bg-gray-50`
- **Padding:** `p-4`
- **Border radius:** `rounded-xl`
- **Margin:** `mb-3`

**Card Content:**
- Note text (multi-line)
- Author avatar + name
- Timestamp
- Edit/Delete actions (if current user's note)

#### Add Note Input
- **Position:** Bottom of notes list or floating
- **Input:** Multi-line textarea
- **Placeholder:** "Add a note..."
- **Submit button:** Send icon or "Add" button

---

## State Management

```javascript
import { page } from '$app/stores';
import { leads, activities, getUserById } from '$lib/stores/crmStore.svelte.js';

// Get lead ID from route params
let leadId = $derived($page.params.id);

// Find the lead
let lead = $derived(leads.find(l => l.id === leadId));

// Get assigned user
let assignedUser = $derived(lead ? getUserById(lead.assignedTo) : null);

// Filter activities for this lead
let leadActivities = $derived(
  activities
    .filter(a => a.relatedTo?.type === 'lead' && a.relatedTo?.id === leadId)
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
);

// Active tab state
let activeTab = $state('overview');
```

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Header background | primary-50 | #eff6ff |
| Avatar bg | varied | deterministic |
| Quick action bg | primary-100 | #dbeafe |
| Quick action icon | primary-600 | #2563eb |
| Tab active indicator | primary-600 | #2563eb |
| Tab inactive text | gray-500 | #6b7280 |
| Timeline line | gray-200 | #e5e7eb |
| Note card bg | gray-50 | #f9fafb |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| Header padding | 24px (p-6) |
| Avatar size | 64px (xl) |
| Quick actions gap | 16px (gap-4) |
| Tab bar height | 48px |
| Tab content padding | 16px (p-4) |
| Card padding | 16px (p-4) |
| Timeline icon size | 32px |
| Timeline left offset | 16px |

---

## Interactions

### Quick Actions
- **Call:** Opens phone dialer with `tel:{phone}`
- **Email:** Opens email client with `mailto:{email}`
- **Message:** Opens SMS app (or in-app chat)

### Tab Navigation
- Tap tab to switch content
- Smooth transition between tabs
- Preserve scroll position per tab

### Contact Info Tap
- Email: Opens mailto link
- Phone: Opens tel link

### Notes
- Add note: Submit form
- Edit note: Inline edit or modal
- Delete note: Confirmation dialog

### Status Change
- Dropdown in header or menu
- Confirm status change
- Update timeline automatically

### Edit Lead
- Navigate to edit screen
- Preserve current state
- Reload on return

---

## Flutter Implementation Notes

### Screen Structure
```dart
class LeadDetailScreen extends StatefulWidget {
  final String leadId;

  @override
  State<LeadDetailScreen> createState() => _LeadDetailScreenState();
}

class _LeadDetailScreenState extends State<LeadDetailScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
  }

  @override
  Widget build(BuildContext context) {
    final lead = // Get lead from provider/state

    return Scaffold(
      body: NestedScrollView(
        headerSliverBuilder: (context, innerBoxIsScrolled) => [
          SliverAppBar(
            expandedHeight: 280,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              background: LeadDetailHeader(lead: lead),
            ),
            bottom: TabBar(
              controller: _tabController,
              tabs: [
                Tab(text: 'Overview'),
                Tab(text: 'Timeline'),
                Tab(text: 'Notes'),
              ],
            ),
          ),
        ],
        body: TabBarView(
          controller: _tabController,
          children: [
            OverviewTab(lead: lead),
            TimelineTab(leadId: lead.id),
            NotesTab(leadId: lead.id),
          ],
        ),
      ),
    );
  }
}
```

### Quick Action Button
```dart
class QuickActionButton extends StatelessWidget {
  final IconData icon;
  final VoidCallback onTap;
  final String label;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Material(
          color: AppColors.primary100,
          shape: CircleBorder(),
          child: InkWell(
            onTap: onTap,
            customBorder: CircleBorder(),
            child: Container(
              width: 48,
              height: 48,
              alignment: Alignment.center,
              child: Icon(icon, color: AppColors.primary600),
            ),
          ),
        ),
        SizedBox(height: 4),
        Text(label, style: TextStyle(fontSize: 12, color: Colors.grey[600])),
      ],
    );
  }
}
```

### Timeline Item Widget
```dart
class TimelineItem extends StatelessWidget {
  final String type;
  final String title;
  final String? description;
  final DateTime timestamp;
  final bool isLast;

  Color get iconColor {
    switch (type) {
      case 'call':
      case 'email':
        return AppColors.primary500;
      case 'meeting':
        return AppColors.warning500;
      case 'stage_change':
        return AppColors.success500;
      default:
        return AppColors.gray400;
    }
  }

  @override
  Widget build(BuildContext context) {
    return IntrinsicHeight(
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(
            children: [
              Container(
                width: 32,
                height: 32,
                decoration: BoxDecoration(
                  color: iconColor,
                  shape: BoxShape.circle,
                ),
                child: Icon(_getIcon(), color: Colors.white, size: 16),
              ),
              if (!isLast)
                Expanded(
                  child: Container(
                    width: 2,
                    color: AppColors.gray200,
                  ),
                ),
            ],
          ),
          SizedBox(width: 12),
          Expanded(
            child: Padding(
              padding: EdgeInsets.only(bottom: 24),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title, style: TextStyle(fontWeight: FontWeight.w500)),
                  if (description != null)
                    Text(description!, style: TextStyle(color: Colors.grey[500])),
                  Text(
                    formatRelativeTime(timestamp),
                    style: TextStyle(fontSize: 12, color: Colors.grey[400]),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
```

---

## Accessibility

- **Header:** Announce lead name, company, status
- **Quick actions:** Clear labels (Call, Email, Message)
- **Tabs:** Announce tab name and selection state
- **Timeline:** Announce activity type, title, time
- **Notes:** Announce author and content

---

## Error States

### Lead Not Found
- Display error screen
- Back button to return to list
- Message: "Lead not found"

### Failed to Load Activities
- Show retry button
- Toast error message

### Failed to Add Note
- Keep note in input
- Show error toast
- Enable retry
