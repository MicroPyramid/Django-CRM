# SalesPro CRM - Flutter Implementation Documentation

This documentation provides comprehensive specifications for implementing the SalesPro CRM mobile application in Flutter. The specifications are derived from a fully functional SvelteKit prototype.

---

## Quick Start

1. **Read the Design System** - Start with [DESIGN-SYSTEM.md](./DESIGN-SYSTEM.md) for colors, typography, spacing, and overall architecture
2. **Review Components** - Check [components/ui-components.md](./components/ui-components.md) for reusable widget specifications
3. **Implement Screens** - Follow the route documentation in sequential order

---

## Documentation Index

### Core Documents

| Document | Description |
|----------|-------------|
| [DESIGN-SYSTEM.md](./DESIGN-SYSTEM.md) | **Start here** - Complete design system with colors, typography, spacing, data models, and implementation checklist |
| [components/ui-components.md](./components/ui-components.md) | Detailed specifications for all reusable UI components |

### Authentication Screens

| Document | Route | Description |
|----------|-------|-------------|
| [01-splash.md](./routes/01-splash.md) | `/splash` | Animated splash screen with brand identity |
| [02-login.md](./routes/02-login.md) | `/login` | Email/password login with Google OAuth |
| [03-forgot-password.md](./routes/03-forgot-password.md) | `/forgot-password` | Password reset flow |
| [04-onboarding.md](./routes/04-onboarding.md) | `/onboarding` | Feature introduction carousel |

### Main Application Screens

| Document | Route | Description |
|----------|-------|-------------|
| [05-dashboard.md](./routes/05-dashboard.md) | `/dashboard` | KPI cards, charts, pipeline, tasks, activity feed |
| [06-leads-list.md](./routes/06-leads-list.md) | `/leads` | Searchable, filterable leads list |
| [07-lead-detail.md](./routes/07-lead-detail.md) | `/leads/[id]` | Lead detail with tabs (Overview, Timeline, Notes) |
| [08-lead-create.md](./routes/08-lead-create.md) | `/leads/create` | New lead creation form |
| [09-deals-list.md](./routes/09-deals-list.md) | `/deals` | Kanban board + list view |
| [10-deal-detail.md](./routes/10-deal-detail.md) | `/deals/[id]` | Deal detail with stage stepper |
| [11-tasks-list.md](./routes/11-tasks-list.md) | `/tasks` | Calendar + grouped list view |
| [12-more-settings.md](./routes/12-more-settings.md) | `/more` | Settings, profile, team management |

---

## App Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    AUTH FLOW                         │
│  Splash → Login ←→ Forgot Password                  │
│              ↓                                       │
│         Onboarding → Dashboard                       │
└─────────────────────────────────────────────────────┘
                         │
┌─────────────────────────────────────────────────────┐
│              MAIN APPLICATION                        │
│                                                      │
│  ┌─────────┬─────────┬─────────┬─────────┬───────┐ │
│  │Dashboard│  Leads  │  Deals  │  Tasks  │  More │ │
│  └────┬────┴────┬────┴────┬────┴────┬────┴───┬───┘ │
│       │         │         │         │        │      │
│       │    ┌────┴────┐    │    ┌────┴────┐   │     │
│       │    │  List   │    │    │Calendar │   │     │
│       │    │  Detail │    │    │  List   │   │     │
│       │    │  Create │    │    │  Detail │   │     │
│       │    └─────────┘    │    └─────────┘   │     │
│       │                   │                  │      │
│       │         ┌─────────┴──────┐          │      │
│       │         │  Kanban/List   │          │      │
│       │         │    Detail      │          │      │
│       │         └────────────────┘          │      │
│       │                                     │      │
│  ┌────┴────────────────────────────────────┴────┐ │
│  │              Floating Action Button          │ │
│  │         (Add Lead / Deal / Task)             │ │
│  └──────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## Key Features by Screen

### Dashboard
- 4 KPI cards (horizontal scroll)
- Sales trend bar chart
- Task completion ring
- Pipeline funnel
- Deals closing this week
- Today's tasks
- Recent activity feed
- Expandable FAB

### Leads
- Search by name/company/email
- Filter by status and source
- Sort by date, name, priority
- Lead cards with avatar, badges, tags
- Detail view with 3 tabs
- Quick actions (call, email, message)
- Activity timeline

### Deals
- **Kanban View**: Draggable cards across pipeline stages
- **List View**: Grouped by stage
- Deal cards with value, probability, close date
- Stage stepper for progression
- Visual probability bar
- Related products section

### Tasks
- **Calendar View**: Month calendar with task dots
- **List View**: Grouped (Overdue, Today, Upcoming)
- Checkbox completion toggle
- Swipe-to-delete
- Priority and due time indicators
- Related entity badges

### Settings
- Profile section with avatar
- Account settings
- Team management
- Dark mode toggle
- Support links
- Sign out

---

## Recommended Implementation Order

### Week 1: Foundation
1. Project setup with Flutter
2. Theme configuration (colors, typography)
3. Core UI components (Button, Input, Card, Avatar)
4. Navigation setup

### Week 2: Auth Flow
1. Splash screen
2. Login screen with validation
3. Forgot password screen
4. Onboarding carousel

### Week 3: Main Navigation
1. Bottom navigation shell
2. Dashboard with KPIs
3. FAB component

### Week 4: Leads Module
1. Leads list with search/filter
2. Lead detail with tabs
3. Lead create form

### Week 5: Deals Module
1. Deals Kanban view
2. Deals list view
3. Deal detail with stepper

### Week 6: Tasks & Settings
1. Tasks calendar view
2. Tasks list view
3. Settings/More screen

### Week 7: Polish
1. Animations and transitions
2. Loading states
3. Error handling
4. Testing

---

## Data Models Summary

### Lead
- id, name, company, email, phone
- status (new, contacted, qualified, lost)
- source (website, referral, linkedin, cold-call, trade-show)
- priority (low, medium, high)
- tags, notes, assignedTo, createdAt

### Deal
- id, title, value, stage, probability
- closeDate, leadId, companyName
- products, labels, priority, assignedTo

### Task
- id, title, description, dueDate
- completed, relatedTo, priority, assignedTo

### User
- id, name, email, role, avatar, phone

### Activity
- id, type, title, description, timestamp
- relatedTo, userId

---

## Color Quick Reference

| Color | Hex | Usage |
|-------|-----|-------|
| Primary | #2563EB | Buttons, active states |
| Success | #22C55E | Positive indicators |
| Warning | #F59E0B | Attention states |
| Danger | #EF4444 | Errors, destructive |
| Text Primary | #0F172A | Main text |
| Text Secondary | #6B7280 | Supporting text |
| Background | #F8FAFC | Page backgrounds |
| Surface | #FFFFFF | Cards, modals |

---

## Questions?

Each route document contains:
- Complete UI element specifications
- Color and spacing values
- State management patterns
- Flutter implementation code snippets
- Interaction details
- Accessibility considerations

Refer to individual documents for detailed implementation guidance.
