# Splash Screen

**Route:** `/splash`
**File:** `src/routes/(auth)/splash/+page.svelte`
**Layout:** Auth layout (MobileShell wrapper)

---

## Overview

The splash screen is the entry point of the application, displaying a branded loading animation before transitioning to the login screen. It creates a professional first impression and handles initial app loading states.

---

## Screen Purpose

- Display brand identity during app initialization
- Provide visual feedback during loading
- Smooth transition to authentication flow
- Set the tone for the app's visual language

---

## UI Elements

### Container
- **Type:** Full-screen centered container
- **Background:** `bg-primary-600` (solid blue: #2563eb)
- **Layout:** Flexbox, center-aligned both axes
- **Height:** Full viewport height (`min-h-dvh`)

### Logo/Icon Section
- **Icon:** Briefcase (from lucide-svelte)
- **Size:** 64x64 pixels
- **Color:** White (`text-white`)
- **Container:**
  - White background with 20% opacity (`bg-white/20`)
  - Rounded: `rounded-3xl` (1.5rem)
  - Padding: `p-5`
  - Animation: `animate-pulse` (subtle breathing effect)

### App Name
- **Text:** "SalesPro CRM"
- **Typography:**
  - Font size: `text-3xl` (1.875rem)
  - Font weight: `font-bold`
  - Color: White
  - Margin: `mt-6` (1.5rem top margin)
- **Animation:** Fade-in with slide-up

### Loading Indicator
- **Type:** Three-dot animated loader
- **Dot specifications:**
  - Size: `w-2 h-2` (8px)
  - Color: `bg-white/80`
  - Shape: `rounded-full`
  - Gap between dots: `gap-1.5`
- **Animation:** Sequential bounce with staggered delays
  - Dot 1: No delay
  - Dot 2: 150ms delay
  - Dot 3: 300ms delay
- **Position:** `mt-12` below app name

---

## Animations

### Icon Pulse
```css
animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
```
Creates a gentle breathing effect on the icon container.

### Loading Dots Bounce
```css
@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
animation: bounce 0.6s ease-in-out infinite;
```

### Screen Transition
- **Duration:** 2500ms (2.5 seconds)
- **Action:** Auto-navigate to `/login`
- **Implementation:** `setTimeout` with `goto('/login')`

---

## Behavior & Interactions

### Auto-Navigation
1. Screen mounts and displays splash content
2. Timer starts (2500ms)
3. After timeout, navigates to `/login` using SvelteKit's `goto()`

### onMount Lifecycle
```javascript
onMount(() => {
  const timer = setTimeout(() => {
    goto('/login');
  }, 2500);
  return () => clearTimeout(timer);
});
```

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Background | primary-600 | #2563eb |
| Icon | white | #ffffff |
| Icon container bg | white/20 | rgba(255,255,255,0.2) |
| App name text | white | #ffffff |
| Loading dots | white/80 | rgba(255,255,255,0.8) |

---

## Spacing & Layout

| Element | Spacing |
|---------|---------|
| Icon container padding | 20px (p-5) |
| App name margin-top | 24px (mt-6) |
| Loading dots margin-top | 48px (mt-12) |
| Dot gap | 6px (gap-1.5) |

---

## Flutter Implementation Notes

### Widgets to Use
- `Scaffold` with solid background color
- `Center` widget for content alignment
- `Column` for vertical arrangement
- `AnimatedContainer` or `AnimatedOpacity` for icon pulse
- `Icon` widget (use `business_center` or custom briefcase)
- `Text` widget for app name
- Custom `LoadingDots` widget for animated dots

### Animation Approach
```dart
// Use AnimationController for loading dots
class LoadingDots extends StatefulWidget {
  @override
  State<LoadingDots> createState() => _LoadingDotsState();
}

class _LoadingDotsState extends State<LoadingDots>
    with TickerProviderStateMixin {
  late List<AnimationController> controllers;
  // Stagger animations with 150ms delays
}
```

### Navigation
```dart
// In initState, start timer
Timer(Duration(milliseconds: 2500), () {
  Navigator.pushReplacementNamed(context, '/login');
});
```

### State Management
- No state management needed
- Pure UI screen with timer-based navigation
- Consider using `FutureBuilder` for any initialization logic

---

## Accessibility

- No interactive elements (auto-progression)
- High contrast (white on blue)
- Animation can be disabled via `prefers-reduced-motion`
- Screen reader: Announce "Loading SalesPro CRM"

---

## Edge Cases

1. **Rapid app switching:** Clear timer on dispose
2. **Slow device:** Animation still runs, may feel slow
3. **Deep linking:** Splash should be skipped if user is already authenticated
4. **Dark mode:** Consider darker variant of primary color
