# Forgot Password Screen

**Route:** `/forgot-password`
**File:** `src/routes/(auth)/forgot-password/+page.svelte`
**Layout:** Auth layout (MobileShell wrapper)

---

## Overview

The forgot password screen allows users to initiate a password reset flow by entering their email address. After submission, it displays a success confirmation with instructions to check their email.

---

## Screen Purpose

- Allow users to recover forgotten passwords
- Validate email before sending reset link
- Provide clear feedback on submission success
- Offer navigation back to login

---

## Screen States

### State 1: Email Entry Form
Initial state where user enters their email address.

### State 2: Success Confirmation
Displayed after successful form submission with instructions.

---

## UI Elements

### Back Navigation
- **Component:** `AppBar`
- **Props:** `showBack={true}`, `transparent={true}`
- **Action:** Navigate back to `/login`

### Form State UI

#### Header Section
- **Icon Container:**
  - Size: `w-16 h-16` (64px)
  - Background: `bg-primary-100`
  - Border radius: `rounded-2xl`
  - Icon: KeyRound (lucide), `text-primary-600`, 32px
- **Title:** "Reset Password"
  - Font: `text-2xl`, `font-bold`, `text-gray-900`
  - Margin: `mt-6`
- **Description:** "Enter your email address and we'll send you instructions to reset your password."
  - Font: `text-sm`, `text-gray-500`
  - Margin: `mt-2`
  - Line height: `leading-relaxed`

#### Email Input
- **Component:** `InputFloatingLabel`
- **Label:** "Email address"
- **Type:** `email`
- **Icon:** Mail (lucide)
- **Validation:** Required, must be valid email format
- **Error display:** Below input in red

#### Submit Button
- **Component:** `Button`
- **Text:** "Send Reset Link"
- **Variant:** `primary`
- **Size:** `lg`
- **Props:** `fullWidth`, loading state
- **Margin:** `mt-6`

#### Back to Login Link
- **Text:** "Back to Sign In"
- **Layout:** Centered, with ChevronLeft icon
- **Style:** `text-primary-600`, `font-medium`, `text-sm`
- **Margin:** `mt-6`

### Success State UI

#### Header Section
- **Icon Container:**
  - Size: `w-20 h-20` (80px)
  - Background: `bg-success-100`
  - Border radius: `rounded-full`
  - Icon: CheckCircle2 (lucide), `text-success-600`, 40px
  - Animation: Scale-in entrance
- **Title:** "Check Your Email"
  - Font: `text-2xl`, `font-bold`, `text-gray-900`
  - Margin: `mt-6`
- **Description:** "We've sent password reset instructions to {email}"
  - Font: `text-sm`, `text-gray-500`
  - Email displayed in `font-medium`
  - Margin: `mt-2`

#### Action Buttons
- **Primary:** "Open Email App" (full width)
  - Variant: `primary`
  - Size: `lg`
- **Secondary:** "Back to Sign In"
  - Variant: `ghost`
  - Size: `lg`
  - Margin: `mt-3`

#### Help Text
- **Text:** "Didn't receive the email? Check your spam folder or"
- **Link:** "try again"
  - Color: `text-primary-600`
  - Action: Reset `submitted` state to show form again
- **Style:** `text-xs`, `text-gray-400`, centered
- **Margin:** `mt-8`

---

## Form Validation

### Email Validation
```javascript
function validateEmail() {
  if (!email) {
    error = 'Email is required';
    return false;
  }
  if (!email.includes('@') || !email.includes('.')) {
    error = 'Please enter a valid email address';
    return false;
  }
  error = '';
  return true;
}
```

### Submit Flow
1. Validate email format
2. Set loading state
3. Simulate API call (1500ms)
4. Set `submitted = true` to show success state

---

## State Management

```javascript
let email = $state('');
let error = $state('');
let isLoading = $state(false);
let submitted = $state(false);
```

---

## Animations

