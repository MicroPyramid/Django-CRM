# Onboarding Screen

**Route:** `/onboarding`
**File:** `src/routes/(auth)/onboarding/+page.svelte`
**Layout:** Auth layout (MobileShell wrapper)

---

## Overview

The onboarding screen presents a swipeable carousel introducing key features of the CRM application. Users can navigate through slides manually or skip directly to login. It serves as both education and engagement for new users.

---

## Screen Purpose

- Introduce app features to new users
- Build excitement and set expectations
- Provide guided tour before first use
- Allow skip for returning users

---

## UI Structure

### Main Container
- **Height:** Full viewport (`min-h-dvh`)
- **Layout:** Flex column
- **Background:** White (surface)

### Skip Button
- **Position:** Top-right, fixed within container
- **Text:** "Skip"
- **Style:** `text-sm`, `text-gray-500`, `font-medium`
- **Padding:** `p-6`
- **Action:** Navigate directly to `/login`

### Carousel Section
- **Layout:** Horizontal scroll with snap points
- **Scroll behavior:** `scroll-snap-type: x mandatory`
- **Item snap:** `scroll-snap-align: center`
- **Overflow:** Hidden scrollbar (`.scrollbar-hide`)
- **Height:** Flex-1 (fills available space)

### Slide Content Structure (per slide)
Each slide contains:

#### Illustration Container
- **Size:** `w-64 h-64` (256px)
- **Background:** Colored circle matching theme
- **Border radius:** `rounded-full`
- **Content:** Large icon centered
- **Margin bottom:** `mb-8`

#### Title
- **Font:** `text-2xl`, `font-bold`, `text-gray-900`
- **Alignment:** Center
- **Margin bottom:** `mb-4`

#### Description
- **Font:** `text-gray-500`, `text-center`
- **Line height:** `leading-relaxed`
- **Max width:** Constrained for readability
- **Padding:** Horizontal padding for margins

---

## Slide Content

### Slide 1: Track Your Leads
- **Icon:** Users (lucide)
- **Icon Color:** `text-primary-600`
- **Background:** `bg-primary-100`
- **Title:** "Track Your Leads"
- **Description:** "Manage and organize all your leads in one place. Never miss a follow-up again."

### Slide 2: Close More Deals
- **Icon:** TrendingUp (lucide)
- **Icon Color:** `text-success-600`
- **Background:** `bg-success-100`
- **Title:** "Close More Deals"
- **Description:** "Visualize your sales pipeline and move deals through stages effortlessly."

### Slide 3: Stay Organized
- **Icon:** Calendar (lucide)
- **Icon Color:** `text-warning-600`
- **Background:** `bg-warning-100`
- **Title:** "Stay Organized"
- **Description:** "Keep track of tasks, meetings, and deadlines. Boost your productivity."

---

## Navigation Elements

### Page Indicator Dots
- **Position:** Below carousel, centered
- **Layout:** Horizontal flex with `gap-2`
- **Dot size:** `w-2 h-2` (8px)
- **Active state:** `bg-primary-600`, `w-6` (stretched pill shape)
- **Inactive state:** `bg-gray-300`
- **Transition:** Width and color animate on change
- **Margin:** `mb-8` below, `mt-auto` above

### Action Button
- **Component:** `Button`
- **Variant:** `primary`
- **Size:** `lg`
- **Width:** Full width with horizontal padding
- **Text (slides 1-2):** "Next"
- **Text (slide 3):** "Get Started"
- **Action (slides 1-2):** Advance to next slide
- **Action (slide 3):** Navigate to `/login`

---

## State Management

```javascript
let currentSlide = $state(0);
let carouselRef = $state(null);

const slides = [
  {
    icon: Users,
    iconColor: 'text-primary-600',
    bgColor: 'bg-primary-100',
    title: 'Track Your Leads',
    description: 'Manage and organize all your leads...'
  },
  // ... more slides
];
```

---

## Interactions

### Swipe Navigation
- **Touch gesture:** Horizontal swipe advances/retreats slides
- **Scroll snap:** Content snaps to nearest slide
- **Indicator update:** Dots update based on scroll position

### Scroll Position Tracking
```javascript
function handleScroll(e) {
  const container = e.target;
  const slideWidth = container.clientWidth;
  const scrollPosition = container.scrollLeft;
  currentSlide = Math.round(scrollPosition / slideWidth);
}
```

### Programmatic Navigation
```javascript
function goToSlide(index) {
  if (carouselRef) {
    const slideWidth = carouselRef.clientWidth;
    carouselRef.scrollTo({
      left: slideWidth * index,
      behavior: 'smooth'
    });
  }
}

function nextSlide() {
  if (currentSlide < slides.length - 1) {
    goToSlide(currentSlide + 1);
  } else {
    goto('/login');
  }
}
```

### Dot Tap Navigation
- Tapping a dot navigates directly to that slide
- Smooth scroll animation

---

## Animations

### Slide Transition
```css
scroll-behavior: smooth;
scroll-snap-type: x mandatory;
```

### Dot Indicator Animation
```css
transition: width 0.3s ease, background-color 0.3s ease;
```

