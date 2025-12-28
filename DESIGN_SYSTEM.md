# CRM Design System — Style Guide

> Version 1.0 | Last Updated: December 2024

A comprehensive design system reference for building consistent, accessible, and modern CRM interfaces.

---

## Table of Contents

1. [Design Principles](#design-principles)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Spacing & Layout](#spacing--layout)
5. [Border Radius](#border-radius)
6. [Elevation & Shadows](#elevation--shadows)
7. [Components](#components)
8. [Icons](#icons)
9. [Grid & Breakpoints](#grid--breakpoints)
10. [CSS Variables Reference](#css-variables-reference)

---

## Design Principles

1. **Clarity First** — Every element should serve a purpose. Remove visual clutter.
2. **Data-Driven** — Prioritize readability of data in tables, lists, and cards.
3. **Consistent Rhythm** — Use the 8px grid system for all spacing decisions.
4. **Accessible** — WCAG 2.0 AA compliant color contrast and interactions.
5. **Theme-Ready** — Semantic tokens enable light/dark mode switching.

---

## Color System

### Token Architecture

We use a **three-layer token system**:

```
Base Layer (Primitives) → Semantic Layer (Purpose) → Component Layer (Usage)
```

### Brand Colors

| Token | Hex | RGB | Usage |
|-------|-----|-----|-------|
| `--color-brand-primary` | `#08A742` | 8, 167, 66 | Primary actions, CTAs, positive indicators |
| `--color-brand-dark` | `#404346` | 64, 67, 70 | Primary text, dark UI elements |
| `--color-brand-white` | `#FFFFFF` | 255, 255, 255 | Backgrounds, cards, surfaces |

### Neutral Palette

| Token | Hex | Usage |
|-------|-----|-------|
| `--color-grey-50` | `#FAFAFA` | Subtle backgrounds |
| `--color-grey-100` | `#F5F5F5` | Hover states, zebra stripes |
| `--color-grey-200` | `#EEEEEE` | Borders, dividers |
| `--color-grey-300` | `#E0E0E0` | Disabled borders |
| `--color-grey-400` | `#BDBDBD` | Placeholder text |
| `--color-grey-500` | `#9E9E9E` | Secondary icons |
| `--color-grey-600` | `#757575` | Secondary text |
| `--color-grey-700` | `#616161` | Body text |
| `--color-grey-800` | `#424242` | Headings |
| `--color-grey-900` | `#212121` | Primary text |

### Semantic Colors

| Category | Token | Hex | Usage |
|----------|-------|-----|-------|
| **Primary** | `--color-primary-default` | `#08A742` | Primary buttons, links |
| | `--color-primary-hover` | `#079239` | Primary hover state |
| | `--color-primary-active` | `#068030` | Primary active/pressed |
| | `--color-primary-light` | `#E8F5EC` | Primary backgrounds |
| **Negative/Error** | `--color-negative-default` | `#DC3545` | Error states, destructive actions |
| | `--color-negative-hover` | `#C82333` | Error hover |
| | `--color-negative-light` | `#FDEAEA` | Error backgrounds |
| **Warning** | `--color-warning-default` | `#FFC107` | Warning states |
| | `--color-warning-dark` | `#E0A800` | Warning text on light bg |
| | `--color-warning-light` | `#FFF8E1` | Warning backgrounds |
| **Success** | `--color-success-default` | `#28A745` | Success states |
| | `--color-success-light` | `#E8F5E9` | Success backgrounds |
| **Info** | `--color-info-default` | `#17A2B8` | Informational states |
| | `--color-info-light` | `#E3F2FD` | Info backgrounds |

### Surface Colors

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--surface-default` | `#FFFFFF` | `#1E1E1E` | Main background |
| `--surface-raised` | `#FFFFFF` | `#252525` | Cards, elevated elements |
| `--surface-sunken` | `#F5F5F5` | `#141414` | Inset areas, sidebars |
| `--surface-overlay` | `#FFFFFF` | `#2D2D2D` | Modals, dropdowns |

### Text Colors

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--text-primary` | `#212121` | `#FFFFFF` | Headings, primary content |
| `--text-secondary` | `#616161` | `#B0B0B0` | Descriptions, metadata |
| `--text-tertiary` | `#9E9E9E` | `#757575` | Placeholders, hints |
| `--text-disabled` | `#BDBDBD` | `#525252` | Disabled states |
| `--text-inverse` | `#FFFFFF` | `#212121` | Text on colored backgrounds |
| `--text-link` | `#08A742` | `#4ADE80` | Links |
| `--text-error` | `#DC3545` | `#F87171` | Error messages |

### Border Colors

| Token | Light Mode | Dark Mode | Usage |
|-------|------------|-----------|-------|
| `--border-default` | `#E0E0E0` | `#3D3D3D` | Default borders |
| `--border-strong` | `#BDBDBD` | `#525252` | Emphasized borders |
| `--border-focus` | `#08A742` | `#4ADE80` | Focus rings |
| `--border-error` | `#DC3545` | `#F87171` | Error state borders |

---

## Typography

### Font Stack

```css
--font-family-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
                     'Helvetica Neue', Arial, sans-serif;
--font-family-mono: 'SF Mono', 'Fira Code', 'Fira Mono', Consolas, monospace;
```

### Type Scale

| Token | Size | Weight | Line Height | Letter Spacing | Usage |
|-------|------|--------|-------------|----------------|-------|
| `--text-display` | 40px | 700 | 1.2 | -0.02em | Hero sections |
| `--text-h1` | 32px | 600 | 1.25 | -0.01em | Page titles |
| `--text-h2` | 24px | 600 | 1.3 | -0.01em | Section headers |
| `--text-h3` | 20px | 600 | 1.35 | 0 | Subsection headers |
| `--text-h4` | 16px | 600 | 1.4 | 0 | Card titles |
| `--text-h5` | 14px | 600 | 1.4 | 0 | Small headers |
| `--text-body-lg` | 16px | 400 | 1.5 | 0 | Primary body text |
| `--text-body` | 14px | 400 | 1.5 | 0 | Default body text |
| `--text-body-sm` | 13px | 400 | 1.45 | 0 | Secondary body text |
| `--text-caption` | 12px | 400 | 1.4 | 0.01em | Captions, metadata |
| `--text-label` | 12px | 500 | 1.3 | 0.02em | Form labels, badges |
| `--text-overline` | 11px | 600 | 1.4 | 0.08em | Overlines (uppercase) |

### Font Weights

| Token | Value | Usage |
|-------|-------|-------|
| `--font-weight-regular` | 400 | Body text, descriptions |
| `--font-weight-medium` | 500 | Labels, emphasis |
| `--font-weight-semibold` | 600 | Headings, buttons |
| `--font-weight-bold` | 700 | Strong emphasis |

### Usage Guidelines

- **Body text**: 14px for dense UI, 16px for reading-focused areas
- **Minimum size**: 12px (never go below for accessibility)
- **Line length**: 60-80 characters maximum for readability
- **Paragraph spacing**: Use `--space-300` (24px) between paragraphs

---

## Spacing & Layout

### Base Unit

All spacing is based on an **8px grid system**.

### Spacing Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--space-0` | 0px | No spacing |
| `--space-25` | 2px | Micro adjustments, borders |
| `--space-50` | 4px | Tight spacing, icon gaps |
| `--space-100` | 8px | Base unit, compact layouts |
| `--space-150` | 12px | Default internal padding |
| `--space-200` | 16px | Component padding, gaps |
| `--space-250` | 20px | Medium spacing |
| `--space-300` | 24px | Section padding |
| `--space-400` | 32px | Section margins |
| `--space-500` | 40px | Large component spacing |
| `--space-600` | 48px | Page sections |
| `--space-800` | 64px | Major section breaks |
| `--space-1000` | 80px | Page-level spacing |

### Spacing Usage Guide

| Context | Recommended Tokens |
|---------|-------------------|
| Icon to text gap | `--space-50` to `--space-100` (4-8px) |
| Button padding (horizontal) | `--space-200` to `--space-300` (16-24px) |
| Button padding (vertical) | `--space-100` to `--space-150` (8-12px) |
| Card internal padding | `--space-200` to `--space-300` (16-24px) |
| Form field gap | `--space-200` (16px) |
| Section gap | `--space-400` to `--space-600` (32-48px) |
| Page margins | `--space-300` to `--space-400` (24-32px) |

---

## Border Radius

| Token | Value | Usage |
|-------|-------|-------|
| `--radius-none` | 0px | Sharp corners |
| `--radius-xs` | 2px | Subtle rounding |
| `--radius-sm` | 4px | Inputs, small buttons |
| `--radius-md` | 6px | Buttons, dropdowns |
| `--radius-lg` | 8px | Cards, containers |
| `--radius-xl` | 12px | Modals, large cards |
| `--radius-2xl` | 16px | Large containers |
| `--radius-full` | 9999px | Pills, avatars, tags |

### Usage by Component

| Component | Radius Token |
|-----------|--------------|
| Buttons | `--radius-md` (6px) |
| Input fields | `--radius-sm` (4px) |
| Cards | `--radius-lg` (8px) |
| Modals | `--radius-xl` (12px) |
| Avatars | `--radius-full` |
| Tags/Badges | `--radius-full` |
| Tooltips | `--radius-sm` (4px) |
| Dropdowns | `--radius-md` (6px) |

---

## Elevation & Shadows

### Shadow Scale

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-none` | none | Flat elements |
| `--shadow-xs` | `0 1px 2px rgba(0,0,0,0.04)` | Subtle lift |
| `--shadow-sm` | `0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04)` | Cards (resting) |
| `--shadow-md` | `0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.05)` | Cards (hover), dropdowns |
| `--shadow-lg` | `0 10px 15px rgba(0,0,0,0.08), 0 4px 6px rgba(0,0,0,0.05)` | Modals, popovers |
| `--shadow-xl` | `0 20px 25px rgba(0,0,0,0.10), 0 10px 10px rgba(0,0,0,0.04)` | Full overlays |

### Elevation Levels

| Level | Shadow Token | Z-Index | Usage |
|-------|--------------|---------|-------|
| Base | `--shadow-none` | 0 | Page background |
| Raised | `--shadow-sm` | 10 | Cards, sections |
| Dropdown | `--shadow-md` | 100 | Dropdowns, tooltips |
| Sticky | `--shadow-md` | 200 | Sticky headers |
| Modal | `--shadow-lg` | 300 | Modals, dialogs |
| Overlay | `--shadow-xl` | 400 | Full overlays |
| Toast | `--shadow-lg` | 500 | Notifications |

### Focus Ring

```css
--focus-ring: 0 0 0 2px var(--surface-default), 0 0 0 4px var(--color-primary-default);
```

---

## Components

### Buttons

#### Variants

| Variant | Background | Text | Border | Usage |
|---------|------------|------|--------|-------|
| **Primary** | `--color-primary-default` | `--text-inverse` | none | Main actions |
| **Secondary** | `transparent` | `--color-primary-default` | `--color-primary-default` | Alternative actions |
| **Tertiary** | `transparent` | `--text-secondary` | none | Low emphasis |
| **Destructive** | `--color-negative-default` | `--text-inverse` | none | Dangerous actions |
| **Ghost** | `transparent` | `--text-primary` | none | Minimal UI |

#### Sizes

| Size | Height | Padding (H) | Font Size | Icon Size |
|------|--------|-------------|-----------|-----------|
| **XS** | 24px | 8px | 11px | 14px |
| **SM** | 28px | 12px | 12px | 16px |
| **MD** | 36px | 16px | 14px | 18px |
| **LG** | 44px | 20px | 16px | 20px |
| **XL** | 52px | 24px | 18px | 24px |

#### States

| State | Opacity/Change |
|-------|----------------|
| Default | 100% |
| Hover | Darken 8% or overlay |
| Active | Darken 12% |
| Disabled | 50% opacity, no pointer |
| Loading | Show spinner, disable |

#### Button Specs

```css
.btn {
  font-weight: 600;
  border-radius: var(--radius-md);
  transition: all 150ms ease;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-100);
}
```

---

### Input Fields

#### Anatomy

```
┌─────────────────────────────────────┐
│ Label *                    (Helper) │
├─────────────────────────────────────┤
│ [Icon] Placeholder text      [Icon] │
├─────────────────────────────────────┤
│ Helper text or error message        │
└─────────────────────────────────────┘
```

#### Specifications

| Property | Value |
|----------|-------|
| Height | 40px (default), 36px (compact), 48px (large) |
| Padding | 12px horizontal, centered vertical |
| Border | 1px solid `--border-default` |
| Border Radius | `--radius-sm` (4px) |
| Font Size | 14px |
| Label Font Size | 12px |
| Helper Font Size | 12px |

#### States

| State | Border Color | Background |
|-------|--------------|------------|
| Default | `--border-default` | `--surface-default` |
| Hover | `--border-strong` | `--surface-default` |
| Focus | `--border-focus` (2px) | `--surface-default` |
| Error | `--border-error` | `--color-negative-light` |
| Disabled | `--border-default` | `--surface-sunken` |
| Read-only | `--border-default` | `--surface-sunken` |

---

### Cards

#### Specifications

| Property | Value |
|----------|-------|
| Background | `--surface-raised` |
| Border | 1px solid `--border-default` (optional) |
| Border Radius | `--radius-lg` (8px) |
| Padding | `--space-200` to `--space-300` (16-24px) |
| Shadow (resting) | `--shadow-sm` |
| Shadow (hover) | `--shadow-md` |

#### Card Types

| Type | Description | Shadow |
|------|-------------|--------|
| **Flat** | Border only, no shadow | `--shadow-none` |
| **Elevated** | Subtle lift | `--shadow-sm` |
| **Interactive** | Hover lift | `--shadow-sm` → `--shadow-md` |

---

### Modals / Dialogs

#### Size Presets

| Size | Width | Max Height | Usage |
|------|-------|------------|-------|
| **SM** | 400px | 80vh | Confirmations, alerts |
| **MD** | 560px | 80vh | Forms, standard content |
| **LG** | 720px | 85vh | Complex forms |
| **XL** | 900px | 90vh | Data-heavy content |
| **Full** | 100% - 48px | 100% - 48px | Wizards, editors |

#### Specifications

| Property | Value |
|----------|-------|
| Border Radius | `--radius-xl` (12px) |
| Padding (Header) | `--space-200` to `--space-300` |
| Padding (Body) | `--space-300` |
| Padding (Footer) | `--space-200` to `--space-300` |
| Shadow | `--shadow-lg` |
| Overlay Background | `rgba(0, 0, 0, 0.5)` |

#### Structure

```
┌─────────────────────────────────────┐
│ Header                        [×]  │
├─────────────────────────────────────┤
│                                     │
│ Body content                        │
│                                     │
├─────────────────────────────────────┤
│             [Secondary] [Primary]   │
└─────────────────────────────────────┘
```

---

### Select / Dropdown

#### Specifications

| Property | Value |
|----------|-------|
| Trigger Height | 40px (matches input) |
| Trigger Padding | 12px horizontal |
| Trigger Border Radius | `--radius-sm` (4px) |
| Dropdown Border Radius | `--radius-md` (6px) |
| Dropdown Shadow | `--shadow-md` |
| Item Height | 36px |
| Item Padding | 12px horizontal |
| Max Dropdown Height | 320px (scrollable) |

---

### Tables

#### Specifications

| Property | Value |
|----------|-------|
| Header Height | 44px |
| Row Height | 52px (default), 40px (compact), 64px (comfortable) |
| Cell Padding | 16px horizontal, centered vertical |
| Border | 1px solid `--border-default` |
| Header Background | `--surface-sunken` |
| Row Background | `--surface-default` |
| Zebra Stripe | Alternating `--surface-default` / `--surface-sunken` |
| Hover Row | `--color-grey-100` |
| Selected Row | `--color-primary-light` |

#### Column Widths

| Content Type | Min Width | Recommended |
|--------------|-----------|-------------|
| Checkbox | 48px | 48px |
| Avatar | 56px | 56px |
| Short text | 100px | 150px |
| Medium text | 150px | 200px |
| Long text | 200px | 300px |
| Actions | 80px | 120px |

---

### Tags / Badges

#### Sizes

| Size | Height | Padding (H) | Font Size | Border Radius |
|------|--------|-------------|-----------|---------------|
| **SM** | 20px | 6px | 11px | `--radius-full` |
| **MD** | 24px | 8px | 12px | `--radius-full` |
| **LG** | 28px | 10px | 13px | `--radius-full` |

#### Variants

| Variant | Background | Text |
|---------|------------|------|
| **Default** | `--color-grey-200` | `--text-primary` |
| **Primary** | `--color-primary-light` | `--color-primary-default` |
| **Success** | `--color-success-light` | `--color-success-default` |
| **Warning** | `--color-warning-light` | `--color-warning-dark` |
| **Error** | `--color-negative-light` | `--color-negative-default` |
| **Info** | `--color-info-light` | `--color-info-default` |

---

### Avatars

#### Sizes

| Size | Dimensions | Font Size | Usage |
|------|------------|-----------|-------|
| **XS** | 24px | 10px | Inline mentions |
| **SM** | 32px | 12px | Lists, compact UI |
| **MD** | 40px | 14px | Default, cards |
| **LG** | 56px | 20px | Profile headers |
| **XL** | 80px | 28px | Profile pages |
| **2XL** | 120px | 40px | Account settings |

#### Specifications

| Property | Value |
|----------|-------|
| Border Radius | `--radius-full` (circle) |
| Background (fallback) | `--color-grey-300` |
| Text Color (initials) | `--text-primary` |
| Border (optional) | 2px solid `--surface-default` |

---

### Toast / Snackbar

#### Specifications

| Property | Value |
|----------|-------|
| Min Width | 300px |
| Max Width | 500px |
| Padding | 12px 16px |
| Border Radius | `--radius-md` (6px) |
| Shadow | `--shadow-lg` |
| Position | Bottom-left, 24px from edges |
| Duration | 4000ms (default), 8000ms (with action) |

#### Variants

| Variant | Icon | Left Border |
|---------|------|-------------|
| **Default** | Info | None |
| **Success** | Check | `--color-success-default` |
| **Warning** | Warning | `--color-warning-default` |
| **Error** | Error | `--color-negative-default` |

---

### Tooltips

#### Specifications

| Property | Value |
|----------|-------|
| Max Width | 240px |
| Padding | 8px 12px |
| Border Radius | `--radius-sm` (4px) |
| Background | `--color-grey-900` |
| Text Color | `--text-inverse` |
| Font Size | 12px |
| Shadow | `--shadow-md` |
| Arrow Size | 6px |

---

## Icons

### Style Guidelines

- **Style**: Line/outline icons (1.5px stroke weight)
- **Corners**: Rounded corners (2px radius on strokes)
- **Grid**: Designed on 24px grid with 2px padding
- **Consistency**: Uniform stroke weight across all icons

### Sizes

| Token | Size | Usage |
|-------|------|-------|
| `--icon-xs` | 12px | Inline with small text |
| `--icon-sm` | 16px | Buttons, form fields |
| `--icon-md` | 20px | Navigation, default |
| `--icon-lg` | 24px | Headers, emphasis |
| `--icon-xl` | 32px | Empty states |
| `--icon-2xl` | 48px | Illustrations |

### Icon Colors

| Context | Color Token |
|---------|-------------|
| Default | `--text-secondary` |
| Interactive | `--text-primary` |
| Primary action | `--color-primary-default` |
| Success | `--color-success-default` |
| Warning | `--color-warning-default` |
| Error | `--color-negative-default` |
| Disabled | `--text-disabled` |

---

## Grid & Breakpoints

### Breakpoints

| Token | Width | Columns | Margin | Gutter |
|-------|-------|---------|--------|--------|
| `--breakpoint-xs` | 0-479px | 4 | 16px | 16px |
| `--breakpoint-sm` | 480-767px | 8 | 16px | 16px |
| `--breakpoint-md` | 768-1023px | 12 | 24px | 24px |
| `--breakpoint-lg` | 1024-1279px | 12 | 32px | 24px |
| `--breakpoint-xl` | 1280-1439px | 12 | 40px | 24px |
| `--breakpoint-2xl` | 1440px+ | 12 | auto | 24px |

### Container Widths

| Token | Max Width | Usage |
|-------|-----------|-------|
| `--container-sm` | 640px | Narrow content |
| `--container-md` | 768px | Forms, articles |
| `--container-lg` | 1024px | Standard content |
| `--container-xl` | 1280px | Wide content |
| `--container-full` | 100% | Full width |

### Layout Patterns

#### Sidebar Layout

```
┌────────────┬────────────────────────────┐
│            │                            │
│  Sidebar   │      Main Content          │
│   (240px)  │        (flex: 1)           │
│            │                            │
└────────────┴────────────────────────────┘
```

| Element | Width |
|---------|-------|
| Sidebar (collapsed) | 64px |
| Sidebar (expanded) | 240px |
| Secondary panel | 320px - 400px |
| Main content | Remaining space |

---

## CSS Variables Reference

### Complete Token Export

```css
:root {
  /* Colors - Brand */
  --color-brand-primary: #08A742;
  --color-brand-dark: #404346;
  --color-brand-white: #FFFFFF;

  /* Colors - Primary */
  --color-primary-default: #08A742;
  --color-primary-hover: #079239;
  --color-primary-active: #068030;
  --color-primary-light: #E8F5EC;

  /* Colors - Negative */
  --color-negative-default: #DC3545;
  --color-negative-hover: #C82333;
  --color-negative-light: #FDEAEA;

  /* Colors - Warning */
  --color-warning-default: #FFC107;
  --color-warning-dark: #E0A800;
  --color-warning-light: #FFF8E1;

  /* Colors - Success */
  --color-success-default: #28A745;
  --color-success-light: #E8F5E9;

  /* Colors - Info */
  --color-info-default: #17A2B8;
  --color-info-light: #E3F2FD;

  /* Colors - Grey Scale */
  --color-grey-50: #FAFAFA;
  --color-grey-100: #F5F5F5;
  --color-grey-200: #EEEEEE;
  --color-grey-300: #E0E0E0;
  --color-grey-400: #BDBDBD;
  --color-grey-500: #9E9E9E;
  --color-grey-600: #757575;
  --color-grey-700: #616161;
  --color-grey-800: #424242;
  --color-grey-900: #212121;

  /* Surface */
  --surface-default: #FFFFFF;
  --surface-raised: #FFFFFF;
  --surface-sunken: #F5F5F5;
  --surface-overlay: #FFFFFF;

  /* Text */
  --text-primary: #212121;
  --text-secondary: #616161;
  --text-tertiary: #9E9E9E;
  --text-disabled: #BDBDBD;
  --text-inverse: #FFFFFF;
  --text-link: #08A742;
  --text-error: #DC3545;

  /* Border */
  --border-default: #E0E0E0;
  --border-strong: #BDBDBD;
  --border-focus: #08A742;
  --border-error: #DC3545;

  /* Typography */
  --font-family-sans: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
  --font-family-mono: 'SF Mono', 'Fira Code', Consolas, monospace;
  
  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Spacing */
  --space-0: 0px;
  --space-25: 2px;
  --space-50: 4px;
  --space-100: 8px;
  --space-150: 12px;
  --space-200: 16px;
  --space-250: 20px;
  --space-300: 24px;
  --space-400: 32px;
  --space-500: 40px;
  --space-600: 48px;
  --space-800: 64px;
  --space-1000: 80px;

  /* Border Radius */
  --radius-none: 0px;
  --radius-xs: 2px;
  --radius-sm: 4px;
  --radius-md: 6px;
  --radius-lg: 8px;
  --radius-xl: 12px;
  --radius-2xl: 16px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-none: none;
  --shadow-xs: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-sm: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.05);
  --shadow-lg: 0 10px 15px rgba(0,0,0,0.08), 0 4px 6px rgba(0,0,0,0.05);
  --shadow-xl: 0 20px 25px rgba(0,0,0,0.10), 0 10px 10px rgba(0,0,0,0.04);

  /* Focus Ring */
  --focus-ring: 0 0 0 2px var(--surface-default), 0 0 0 4px var(--color-primary-default);

  /* Icon Sizes */
  --icon-xs: 12px;
  --icon-sm: 16px;
  --icon-md: 20px;
  --icon-lg: 24px;
  --icon-xl: 32px;
  --icon-2xl: 48px;

  /* Z-Index Scale */
  --z-base: 0;
  --z-raised: 10;
  --z-dropdown: 100;
  --z-sticky: 200;
  --z-modal: 300;
  --z-overlay: 400;
  --z-toast: 500;

  /* Transitions */
  --transition-fast: 100ms ease;
  --transition-normal: 150ms ease;
  --transition-slow: 300ms ease;

  /* Breakpoints (for reference in JS) */
  --breakpoint-xs: 0px;
  --breakpoint-sm: 480px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1280px;
  --breakpoint-2xl: 1440px;

  /* Containers */
  --container-sm: 640px;
  --container-md: 768px;
  --container-lg: 1024px;
  --container-xl: 1280px;
}

/* Dark Mode Override */
[data-theme="dark"] {
  --surface-default: #1E1E1E;
  --surface-raised: #252525;
  --surface-sunken: #141414;
  --surface-overlay: #2D2D2D;

  --text-primary: #FFFFFF;
  --text-secondary: #B0B0B0;
  --text-tertiary: #757575;
  --text-disabled: #525252;
  --text-inverse: #212121;
  --text-link: #4ADE80;
  --text-error: #F87171;

  --border-default: #3D3D3D;
  --border-strong: #525252;
  --border-focus: #4ADE80;
  --border-error: #F87171;

  --color-primary-default: #4ADE80;
  --color-primary-hover: #22C55E;
  --color-primary-active: #16A34A;
  --color-primary-light: #14532D;
}
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Dec 2024 | Initial release |

---

**Questions?** Contact the Design System team.