### Success Icon Entrance
```css
animation: scale-in 0.3s ease-out;

@keyframes scale-in {
  from {
    transform: scale(0.8);
    opacity: 0;
  }
  to {
    transform: scale(1);
    opacity: 1;
  }
}
```

### State Transition
- Smooth fade between form and success states
- Consider using Svelte `{#if}` with `transition:fade`

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Background | surface | #ffffff |
| Form icon bg | primary-100 | #dbeafe |
| Form icon | primary-600 | #2563eb |
| Success icon bg | success-100 | #dcfce7 |
| Success icon | success-600 | #16a34a |
| Title text | gray-900 | #0f172a |
| Description text | gray-500 | #6b7280 |
| Error text | danger-500 | #ef4444 |
| Link text | primary-600 | #2563eb |
| Help text | gray-400 | #9ca3af |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| Outer padding | 24px (p-6) |
| Icon container (form) | 64px |
| Icon container (success) | 80px |
| Title margin-top | 24px (mt-6) |
| Description margin-top | 8px (mt-2) |
| Form margin-top | 32px (mt-8) |
| Submit button margin-top | 24px (mt-6) |
| Back link margin-top | 24px (mt-6) |
| Help text margin-top | 32px (mt-8) |

---

## Interactions

### Form Submission
- **Loading state:** Spinner in button, disabled interaction
- **Success:** Transition to success state
- **Error:** Display inline error message

### "Try Again" Link
- Resets `submitted` to `false`
- Preserves entered email
- Shows form again

### "Open Email App"
- Attempts to open default email client
- Use `mailto:` or deep link on mobile

### Back Navigation
- AppBar back button returns to login
- "Back to Sign In" buttons also return to login

---

## Flutter Implementation Notes

### Widgets Structure
```dart
Scaffold(
  appBar: AppBar(
    backgroundColor: Colors.transparent,
    elevation: 0,
    leading: BackButton(),
  ),
  body: SafeArea(
    child: Padding(
      padding: EdgeInsets.all(24),
      child: submitted
        ? _buildSuccessState()
        : _buildFormState(),
    ),
  ),
)
```

### State Management
```dart
class ForgotPasswordScreen extends StatefulWidget {
  @override
  State<ForgotPasswordScreen> createState() => _ForgotPasswordScreenState();
}

class _ForgotPasswordScreenState extends State<ForgotPasswordScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  bool _isLoading = false;
  bool _submitted = false;

  Future<void> _handleSubmit() async {
    if (_formKey.currentState!.validate()) {
      setState(() => _isLoading = true);
      await Future.delayed(Duration(milliseconds: 1500));
      setState(() {
        _isLoading = false;
        _submitted = true;
      });
    }
  }
}
```

### Email Client Launch
```dart
// Using url_launcher package
Future<void> _openEmailApp() async {
  final uri = Uri.parse('mailto:');
  if (await canLaunchUrl(uri)) {
    await launchUrl(uri);
  }
}
```

### Animated State Transition
```dart
AnimatedSwitcher(
  duration: Duration(milliseconds: 300),
  child: _submitted
    ? SuccessView(key: ValueKey('success'))
    : FormView(key: ValueKey('form')),
)
```

---

## Accessibility

- **Back button:** Has accessible label "Go back"
- **Form labels:** Properly associated with inputs
- **Error announcements:** Live region for validation errors
- **Success state:** Announce "Password reset email sent"
- **Touch targets:** All buttons meet 48px minimum

---

## Error States

### Invalid Email Format
- Inline error: "Please enter a valid email address"
- Input border turns red (danger-500)

### Email Not Found (API)
- Could show error: "No account found with this email"
- Or for security, show generic success message anyway

### Network Error
- Toast: "Unable to connect. Please try again."
- Keep form visible with entered data

### Rate Limiting
- Toast: "Too many requests. Please wait a moment."
- Disable submit temporarily

---

## Security Considerations

- Don't reveal if email exists in system (prevents enumeration)
- Rate limit password reset requests
- Reset tokens should expire (e.g., 1 hour)
- Log all password reset attempts
- Consider CAPTCHA for repeated attempts
