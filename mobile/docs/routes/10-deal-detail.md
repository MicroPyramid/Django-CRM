# Deal Detail Screen

**Route:** `/deals/[id]`
**File:** `src/routes/(app)/deals/[id]/+page.svelte`
**Layout:** App layout (MobileShell)

---

## Overview

The deal detail screen provides comprehensive information about a single deal including value, probability, timeline, associated products, and a visual stage stepper. It enables stage progression and quick access to related lead/contact information.

---

## Screen Purpose

- Display complete deal information
- Visualize deal progression through stages
- Enable stage changes
- Show associated products and value
- Access related lead/contact
- View deal activity timeline

---

## UI Structure

### App Bar
- **Component:** `AppBar`
- **Props:** `showBack={true}`, `transparent={true}`
- **Trailing actions:**
  - Edit icon
  - More/menu icon (dropdown)

### Header Section
- **Background:** Gradient or primary-50
- **Padding:** `p-6`

#### Deal Title
- **Text:** Deal title
- **Style:** `text-2xl`, `font-bold`, `text-gray-900`

#### Company Name
- **Text:** Associated company
- **Style:** `text-base`, `text-gray-500`
- **Action:** Tap to view lead detail

#### Value Display
- **Text:** Formatted deal value
- **Style:** `text-3xl`, `font-bold`, `text-primary-600`
- **Margin:** `mt-4`

#### Badges Row
- **Layout:** `flex gap-2 flex-wrap`
- **Items:**
  - Priority badge
  - Labels (LabelPill components)
- **Margin:** `mt-3`

---

### Stage Stepper Section

#### Component: StageStepper
- **Position:** Below header
- **Background:** White card
- **Padding:** `p-4`
- **Margin:** `mx-4`, `mt-4`
- **Border radius:** `rounded-xl`

#### Stepper Visual

```
[1]----[2]----[3]----[4]----[5]
 ●      ●      ○      ○      ○
Pros   Qual   Prop   Nego   Won
```

#### Stage Steps

| Step | Stage ID | Label | Icon |
|------|----------|-------|------|
| 1 | prospecting | Prospecting | Search |
| 2 | qualified | Qualified | CheckCircle |
| 3 | proposal | Proposal | FileText |
| 4 | negotiation | Negotiation | MessageSquare |
| 5 | closed-won | Closed Won | Trophy |

#### Visual States
- **Completed:** Filled circle, primary-600, line solid
- **Current:** Filled circle, primary-600, pulsing ring
- **Future:** Empty circle, gray-300, line dashed

#### Interaction
- Tap on future stage to advance deal
- Confirmation dialog before stage change
- Cannot go backwards (or require confirmation)

---

### Deal Information Section

#### Card Container
- **Background:** White
- **Padding:** `p-4`
- **Margin:** `mx-4`, `mt-4`
- **Border radius:** `rounded-xl`

#### Information Grid

| Field | Icon | Value |
|-------|------|-------|
| Value | DollarSign | $75,000 |
| Probability | Percent | 60% |
| Expected Close | Calendar | Dec 15, 2024 |
| Created | Clock | Nov 1, 2024 |
| Assigned To | User | Alex Johnson |

#### Field Layout
- **Label:** `text-xs`, `text-gray-500`, `uppercase`
- **Value:** `text-sm`, `font-medium`, `text-gray-900`
- **Icon:** 16px, `text-gray-400`
- **Grid:** 2 columns on mobile

---

### Probability Indicator

#### Visual Bar
- **Height:** 8px
- **Border radius:** `rounded-full`
- **Background:** gray-200
- **Fill:** primary-500, animated width

#### Percentage Label
- **Position:** Above bar, right-aligned
- **Text:** "60%"
- **Style:** `text-sm`, `font-semibold`

---

### Products Section

#### Section Header
- **Title:** "Products"
- **Badge:** Product count
- **Action:** "Add Product" link

#### Product List
- **Layout:** Vertical list
- **Item style:** Row with name, quantity, value

#### Product Item
```
[Product Icon] Product Name
               Qty: 2    $25,000
```

