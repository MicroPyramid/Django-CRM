# More/Settings Screen

**Route:** `/more`
**File:** `src/routes/(app)/more/+page.svelte`
**Layout:** App layout (MobileShell + BottomNav)

---

## Overview

The More/Settings screen provides access to user profile, app preferences, team management, and support options. It serves as the central hub for all configuration and account-related features.

---

## Screen Purpose

- Access user profile and account settings
- Configure app preferences (theme, notifications)
- Manage team members
- Access help and support resources
- Sign out functionality

---

## UI Structure

### App Bar
- **Component:** `AppBar`
- **Title:** "More" or "Settings"
- **Leading:** None
- **Trailing:** None (or notification bell)

### Profile Section
- **Position:** Top of screen
- **Background:** `bg-primary-50` or gradient
- **Padding:** `p-6`

#### Profile Card (Tappable)
- **Action:** Navigate to `/more/profile`

**Content:**
- **Avatar:** Current user avatar (xl size, 64px)
- **Name:** User full name
  - Style: `text-xl`, `font-bold`, `text-gray-900`
- **Role:** User role/title
  - Style: `text-sm`, `text-gray-500`
- **Email:** User email
  - Style: `text-sm`, `text-gray-500`
- **Chevron:** Right arrow indicating tap action

---

### Menu Sections

#### Section Structure
Each section has:
- **Header:** Section title (optional)
- **Items:** List of menu items
- **Divider:** Between sections

---

### Account Section

#### Section Header
- **Title:** "Account"
- **Style:** `text-xs`, `text-gray-500`, `uppercase`, `tracking-wide`
- **Padding:** `px-4`, `pt-6`, `pb-2`

#### Menu Items

**Profile Settings**
- **Icon:** User (lucide)
- **Label:** "Profile Settings"
- **Action:** Navigate to `/more/profile`
- **Chevron:** Right arrow

**Notifications**
- **Icon:** Bell (lucide)
- **Label:** "Notifications"
- **Badge:** Unread count (if any)
- **Action:** Navigate to `/more/notifications`
- **Chevron:** Right arrow

---

### Team Section

#### Section Header
- **Title:** "Team"

#### Menu Items

**Team Management**
- **Icon:** Users (lucide)
- **Label:** "Team Management"
- **Description:** "Manage team members and roles" (optional)
- **Action:** Navigate to `/more/team`
- **Chevron:** Right arrow

---

### Preferences Section

#### Section Header
- **Title:** "Preferences"

#### Menu Items

**Dark Mode**
- **Icon:** Moon (lucide)
- **Label:** "Dark Mode"
- **Control:** Toggle switch (right side)
- **State:** On/Off
- **No navigation:** Toggle in place

**Language (optional)**
- **Icon:** Globe (lucide)
- **Label:** "Language"
- **Value:** "English"
- **Action:** Open language picker
- **Chevron:** Right arrow

---

### Support Section

#### Section Header
- **Title:** "Support"

#### Menu Items

**Help Center**
- **Icon:** HelpCircle (lucide)
- **Label:** "Help Center"
- **Action:** Open help documentation or external link
- **Chevron:** Right arrow (or external link icon)

**Terms of Service**
- **Icon:** FileText (lucide)
- **Label:** "Terms of Service"
- **Action:** Open terms page
- **Chevron:** Right arrow

**Privacy Policy**
- **Icon:** Shield (lucide)
- **Label:** "Privacy Policy"
- **Action:** Open privacy page
- **Chevron:** Right arrow

---

### Sign Out Section

#### Sign Out Button
- **Position:** Bottom of list
- **Style:** Full-width button or destructive menu item
- **Icon:** LogOut (lucide)
- **Label:** "Sign Out"
- **Color:** `text-danger-600`
- **Action:** Confirm and sign out
- **Margin:** `mt-4`, `mb-8`

---

## Menu Item Component

### Item Structure
```
[Icon]  [Label]                    [Badge/Value/Control]  [Chevron]
        [Description - optional]
```

### Item Specifications
- **Height:** 56px (or auto if has description)
- **Padding:** `px-4`, `py-3`
- **Background:** White
- **Border:** Bottom border `border-gray-100`
- **Icon:** 20px, `text-gray-500`
- **Label:** `font-medium`, `text-gray-900`
- **Description:** `text-sm`, `text-gray-500`
- **Chevron:** ChevronRight, 20px, `text-gray-400`

### Item States
- **Default:** White background
- **Pressed:** `bg-gray-50`
- **Disabled:** Opacity 50%

---

## State Management