### Content Entrance (optional)
- Fade-in for icon and text as slide becomes visible
- Scale animation for illustration container

---

## Color Specifications

| Element | Slide 1 | Slide 2 | Slide 3 |
|---------|---------|---------|---------|
| Icon bg | primary-100 (#dbeafe) | success-100 (#dcfce7) | warning-100 (#fef3c7) |
| Icon color | primary-600 (#2563eb) | success-600 (#16a34a) | warning-600 (#d97706) |

| Element | Color | Hex Value |
|---------|-------|-----------|
| Background | surface | #ffffff |
| Title text | gray-900 | #0f172a |
| Description text | gray-500 | #6b7280 |
| Skip text | gray-500 | #6b7280 |
| Active dot | primary-600 | #2563eb |
| Inactive dot | gray-300 | #d1d5db |
| Button | primary-600 | #2563eb |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| Skip button padding | 24px (p-6) |
| Illustration size | 256px |
| Illustration margin-bottom | 32px (mb-8) |
| Title margin-bottom | 16px (mb-4) |
| Description horizontal padding | 24px |
| Dots gap | 8px (gap-2) |
| Dots margin-bottom | 32px (mb-8) |
| Button horizontal padding | 24px (px-6) |
| Button margin-bottom | safe-area + 32px |

---

## Flutter Implementation Notes

### PageView Implementation
```dart
class OnboardingScreen extends StatefulWidget {
  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  final PageController _pageController = PageController();
  int _currentPage = 0;

  final List<OnboardingSlide> _slides = [
    OnboardingSlide(
      icon: Icons.people,
      iconColor: AppColors.primary600,
      bgColor: AppColors.primary100,
      title: 'Track Your Leads',
      description: 'Manage and organize...',
    ),
    // ... more slides
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: Column(
          children: [
            // Skip button row
            Align(
              alignment: Alignment.centerRight,
              child: TextButton(
                onPressed: () => Navigator.pushReplacementNamed(context, '/login'),
                child: Text('Skip'),
              ),
            ),
            // PageView
            Expanded(
              child: PageView.builder(
                controller: _pageController,
                onPageChanged: (index) => setState(() => _currentPage = index),
                itemCount: _slides.length,
                itemBuilder: (context, index) => _buildSlide(_slides[index]),
              ),
            ),
            // Dot indicators
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: List.generate(
                _slides.length,
                (index) => _buildDot(index),
              ),
            ),
            // Next/Get Started button
            Padding(
              padding: EdgeInsets.all(24),
              child: ElevatedButton(
                onPressed: _handleNext,
                child: Text(_currentPage == _slides.length - 1 ? 'Get Started' : 'Next'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
```

### Animated Dot Indicator
```dart
Widget _buildDot(int index) {
  return AnimatedContainer(
    duration: Duration(milliseconds: 300),
    margin: EdgeInsets.symmetric(horizontal: 4),
    height: 8,
    width: _currentPage == index ? 24 : 8,
    decoration: BoxDecoration(
      color: _currentPage == index
        ? AppColors.primary600
        : AppColors.gray300,
      borderRadius: BorderRadius.circular(4),
    ),
  );
}
```

### Slide Widget
```dart
Widget _buildSlide(OnboardingSlide slide) {
  return Padding(
    padding: EdgeInsets.symmetric(horizontal: 24),
    child: Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Container(
          width: 256,
          height: 256,
          decoration: BoxDecoration(
            color: slide.bgColor,
            shape: BoxShape.circle,
          ),
          child: Icon(
            slide.icon,
            size: 120,
            color: slide.iconColor,
          ),
        ),
        SizedBox(height: 32),
        Text(
          slide.title,
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.bold,
          ),
        ),
        SizedBox(height: 16),
        Text(
          slide.description,
          textAlign: TextAlign.center,
          style: TextStyle(
            color: AppColors.gray500,
          ),
        ),
      ],
    ),
  );
}
```

### Skip Onboarding for Returning Users
```dart
// Check SharedPreferences on app start
Future<bool> hasSeenOnboarding() async {
  final prefs = await SharedPreferences.getInstance();
  return prefs.getBool('hasSeenOnboarding') ?? false;
}

// Set flag after completing onboarding
Future<void> completeOnboarding() async {
  final prefs = await SharedPreferences.getInstance();
  await prefs.setBool('hasSeenOnboarding', true);
}
```

---

## Accessibility

- **Swipe gesture:** Standard iOS/Android swipe recognition
- **Screen reader:** Announce slide title and description
- **Focus management:** Focus on title when slide changes
- **Skip button:** Clearly accessible for keyboard users
- **Dot indicators:** Tappable with adequate touch target (expand hitbox)

---

## Best Practices

### Content Guidelines
- Keep titles short (3-4 words max)
- Descriptions should be 1-2 sentences
- Use action-oriented language
- Highlight key benefits, not features

### Visual Guidelines
- Use consistent illustration style
- Maintain color harmony with brand
- Icons should be instantly recognizable
- Don't overload with information

### UX Guidelines
- Allow skipping at any point
- Remember if user has seen onboarding
- Consider showing again after major updates
- A/B test different copy and visuals