- **Name:** `font-medium`
- **Details:** `text-sm`, `text-gray-500`
- **Value:** `font-semibold`, right-aligned

---

### Related Lead Section

#### Card Container
- **Title:** "Related Lead"
- **Padding:** `p-4`

#### Content
- **Avatar:** Lead avatar (md)
- **Name:** Lead name, `font-medium`
- **Company:** `text-sm`, `text-gray-500`
- **Action:** Tap to navigate to lead detail

---

### Activity Timeline Section

#### Section Header
- **Title:** "Activity"
- **Action:** "See All" (if more than 5)

#### Timeline Items
- Same as Lead Detail timeline
- Filtered for this deal's activities
- Types: stage_change, note, meeting, call, email

---

### Action Buttons (Bottom)

#### Move to Next Stage
- **Component:** `Button`
- **Variant:** `primary`
- **Size:** `lg`
- **Width:** Full width
- **Text:** "Move to {Next Stage}"
- **Disabled:** If at final stage

#### Mark as Lost
- **Component:** `Button`
- **Variant:** `ghost` or `danger`
- **Size:** `md`
- **Text:** "Mark as Lost"
- **Position:** Below primary button

---

## State Management

```javascript
import { page } from '$app/stores';
import { deals, activities, updateDealStage, getUserById } from '$lib/stores/crmStore.svelte.js';

let dealId = $derived($page.params.id);
let deal = $derived(deals.find(d => d.id === dealId));
let assignedUser = $derived(deal ? getUserById(deal.assignedTo) : null);

let dealActivities = $derived(
  activities
    .filter(a => a.relatedTo?.type === 'deal' && a.relatedTo?.id === dealId)
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))
);

const stageOrder = ['prospecting', 'qualified', 'proposal', 'negotiation', 'closed-won'];

let currentStageIndex = $derived(stageOrder.indexOf(deal?.stage));
let nextStage = $derived(stageOrder[currentStageIndex + 1]);

async function handleStageChange(newStage) {
  // Show confirmation
  if (confirm(`Move deal to ${newStage}?`)) {
    updateDealStage(dealId, newStage);
  }
}
```

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Header background | primary-50 | #eff6ff |
| Value text | primary-600 | #2563eb |
| Stage completed | primary-600 | #2563eb |
| Stage current | primary-600 | #2563eb |
| Stage future | gray-300 | #d1d5db |
| Stage line completed | primary-400 | #60a5fa |
| Stage line future | gray-300 | #d1d5db |
| Probability bar bg | gray-200 | #e5e7eb |
| Probability bar fill | primary-500 | #3b82f6 |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| Header padding | 24px (p-6) |
| Card margin horizontal | 16px (mx-4) |
| Card margin top | 16px (mt-4) |
| Card padding | 16px (p-4) |
| Section gap | 16px |
| Bottom padding | 100px (for buttons + BottomNav) |

---

## Interactions

### Stage Stepper
- Tap future stage to advance
- Show confirmation dialog
- Animate stage transition
- Update probability automatically

### Stage Change Effects
| Stage Change | Probability Update |
|--------------|-------------------|
| → Prospecting | 10% |
| → Qualified | 25% |
| → Proposal | 50% |
| → Negotiation | 75% |
| → Closed Won | 100% |

### Mark as Lost
- Confirmation dialog with reason input
- Changes stage to "closed-lost"
- Sets probability to 0%
- Adds timeline entry

### Product Management
- Tap product to edit
- "Add Product" opens product selector
- Swipe to remove product

### Related Lead Tap
- Navigate to lead detail
- Preserve deal context for back navigation

---

## Flutter Implementation Notes