```javascript
import { currentUser, notifications } from '$lib/stores/crmStore.svelte.js';

let darkMode = $state(false);
let unreadCount = $derived(notifications.filter(n => !n.read).length);

function toggleDarkMode() {
  darkMode = !darkMode;
  document.documentElement.classList.toggle('dark', darkMode);
  // Persist to localStorage
  localStorage.setItem('darkMode', darkMode);
}

function handleSignOut() {
  if (confirm('Are you sure you want to sign out?')) {
    // Clear session
    // Navigate to login
    goto('/login');
  }
}
```

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Profile section bg | primary-50 | #eff6ff |
| Section header | gray-500 | #6b7280 |
| Item background | surface | #ffffff |
| Item border | gray-100 | #f3f4f6 |
| Icon color | gray-500 | #6b7280 |
| Label text | gray-900 | #0f172a |
| Description text | gray-500 | #6b7280 |
| Chevron | gray-400 | #9ca3af |
| Badge bg | danger-500 | #ef4444 |
| Sign out text | danger-600 | #dc2626 |
| Toggle track on | primary-600 | #2563eb |
| Toggle track off | gray-200 | #e5e7eb |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| Profile section padding | 24px (p-6) |
| Profile avatar size | 64px |
| Section header padding | 16px horizontal, 24px top, 8px bottom |
| Menu item height | 56px |
| Menu item padding | 16px horizontal, 12px vertical |
| Icon size | 20px |
| Icon-label gap | 12px |
| Bottom padding | 80px (BottomNav) |

---

## Interactions

### Profile Tap
- Navigate to profile edit screen
- Shows full profile details
- Edit capability

### Menu Item Tap
- Navigate to respective screen
- Or perform action (toggle, modal)

### Toggle Switch
- Immediate state change
- No confirmation needed
- Persist to storage

### Sign Out
- Show confirmation dialog
- Clear session data
- Navigate to login screen
- Show toast: "Signed out successfully"

### Badge Tap (Notifications)
- Navigate to notifications screen
- Badge shows unread count

---

## Flutter Implementation Notes

### Screen Structure
```dart
class MoreScreen extends StatefulWidget {
  @override
  State<MoreScreen> createState() => _MoreScreenState();
}

class _MoreScreenState extends State<MoreScreen> {
  bool _darkMode = false;

  @override
  Widget build(BuildContext context) {
    final user = // Get from provider

    return Scaffold(
      appBar: AppBar(title: Text('More')),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildProfileSection(user),
            _buildSectionHeader('Account'),
            _buildMenuItem(
              icon: Icons.person_outline,
              label: 'Profile Settings',
              onTap: () => Navigator.pushNamed(context, '/more/profile'),
            ),
            _buildMenuItem(
              icon: Icons.notifications_outlined,
              label: 'Notifications',
              badge: unreadCount > 0 ? '$unreadCount' : null,
              onTap: () => Navigator.pushNamed(context, '/more/notifications'),
            ),
            _buildSectionHeader('Team'),
            _buildMenuItem(
              icon: Icons.people_outline,
              label: 'Team Management',
              onTap: () => Navigator.pushNamed(context, '/more/team'),
            ),
            _buildSectionHeader('Preferences'),
            _buildToggleItem(
              icon: Icons.dark_mode_outlined,
              label: 'Dark Mode',
              value: _darkMode,
              onChanged: (value) => setState(() => _darkMode = value),
            ),
            _buildSectionHeader('Support'),
            _buildMenuItem(
              icon: Icons.help_outline,
              label: 'Help Center',
              onTap: () => _openHelpCenter(),
            ),
            _buildMenuItem(
              icon: Icons.description_outlined,
              label: 'Terms of Service',
              onTap: () => _openTerms(),
            ),
            _buildMenuItem(
              icon: Icons.privacy_tip_outlined,
              label: 'Privacy Policy',
              onTap: () => _openPrivacy(),
            ),
            SizedBox(height: 16),
            _buildSignOutButton(),
            SizedBox(height: 100),
          ],
        ),
      ),
      bottomNavigationBar: BottomNav(currentIndex: 4),
    );
  }
}
```

### Profile Section
```dart
Widget _buildProfileSection(User user) {
  return Container(
    color: AppColors.primary50,
    padding: EdgeInsets.all(24),
    child: InkWell(
      onTap: () => Navigator.pushNamed(context, '/more/profile'),
      child: Row(
        children: [
          Avatar(
            src: user.avatar,
            name: user.name,
            size: 64,
          ),
          SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  user.name,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                SizedBox(height: 4),
                Text(
                  user.role,
                  style: TextStyle(
                    color: AppColors.gray500,
                    fontSize: 14,
                  ),
                ),
                Text(
                  user.email,
                  style: TextStyle(
                    color: AppColors.gray500,
                    fontSize: 14,
                  ),
                ),
              ],
            ),
          ),
          Icon(Icons.chevron_right, color: AppColors.gray400),
        ],
      ),
    ),
  );
}
```

