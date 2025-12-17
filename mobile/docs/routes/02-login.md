# Login Screen

**Route:** `/login`
**File:** `src/routes/(auth)/login/+page.svelte`
**Layout:** Auth layout (MobileShell wrapper)

---

## Overview

The login screen provides user authentication through email/password credentials or Google OAuth. It features Material Design-inspired floating label inputs, form validation, and a clean, professional appearance.

---

## Screen Purpose

- Authenticate existing users
- Provide alternative OAuth login (Google)
- Navigate to password recovery
- Direct new users to registration (onboarding)

---

## UI Elements

### Header Section
- **Logo Icon:** Briefcase in primary-600 circle
  - Container: `w-16 h-16` (64px), `rounded-2xl`, `bg-primary-600`
  - Icon: White, 32x32 pixels
- **Title:** "Welcome Back"
  - Font: `text-2xl`, `font-bold`, `text-gray-900`
  - Margin: `mt-6`
- **Subtitle:** "Sign in to continue to SalesPro"
  - Font: `text-sm`, `text-gray-500`
  - Margin: `mt-2`

### Form Section

#### Email Input
- **Component:** `InputFloatingLabel`
- **Label:** "Email address"
- **Type:** `email`
- **Icon:** Mail (lucide)
- **Validation:** Required, must contain "@"
- **Error state:** Red border + error message

#### Password Input
- **Component:** `InputFloatingLabel`
- **Label:** "Password"
- **Type:** `password`
- **Icon:** Lock (lucide)
- **Trailing:** Eye/EyeOff toggle button
- **Validation:** Required, minimum 6 characters
- **Error state:** Red border + error message

#### Remember Me Row
- **Checkbox:** Native checkbox with `accent-primary-600`
- **Label:** "Remember me" (text-sm, text-gray-600)
- **Link:** "Forgot password?" aligned right
  - Color: `text-primary-600`
  - Action: Navigate to `/forgot-password`

#### Submit Button
- **Component:** `Button`
- **Text:** "Sign In"
- **Variant:** `primary`
- **Size:** `lg`
- **Props:** `fullWidth`, loading state
- **Disabled:** When loading or validation fails

### OAuth Section

#### Divider
- **Layout:** Horizontal line with centered text
- **Text:** "or continue with"
- **Style:** `text-xs`, `text-gray-400`, `uppercase`, `tracking-wide`

#### Google Button
- **Layout:** Full-width outlined button
- **Content:** Google "G" logo + "Continue with Google"
- **Style:**
  - Border: `border-gray-200`
  - Background: White
  - Text: `text-gray-700`, `font-medium`
  - Height: 48px
  - Rounded: `rounded-xl`
- **Hover:** `bg-gray-50`

### Footer Section
- **Text:** "Don't have an account?"
- **Link:** "Sign up"
  - Color: `text-primary-600`, `font-semibold`
  - Action: Navigate to `/onboarding`

---

## Form Validation

### Email Validation
```javascript
function validateEmail() {
  if (!email) {
    emailError = 'Email is required';
  } else if (!email.includes('@')) {
    emailError = 'Please enter a valid email';
  } else {
    emailError = '';
  }
}
```

### Password Validation
```javascript
function validatePassword() {
  if (!password) {
    passwordError = 'Password is required';
  } else if (password.length < 6) {
    passwordError = 'Password must be at least 6 characters';
  } else {
    passwordError = '';
  }
}
```

### Form Submit Flow
1. Prevent default form submission
2. Validate all fields
3. Check for any errors
4. Set loading state
5. Simulate API call (1500ms)
6. Navigate to `/dashboard`

---

## State Management

```javascript
let email = $state('');
let password = $state('');
let showPassword = $state(false);
let rememberMe = $state(false);
let isLoading = $state(false);
let emailError = $state('');
let passwordError = $state('');
```

---

## Animations & Transitions

### Input Focus Animation
- Border color transition to primary-500
- Label float animation (translate + scale)

### Button Loading State
- Spinner replaces "Sign In" text
- Opacity reduction on button

### Error Shake (optional)
- Subtle horizontal shake on validation error

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Background | surface | #ffffff |
| Logo container | primary-600 | #2563eb |
| Title text | gray-900 | #0f172a |
| Subtitle text | gray-500 | #6b7280 |
| Input border default | gray-200 | #e5e7eb |
| Input border focus | primary-500 | #3b82f6 |
| Input border error | danger-500 | #ef4444 |
| Error text | danger-500 | #ef4444 |
| Link text | primary-600 | #2563eb |
| Button primary | primary-600 | #2563eb |
| Google button border | gray-200 | #e5e7eb |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| Outer padding | 24px (p-6) |
| Logo size | 64px |
| Title margin-top | 24px |
| Form section margin-top | 32px |
| Input gap | 16px |
| Remember row margin-top | 16px |
| Submit button margin-top | 24px |
| Divider margin | 24px vertical |
| Footer margin-top | 32px |

---

## Interactions

### Password Visibility Toggle
- **Trigger:** Tap eye icon
- **Action:** Toggle `showPassword` state
- **Visual:** Eye icon changes to EyeOff

### Input Focus
- **Border:** Transition to primary-500
- **Label:** Float up with scale(0.85)
- **Shadow:** Subtle focus ring

### Remember Me Checkbox
- **Style:** Accent color primary-600
- **Size:** Default browser size with custom accent

### Form Submission
- **Loading:** Button shows spinner, disabled state
- **Success:** Navigate to dashboard
- **Error:** Show error messages, shake animation

---

## Flutter Implementation Notes

### Widgets Structure
```dart
Scaffold(
  body: SafeArea(
    child: SingleChildScrollView(
      padding: EdgeInsets.all(24),
      child: Column(
        children: [
          // Logo section
          // Title section
          // Form section
          Form(
            child: Column(
              children: [
                // Email TextFormField
                // Password TextFormField with visibility toggle
                // Remember me row
                // Submit button
              ],
            ),
          ),
          // Divider
          // Google button
          // Footer
        ],
      ),
    ),
  ),
)
```

### Custom FloatingLabelTextField
```dart
class FloatingLabelTextField extends StatelessWidget {
  final String label;
  final TextEditingController controller;
  final IconData? prefixIcon;
  final Widget? suffixIcon;
  final bool obscureText;
  final String? errorText;
  final TextInputType keyboardType;
  // ... build method with decoration
}
```

### Form Validation
```dart
final _formKey = GlobalKey<FormState>();

// In TextFormField
validator: (value) {
  if (value == null || value.isEmpty) {
    return 'Email is required';
  }
  if (!value.contains('@')) {
    return 'Please enter a valid email';
  }
  return null;
}
```

### Google Sign-In
- Use `google_sign_in` package
- Configure OAuth credentials in Firebase/Google Cloud
- Handle sign-in flow and error states

---

## Accessibility

- **Labels:** All inputs have associated labels
- **Error announcements:** Live region for validation errors
- **Tab order:** Logical flow (email → password → remember → forgot → submit → google → signup)
- **Touch targets:** Minimum 48px for all interactive elements
- **Contrast:** All text meets WCAG AA standards

---

## Error States

### Network Error
- Display toast/snackbar: "Unable to connect. Please check your internet."

### Invalid Credentials
- Display inline error: "Invalid email or password"
- Clear password field
- Keep email field populated

### Rate Limiting
- Display toast: "Too many attempts. Please try again later."
- Disable form temporarily

---

## Security Considerations

- Never store password in plain text
- Use secure storage for "Remember me" tokens
- Implement rate limiting on API
- Consider biometric authentication option
- Clear sensitive data on logout