### Screen Structure
```dart
class DealDetailScreen extends StatelessWidget {
  final String dealId;

  @override
  Widget build(BuildContext context) {
    final deal = // Get from provider

    return Scaffold(
      body: CustomScrollView(
        slivers: [
          SliverAppBar(
            expandedHeight: 200,
            pinned: true,
            flexibleSpace: FlexibleSpaceBar(
              background: DealHeader(deal: deal),
            ),
          ),
          SliverToBoxAdapter(
            child: Column(
              children: [
                StageStepper(
                  currentStage: deal.stage,
                  onStageChange: (stage) => _handleStageChange(context, stage),
                ),
                DealInfoCard(deal: deal),
                ProbabilityIndicator(probability: deal.probability),
                ProductsSection(products: deal.products),
                RelatedLeadCard(leadId: deal.leadId),
                ActivityTimeline(dealId: deal.id),
                SizedBox(height: 100),
              ],
            ),
          ),
        ],
      ),
      bottomSheet: DealActionButtons(
        deal: deal,
        onAdvance: () => _handleAdvance(context, deal),
        onMarkLost: () => _handleMarkLost(context, deal),
      ),
    );
  }
}
```

### Stage Stepper Widget
```dart
class StageStepper extends StatelessWidget {
  final String currentStage;
  final Function(String) onStageChange;

  static const stages = [
    ('prospecting', 'Prospecting', Icons.search),
    ('qualified', 'Qualified', Icons.check_circle),
    ('proposal', 'Proposal', Icons.description),
    ('negotiation', 'Negotiation', Icons.chat),
    ('closed-won', 'Won', Icons.emoji_events),
  ];

  int get currentIndex => stages.indexWhere((s) => s.$1 == currentStage);

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: EdgeInsets.all(16),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Row(
          children: List.generate(stages.length * 2 - 1, (index) {
            if (index.isOdd) {
              // Connector line
              final stageIndex = index ~/ 2;
              final isCompleted = stageIndex < currentIndex;
              return Expanded(
                child: Container(
                  height: 2,
                  color: isCompleted
                    ? AppColors.primary400
                    : AppColors.gray300,
                ),
              );
            } else {
              // Stage circle
              final stageIndex = index ~/ 2;
              final stage = stages[stageIndex];
              final isCompleted = stageIndex < currentIndex;
              final isCurrent = stageIndex == currentIndex;
              final isFuture = stageIndex > currentIndex;

              return GestureDetector(
                onTap: isFuture ? () => onStageChange(stage.$1) : null,
                child: Column(
                  children: [
                    Container(
                      width: 32,
                      height: 32,
                      decoration: BoxDecoration(
                        color: isCompleted || isCurrent
                          ? AppColors.primary600
                          : Colors.transparent,
                        border: Border.all(
                          color: isFuture
                            ? AppColors.gray300
                            : AppColors.primary600,
                          width: 2,
                        ),
                        shape: BoxShape.circle,
                      ),
                      child: Icon(
                        isCompleted ? Icons.check : stage.$3,
                        size: 16,
                        color: isCompleted || isCurrent
                          ? Colors.white
                          : AppColors.gray400,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      stage.$2,
                      style: TextStyle(
                        fontSize: 10,
                        color: isCurrent
                          ? AppColors.primary600
                          : AppColors.gray500,
                        fontWeight: isCurrent
                          ? FontWeight.w600
                          : FontWeight.normal,
                      ),
                    ),
                  ],
                ),
              );
            }
          }),
        ),
      ),
    );
  }
}
```

### Probability Indicator
```dart
class ProbabilityIndicator extends StatelessWidget {
  final int probability;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.symmetric(horizontal: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text(
            '$probability%',
            style: TextStyle(
              fontWeight: FontWeight.w600,
              fontSize: 14,
            ),
          ),
          SizedBox(height: 4),
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: probability / 100,
              minHeight: 8,
              backgroundColor: AppColors.gray200,
              valueColor: AlwaysStoppedAnimation(AppColors.primary500),
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

- **Stage stepper:** Announce stage name and status
- **Values:** Announce currency and percentage
- **Buttons:** Clear action labels
- **Timeline:** Announce event type and time

---

## Error States

### Deal Not Found
- Display error screen
- Back button to deals list

### Stage Change Failed
- Show error toast
- Keep current state
- Enable retry

### Network Error
- Cache deal data for offline viewing
- Queue stage changes for sync