### Menu Item Widget
```dart
Widget _buildMenuItem({
  required IconData icon,
  required String label,
  String? description,
  String? badge,
  String? value,
  required VoidCallback onTap,
}) {
  return InkWell(
    onTap: onTap,
    child: Container(
      padding: EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      decoration: BoxDecoration(
        color: Colors.white,
        border: Border(
          bottom: BorderSide(color: AppColors.gray100),
        ),
      ),
      child: Row(
        children: [
          Icon(icon, size: 20, color: AppColors.gray500),
          SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: TextStyle(
                    fontWeight: FontWeight.w500,
                    color: AppColors.gray900,
                  ),
                ),
                if (description != null)
                  Text(
                    description,
                    style: TextStyle(
                      fontSize: 12,
                      color: AppColors.gray500,
                    ),
                  ),
              ],
            ),
          ),
          if (badge != null)
            Container(
              padding: EdgeInsets.symmetric(horizontal: 8, vertical: 2),
              decoration: BoxDecoration(
                color: AppColors.danger500,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Text(
                badge,
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          if (value != null)
            Text(
              value,
              style: TextStyle(color: AppColors.gray500),
            ),
          SizedBox(width: 8),
          Icon(Icons.chevron_right, size: 20, color: AppColors.gray400),
        ],
      ),
    ),
  );
}
```

### Toggle Item Widget
```dart
Widget _buildToggleItem({
  required IconData icon,
  required String label,
  required bool value,
  required ValueChanged<bool> onChanged,
}) {
  return Container(
    padding: EdgeInsets.symmetric(horizontal: 16, vertical: 10),
    decoration: BoxDecoration(
      color: Colors.white,
      border: Border(
        bottom: BorderSide(color: AppColors.gray100),
      ),
    ),
    child: Row(
      children: [
        Icon(icon, size: 20, color: AppColors.gray500),
        SizedBox(width: 12),
        Expanded(
          child: Text(
            label,
            style: TextStyle(
              fontWeight: FontWeight.w500,
              color: AppColors.gray900,
            ),
          ),
        ),
        Switch(
          value: value,
          onChanged: onChanged,
          activeColor: AppColors.primary600,
        ),
      ],
    ),
  );
}
```

### Sign Out Button
```dart
Widget _buildSignOutButton() {
  return Padding(
    padding: EdgeInsets.symmetric(horizontal: 16),
    child: OutlinedButton.icon(
      onPressed: _handleSignOut,
      icon: Icon(Icons.logout, color: AppColors.danger600),
      label: Text(
        'Sign Out',
        style: TextStyle(color: AppColors.danger600),
      ),
      style: OutlinedButton.styleFrom(
        side: BorderSide(color: AppColors.danger200),
        minimumSize: Size(double.infinity, 48),
      ),
    ),
  );
}

void _handleSignOut() {
  showDialog(
    context: context,
    builder: (context) => AlertDialog(
      title: Text('Sign Out'),
      content: Text('Are you sure you want to sign out?'),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('Cancel'),
        ),
        TextButton(
          onPressed: () {
            // Clear auth state
            Navigator.pushNamedAndRemoveUntil(
              context,
              '/login',
              (route) => false,
            );
          },
          child: Text('Sign Out', style: TextStyle(color: AppColors.danger600)),
        ),
      ],
    ),
  );
}
```

---

## Sub-Routes

### Profile Screen (`/more/profile`)
- Edit user profile
- Change avatar
- Update contact info
- Change password

### Notifications Screen (`/more/notifications`)
- List of notifications
- Mark as read
- Clear all
- Notification preferences

### Team Screen (`/more/team`)
- List team members
- Add/remove members
- Change roles
- Invite new members

---

## Accessibility

- **Profile section:** Announce user name and role
- **Menu items:** Clear labels
- **Toggle switch:** Announce on/off state
- **Badge:** Announce notification count
- **Sign out:** Confirm action with dialog

---

## Dark Mode Implementation

### CSS Variables
```css
:root {
  --surface: #ffffff;
  --surface-dim: #f8fafc;
  --text-primary: #0f172a;
}

:root.dark {
  --surface: #1e293b;
  --surface-dim: #0f172a;
  --text-primary: #f1f5f9;
}
```

### Flutter Theme
```dart
ThemeData lightTheme = ThemeData(
  brightness: Brightness.light,
  // ... light colors
);

ThemeData darkTheme = ThemeData(
  brightness: Brightness.dark,
  // ... dark colors
);
```

---

## Version Info (Optional)

Add app version at bottom of settings:
- **Text:** "Version 1.0.0"
- **Style:** `text-xs`, `text-gray-400`, centered
- **Position:** Below sign out button
