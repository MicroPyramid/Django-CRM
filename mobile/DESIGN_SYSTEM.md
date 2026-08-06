# BottleCRM Mobile Design System

A comprehensive design guide for the BottleCRM mobile app, inspired by modern CRM apps like HubSpot.

> **This is the authoritative design reference for the Flutter app.** Change a
> colour or a spacing value here. There is a second, similarly named file at
> [`docs/DESIGN-SYSTEM.md`](./docs/DESIGN-SYSTEM.md): that one is the original
> pre-build spec, kept for its data models and screen inventory. The two agree
> on the values they share; where they ever diverge, this file wins.
>
> A third file, `Django-CRM/DESIGN_SYSTEM.md` at the repo root, is the **web**
> design system. It describes CSS variables and does not apply here.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Color Palette](#color-palette)
3. [Typography](#typography)
4. [Spacing & Layout](#spacing--layout)
5. [Components](#components)
6. [Icons](#icons)
7. [Patterns](#patterns)
8. [Accessibility](#accessibility)

---

## Design Principles

### Core Values

1. **Clarity First** - Every element should have a clear purpose
2. **Scannable** - Users should quickly find what they need
3. **Minimal Friction** - Reduce taps to complete actions
4. **Consistent** - Same patterns across all screens
5. **Professional** - Clean, modern, business-appropriate

### Design Philosophy

- **Flat Design** - No heavy shadows, use borders for depth
- **White Space** - Generous spacing for readability
- **High Contrast** - Clear text hierarchy
- **Touch Friendly** - Minimum 44px touch targets

---

## Color Palette

### Primary Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Primary 600** | `#2563EB` | Primary actions, links, selected states |
| **Primary 500** | `#3B82F6` | Hover states, secondary emphasis |
| **Primary 100** | `#DBEAFE` | Light backgrounds, chips |
| **Primary 50** | `#EFF6FF` | Subtle backgrounds |

### Accent Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Accent** | `#F97316` | FAB, important CTAs, notifications |
| **Accent Light** | `#FED7AA` | Accent backgrounds, highlights |

### Semantic Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Success 500** | `#22C55E` | Won deals, completed tasks |
| **Success 100** | `#DCFCE7` | Success backgrounds |
| **Warning 500** | `#F59E0B` | Attention needed, medium priority |
| **Warning 100** | `#FEF3C7` | Warning backgrounds |
| **Danger 500** | `#EF4444` | Errors, overdue, lost deals |
| **Danger 100** | `#FEE2E2` | Error backgrounds |

### Neutral Colors

| Name | Hex | Usage |
|------|-----|-------|
| **Gray 900** | `#0F172A` | Primary text |
| **Gray 700** | `#374151` | Secondary text |
| **Gray 500** | `#6B7280` | Tertiary text, placeholders |
| **Gray 300** | `#D1D5DB` | Borders, dividers |
| **Gray 200** | `#E5E7EB` | Card borders, separators |
| **Gray 100** | `#F3F4F6` | Backgrounds, disabled states |
| **Gray 50** | `#F9FAFB` | Page background |
| **White** | `#FFFFFF` | Cards, surfaces |

### Status Colors for CRM

```
Lead Status:
- New        → Primary 500 (#3B82F6)
- Contacted  → Warning 500 (#F59E0B)
- Qualified  → Success 500 (#22C55E)
- Lost       → Danger 500 (#EF4444)

Deal Stages:
- Prospecting  → Gray 400 (#9CA3AF)
- Qualified    → Primary 500 (#3B82F6)
- Proposal     → Purple 500 (#A855F7)
- Negotiation  → Warning 500 (#F59E0B)
- Closed Won   → Success 500 (#22C55E)
- Closed Lost  → Danger 500 (#EF4444)

Priority:
- Low    → Gray 400 (#9CA3AF)
- Medium → Warning 500 (#F59E0B)
- High   → Danger 500 (#EF4444)
- Urgent → Purple 500 (#A855F7)
```

---

## Typography

### Font Family

**Primary Font:** Inter (Google Fonts)
- Designed for screens
- Excellent readability at small sizes
- 9 weights available
- Free and open source

**Fallback:** System fonts (SF Pro on iOS, Roboto on Android)

### Type Scale

| Style | Size | Weight | Line Height | Letter Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| **Display** | 28px | Bold (700) | 1.2 | -0.5px | KPIs, large numbers |
| **H1** | 22px | Semi-bold (600) | 1.3 | -0.3px | Page titles |
| **H2** | 18px | Semi-bold (600) | 1.4 | -0.2px | Section headers |
| **H3** | 16px | Semi-bold (600) | 1.4 | 0 | Card titles, list item titles |
| **Body Large** | 16px | Regular (400) | 1.5 | 0 | Important body text |
| **Body** | 15px | Regular (400) | 1.5 | 0 | Default body text |
| **Body Small** | 14px | Regular (400) | 1.4 | 0 | Secondary text |
| **Caption** | 12px | Regular (400) | 1.3 | 0 | Timestamps, helper text |
| **Overline** | 11px | Semi-bold (600) | 1.3 | 0.5px | Section labels (uppercase) |

### Number Typography

| Style | Size | Weight | Usage |
|-------|------|--------|-------|
| **Number Large** | 28px | Bold (700) | Dashboard KPIs |
| **Number Medium** | 20px | Semi-bold (600) | Card metrics |
| **Number Small** | 14px | Medium (500) | Inline numbers |

Use `FontFeature.tabularFigures()` for aligned numbers in tables/lists.

### Text Colors

| Type | Color | Hex |
|------|-------|-----|
| Primary | Gray 900 | `#0F172A` |
| Secondary | Gray 500 | `#6B7280` |
| Tertiary | Gray 400 | `#9CA3AF` |
| Disabled | Gray 400 @ 50% | `#9CA3AF80` |
| Link | Primary 600 | `#2563EB` |
| Error | Danger 500 | `#EF4444` |

---

## Spacing & Layout

### Spacing Scale (4px base)

| Token | Value | Usage |
|-------|-------|-------|
| `xs` | 4px | Tight gaps, icon padding |
| `sm` | 8px | Small gaps, list item spacing |
| `md` | 12px | Default component padding |
| `lg` | 16px | Section padding, card padding |
| `xl` | 20px | Large gaps |
| `xxl` | 24px | Section spacing |
| `xxxl` | 32px | Page sections |

### Page Layout

```
┌─────────────────────────────────────┐
│  Status Bar (system)                │
├─────────────────────────────────────┤
│  App Bar (52-56px)                  │
│  ← Title                    Actions │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │  Content Area               │   │
│  │  Padding: 16px horizontal   │   │
│  │                             │   │
│  │  Section Gap: 20-24px       │   │
│  │                             │   │
│  └─────────────────────────────┘   │
│                                     │
│                            ┌───┐   │
│                            │FAB│   │
│                            └───┘   │
├─────────────────────────────────────┤
│  Bottom Navigation (56-60px)        │
│  Home  Contacts  Deals  Tasks  More │
└─────────────────────────────────────┘
```

### Component Heights

| Component | Height |
|-----------|--------|
| App Bar | 52-56px |
| Bottom Nav | 56-60px |
| Button Large | 48px |
| Button Medium | 44px |
| Button Small | 36px |
| Input Field | 48px |
| List Item | 64-72px |
| Quick Action Button | 56px |
| FAB | 56px |
| Tab Bar | 48px |
| Search Bar | 44px |
| Filter Chip | 36px |

### Border Radius

| Size | Value | Usage |
|------|-------|-------|
| XS | 4px | Small elements, inputs |
| SM | 6px | Buttons, chips |
| MD | 8px | Cards, dialogs |
| LG | 12px | Large cards, modals |
| XL | 16px | Bottom sheets |
| Full | 9999px | Pills, avatars, FAB |

---

## Components

### Cards

```
┌─────────────────────────────────────┐
│  Card Title              Action ⋮  │  ← 16px padding
│  Subtitle or count                  │
├─────────────────────────────────────┤
│                                     │
│  Card Content                       │
│                                     │
└─────────────────────────────────────┘

Style:
- Background: White
- Border: 1px solid Gray 200
- Border Radius: 8px
- Shadow: NONE (flat design)
- Padding: 16px
```

### List Items

```
┌─────────────────────────────────────┐
│ ○  Title Text                   ⋮  │
│    Subtitle or description          │
│    📅 Date/time        [Badge]      │
└─────────────────────────────────────┘

Style:
- Height: 64-72px
- Padding: 16px horizontal, 12px vertical
- Border Bottom: 1px solid Gray 200
- Icon/Avatar: 40px, left aligned
- Action: Right aligned
```

### Buttons

**Primary Button (Filled)**
```
Background: Primary 600
Text: White, 15px Semi-bold
Height: 48px
Border Radius: 8px
Padding: 16px horizontal
```

**Secondary Button (Outlined)**
```
Background: Transparent
Border: 1px solid Gray 300
Text: Gray 900, 15px Semi-bold
Height: 48px
Border Radius: 8px
```

**Text Button**
```
Background: Transparent
Text: Primary 600, 15px Semi-bold
Height: 44px
Padding: 8px horizontal
```

**FAB (Floating Action Button)**
```
Background: Accent (#F97316)
Icon: White, 24px
Size: 56px
Border Radius: 16px (or full)
Shadow: Subtle elevation
Position: Bottom-right, 16px from edges
```

### Quick Action Buttons

```
┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐
│   🏠    │ │   📊    │ │   👥    │ │   📞    │
│  Feed   │ │Dashboard│ │  Leads  │ │  Calls  │
└─────────┘ └─────────┘ └─────────┘ └─────────┘

Style:
- Size: 72px width, 56px height
- Background: White
- Border: 1px solid Gray 200
- Border Radius: 8px
- Icon: 24px, Gray 700
- Label: 11px, Gray 500
- Gap between: 12px
- Horizontal scroll if overflow
```

### Chips & Badges

**Filter Chip**
```
Height: 36px
Padding: 12px horizontal
Border: 1px solid Primary 600
Border Radius: 18px (full)
Text: Primary 600, 13px Medium
Background: Transparent (or Primary 50 when selected)
```

**Status Badge**
```
Height: 22px
Padding: 8px horizontal
Border Radius: 11px (full)
Text: 11px Semi-bold, White
Background: Status color
```

**Contact Chip**
```
Height: 32px
Padding: 12px horizontal
Border Radius: 16px
Background: Primary 100
Text: Primary 700, 13px Medium
```

### Bottom Navigation

```
┌─────────────────────────────────────┐
│  🏠      👤      💼      ✓      🔍  │
│ Home  Contacts  Deals  Tasks Search │
└─────────────────────────────────────┘

Style:
- Height: 56-60px
- Background: White
- Border Top: 1px solid Gray 200
- Icon: 24px
- Label: 11px
- Active: Primary 600
- Inactive: Gray 400
- 5 items maximum
```

### Input Fields

```
┌─────────────────────────────────────┐
│ Label                               │
├─────────────────────────────────────┤
│ Placeholder text...                 │
└─────────────────────────────────────┘

Style:
- Height: 48px
- Background: White
- Border: 1px solid Gray 300
- Border Radius: 8px
- Padding: 16px horizontal
- Label: 13px Medium, Gray 700
- Input Text: 15px Regular, Gray 900
- Placeholder: 15px Regular, Gray 400
- Focus Border: Primary 600
- Error Border: Danger 500
```

### Section Header

```
Guided actions                   View all →
Subtitle text here

Style:
- Title: 16px Semi-bold, Gray 900
- Subtitle: 13px Regular, Gray 500
- Link: 14px Medium, Primary 600
- Margin Bottom: 12px
```

---

## Icons

### Icon Sizes

| Size | Pixels | Usage |
|------|--------|-------|
| XS | 16px | Inline, badges |
| SM | 20px | List items, buttons |
| MD | 24px | Default, nav items |
| LG | 28px | Emphasis |
| XL | 32px | Empty states |
| XXL | 48px | Illustrations |

### Icon Style

- **Library:** Lucide Icons (consistent with web app)
- **Stroke Width:** 1.5-2px
- **Style:** Outlined (not filled)
- **Color:** Inherit from text or specific semantic color

### Common Icons

```
Navigation:
- Home: home
- Contacts: users
- Deals: briefcase
- Tasks: check-square
- Search: search
- Settings: settings
- More: more-horizontal

Actions:
- Add: plus
- Edit: pencil
- Delete: trash-2
- Share: share
- Filter: filter
- Sort: arrow-up-down
- Refresh: refresh-cw

Communication:
- Email: mail
- Call: phone
- Meeting: calendar
- Note: file-text

Status:
- Success: check-circle
- Warning: alert-triangle
- Error: x-circle
- Info: info
```

---

## Patterns

### Dashboard Layout

```
┌─────────────────────────────────────┐
│ Page Title                          │
├─────────────────────────────────────┤
│ [Quick Actions Row - Horizontal]    │
├─────────────────────────────────────┤
│ Section Header              View all│
│ ┌─────────────────────────────────┐ │
│ │ Metric Card / Chart             │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ Section Header              View all│
│ ┌─────────────────────────────────┐ │
│ │ List Item 1                     │ │
│ ├─────────────────────────────────┤ │
│ │ List Item 2                     │ │
│ ├─────────────────────────────────┤ │
│ │ List Item 3                     │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

### List View Layout

```
┌─────────────────────────────────────┐
│ ← Page Title              🔍  ⋮    │
├─────────────────────────────────────┤
│ [Filter Chips - Horizontal Scroll]  │
├─────────────────────────────────────┤
│ ┌─────────────────────────────────┐ │
│ │ List Item with Avatar           │ │
│ │ Title                     →     │ │
│ │ Subtitle          Status Badge  │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ List Item                       │ │
│ └─────────────────────────────────┘ │
│                             [+ FAB] │
└─────────────────────────────────────┘
```

### Detail View Layout

```
┌─────────────────────────────────────┐
│ ← Back        Title        Edit  ⋮  │
├─────────────────────────────────────┤
│                                     │
│        [Avatar / Icon - 64px]       │
│           Primary Name              │
│           Secondary Info            │
│                                     │
│ ┌─────────────────────────────────┐ │
│ │ [Action Buttons Row]            │ │
│ │  📧 Email  📞 Call  📝 Note     │ │
│ └─────────────────────────────────┘ │
├─────────────────────────────────────┤
│ [Tab Bar: Details | Activity | ... ]│
├─────────────────────────────────────┤
│                                     │
│ Field Label                         │
│ Field Value                         │
│ ─────────────────────────────────── │
│ Field Label                         │
│ Field Value                         │
│                                     │
└─────────────────────────────────────┘
```

### Form Layout

```
┌─────────────────────────────────────┐
│ ← Cancel      Title          Save   │
├─────────────────────────────────────┤
│                                     │
│ Section Label                       │
│ ┌─────────────────────────────────┐ │
│ │ Input Field                     │ │
│ └─────────────────────────────────┘ │
│ ┌─────────────────────────────────┐ │
│ │ Input Field                     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ Section Label                       │
│ ┌─────────────────────────────────┐ │
│ │ Dropdown / Picker               │ │
│ └─────────────────────────────────┘ │
│                                     │
└─────────────────────────────────────┘

Spacing:
- Section gap: 24px
- Field gap: 16px
- Label to field: 8px
```

### Empty State

```
┌─────────────────────────────────────┐
│                                     │
│                                     │
│            [Icon - 48px]            │
│                                     │
│          No items yet               │
│    Description text goes here       │
│    explaining what to do next       │
│                                     │
│         [ Primary Action ]          │
│                                     │
│                                     │
└─────────────────────────────────────┘

Style:
- Icon: Gray 300, 48px
- Title: 18px Semi-bold, Gray 700
- Description: 14px Regular, Gray 500, centered
- Max width: 280px
```

### Loading States

**Skeleton Loading**
```
Use animated placeholder shapes matching content layout:
- Rectangles for text (with rounded corners)
- Circles for avatars
- Animation: Shimmer effect (light gray pulse)
```

**Inline Loading**
```
- Small spinner (20px) next to action
- Or three-dot animation
```

**Full Screen Loading**
```
- Centered spinner (40px)
- Optional: Brand logo animation
```

---

## Accessibility

### Minimum Requirements

1. **Touch Targets:** Minimum 44x44px for all interactive elements
2. **Color Contrast:** 4.5:1 ratio for normal text, 3:1 for large text
3. **Focus Indicators:** Visible focus states for keyboard navigation
4. **Screen Readers:** Proper semantic labels and hints

### Color Contrast Ratios

| Combination | Ratio | Status |
|-------------|-------|--------|
| Gray 900 on White | 15.5:1 | ✅ AAA |
| Gray 500 on White | 4.6:1 | ✅ AA |
| Primary 600 on White | 4.5:1 | ✅ AA |
| White on Primary 600 | 4.5:1 | ✅ AA |
| White on Accent | 3.1:1 | ⚠️ AA Large |

### Text Scaling

- Support system text scaling up to 200%
- Use flexible layouts that accommodate larger text
- Test with accessibility settings enabled

---

## Implementation Notes

### Flutter Specifics

```dart
// Theme setup
ThemeData(
  useMaterial3: true,
  colorScheme: ColorScheme.light(
    primary: Color(0xFF2563EB),
    secondary: Color(0xFFF97316),
    surface: Colors.white,
    background: Color(0xFFF9FAFB),
    error: Color(0xFFEF4444),
  ),
  textTheme: GoogleFonts.interTextTheme(),
)

// No elevation/shadows on cards
Card(
  elevation: 0,
  shape: RoundedRectangleBorder(
    borderRadius: BorderRadius.circular(8),
    side: BorderSide(color: Color(0xFFE5E7EB)),
  ),
)
```

### Do's and Don'ts

**Do:**
- Use consistent spacing from the scale
- Keep cards flat with borders
- Use semantic colors for status
- Maintain touch target sizes
- Test on multiple screen sizes

**Don't:**
- Use shadows on cards (flat design)
- Mix different border radius sizes
- Use colors outside the palette
- Create touch targets smaller than 44px
- Hardcode pixel values (use tokens)

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Jan 2026 | Initial design system based on HubSpot mobile app analysis |

---

*This design system is a living document. Update as the app evolves.*
