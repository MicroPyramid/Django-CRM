# Design Specification Document
## SalesPro CRM Web Application

**Version:** 1.0
**Date:** November 2025
**Design Style:** Notion-inspired, Minimal/Clean
**Target Platform:** Desktop-first with responsive support

---

## Table of Contents

1. [Design Philosophy](#1-design-philosophy)
2. [Layout Architecture](#2-layout-architecture)
3. [Color System](#3-color-system)
4. [Typography](#4-typography)
5. [Spacing & Grid](#5-spacing--grid)
6. [Core Components](#6-core-components)
7. [Navigation & Sidebar](#7-navigation--sidebar)
8. [Side Drawer Panels](#8-side-drawer-panels)
9. [Screen Specifications](#9-screen-specifications)
10. [Interaction Patterns](#10-interaction-patterns)
11. [Animation Guidelines](#11-animation-guidelines)
12. [Responsive Breakpoints](#12-responsive-breakpoints)

---

## 1. Design Philosophy

### 1.1 Core Principles

| Principle | Description |
|-----------|-------------|
| **Content-first** | UI fades into the background; content takes center stage |
| **Contextual details** | Details appear in side drawers without losing list context |
| **Progressive disclosure** | Show essentials first, reveal more on demand |
| **Quiet confidence** | Subtle visual hierarchy, minimal ornamentation |
| **Spatial consistency** | Predictable layouts across all modules |

### 1.2 Design Inspirations

- **Notion**: Collapsible sidebar, clean typography, peek drawers
- **Linear**: Dense but readable data, keyboard-first navigation
- **Figma**: Subtle borders, layered panels, hover states
- **Apple Notes**: Whitespace usage, soft shadows

### 1.3 Key Differentiators from Mobile Mockup

| Aspect | Mobile App | Web App |
|--------|-----------|---------|
| Navigation | Bottom tab bar | Collapsible left sidebar |
| Details | Full-screen navigation | Side drawer overlay (peek) |
| Forms | Full-screen modal | Side drawer panel |
| Data density | Single column cards | Multi-column tables/grids |
| Actions | FAB button | Inline buttons + keyboard shortcuts |

---

## 2. Layout Architecture

### 2.1 Master Layout Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ┌─────────┐ ┌─────────────────────────────────────┐ ┌─────────────────┐ │
│ │         │ │                                     │ │                 │ │
│ │         │ │                                     │ │   Side Drawer   │ │
│ │ Sidebar │ │         Main Content Area           │ │   (Optional)    │ │
│ │  (240px │ │                                     │ │   (420-480px)   │ │
│ │   or    │ │                                     │ │                 │ │
│ │  64px)  │ │                                     │ │   Overlay on    │ │
│ │         │ │                                     │ │   main content  │ │
│ │         │ │                                     │ │                 │ │
│ └─────────┘ └─────────────────────────────────────┘ └─────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Layout Dimensions

| Element | Expanded | Collapsed | Notes |
|---------|----------|-----------|-------|
| Sidebar | 240px | 64px | Icon-only when collapsed |
| Main content | Fluid | Fluid | `calc(100vw - sidebar)` |
| Side drawer | 420-480px | 0px | Overlays main content |
| Top header | 56px | 56px | Within main content area |
| Content padding | 24px | 24px | Inner content spacing |

### 2.3 Z-Index Layers

| Layer | Z-Index | Elements |
|-------|---------|----------|
| Base | 0 | Main content |
| Sidebar | 10 | Navigation sidebar |
| Drawer backdrop | 40 | Semi-transparent overlay |
| Side drawer | 50 | Detail/form panels |
| Dropdowns | 60 | Select menus, popovers |
| Modals | 70 | Confirmation dialogs |
| Toasts | 80 | Notifications |
| Tooltips | 90 | Hover hints |

---

## 3. Color System

### 3.1 Base Palette (Light Mode)

```css
/* Background Layers */
--bg-base: #ffffff;           /* Main background */
--bg-subtle: #fafafa;         /* Sidebar, cards */
--bg-muted: #f5f5f5;          /* Hover states, inputs */
--bg-emphasis: #ededed;       /* Active states */

/* Border Colors */
--border-default: #e5e5e5;    /* Dividers, card borders */
--border-strong: #d4d4d4;     /* Input borders, focus */
--border-subtle: #f0f0f0;     /* Subtle separators */

/* Text Colors */
--text-primary: #171717;      /* Headings, primary text */
--text-secondary: #525252;    /* Body text, descriptions */
--text-tertiary: #a3a3a3;     /* Placeholders, hints */
--text-inverse: #ffffff;      /* On dark backgrounds */

/* Accent Colors (Muted) */
--accent-primary: #2563eb;    /* Primary actions, links */
--accent-primary-hover: #1d4ed8;
--accent-primary-subtle: #eff6ff;  /* Primary backgrounds */

/* Status Colors (Soft) */
--status-success: #16a34a;
--status-success-bg: #f0fdf4;
--status-warning: #ca8a04;
--status-warning-bg: #fefce8;
--status-danger: #dc2626;
--status-danger-bg: #fef2f2;
--status-info: #0284c7;
--status-info-bg: #f0f9ff;

/* Stage Colors (Pipeline) */
--stage-prospecting: #6b7280;
--stage-qualified: #2563eb;
--stage-proposal: #7c3aed;
--stage-negotiation: #ea580c;
--stage-won: #16a34a;
--stage-lost: #dc2626;
```

### 3.2 Dark Mode Palette

```css
/* Background Layers */
--bg-base: #191919;
--bg-subtle: #212121;
--bg-muted: #2a2a2a;
--bg-emphasis: #333333;

/* Border Colors */
--border-default: #333333;
--border-strong: #404040;
--border-subtle: #262626;

/* Text Colors */
--text-primary: #fafafa;
--text-secondary: #a3a3a3;
--text-tertiary: #737373;
```

### 3.3 Semantic Color Usage

| Element | Light Mode | Usage |
|---------|------------|-------|
| Page background | `--bg-base` | Main content area |
| Sidebar background | `--bg-subtle` | Left navigation |
| Card background | `--bg-base` | Content cards |
| Card border | `--border-default` | 1px solid |
| Row hover | `--bg-muted` | Table/list hover |
| Selected row | `--accent-primary-subtle` | Active item |
| Input background | `--bg-base` | Form inputs |
| Input border | `--border-strong` | 1px solid |
| Drawer backdrop | `rgba(0,0,0,0.4)` | Overlay |

---

## 4. Typography

### 4.1 Font Stack

```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', monospace;
```

### 4.2 Type Scale

| Name | Size | Weight | Line Height | Usage |
|------|------|--------|-------------|-------|
| `display` | 28px | 600 | 1.2 | Page titles |
| `heading-lg` | 20px | 600 | 1.3 | Section headers |
| `heading-md` | 16px | 600 | 1.4 | Card titles |
| `heading-sm` | 14px | 600 | 1.4 | Subsection headers |
| `body` | 14px | 400 | 1.5 | Default text |
| `body-sm` | 13px | 400 | 1.5 | Secondary text |
| `caption` | 12px | 400 | 1.4 | Labels, timestamps |
| `overline` | 11px | 500 | 1.3 | All-caps labels |

### 4.3 Typography Tokens

```css
/* Headings */
--text-display: 600 28px/1.2 var(--font-sans);
--text-heading-lg: 600 20px/1.3 var(--font-sans);
--text-heading-md: 600 16px/1.4 var(--font-sans);
--text-heading-sm: 600 14px/1.4 var(--font-sans);

/* Body */
--text-body: 400 14px/1.5 var(--font-sans);
--text-body-sm: 400 13px/1.5 var(--font-sans);
--text-caption: 400 12px/1.4 var(--font-sans);
--text-overline: 500 11px/1.3 var(--font-sans);
```

---

## 5. Spacing & Grid

### 5.1 Spacing Scale (4px base)

| Token | Value | Usage |
|-------|-------|-------|
| `--space-0` | 0px | None |
| `--space-1` | 4px | Tight gaps |
| `--space-2` | 8px | Icon gaps, inline spacing |
| `--space-3` | 12px | List item padding |
| `--space-4` | 16px | Card padding, section gaps |
| `--space-5` | 20px | Medium sections |
| `--space-6` | 24px | Page padding |
| `--space-8` | 32px | Large sections |
| `--space-10` | 40px | Page section gaps |
| `--space-12` | 48px | Major section dividers |

### 5.2 Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-sm` | 4px | Badges, small pills |
| `--radius-md` | 6px | Buttons, inputs |
| `--radius-lg` | 8px | Cards, panels |
| `--radius-xl` | 12px | Modals, drawers |
| `--radius-full` | 9999px | Avatars, circular buttons |

### 5.3 Content Grid

```css
/* Main content area max-width */
--content-max-width: 1200px;

/* Card grid for dashboard */
.grid-auto {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--space-4);
}

/* Table layout */
.table-layout {
  display: grid;
  grid-template-columns: 1fr 200px 120px 100px 48px;
  align-items: center;
}
```

---

## 6. Core Components

### 6.1 Button

**Variants:**

| Variant | Background | Border | Text | Usage |
|---------|------------|--------|------|-------|
| Primary | `--accent-primary` | none | white | Main CTAs |
| Secondary | `--bg-base` | `--border-strong` | `--text-primary` | Secondary actions |
| Ghost | transparent | none | `--text-secondary` | Tertiary actions |
| Danger | `--status-danger` | none | white | Destructive actions |

**Sizes:**

| Size | Height | Padding | Font |
|------|--------|---------|------|
| sm | 28px | 8px 12px | 12px |
| md | 36px | 8px 16px | 14px |
| lg | 44px | 12px 24px | 14px |

**States:**
- Default → Hover (darken 8%) → Active (darken 12%) → Disabled (opacity 0.5)

```
┌─────────────────┐
│   + New Lead    │  Primary button
└─────────────────┘
     ↓ hover
┌─────────────────┐
│   + New Lead    │  Slight darken
└─────────────────┘
```

### 6.2 Input Field

**Structure:**
```
┌──────────────────────────────────────┐
│ Label                                │
├──────────────────────────────────────┤
│ ┌──────────────────────────────────┐ │
│ │ Placeholder or value...          │ │
│ └──────────────────────────────────┘ │
│ Helper text or error message         │
└──────────────────────────────────────┘
```

**Specifications:**

| Property | Value |
|----------|-------|
| Height | 40px |
| Padding | 12px horizontal |
| Border | 1px solid `--border-strong` |
| Border radius | `--radius-md` |
| Background | `--bg-base` |
| Focus ring | 2px solid `--accent-primary` (with 2px offset) |
| Label | `--text-caption`, `--text-secondary`, mb 4px |
| Error state | Red border, red helper text |

### 6.3 Card

**Structure:**
```
┌────────────────────────────────────────┐
│ Card Header (optional)         Action │ ← 16px padding
├────────────────────────────────────────┤
│                                        │
│ Card Content                           │ ← 16px padding
│                                        │
├────────────────────────────────────────┤
│ Card Footer (optional)                 │ ← 12px padding
└────────────────────────────────────────┘
```

**Variants:**

| Variant | Border | Shadow | Background |
|---------|--------|--------|------------|
| Default | 1px `--border-default` | none | `--bg-base` |
| Elevated | none | `0 1px 3px rgba(0,0,0,0.08)` | `--bg-base` |
| Muted | 1px `--border-subtle` | none | `--bg-subtle` |

### 6.4 Badge / Status Pill

**Lead Status:**
```
┌─────────┐  ┌───────────┐  ┌───────────┐  ┌──────┐
│   New   │  │ Contacted │  │ Qualified │  │ Lost │
└─────────┘  └───────────┘  └───────────┘  └──────┘
  Blue bg      Yellow bg      Green bg      Red bg
```

**Specifications:**

| Property | Value |
|----------|-------|
| Height | 22px |
| Padding | 4px 8px |
| Border radius | `--radius-sm` |
| Font | 12px, 500 weight |
| Background | Status color with 10% opacity |
| Text | Status color at 100% |

### 6.5 Avatar

**Sizes:**

| Size | Dimensions | Font | Usage |
|------|------------|------|-------|
| xs | 24px | 10px | Inline mentions |
| sm | 32px | 12px | List items |
| md | 40px | 14px | Headers, cards |
| lg | 56px | 18px | Profile sections |
| xl | 80px | 24px | Profile page |

**Fallback:** Show initials on colored background (generated from name hash)

### 6.6 Table / List Row

**Structure:**
```
┌────────────────────────────────────────────────────────────────────┐
│ □  │ Avatar │ Primary Text      │ Status │ Value  │ Date   │ ···  │
│    │        │ Secondary text    │        │        │        │      │
└────────────────────────────────────────────────────────────────────┘
  ↑      ↑           ↑                ↑         ↑        ↑       ↑
 Check  40px     flex-grow          Badge    Number   Caption  Menu
```

**Specifications:**

| Property | Value |
|----------|-------|
| Row height | 56-64px |
| Padding | 12px 16px |
| Border bottom | 1px solid `--border-subtle` |
| Hover | `--bg-muted` background |
| Selected | `--accent-primary-subtle` background |
| Clickable | `cursor: pointer` |

### 6.7 Dropdown / Select

**Trigger:**
```
┌────────────────────────────────┐
│ Selected Option              ▼ │
└────────────────────────────────┘
```

**Menu:**
```
┌────────────────────────────────┐
│ Option 1                       │ ← Hover: --bg-muted
├────────────────────────────────┤
│ Option 2 ✓                     │ ← Selected: checkmark
├────────────────────────────────┤
│ Option 3                       │
└────────────────────────────────┘
```

**Specifications:**
- Trigger height: 36px
- Menu max-height: 280px (scrollable)
- Menu shadow: `0 4px 12px rgba(0,0,0,0.15)`
- Option padding: 8px 12px
- Selected indicator: Checkmark icon on right

---

## 7. Navigation & Sidebar

### 7.1 Sidebar Structure

**Expanded (240px):**
```
┌─────────────────────────────┐
│  ≡  SalesPro               │ ← Logo + collapse toggle
├─────────────────────────────┤
│                             │
│  🏠 Dashboard               │ ← Active item
│  👥 Leads                   │
│  💼 Deals                   │
│  ✓  Tasks                   │
│                             │
├─────────────────────────────┤
│  ⚙  Settings               │
│  👤 Alex Johnson           │ ← User menu
└─────────────────────────────┘
```

**Collapsed (64px):**
```
┌────────┐
│   ≡    │
├────────┤
│   🏠   │ ← Tooltip on hover
│   👥   │
│   💼   │
│   ✓    │
├────────┤
│   ⚙    │
│   AJ   │
└────────┘
```

### 7.2 Sidebar Item Specifications

| State | Background | Text | Icon |
|-------|------------|------|------|
| Default | transparent | `--text-secondary` | `--text-tertiary` |
| Hover | `--bg-muted` | `--text-primary` | `--text-secondary` |
| Active | `--bg-emphasis` | `--text-primary` | `--accent-primary` |

**Item dimensions:**
- Height: 40px
- Padding: 8px 12px
- Icon size: 20px
- Gap between icon and text: 12px
- Border radius: `--radius-md`

### 7.3 Top Header (Within Main Content)

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  Leads                              🔍  🔔²  AJ                    │
│  6 total                                                          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
   ↑                                   ↑   ↑    ↑
 Page title                        Search Bell Avatar
 + subtitle                              badge
```

**Specifications:**
- Height: 56px
- Padding: 0 24px
- Title: `--text-heading-lg`
- Subtitle: `--text-caption`, `--text-tertiary`
- Right actions: 8px gap between items

---

## 8. Side Drawer Panels

### 8.1 Drawer Behavior

| Aspect | Specification |
|--------|---------------|
| Width | 420-480px (fixed) |
| Position | Right edge of viewport |
| Entry | Slide in from right (300ms ease-out) |
| Exit | Slide out to right (200ms ease-in) |
| Backdrop | `rgba(0,0,0,0.4)`, click to close |
| Close button | X icon in header, top-right |
| Keyboard | ESC to close |

### 8.2 Drawer Layout

```
┌───────────────────────────────────────────┐
│ ← Back   Lead Details               ✕     │ ← Header (56px)
├───────────────────────────────────────────┤
│                                           │
│  ┌─────────────────────────────────────┐  │
│  │  Sarah Mitchell                  ✏️  │  │ ← Primary info
│  │  TechCorp Solutions                  │  │
│  │  sarah@techcorp.com · +1 555-0123   │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ┌─ Status ────────────────────────────┐  │
│  │  ● New        ▼                     │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ┌─ Details ───────────────────────────┐  │ ← Scrollable
│  │  Source      Website                │  │    content
│  │  Priority    High ●                 │  │
│  │  Owner       Alex Johnson           │  │
│  │  Created     Nov 15, 2025           │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ┌─ Tags ──────────────────────────────┐  │
│  │  enterprise   hot-lead    +         │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ┌─ Timeline ──────────────────────────┐  │
│  │  📞 Call · Nov 20                   │  │
│  │  Discussed pricing options          │  │
│  │  ────────────────────────────────   │  │
│  │  ✉️ Email · Nov 18                  │  │
│  │  Sent product brochure              │  │
│  └─────────────────────────────────────┘  │
│                                           │
├───────────────────────────────────────────┤
│        Convert to Deal        Delete      │ ← Footer actions
└───────────────────────────────────────────┘
```

### 8.3 Drawer Header

| Property | Value |
|----------|-------|
| Height | 56px |
| Padding | 0 16px |
| Border bottom | 1px solid `--border-default` |
| Back button | Ghost button with arrow icon |
| Title | `--text-heading-md` |
| Close button | 32px icon button, top-right |

### 8.4 Drawer Content

| Property | Value |
|----------|-------|
| Padding | 24px |
| Overflow | scroll-y |
| Max height | `calc(100vh - 56px - 64px)` |
| Section gap | 24px |
| Section title | `--text-overline`, `--text-tertiary`, uppercase |

### 8.5 Drawer Footer

| Property | Value |
|----------|-------|
| Height | 64px |
| Padding | 12px 16px |
| Border top | 1px solid `--border-default` |
| Background | `--bg-subtle` |
| Button alignment | Right-aligned, 8px gap |

### 8.6 Form Drawer Variant

For create/edit forms:

```
┌───────────────────────────────────────────┐
│ ← Cancel    New Lead               Save   │ ← Actions in header
├───────────────────────────────────────────┤
│                                           │
│  Name *                                   │
│  ┌─────────────────────────────────────┐  │
│  │ Contact name                        │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  Company                                  │
│  ┌─────────────────────────────────────┐  │
│  │ Company name                        │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  Email                                    │
│  ┌─────────────────────────────────────┐  │
│  │ email@example.com                   │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  Source *                                 │
│  ┌─────────────────────────────────────┐  │
│  │ Select source                     ▼ │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ...                                      │
│                                           │
└───────────────────────────────────────────┘
```

---

## 9. Screen Specifications

### 9.1 Dashboard

**Layout:**
```
┌────────────────────────────────────────────────────────────────────┐
│ Dashboard                                         🔔  AJ           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌───────────┐ │
│  │ Total Sales  │ │ Open Deals   │ │ Pipeline     │ │ Converted │ │
│  │ $48,000      │ │ 5            │ │ $505,000     │ │ 12%       │ │
│  │ ↑ 12%        │ │ ↑ 5%         │ │ ↓ 3%         │ │ ↑ 2%      │ │
│  └──────────────┘ └──────────────┘ └──────────────┘ └───────────┘ │
│                                                                    │
│  ┌──────────────────────────────────┐ ┌──────────────────────────┐ │
│  │ Sales Trend                      │ │ Task Progress            │ │
│  │ [Bar chart: Jul-Dec]             │ │ [Circular progress: 68%] │ │
│  │                                  │ │                          │ │
│  └──────────────────────────────────┘ └──────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────┐ ┌──────────────────────────┐ │
│  │ Pipeline Overview                │ │ Closing This Week        │ │
│  │ [Horizontal bar chart by stage]  │ │ [Deal cards list]        │ │
│  │                                  │ │                          │ │
│  └──────────────────────────────────┘ └──────────────────────────┘ │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Recent Activity                                              │  │
│  │ [Activity feed list]                                         │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**KPI Card Specifications:**
- Grid: 4 columns on desktop, 2 on tablet, 1 on mobile
- Card height: auto (content-driven)
- Value: `--text-heading-lg`
- Label: `--text-caption`, `--text-tertiary`, uppercase
- Trend: Small text with colored arrow icon

### 9.2 Leads List

**Layout:**
```
┌────────────────────────────────────────────────────────────────────┐
│ Leads                                              + New Lead      │
│ 6 leads                                                           │
├────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────┐ ┌─────────────┐ ┌───────────────┐  │
│ │ 🔍 Search leads...         │ │ All Status ▼│ │ Newest First ▼│  │
│ └────────────────────────────┘ └─────────────┘ └───────────────┘  │
├────────────────────────────────────────────────────────────────────┤
│ □  Name              Company           Status    Source    Owner  │
├────────────────────────────────────────────────────────────────────┤
│ □  Sarah Mitchell    TechCorp          New ●     Website   AJ     │ → Click opens drawer
│ □  David Kim         StartupXYZ        New ●     LinkedIn  JW     │
│ □  Michael Chen      Innovate Labs     Contacted Referral  MG     │
│ □  Emily Rodriguez   Global Retail     Qualified Trade     AJ     │
│ □  Jennifer Walsh    HealthFirst       Contacted Cold      JW     │
│ □  Robert Taylor     Finance Plus      Lost ●    Website   MG     │
└────────────────────────────────────────────────────────────────────┘
```

**Table Columns:**

| Column | Width | Content |
|--------|-------|---------|
| Checkbox | 40px | Multi-select |
| Name | flex | Name + avatar + tags |
| Company | 180px | Company name |
| Status | 100px | Status badge |
| Source | 100px | Text |
| Owner | 80px | Avatar only |
| Actions | 48px | More menu |

### 9.3 Deals Kanban

**Layout:**
```
┌────────────────────────────────────────────────────────────────────┐
│ Deals                                    List │ Kanban   + New     │
│ Pipeline: $505,000                                                 │
├────────────────────────────────────────────────────────────────────┤
│ 🔍 Search deals...                                                 │
├────────────────────────────────────────────────────────────────────┤
│ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌───────────────┐  │
│ │ Prospecting │ │ Qualified   │ │ Proposal    │ │ Negotiation   │  │
│ │ 1 · $6k     │ │ 2 · $274k   │ │ 1 · $75k    │ │ 1 · $150k     │  │
│ ├─────────────┤ ├─────────────┤ ├─────────────┤ ├───────────────┤  │
│ │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌─────────┐ │ │ ┌───────────┐ │  │
│ │ │ Deal 1  │ │ │ │ Deal 2  │ │ │ │ Deal 4  │ │ │ │ Deal 5    │ │  │
│ │ │ $6,000  │ │ │ │ $24,000 │ │ │ │ $75,000 │ │ │ │ $150,000  │ │  │
│ │ │ ▓▓░░░░░ │ │ │ │ ▓▓▓▓░░░ │ │ │ │ ▓▓▓▓▓░░ │ │ │ │ ▓▓▓▓▓▓▓░ │ │  │
│ │ │ AJ  1/10│ │ │ │ MG      │ │ │ │ JW 1/15 │ │ │ │ AJ  1/20  │ │  │
│ │ └─────────┘ │ │ └─────────┘ │ │ └─────────┘ │ │ └───────────┘ │  │
│ │             │ │ ┌─────────┐ │ │             │ │               │  │
│ │             │ │ │ Deal 3  │ │ │             │ │               │  │
│ │             │ │ │ $250k   │ │ │             │ │               │  │
│ │             │ │ └─────────┘ │ │             │ │               │  │
│ └─────────────┘ └─────────────┘ └─────────────┘ └───────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

**Kanban Column:**
- Width: 280px (fixed)
- Gap between columns: 16px
- Header: Stage name + count + total value
- Scrollable vertically if overflow
- Drop zone highlight on drag

**Deal Card (Kanban):**
- Padding: 12px
- Border: 1px `--border-default`
- Border-left: 3px colored by stage
- Title: `--text-heading-sm`
- Value: `--text-body`, `--accent-primary`
- Progress bar: 4px height, stage color
- Footer: Avatar + close date

### 9.4 Tasks

**Layout:**
```
┌────────────────────────────────────────────────────────────────────┐
│ Tasks                                   Calendar │ List   + New    │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────┐  ┌────────────────────────────┐  │
│  │       November 2025          │  │ Wed, November 26           │  │
│  │ ◄                         ►  │  │                            │  │
│  │ Su Mo Tu We Th Fr Sa         │  │ ┌────────────────────────┐ │  │
│  │                          1   │  │ │ ○ Team standup meeting │ │  │
│  │  2  3  4  5  6  7  8        │  │ │   10:44 PM             │ │  │
│  │  9 10 11 12 13 14 15        │  │ └────────────────────────┘ │  │
│  │ 16 17 18 19 20 21 22        │  │                            │  │
│  │ 23 24 25 [26] 27• 28 29     │  │ No other tasks             │  │
│  │ 30                          │  │                            │  │
│  └──────────────────────────────┘  └────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Overdue · 2 tasks                                            │  │
│  │ ┌──────────────────────────────────────────────────────────┐ │  │
│  │ │ ○ Follow up with TechCorp     High ●     Nov 24   AJ     │ │  │
│  │ │ ○ Send proposal to client     Medium    Nov 25   MG     │ │  │
│  │ └──────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Upcoming · 5 tasks                                           │  │
│  │ ┌──────────────────────────────────────────────────────────┐ │  │
│  │ │ ○ Review contract terms       Low        Nov 28   JW     │ │  │
│  │ │ ○ Demo for Global Retail      High ●     Nov 29   AJ     │ │  │
│  │ └──────────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Calendar:**
- Month header with navigation arrows
- 7-column grid for days
- Selected day: Filled circle background
- Days with tasks: Dot indicator below number
- Click day → filters task list

**Task Row:**
- Height: 48px
- Checkbox: Circle, not square (task completion style)
- Completed: Strikethrough text, muted color
- Priority indicator: Colored dot
- Overdue: Red text for date

### 9.5 Settings / More

**Layout:**
```
┌────────────────────────────────────────────────────────────────────┐
│ Settings                                                           │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  AJ   Alex Johnson                                        ›  │  │
│  │       Sales Manager · alex.johnson@company.com               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ACCOUNT                                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  👤  Profile Settings                                     ›  │  │
│  │  🔔  Notifications                                    2   ›  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  TEAM                                                             │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  👥  Team Management                                      ›  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  PREFERENCES                                                      │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  🌙  Dark Mode                                         ○──   │  │
│  │  🌐  Language                                      English › │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  SUPPORT                                                          │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  ❓  Help & Support                                       ›  │  │
│  │  📄  Terms of Service                                     ›  │  │
│  │  🔒  Privacy Policy                                       ›  │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │  🚪  Sign Out                                                │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Version 1.0.0                                                    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

**Settings Row:**
- Height: 52px
- Icon: 20px, `--text-tertiary`
- Label: `--text-body`
- Chevron: Right arrow for navigation items
- Toggle: For boolean settings
- Section header: `--text-overline`, `--text-tertiary`, 12px top margin

---

## 10. Interaction Patterns

### 10.1 Click Behaviors

| Element | Single Click | Double Click |
|---------|--------------|--------------|
| List row | Open side drawer | - |
| Kanban card | Open side drawer | - |
| Table row | Select row | Open side drawer |
| Checkbox | Toggle selection | - |
| Status badge | Open status dropdown | - |
| Tag | Filter by tag | - |

### 10.2 Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `⌘/Ctrl + K` | Open command palette / search |
| `⌘/Ctrl + N` | New item (context-aware) |
| `⌘/Ctrl + /` | Toggle sidebar |
| `Escape` | Close drawer / modal |
| `↑/↓` | Navigate list items |
| `Enter` | Open selected item |
| `Space` | Toggle checkbox |
| `⌘/Ctrl + S` | Save form |

### 10.3 Drag and Drop

**Kanban Cards:**
- Cursor: `grab` on hover, `grabbing` while dragging
- Drag preview: Semi-transparent card following cursor
- Drop zones: Highlight column with dashed border
- Invalid drop: Return to original position

**List Reordering:**
- Handle icon on left side of row
- Drag indicator line between rows
- Auto-scroll when near edges

### 10.4 Selection States

**Single Selection (default):**
- Click row → opens drawer
- Click checkbox → selects row
- Selected row: `--accent-primary-subtle` background

**Multi-Selection:**
- Shift+Click: Select range
- Cmd/Ctrl+Click: Add to selection
- Bulk actions bar appears at bottom

### 10.5 Empty States

**Structure:**
```
┌────────────────────────────────────────┐
│                                        │
│           [Illustration]               │
│                                        │
│         No leads yet                   │
│   Create your first lead to get        │
│   started with your sales pipeline.    │
│                                        │
│         [ + Create Lead ]              │
│                                        │
└────────────────────────────────────────┘
```

**Specifications:**
- Illustration: 120px max height, muted colors
- Title: `--text-heading-md`
- Description: `--text-body`, `--text-secondary`, max-width 300px, centered
- CTA button: Primary variant

### 10.6 Loading States

**Skeleton Screens:**
- Use animated gradient shimmer
- Match layout of actual content
- Show immediately (no loading spinner for <300ms)

**Button Loading:**
- Replace text with spinner
- Maintain button width
- Disable interaction

---

## 11. Animation Guidelines

### 11.1 Timing Functions

| Name | Value | Usage |
|------|-------|-------|
| `ease-out` | `cubic-bezier(0.0, 0.0, 0.2, 1)` | Elements entering |
| `ease-in` | `cubic-bezier(0.4, 0.0, 1, 1)` | Elements exiting |
| `ease-in-out` | `cubic-bezier(0.4, 0.0, 0.2, 1)` | Moving elements |
| `spring` | `cubic-bezier(0.175, 0.885, 0.32, 1.275)` | Playful bounces |

### 11.2 Duration Scale

| Name | Duration | Usage |
|------|----------|-------|
| `instant` | 0ms | Immediate state changes |
| `fast` | 100ms | Hovers, focus states |
| `normal` | 200ms | Most transitions |
| `slow` | 300ms | Drawer/modal entry |
| `slower` | 400ms | Complex animations |

### 11.3 Common Animations

**Drawer Entry:**
```css
@keyframes drawer-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
/* Duration: 300ms, ease-out */
```

**Drawer Exit:**
```css
@keyframes drawer-out {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}
/* Duration: 200ms, ease-in */
```

**Backdrop:**
```css
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}
/* Duration: 200ms */
```

**Row Hover:**
```css
.row {
  transition: background-color 100ms ease;
}
```

**Button Press:**
```css
.button:active {
  transform: scale(0.98);
  transition: transform 50ms ease;
}
```

---

## 12. Responsive Breakpoints

### 12.1 Breakpoint Scale

| Name | Width | Sidebar | Drawer |
|------|-------|---------|--------|
| `xs` | <640px | Hidden | Full screen |
| `sm` | 640-768px | Collapsed (64px) | Full screen |
| `md` | 768-1024px | Collapsed | Overlay (420px) |
| `lg` | 1024-1280px | Expanded | Overlay (420px) |
| `xl` | >1280px | Expanded | Overlay (480px) |

### 12.2 Layout Adjustments

**Mobile (<768px):**
- Sidebar: Becomes slide-out menu (hamburger toggle)
- Drawer: Full screen overlay
- Kanban: Horizontal scroll, single column visible
- Tables: Convert to stacked cards
- KPI grid: 2 columns

**Tablet (768-1024px):**
- Sidebar: Collapsed by default, expand on hover
- Drawer: Full width overlay
- Kanban: 2-3 columns visible
- Tables: Hide non-essential columns
- KPI grid: 2 columns

**Desktop (>1024px):**
- Full layout as specified
- Sidebar: Expanded by default
- Drawer: Side overlay
- Kanban: All columns visible
- Tables: Full columns
- KPI grid: 4 columns

### 12.3 Touch Adaptations

For touch devices:
- Minimum touch target: 44px × 44px
- Increase row heights to 56px
- Add swipe gestures for drawer
- Long press for context menu

---

## Appendix A: Icon Reference

Use **Lucide Icons** (consistent with current implementation).

| Context | Icons |
|---------|-------|
| Navigation | `LayoutDashboard`, `Users`, `Briefcase`, `CheckSquare`, `Settings` |
| Actions | `Plus`, `Edit2`, `Trash2`, `MoreHorizontal`, `Search`, `Filter` |
| Status | `Circle`, `CheckCircle`, `AlertCircle`, `XCircle` |
| Communication | `Phone`, `Mail`, `MessageSquare`, `Calendar` |
| Navigation | `ChevronLeft`, `ChevronRight`, `ChevronDown`, `X`, `Menu` |
| Misc | `Bell`, `User`, `LogOut`, `Moon`, `Sun`, `ExternalLink` |

---

## Appendix B: Component Checklist

### Layout Components
- [ ] `AppShell` - Master layout with sidebar + main + drawer slots
- [ ] `Sidebar` - Collapsible navigation sidebar
- [ ] `SideDrawer` - Right-side detail/form panel
- [ ] `PageHeader` - Title, subtitle, actions area

### UI Components
- [ ] `Button` - All variants and sizes
- [ ] `Input` - Text, email, password, textarea
- [ ] `Select` - Dropdown with search
- [ ] `Checkbox` / `Radio`
- [ ] `Toggle` - Boolean switch
- [ ] `Badge` - Status and label pills
- [ ] `Avatar` - Image with fallback initials
- [ ] `Card` - Content container
- [ ] `Table` - Data table with sorting
- [ ] `EmptyState` - No data placeholder
- [ ] `Skeleton` - Loading placeholders

### Feature Components
- [ ] `KPICard` - Dashboard metric card
- [ ] `LeadRow` - Lead list item
- [ ] `DealCard` - Kanban deal card
- [ ] `TaskRow` - Task list item
- [ ] `Calendar` - Month calendar picker
- [ ] `ActivityItem` - Timeline activity entry
- [ ] `SettingsRow` - Settings menu item

---

*Document generated for SalesPro CRM Web Application redesign.*
