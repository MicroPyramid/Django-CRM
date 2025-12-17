# UI Components Reference

This document provides detailed specifications for all reusable UI components in the CRM application. Use these specifications to build equivalent Flutter widgets.

---

## Table of Contents

1. [Layout Components](#layout-components)
2. [Form Components](#form-components)
3. [Display Components](#display-components)
4. [Navigation Components](#navigation-components)
5. [Feedback Components](#feedback-components)
6. [Data Visualization](#data-visualization)

---

## Layout Components

### MobileShell

A wrapper component that constrains content to mobile viewport dimensions.

#### Purpose
- Constrain content to max 430px width
- Handle safe area insets
- Center content on larger screens

#### Specifications
| Property | Value |
|----------|-------|
| Max width | 430px |
| Min height | 100dvh |
| Background | `bg-gray-100` |
| Safe areas | Top and bottom insets |

#### Flutter Implementation
```dart
class MobileShell extends StatelessWidget {
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: ConstrainedBox(
        constraints: BoxConstraints(maxWidth: 430),
        child: SafeArea(child: child),
      ),
    );
  }
}
```

---

### AppBar

Custom app bar with flexible leading/trailing slots.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| title | String? | - | Title text |
| showBack | bool | false | Show back button |
| onBack | Function? | history.back() | Back action |
| transparent | bool | false | Transparent background |
| leading | Widget? | - | Leading slot content |
| trailing | Widget? | - | Trailing slot content |

#### Specifications
| Property | Value |
|----------|-------|
| Height | 56px |
| Background | White or transparent |
| Shadow | None (clean look) |
| Z-index | 40 |
| Position | Sticky top |

#### Visual Layout
```
[Back/Leading]     [Title]     [Trailing Actions]
```

#### Flutter Implementation
```dart
class CustomAppBar extends StatelessWidget implements PreferredSizeWidget {
  final String? title;
  final bool showBack;
  final VoidCallback? onBack;
  final bool transparent;
  final Widget? leading;
  final Widget? trailing;

  @override
  Size get preferredSize => Size.fromHeight(56);

  @override
  Widget build(BuildContext context) {
    return AppBar(
      backgroundColor: transparent ? Colors.transparent : Colors.white,
      elevation: 0,
      leading: showBack
        ? IconButton(
            icon: Icon(Icons.arrow_back, color: AppColors.gray900),
            onPressed: onBack ?? () => Navigator.pop(context),
          )
        : leading,
      title: title != null
        ? Text(title!, style: TextStyle(
            color: AppColors.gray900,
            fontWeight: FontWeight.w600,
          ))
        : null,
      centerTitle: true,
      actions: trailing != null ? [trailing!] : null,
    );
  }
}
```

---

### Card

Container component with elevation and styling variants.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | String | 'elevated' | 'elevated', 'outlined', 'filled' |
| padding | String | 'md' | 'none', 'sm', 'md', 'lg' |
| onclick | Function? | - | Makes card tappable |

#### Variant Styles
| Variant | Background | Border | Shadow |
|---------|------------|--------|--------|
| elevated | white | none | shadow-sm |
| outlined | white | 1px gray-200 | none |
| filled | gray-50 | none | none |

#### Padding Sizes
| Size | Value |
|------|-------|
| none | 0 |
| sm | 12px |
| md | 16px |
| lg | 24px |

#### Flutter Implementation
```dart
class AppCard extends StatelessWidget {
  final CardVariant variant;
  final CardPadding padding;
  final VoidCallback? onTap;
  final Widget child;

  @override
  Widget build(BuildContext context) {
    return Material(
      color: variant == CardVariant.filled
        ? AppColors.gray50
        : Colors.white,
      borderRadius: BorderRadius.circular(16),
      elevation: variant == CardVariant.elevated ? 2 : 0,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Container(
          padding: _getPadding(),
          decoration: variant == CardVariant.outlined
            ? BoxDecoration(
                border: Border.all(color: AppColors.gray200),
                borderRadius: BorderRadius.circular(16),
              )
            : null,
          child: child,
        ),
      ),
    );
  }
}
```

---

## Form Components

### Button

Primary action button with multiple variants and states.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | String | 'primary' | 'primary', 'secondary', 'ghost', 'danger' |
| size | String | 'md' | 'sm', 'md', 'lg' |
| fullWidth | bool | false | Full container width |
| disabled | bool | false | Disabled state |
| loading | bool | false | Loading state |
| icon | Widget? | - | Leading icon |

#### Size Specifications
| Size | Height | Padding | Font Size |
|------|--------|---------|-----------|
| sm | 36px | 12px h | 14px |
| md | 44px | 16px h | 14px |
| lg | 48px | 20px h | 16px |

#### Variant Colors
| Variant | Background | Text | Border |
|---------|------------|------|--------|
| primary | primary-600 | white | none |
| secondary | gray-100 | gray-700 | none |
| ghost | transparent | gray-700 | none |
| danger | danger-600 | white | none |

#### States
| State | Effect |
|-------|--------|
| Hover | Slight darken |
| Active | Scale 0.98 |
| Disabled | Opacity 50% |
| Loading | Spinner replaces content |

#### Flutter Implementation
```dart
class AppButton extends StatelessWidget {
  final String label;
  final ButtonVariant variant;
  final ButtonSize size;
  final bool fullWidth;
  final bool disabled;
  final bool loading;
  final Widget? icon;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: fullWidth ? double.infinity : null,
      height: _getHeight(),
      child: ElevatedButton(
        onPressed: disabled || loading ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: _getBackgroundColor(),
          foregroundColor: _getTextColor(),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
        child: loading
          ? SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation(_getTextColor()),
              ),
            )
          : Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (icon != null) ...[icon!, SizedBox(width: 8)],
                Text(label),
              ],
            ),
      ),
    );
  }
}
```

---

### InputFloatingLabel

Material Design-style input with floating label animation.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| label | String | required | Label text |
| type | String | 'text' | Input type |
| value | String | '' | Bindable value |
| placeholder | String? | - | Placeholder text |
| error | String? | - | Error message |
| disabled | bool | false | Disabled state |
| required | bool | false | Required indicator |
| icon | Widget? | - | Leading icon |
| trailing | Widget? | - | Trailing widget |

#### Supported Types
- text
- email
- password
- tel
- number
- search

#### Visual States
| State | Border Color | Label Position |
|-------|-------------|----------------|
| Default | gray-200 | Inside (placeholder position) |
| Focused | primary-500 | Floated above |
| Filled | gray-200 | Floated above |
| Error | danger-500 | Floated above |
| Disabled | gray-100 | Varies |

#### Specifications
| Property | Value |
|----------|-------|
| Height | 56px |
| Border radius | 12px |
| Border width | 1px (2px focused) |
| Padding | 16px horizontal |
| Icon size | 20px |
| Label font | 14px (floated: 12px) |

#### Flutter Implementation
```dart
class FloatingLabelInput extends StatefulWidget {
  final String label;
  final TextInputType keyboardType;
  final TextEditingController controller;
  final String? errorText;
  final bool obscureText;
  final Widget? prefixIcon;
  final Widget? suffixIcon;

  @override
  State<FloatingLabelInput> createState() => _FloatingLabelInputState();
}

class _FloatingLabelInputState extends State<FloatingLabelInput> {
  final FocusNode _focusNode = FocusNode();
  bool _isFocused = false;

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: widget.controller,
      focusNode: _focusNode,
      keyboardType: widget.keyboardType,
      obscureText: widget.obscureText,
      decoration: InputDecoration(
        labelText: widget.label,
        errorText: widget.errorText,
        prefixIcon: widget.prefixIcon,
        suffixIcon: widget.suffixIcon,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppColors.gray200),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppColors.primary500, width: 2),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: AppColors.danger500),
        ),
        contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      ),
    );
  }
}
```

---

### IconButton

Circular button for icon-only actions.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | String | 'default' | 'default', 'primary', 'ghost' |
| size | String | 'md' | 'sm', 'md', 'lg' |
| disabled | bool | false | Disabled state |
| label | String | required | Accessibility label |

#### Size Specifications
| Size | Dimensions | Icon Size |
|------|------------|-----------|
| sm | 32px | 16px |
| md | 40px | 20px |
| lg | 48px | 24px |

#### Variant Styles
| Variant | Background | Icon Color |
|---------|------------|------------|
| default | gray-100 | gray-700 |
| primary | primary-600 | white |
| ghost | transparent | gray-700 |

#### Flutter Implementation
```dart
class AppIconButton extends StatelessWidget {
  final IconData icon;
  final IconButtonVariant variant;
  final IconButtonSize size;
  final bool disabled;
  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) {
    return Semantics(
      label: label,
      button: true,
      child: Material(
        color: _getBackgroundColor(),
        shape: CircleBorder(),
        child: InkWell(
          onTap: disabled ? null : onPressed,
          customBorder: CircleBorder(),
          child: Container(
            width: _getSize(),
            height: _getSize(),
            alignment: Alignment.center,
            child: Icon(
              icon,
              size: _getIconSize(),
              color: _getIconColor(),
            ),
          ),
        ),
      ),
    );
  }
}
```

---

## Display Components

### Avatar

User avatar with image or initials fallback.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| src | String? | - | Image URL |
| name | String? | - | Name for initials |
| size | String | 'md' | 'xs', 'sm', 'md', 'lg', 'xl' |

#### Size Specifications
| Size | Dimensions | Font Size |
|------|------------|-----------|
| xs | 24px | 10px |
| sm | 32px | 12px |
| md | 40px | 14px |
| lg | 48px | 16px |
| xl | 64px | 20px |

#### Color Generation
Deterministic color based on name hash:
```javascript
const colors = [
  'bg-red-500', 'bg-orange-500', 'bg-amber-500', 'bg-green-500',
  'bg-teal-500', 'bg-blue-500', 'bg-indigo-500', 'bg-purple-500'
];
const index = name.charCodeAt(0) % colors.length;
```

#### Flutter Implementation
```dart
class Avatar extends StatelessWidget {
  final String? imageUrl;
  final String? name;
  final AvatarSize size;

  String get initials {
    if (name == null || name!.isEmpty) return '?';
    final parts = name!.split(' ');
    if (parts.length >= 2) {
      return '${parts[0][0]}${parts[1][0]}'.toUpperCase();
    }
    return name![0].toUpperCase();
  }

  Color get backgroundColor {
    if (name == null) return AppColors.gray400;
    final colors = [
      Colors.red, Colors.orange, Colors.amber, Colors.green,
      Colors.teal, Colors.blue, Colors.indigo, Colors.purple,
    ];
    return colors[name!.codeUnitAt(0) % colors.length];
  }

  @override
  Widget build(BuildContext context) {
    final dimension = _getDimension();

    if (imageUrl != null) {
      return ClipOval(
        child: Image.network(
          imageUrl!,
          width: dimension,
          height: dimension,
          fit: BoxFit.cover,
        ),
      );
    }

    return Container(
      width: dimension,
      height: dimension,
      decoration: BoxDecoration(
        color: backgroundColor,
        shape: BoxShape.circle,
      ),
      alignment: Alignment.center,
      child: Text(
        initials,
        style: TextStyle(
          color: Colors.white,
          fontSize: _getFontSize(),
          fontWeight: FontWeight.w600,
        ),
      ),
    );
  }
}
```

---

### Badge

Status indicator with color variants.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| variant | String | 'default' | Status variant |
| size | String | 'md' | 'sm', 'md' |

#### Variants
| Variant | Background | Text Color |
|---------|------------|------------|
| new | primary-100 | primary-700 |
| contacted | warning-50 | warning-700 |
| qualified | success-50 | success-700 |
| lost | danger-50 | danger-700 |
| hot | danger-500 | white |
| default | gray-100 | gray-700 |

#### Size Specifications
| Size | Padding | Font Size |
|------|---------|-----------|
| sm | 8px h, 2px v | 12px |
| md | 10px h, 4px v | 14px |

#### Flutter Implementation
```dart
class StatusBadge extends StatelessWidget {
  final String label;
  final BadgeVariant variant;
  final BadgeSize size;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: size == BadgeSize.sm ? 8 : 10,
        vertical: size == BadgeSize.sm ? 2 : 4,
      ),
      decoration: BoxDecoration(
        color: _getBackgroundColor(),
        borderRadius: BorderRadius.circular(20),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: _getTextColor(),
          fontSize: size == BadgeSize.sm ? 12 : 14,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }
}
```

---

### PriorityBadge

Priority indicator with icon and color.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| priority | String | required | 'low', 'medium', 'high' |
| showLabel | bool | false | Show text label |
| size | String | 'md' | 'sm', 'md' |

#### Priority Styles
| Priority | Icon | Color |
|----------|------|-------|
| high | AlertTriangle | danger-600 |
| medium | Flag | warning-600 |
| low | Minus | gray-500 |

#### Flutter Implementation
```dart
class PriorityBadge extends StatelessWidget {
  final Priority priority;
  final bool showLabel;
  final bool small;

  IconData get icon {
    switch (priority) {
      case Priority.high: return Icons.warning_amber;
      case Priority.medium: return Icons.flag;
      case Priority.low: return Icons.remove;
    }
  }

  Color get color {
    switch (priority) {
      case Priority.high: return AppColors.danger600;
      case Priority.medium: return AppColors.warning600;
      case Priority.low: return AppColors.gray500;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: small ? 14 : 16, color: color),
        if (showLabel) ...[
          SizedBox(width: 4),
          Text(
            priority.name.capitalize(),
            style: TextStyle(
              color: color,
              fontSize: small ? 12 : 14,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ],
    );
  }
}
```

---

### LabelPill

Colored tag/label pill with auto-color mapping.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| label | String | required | Label text |
| color | String? | auto | Optional explicit color |

#### Auto-Color Mapping
| Keywords | Color |
|----------|-------|
| enterprise, tech, startup | blue |
| expansion, new-business, finance | green |
| renewal | yellow |
| strategic, retail | purple |
| hot-lead, whale | pink |
| smb, early-stage | gray |

#### Flutter Implementation
```dart
class LabelPill extends StatelessWidget {
  final String label;
  final Color? explicitColor;

  Color get backgroundColor {
    if (explicitColor != null) return explicitColor!;

    final lowerLabel = label.toLowerCase();
    if (['enterprise', 'tech', 'startup'].any((k) => lowerLabel.contains(k))) {
      return AppColors.blue100;
    }
    if (['expansion', 'new-business', 'finance'].any((k) => lowerLabel.contains(k))) {
      return AppColors.green100;
    }
    // ... more mappings
    return AppColors.gray100;
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: backgroundColor,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w500,
          color: _getTextColor(),
        ),
      ),
    );
  }
}
```

---

## Navigation Components

### BottomNav

Fixed bottom navigation bar with 5 tabs.

#### Tabs
| Index | Icon | Label | Route |
|-------|------|-------|-------|
| 0 | LayoutDashboard | Dashboard | /dashboard |
| 1 | Users | Leads | /leads |
| 2 | Briefcase | Deals | /deals |
| 3 | CheckSquare | Tasks | /tasks |
| 4 | MoreHorizontal | More | /more |

#### Specifications
| Property | Value |
|----------|-------|
| Height | 64px |
| Background | white |
| Border top | 1px gray-100 |
| Z-index | 50 |
| Active color | primary-600 |
| Inactive color | gray-400 |
| Icon size | 24px |
| Label font | 12px |

#### Flutter Implementation
```dart
class BottomNav extends StatelessWidget {
  final int currentIndex;

  @override
  Widget build(BuildContext context) {
    return BottomNavigationBar(
      currentIndex: currentIndex,
      type: BottomNavigationBarType.fixed,
      selectedItemColor: AppColors.primary600,
      unselectedItemColor: AppColors.gray400,
      selectedFontSize: 12,
      unselectedFontSize: 12,
      items: [
        BottomNavigationBarItem(
          icon: Icon(Icons.dashboard_outlined),
          activeIcon: Icon(Icons.dashboard),
          label: 'Dashboard',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.people_outline),
          activeIcon: Icon(Icons.people),
          label: 'Leads',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.work_outline),
          activeIcon: Icon(Icons.work),
          label: 'Deals',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.check_box_outlined),
          activeIcon: Icon(Icons.check_box),
          label: 'Tasks',
        ),
        BottomNavigationBarItem(
          icon: Icon(Icons.more_horiz),
          label: 'More',
        ),
      ],
      onTap: (index) => _navigateToIndex(context, index),
    );
  }
}
```

---

### TabBar

Horizontal tab switcher with underline indicator.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| tabs | List<Tab> | required | Tab definitions |
| activeTab | String | required | Currently active tab ID |
| onTabChange | Function? | - | Tab change callback |

#### Specifications
| Property | Value |
|----------|-------|
| Height | 48px |
| Tab padding | 16px horizontal |
| Active indicator | 2px height, primary-600 |
| Active text | primary-600, font-semibold |
| Inactive text | gray-500 |

#### Flutter Implementation
```dart
class AppTabBar extends StatelessWidget {
  final List<TabItem> tabs;
  final String activeTab;
  final Function(String) onTabChange;

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 48,
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: AppColors.gray200),
        ),
      ),
      child: Row(
        children: tabs.map((tab) {
          final isActive = tab.id == activeTab;
          return Expanded(
            child: InkWell(
              onTap: () => onTabChange(tab.id),
              child: Container(
                alignment: Alignment.center,
                decoration: BoxDecoration(
                  border: Border(
                    bottom: BorderSide(
                      color: isActive ? AppColors.primary600 : Colors.transparent,
                      width: 2,
                    ),
                  ),
                ),
                child: Text(
                  tab.label,
                  style: TextStyle(
                    color: isActive ? AppColors.primary600 : AppColors.gray500,
                    fontWeight: isActive ? FontWeight.w600 : FontWeight.normal,
                  ),
                ),
              ),
            ),
          );
        }).toList(),
      ),
    );
  }
}
```

---

### FAB (Floating Action Button)

Expandable floating action button with multiple actions.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| onAction | Function | - | Callback with action type |

#### Actions
| Action | Icon | Label |
|--------|------|-------|
| lead | User | Add Lead |
| deal | Briefcase | Add Deal |
| task | CheckSquare | Add Task |

#### Specifications
| Property | Value |
|----------|-------|
| Main button size | 56px |
| Mini button size | 48px |
| Position | Bottom-right |
| Bottom offset | 80px (above BottomNav) |
| Right offset | 16px |
| Expanded gap | 12px between buttons |

#### States
- **Collapsed:** Plus icon, primary-600 background
- **Expanded:** X icon, backdrop overlay, action buttons visible

#### Flutter Implementation
```dart
class ExpandableFAB extends StatefulWidget {
  final Function(String) onAction;

  @override
  State<ExpandableFAB> createState() => _ExpandableFABState();
}

class _ExpandableFABState extends State<ExpandableFAB>
    with SingleTickerProviderStateMixin {
  bool _isExpanded = false;
  late AnimationController _controller;

  @override
  Widget build(BuildContext context) {
    return Stack(
      alignment: Alignment.bottomRight,
      children: [
        if (_isExpanded)
          GestureDetector(
            onTap: () => setState(() => _isExpanded = false),
            child: Container(
              color: Colors.black54,
            ),
          ),
        Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            if (_isExpanded) ...[
              _buildMiniFAB('task', Icons.check_box, 'Add Task'),
              SizedBox(height: 12),
              _buildMiniFAB('deal', Icons.work, 'Add Deal'),
              SizedBox(height: 12),
              _buildMiniFAB('lead', Icons.person, 'Add Lead'),
              SizedBox(height: 12),
            ],
            FloatingActionButton(
              onPressed: () => setState(() => _isExpanded = !_isExpanded),
              backgroundColor: AppColors.primary600,
              child: Icon(_isExpanded ? Icons.close : Icons.add),
            ),
          ],
        ),
      ],
    );
  }
}
```

---

## Data Visualization

### ProgressRing

Circular progress indicator with center text.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| percent | number | required | 0-100 percentage |
| size | number | 100 | Diameter in pixels |
| strokeWidth | number | 8 | Ring thickness |
| color | String | 'primary-500' | Ring color |
| label | String? | - | Center label text |

#### Flutter Implementation
```dart
class ProgressRing extends StatelessWidget {
  final int percent;
  final double size;
  final double strokeWidth;
  final Color color;
  final String? label;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: size,
      height: size,
      child: Stack(
        alignment: Alignment.center,
        children: [
          CircularProgressIndicator(
            value: percent / 100,
            strokeWidth: strokeWidth,
            backgroundColor: AppColors.gray200,
            valueColor: AlwaysStoppedAnimation(color),
          ),
          Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                '$percent%',
                style: TextStyle(
                  fontSize: size * 0.2,
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (label != null)
                Text(
                  label!,
                  style: TextStyle(
                    fontSize: size * 0.1,
                    color: AppColors.gray500,
                  ),
                ),
            ],
          ),
        ],
      ),
    );
  }
}
```

---

### SalesChart

Bar chart for sales trend visualization.

#### Props
| Prop | Type | Default | Description |
|------|------|---------|-------------|
| data | List<DataPoint> | required | Month, value, deals |

#### Data Point Structure
```dart
class SalesDataPoint {
  final String month;  // "Jan", "Feb", etc.
  final int value;     // Dollar amount
  final int deals;     // Deal count
}
```

#### Specifications
| Property | Value |
|----------|-------|
| Bar color | primary-500 |
| Bar radius | 4px top |
| Grid lines | Horizontal, gray-100 |
| X-axis labels | Month abbreviations |
| Tooltip | Value + deal count |

#### Flutter Implementation
Use `fl_chart` package:
```dart
class SalesChart extends StatelessWidget {
  final List<SalesDataPoint> data;

  @override
  Widget build(BuildContext context) {
    return BarChart(
      BarChartData(
        barGroups: data.asMap().entries.map((entry) {
          return BarChartGroupData(
            x: entry.key,
            barRods: [
              BarChartRodData(
                toY: entry.value.value.toDouble(),
                color: AppColors.primary500,
                width: 20,
                borderRadius: BorderRadius.vertical(top: Radius.circular(4)),
              ),
            ],
          );
        }).toList(),
        titlesData: FlTitlesData(
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                return Text(data[value.toInt()].month);
              },
            ),
          ),
        ),
      ),
    );
  }
}
```

---

## Component Index

| Component | Category | File Location |
|-----------|----------|---------------|
| MobileShell | Layout | lib/components/layout/ |
| AppBar | Layout | lib/components/layout/ |
| BottomNav | Navigation | lib/components/layout/ |
| FAB | Navigation | lib/components/layout/ |
| Card | Layout | lib/components/ui/ |
| Button | Form | lib/components/ui/ |
| InputFloatingLabel | Form | lib/components/ui/ |
| IconButton | Form | lib/components/ui/ |
| Avatar | Display | lib/components/ui/ |
| Badge | Display | lib/components/ui/ |
| PriorityBadge | Display | lib/components/ui/ |
| LabelPill | Display | lib/components/ui/ |
| TabBar | Navigation | lib/components/ui/ |
| ProgressRing | Charts | lib/components/charts/ |
| SalesChart | Charts | lib/components/charts/ |
| LeadCard | Domain | lib/components/leads/ |
| DealCard | Domain | lib/components/deals/ |
| TaskRow | Domain | lib/components/tasks/ |
| KanbanColumn | Domain | lib/components/deals/ |
| TimelineItem | Domain | lib/components/leads/ |
| Calendar | Domain | lib/components/tasks/ |
