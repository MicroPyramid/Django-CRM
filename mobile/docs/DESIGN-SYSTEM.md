# CRM Mobile App Design System

A comprehensive design system document for implementing the SalesPro CRM application in Flutter. This document serves as the single source of truth for colors, typography, spacing, components, and interaction patterns.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Spacing & Layout](#spacing--layout)
5. [Icons](#icons)
6. [Components Overview](#components-overview)
7. [Animation & Motion](#animation--motion)
8. [Interaction Patterns](#interaction-patterns)
9. [Data Models](#data-models)
10. [Navigation Structure](#navigation-structure)
11. [Screen Inventory](#screen-inventory)

---

## Design Principles

### 1. Mobile-First
- Designed for 375-430px viewport width
- Touch-friendly targets (minimum 44px)
- Bottom-aligned navigation
- Thumb-zone optimized actions

### 2. Professional & Clean
- Minimal visual clutter
- Consistent spacing rhythm
- Clear visual hierarchy
- White space as design element

### 3. Action-Oriented
- Primary actions always visible
- Quick actions via FAB
- Swipe gestures for common tasks
- One-tap access to critical functions

### 4. Data-Dense but Readable
- Information hierarchy through typography
- Color-coded status indicators
- Compact cards with essential info
- Progressive disclosure for details

---

## Color System

### Primary Palette (Blue)

The primary color represents the brand and is used for:
- Primary buttons
- Active navigation items
- Links and interactive elements
- Focus states

```dart
class AppColors {
  // Primary Blue
  static const primary50 = Color(0xFFEFF6FF);
  static const primary100 = Color(0xFFDBEAFE);
  static const primary200 = Color(0xFFBFDBFE);
  static const primary300 = Color(0xFF93C5FD);
  static const primary400 = Color(0xFF60A5FA);
  static const primary500 = Color(0xFF3B82F6);
  static const primary600 = Color(0xFF2563EB);  // Main action color
  static const primary700 = Color(0xFF1D4ED8);
  static const primary800 = Color(0xFF1E40AF);
  static const primary900 = Color(0xFF1E3A8A);
}
```

### Semantic Colors

```dart
class AppColors {
  // Success (Green)
  static const success50 = Color(0xFFF0FDF4);
  static const success100 = Color(0xFFDCFCE7);
  static const success500 = Color(0xFF22C55E);
  static const success600 = Color(0xFF16A34A);
  static const success700 = Color(0xFF15803D);

  // Warning (Amber)
  static const warning50 = Color(0xFFFFFBEB);
  static const warning100 = Color(0xFFFEF3C7);
  static const warning500 = Color(0xFFF59E0B);
  static const warning600 = Color(0xFFD97706);
  static const warning700 = Color(0xFFB45309);

  // Danger (Red)
  static const danger50 = Color(0xFFFEF2F2);
  static const danger100 = Color(0xFFFEE2E2);
  static const danger500 = Color(0xFFEF4444);
  static const danger600 = Color(0xFFDC2626);
  static const danger700 = Color(0xFFB91C1C);
}
```

### Neutral Colors (Gray)

```dart
class AppColors {
  // Gray Scale
  static const gray50 = Color(0xFFF9FAFB);
  static const gray100 = Color(0xFFF3F4F6);
  static const gray200 = Color(0xFFE5E7EB);
  static const gray300 = Color(0xFFD1D5DB);
  static const gray400 = Color(0xFF9CA3AF);
  static const gray500 = Color(0xFF6B7280);
  static const gray600 = Color(0xFF4B5563);
  static const gray700 = Color(0xFF374151);
  static const gray800 = Color(0xFF1F2937);
  static const gray900 = Color(0xFF0F172A);  // Primary text
}
```

### Surface Colors

```dart
class AppColors {
  // Surfaces
  static const surface = Color(0xFFFFFFFF);      // Cards, modals
  static const surfaceDim = Color(0xFFF8FAFC);   // Page backgrounds
  static const surfaceBright = Color(0xFFFFFFFF);
}
```

### Color Usage Guidelines

| Use Case | Color |
|----------|-------|
| Primary text | gray-900 (#0F172A) |
| Secondary text | gray-500 (#6B7280) |
| Tertiary/hint text | gray-400 (#9CA3AF) |
| Disabled text | gray-400 with 50% opacity |
| Dividers/borders | gray-200 (#E5E7EB) |
| Page background | surfaceDim (#F8FAFC) |
| Card background | surface (#FFFFFF) |
| Primary button | primary-600 (#2563EB) |
| Success indicator | success-500 (#22C55E) |
| Warning indicator | warning-500 (#F59E0B) |
| Error/danger | danger-500 (#EF4444) |

---

## Typography

### Font Family

Use the system font stack for optimal performance and native feel:

```dart
// Flutter default handles this automatically
// For explicit control:
fontFamily: '.SF Pro Text', // iOS
fontFamily: 'Roboto',       // Android
```

### Type Scale

```dart
class AppTypography {
  // Display (Hero text)
  static const display = TextStyle(
    fontSize: 32,
    fontWeight: FontWeight.bold,
    height: 1.2,
  );

  // Headings
  static const h1 = TextStyle(
    fontSize: 24,
    fontWeight: FontWeight.bold,
    height: 1.3,
  );

  static const h2 = TextStyle(
    fontSize: 20,
    fontWeight: FontWeight.w600,
    height: 1.4,
  );

  static const h3 = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w600,
    height: 1.4,
  );

  // Body text
  static const bodyLarge = TextStyle(
    fontSize: 16,
    fontWeight: FontWeight.normal,
    height: 1.5,
  );

  static const body = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.normal,
    height: 1.5,
  );

  static const bodySmall = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.normal,
    height: 1.4,
  );

  // Labels
  static const label = TextStyle(
    fontSize: 14,
    fontWeight: FontWeight.w500,
    height: 1.4,
  );

  static const labelSmall = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w500,
    height: 1.3,
  );

  // Caption
  static const caption = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.normal,
    color: AppColors.gray500,
    height: 1.3,
  );

  // Overline (section headers)
  static const overline = TextStyle(
    fontSize: 12,
    fontWeight: FontWeight.w600,
    letterSpacing: 0.5,
    color: AppColors.gray500,
  );
}
```

### Font Weights

| Weight | Value | Usage |
|--------|-------|-------|
| Regular | 400 | Body text, descriptions |
| Medium | 500 | Labels, emphasized text |
| Semi-bold | 600 | Headings, buttons |
| Bold | 700 | Titles, important numbers |

---

## Spacing & Layout

### Spacing Scale

Use a 4px base unit system:

```dart
class AppSpacing {
  static const xs = 4.0;    // 4px
  static const sm = 8.0;    // 8px
  static const md = 12.0;   // 12px
  static const lg = 16.0;   // 16px
  static const xl = 20.0;   // 20px
  static const xxl = 24.0;  // 24px
  static const xxxl = 32.0; // 32px
}
```

### Common Spacing Patterns

| Pattern | Value | Usage |
|---------|-------|-------|
| Page padding | 16px | Horizontal padding for screens |
| Card padding | 16px | Internal card padding |
| Card margin | 12px | Space between cards |
| Section gap | 24px | Space between major sections |
| Item gap | 8-12px | Space between list items |
| Input height | 56px | Text field height |
| Button height | 48px (lg), 44px (md), 36px (sm) | Action buttons |

### Layout Constants

```dart
class AppLayout {
  // Screen constraints
  static const maxWidth = 430.0;
  static const minTouchTarget = 44.0;

  // Component heights
  static const appBarHeight = 56.0;
  static const bottomNavHeight = 64.0;
  static const fabSize = 56.0;
  static const fabMiniSize = 48.0;

  // Border radius
  static const radiusSm = 8.0;
  static const radiusMd = 12.0;
  static const radiusLg = 16.0;
  static const radiusXl = 20.0;
  static const radiusFull = 9999.0;
}
```

### Safe Areas

Account for device notches and home indicators:

```dart
// Always wrap in SafeArea or account for padding
SafeArea(
  child: YourContent(),
)

// Or manually
MediaQuery.of(context).padding.top    // Status bar
MediaQuery.of(context).padding.bottom // Home indicator
```

---

## Icons

### Icon Library

Use Lucide icons (available as Flutter package `lucide_icons` or Material Icons equivalents):

### Common Icon Mappings

| Feature | Lucide Icon | Material Equivalent |
|---------|-------------|---------------------|
| Dashboard | LayoutDashboard | dashboard |
| Leads | Users | people |
| Deals | Briefcase | work |
| Tasks | CheckSquare | check_box |
| More/Settings | MoreHorizontal | more_horiz |
| Add | Plus | add |
| Back | ChevronLeft | arrow_back |
| Search | Search | search |
| Filter | Filter | filter_list |
| Sort | ArrowUpDown | sort |
| Call | Phone | phone |
| Email | Mail | email |
| Message | MessageSquare | chat |
| Calendar | Calendar | calendar_today |
| Edit | Pencil | edit |
| Delete | Trash2 | delete |
| Close | X | close |
| Check | Check | check |
| Warning | AlertTriangle | warning |
| Info | Info | info |
| User | User | person |
| Settings | Settings | settings |
| Notification | Bell | notifications |
| Logout | LogOut | logout |

### Icon Sizes

| Size | Pixels | Usage |
|------|--------|-------|
| xs | 16px | Inline with text |
| sm | 20px | List items, badges |
| md | 24px | Navigation, buttons |
| lg | 32px | Feature icons |
| xl | 48px | Empty states, headers |

---

## Components Overview

### Core UI Components

| Component | Purpose | Location |
|-----------|---------|----------|
| Button | Primary actions | `/components/ui/` |
| IconButton | Icon-only actions | `/components/ui/` |
| Card | Content containers | `/components/ui/` |
| InputFloatingLabel | Form inputs | `/components/ui/` |
| Avatar | User images | `/components/ui/` |
| Badge | Status indicators | `/components/ui/` |
| PriorityBadge | Priority display | `/components/ui/` |
| LabelPill | Tags/labels | `/components/ui/` |
| TabBar | Tab navigation | `/components/ui/` |

### Layout Components

| Component | Purpose | Location |
|-----------|---------|----------|
| MobileShell | Viewport wrapper | `/components/layout/` |
| AppBar | Top navigation | `/components/layout/` |
| BottomNav | Bottom navigation | `/components/layout/` |
| FAB | Quick actions | `/components/layout/` |

### Domain Components

| Component | Purpose | Location |
|-----------|---------|----------|
| LeadCard | Lead list item | `/components/leads/` |
| LeadDetailHeader | Lead header | `/components/leads/` |
| TimelineItem | Activity entry | `/components/leads/` |
| DealCard | Deal list item | `/components/deals/` |
| KanbanColumn | Pipeline column | `/components/deals/` |
| StageStepper | Deal progression | `/components/deals/` |
| TaskRow | Task list item | `/components/tasks/` |
| TaskGroup | Task section | `/components/tasks/` |
| Calendar | Date picker | `/components/tasks/` |
| KPICard | Metric display | `/components/dashboard/` |
| ActivityItem | Activity feed | `/components/dashboard/` |

### Chart Components

| Component | Purpose |
|-----------|---------|
| SalesChart | Bar chart for trends |
| ProgressRing | Circular progress |
| PipelineFunnel | Pipeline visualization |

---

## Animation & Motion

### Duration Scale

```dart
class AppDurations {
  static const fast = Duration(milliseconds: 150);
  static const normal = Duration(milliseconds: 200);
  static const slow = Duration(milliseconds: 300);
  static const slower = Duration(milliseconds: 500);
}
```

### Easing Curves

```dart
class AppCurves {
  static const defaultCurve = Curves.easeInOut;
  static const enterCurve = Curves.easeOut;
  static const exitCurve = Curves.easeIn;
  static const bounceCurve = Curves.elasticOut;
}
```

### Common Animations

| Animation | Duration | Curve | Usage |
|-----------|----------|-------|-------|
| Fade in | 200ms | easeOut | Content appearance |
| Slide up | 300ms | easeOut | Modal/sheet entry |
| Scale | 150ms | easeInOut | Button press |
| Expand/collapse | 200ms | easeInOut | Accordion |
| Page transition | 300ms | easeInOut | Navigation |

### Animation Patterns

```dart
// Fade in
AnimatedOpacity(
  opacity: isVisible ? 1.0 : 0.0,
  duration: AppDurations.normal,
  curve: AppCurves.enterCurve,
  child: content,
)

// Slide up
SlideTransition(
  position: Tween<Offset>(
    begin: Offset(0, 0.2),
    end: Offset.zero,
  ).animate(animation),
  child: content,
)

// Scale on press
Transform.scale(
  scale: isPressed ? 0.98 : 1.0,
  child: button,
)
```

---

## Interaction Patterns

### Touch Feedback

| Interaction | Feedback |
|-------------|----------|
| Button tap | Scale 0.98, slight opacity change |
| Card tap | Ripple effect (Material) |
| List item tap | Highlight + ripple |
| Icon button tap | Circular ripple |

### Gestures

| Gesture | Action | Example |
|---------|--------|---------|
| Tap | Primary action | Open detail |
| Long press | Context menu | Quick actions |
| Swipe left | Destructive action | Delete task |
| Swipe right | Positive action | Complete task |
| Pull down | Refresh content | Reload data |
| Drag | Reorder/move | Kanban cards |

### Form Interactions

| State | Visual |
|-------|--------|
| Default | Gray border |
| Focused | Primary border, elevated |
| Filled | Gray border, floating label |
| Error | Red border, error message |
| Disabled | Muted colors, no interaction |

### Navigation Patterns

| Pattern | Usage |
|---------|-------|
| Push | Navigate to detail |
| Replace | Auth flow transitions |
| Bottom sheet | Quick actions, filters |
| Modal | Confirmations, forms |
| Tab switch | Same-level navigation |

---

## Data Models

### Core Entities

```dart
// Lead
class Lead {
  final String id;
  final String name;
  final String company;
  final String email;
  final String? phone;
  final LeadStatus status;
  final LeadSource source;
  final String assignedTo;
  final DateTime createdAt;
  final List<String> tags;
  final Priority priority;
  final String? avatar;
  final String? notes;
}

enum LeadStatus { newLead, contacted, qualified, lost }
enum LeadSource { website, referral, linkedin, coldCall, tradeShow }

// Deal
class Deal {
  final String id;
  final String title;
  final int value;
  final DealStage stage;
  final int probability;
  final DateTime closeDate;
  final String leadId;
  final String companyName;
  final List<String> products;
  final String assignedTo;
  final Priority priority;
  final List<String> labels;
}

enum DealStage {
  prospecting,
  qualified,
  proposal,
  negotiation,
  closedWon,
  closedLost,
}

// Task
class Task {
  final String id;
  final String title;
  final String? description;
  final DateTime dueDate;
  final bool completed;
  final RelatedEntity? relatedTo;
  final Priority priority;
  final String assignedTo;
}

enum Priority { low, medium, high }

// Activity
class Activity {
  final String id;
  final ActivityType type;
  final String title;
  final String? description;
  final DateTime timestamp;
  final RelatedEntity? relatedTo;
  final String userId;
}

enum ActivityType {
  call,
  email,
  note,
  meeting,
  stageChange,
  dealWon,
  dealLost,
  taskCompleted,
}

// User
class User {
  final String id;
  final String name;
  final String email;
  final String role;
  final String? avatar;
  final String? phone;
}

// Notification
class Notification {
  final String id;
  final String title;
  final String message;
  final DateTime timestamp;
  final bool read;
  final NotificationType type;
}
```

---

## Navigation Structure

### Route Hierarchy

```
/ (root redirect)
├── /splash
├── /login
├── /forgot-password
├── /onboarding
│
├── /dashboard
│
├── /leads
│   ├── /leads/create
│   └── /leads/[id]
│
├── /deals
│   ├── /deals/create
│   └── /deals/[id]
│
├── /tasks
│   ├── /tasks/create
│   └── /tasks/[id]
│
└── /more
    ├── /more/profile
    ├── /more/notifications
    └── /more/team
```

### Navigation Types

| Route Pattern | Navigation Type |
|---------------|-----------------|
| Splash → Login | Replace (no back) |
| Login → Dashboard | Replace (no back) |
| Tab navigation | Switch (preserve state) |
| List → Detail | Push (stack) |
| Detail → Edit | Push (stack) |
| FAB → Create | Push or Modal |
| Settings items | Push |
| Logout | Replace all |

### Bottom Navigation Mapping

| Index | Label | Route | Icon |
|-------|-------|-------|------|
| 0 | Dashboard | /dashboard | dashboard |
| 1 | Leads | /leads | people |
| 2 | Deals | /deals | work |
| 3 | Tasks | /tasks | check_box |
| 4 | More | /more | more_horiz |

---

## Screen Inventory

### Authentication Flow

| Screen | Route | Description |
|--------|-------|-------------|
| Splash | /splash | Brand animation, 2.5s auto-nav |
| Login | /login | Email/password + Google OAuth |
| Forgot Password | /forgot-password | Email reset flow |
| Onboarding | /onboarding | 3-slide feature intro |

### Main Application

| Screen | Route | Description |
|--------|-------|-------------|
| Dashboard | /dashboard | KPIs, charts, tasks, activity |
| Leads List | /leads | Searchable, filterable lead list |
| Lead Detail | /leads/[id] | Overview, timeline, notes tabs |
| Lead Create | /leads/create | New lead form |
| Deals List | /deals | Kanban + list views |
| Deal Detail | /deals/[id] | Stage stepper, products |
| Tasks List | /tasks | Calendar + list views |
| Task Detail | /tasks/[id] | Task details |
| More/Settings | /more | Profile, preferences, support |
| Profile | /more/profile | Edit user profile |
| Notifications | /more/notifications | Notification center |
| Team | /more/team | Team management |

---

## Implementation Checklist

### Phase 1: Foundation
- [ ] Set up Flutter project structure
- [ ] Configure theme (colors, typography)
- [ ] Create spacing/layout constants
- [ ] Set up navigation (go_router or Navigator 2.0)
- [ ] Create AppColors, AppTypography, AppLayout classes

### Phase 2: Core Components
- [ ] Button component (all variants)
- [ ] Input/TextField component
- [ ] Card component
- [ ] Avatar component
- [ ] Badge components
- [ ] IconButton component

### Phase 3: Layout Components
- [ ] AppBar component
- [ ] BottomNav component
- [ ] FAB component
- [ ] MobileShell wrapper

### Phase 4: Auth Screens
- [ ] Splash screen
- [ ] Login screen
- [ ] Forgot password screen
- [ ] Onboarding screen

### Phase 5: Main Screens
- [ ] Dashboard screen
- [ ] Leads list + detail + create
- [ ] Deals list (Kanban + List) + detail
- [ ] Tasks list (Calendar + List) + detail
- [ ] Settings/More screen

### Phase 6: Data & State
- [ ] Define data models
- [ ] Set up state management (Provider/Riverpod/Bloc)
- [ ] Create mock data
- [ ] Implement API services

### Phase 7: Polish
- [ ] Add animations
- [ ] Implement pull-to-refresh
- [ ] Add loading states
- [ ] Create empty states
- [ ] Add error handling
- [ ] Test on devices

---

## Resources

### Documentation Files

| Document | Description |
|----------|-------------|
| `docs/routes/01-splash.md` | Splash screen spec |
| `docs/routes/02-login.md` | Login screen spec |
| `docs/routes/03-forgot-password.md` | Forgot password spec |
| `docs/routes/04-onboarding.md` | Onboarding spec |
| `docs/routes/05-dashboard.md` | Dashboard spec |
| `docs/routes/06-leads-list.md` | Leads list spec |
| `docs/routes/07-lead-detail.md` | Lead detail spec |
| `docs/routes/08-lead-create.md` | Lead create spec |
| `docs/routes/09-deals-list.md` | Deals list spec |
| `docs/routes/10-deal-detail.md` | Deal detail spec |
| `docs/routes/11-tasks-list.md` | Tasks list spec |
| `docs/routes/12-more-settings.md` | Settings spec |
| `docs/components/ui-components.md` | Component specs |

### Recommended Flutter Packages

| Package | Purpose |
|---------|---------|
| `go_router` | Declarative routing |
| `flutter_riverpod` | State management |
| `lucide_icons` | Icon library |
| `fl_chart` | Charts |
| `table_calendar` | Calendar widget |
| `shimmer` | Loading skeletons |
| `cached_network_image` | Image caching |
| `url_launcher` | Tel/mailto links |
| `shared_preferences` | Local storage |

---

*This design system document was generated from the SvelteKit CRM prototype to guide Flutter implementation. Refer to individual route and component documentation for detailed specifications.*
