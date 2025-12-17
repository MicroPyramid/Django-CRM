# Lead Create Screen

**Route:** `/leads/create`
**File:** `src/routes/(app)/leads/create/+page.svelte`
**Layout:** App layout (MobileShell)

---

## Overview

The lead creation screen provides a form for adding new leads to the CRM. It features a clean, mobile-optimized layout with floating label inputs, dropdown selectors, and an optional advanced section for additional fields.

---

## Screen Purpose

- Capture new lead information
- Validate required fields
- Assign to team members
- Set priority and tags
- Save lead to database

---

## UI Structure

### App Bar
- **Component:** `AppBar`
- **Title:** "New Lead"
- **Props:** `showBack={true}`
- **Trailing:** Save/checkmark button (optional, or use form button)

### Form Content
- **Layout:** Vertical scroll
- **Padding:** `p-6`
- **Gap:** `gap-6` between sections

---

## Form Sections

### Basic Information Section

#### Section Header
- **Title:** "Basic Information"
- **Style:** `text-sm`, `font-semibold`, `text-gray-500`, `uppercase`, `tracking-wide`
- **Margin:** `mb-4`

#### Fields

**Full Name** (Required)
- **Component:** `InputFloatingLabel`
- **Label:** "Full Name"
- **Type:** `text`
- **Icon:** User (lucide)
- **Validation:** Required, min 2 characters
- **Placeholder:** "John Doe"

**Company** (Required)
- **Component:** `InputFloatingLabel`
- **Label:** "Company"
- **Type:** `text`
- **Icon:** Building2 (lucide)
- **Validation:** Required
- **Placeholder:** "Acme Inc."

**Email** (Required)
- **Component:** `InputFloatingLabel`
- **Label:** "Email"
- **Type:** `email`
- **Icon:** Mail (lucide)
- **Validation:** Required, valid email format
- **Placeholder:** "john@acme.com"

**Phone** (Optional)
- **Component:** `InputFloatingLabel`
- **Label:** "Phone"
- **Type:** `tel`
- **Icon:** Phone (lucide)
- **Validation:** Optional, valid phone format
- **Placeholder:** "+1 (555) 123-4567"

---

### Classification Section

#### Section Header
- **Title:** "Classification"
- **Style:** Same as above
- **Margin:** `mt-8`, `mb-4`

#### Fields

**Status** (Required)
- **Component:** Custom select/dropdown
- **Label:** "Status"
- **Options:**
  - New (default)
  - Contacted
  - Qualified
  - Lost
- **Style:** Full-width dropdown button

**Source** (Required)
- **Component:** Custom select/dropdown
- **Label:** "Source"
- **Options:**
  - Website
  - Referral
  - LinkedIn
  - Cold Call
  - Trade Show
- **Style:** Full-width dropdown button

**Priority**
- **Component:** Segmented control or radio buttons
- **Label:** "Priority"
- **Options:**
  - Low
  - Medium (default)
  - High
- **Visual:** Color-coded segments

---

### Assignment Section

#### Section Header
- **Title:** "Assignment"
- **Style:** Same as above
- **Margin:** `mt-8`, `mb-4`

#### Fields

**Assigned To**
- **Component:** User picker dropdown
- **Label:** "Assign to team member"
- **Options:** List of team members with avatars
- **Default:** Current user
- **Display:** Avatar + Name in selected state

---

### Advanced Section (Collapsible)

#### Toggle Header
- **Layout:** Row with chevron icon
- **Text:** "Advanced Options"
- **Icon:** ChevronDown/ChevronUp (rotates)
- **Style:** Tappable, `text-sm`, `text-gray-600`

#### Collapsed by default

#### Expanded Content

**Tags**
- **Component:** Tag input or multi-select
- **Label:** "Tags"
- **Behavior:** Add tags by typing and pressing enter
- **Display:** Chip list with remove buttons
- **Suggestions:** Common tags dropdown

**Notes**
- **Component:** Textarea
- **Label:** "Notes"
- **Placeholder:** "Add any additional notes about this lead..."
- **Rows:** 4
- **Character limit:** 500 (optional)

---

### Submit Section

#### Submit Button
- **Component:** `Button`
- **Text:** "Create Lead"
- **Variant:** `primary`
- **Size:** `lg`
- **Props:** `fullWidth`, loading state
- **Margin:** `mt-8`

#### Cancel Link
- **Text:** "Cancel"
- **Style:** `text-gray-500`, centered
- **Action:** Navigate back
- **Margin:** `mt-4`

---

## Form State

```javascript
let formData = $state({
  name: '',
  company: '',
  email: '',
  phone: '',
  status: 'new',
  source: 'website',
  priority: 'medium',
  assignedTo: currentUser.id,
  tags: [],
  notes: ''
});

let errors = $state({
  name: '',
  company: '',
  email: '',
  phone: ''
});

let isLoading = $state(false);
let showAdvanced = $state(false);
```

---

## Validation Rules

```javascript
function validateForm() {
  let isValid = true;

  // Name validation
  if (!formData.name.trim()) {
    errors.name = 'Name is required';
    isValid = false;
  } else if (formData.name.trim().length < 2) {
    errors.name = 'Name must be at least 2 characters';
    isValid = false;
  } else {
    errors.name = '';
  }

  // Company validation
  if (!formData.company.trim()) {
    errors.company = 'Company is required';
    isValid = false;
  } else {
    errors.company = '';
  }

  // Email validation
  if (!formData.email.trim()) {
    errors.email = 'Email is required';
    isValid = false;
  } else if (!isValidEmail(formData.email)) {
    errors.email = 'Please enter a valid email';
    isValid = false;
  } else {
    errors.email = '';
  }

  // Phone validation (optional but must be valid if provided)
  if (formData.phone && !isValidPhone(formData.phone)) {
    errors.phone = 'Please enter a valid phone number';
    isValid = false;
  } else {
    errors.phone = '';
  }

  return isValid;
}

function isValidEmail(email) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function isValidPhone(phone) {
  return /^[\d\s\-\+\(\)]{10,}$/.test(phone);
}
```

---

## Form Submission

```javascript
async function handleSubmit() {
  if (!validateForm()) return;

  isLoading = true;

  try {
    const newLead = {
      id: generateId(),
      ...formData,
      createdAt: new Date().toISOString()
    };

    // Add to store (or API call)
    leads.push(newLead);

    // Navigate back to leads list
    goto('/leads');

    // Show success toast
    showToast('Lead created successfully');
  } catch (error) {
    showToast('Failed to create lead', 'error');
  } finally {
    isLoading = false;
  }
}
```

---

## Color Specifications

| Element | Color | Hex Value |
|---------|-------|-----------|
| Background | surface | #ffffff |
| Section title | gray-500 | #6b7280 |
| Input border default | gray-200 | #e5e7eb |
| Input border focus | primary-500 | #3b82f6 |
| Input border error | danger-500 | #ef4444 |
| Label text | gray-700 | #374151 |
| Placeholder text | gray-400 | #9ca3b8 |
| Error text | danger-500 | #ef4444 |
| Submit button | primary-600 | #2563eb |
| Cancel text | gray-500 | #6b7280 |

---

## Spacing & Layout

| Element | Value |
|---------|-------|
| Form padding | 24px (p-6) |
| Section gap | 32px (mt-8) |
| Section title margin-bottom | 16px (mb-4) |
| Field gap | 16px (gap-4) |
| Submit margin-top | 32px (mt-8) |
| Cancel margin-top | 16px (mt-4) |

---

## Interactions

### Input Focus
- Border color: primary-500
- Label floats up with animation
- Focus ring appears

### Dropdown Selection
- Tap to open options
- Options appear in bottom sheet or dropdown
- Selected option shows checkmark
- Tapping outside closes dropdown

### Tag Input
- Type tag name
- Press enter or comma to add
- Tap X on tag chip to remove
- Show autocomplete suggestions

### Advanced Toggle
- Tap header to expand/collapse
- Animate chevron rotation
- Slide content in/out

### Form Submit
- Validate all fields
- Show loading state on button
- Navigate on success
- Show error messages on failure

### Cancel/Back
- Confirm if form has unsaved changes
- Navigate back to leads list

---

## Flutter Implementation Notes

### Form Screen Structure
```dart
class LeadCreateScreen extends StatefulWidget {
  @override
  State<LeadCreateScreen> createState() => _LeadCreateScreenState();
}

class _LeadCreateScreenState extends State<LeadCreateScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _companyController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _notesController = TextEditingController();

  String _status = 'new';
  String _source = 'website';
  String _priority = 'medium';
  String? _assignedTo;
  List<String> _tags = [];
  bool _showAdvanced = false;
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('New Lead'),
        leading: BackButton(),
      ),
      body: Form(
        key: _formKey,
        child: SingleChildScrollView(
          padding: EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildSectionTitle('Basic Information'),
              _buildBasicFields(),
              SizedBox(height: 32),
              _buildSectionTitle('Classification'),
              _buildClassificationFields(),
              SizedBox(height: 32),
              _buildSectionTitle('Assignment'),
              _buildAssignmentField(),
              SizedBox(height: 16),
              _buildAdvancedSection(),
              SizedBox(height: 32),
              _buildSubmitButton(),
              SizedBox(height: 16),
              _buildCancelButton(),
            ],
          ),
        ),
      ),
    );
  }
}
```

### Section Title Widget
```dart
Widget _buildSectionTitle(String title) {
  return Padding(
    padding: EdgeInsets.only(bottom: 16),
    child: Text(
      title.toUpperCase(),
      style: TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w600,
        color: Colors.grey[500],
        letterSpacing: 1.2,
      ),
    ),
  );
}
```

### Priority Selector
```dart
Widget _buildPrioritySelector() {
  return Row(
    children: ['low', 'medium', 'high'].map((priority) {
      final isSelected = _priority == priority;
      return Expanded(
        child: GestureDetector(
          onTap: () => setState(() => _priority = priority),
          child: Container(
            padding: EdgeInsets.symmetric(vertical: 12),
            decoration: BoxDecoration(
              color: isSelected ? _getPriorityColor(priority) : Colors.grey[100],
              borderRadius: BorderRadius.horizontal(
                left: priority == 'low' ? Radius.circular(8) : Radius.zero,
                right: priority == 'high' ? Radius.circular(8) : Radius.zero,
              ),
            ),
            child: Text(
              priority.capitalize(),
              textAlign: TextAlign.center,
              style: TextStyle(
                color: isSelected ? Colors.white : Colors.grey[700],
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ),
      );
    }).toList(),
  );
}
```

### Tag Input Widget
```dart
class TagInput extends StatefulWidget {
  final List<String> tags;
  final Function(List<String>) onChanged;

  @override
  State<TagInput> createState() => _TagInputState();
}

class _TagInputState extends State<TagInput> {
  final _controller = TextEditingController();

  void _addTag(String tag) {
    if (tag.isNotEmpty && !widget.tags.contains(tag)) {
      widget.onChanged([...widget.tags, tag]);
      _controller.clear();
    }
  }

  void _removeTag(String tag) {
    widget.onChanged(widget.tags.where((t) => t != tag).toList());
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: widget.tags.map((tag) => Chip(
            label: Text(tag),
            deleteIcon: Icon(Icons.close, size: 16),
            onDeleted: () => _removeTag(tag),
          )).toList(),
        ),
        SizedBox(height: 8),
        TextField(
          controller: _controller,
          decoration: InputDecoration(
            hintText: 'Add tag...',
            border: OutlineInputBorder(),
          ),
          onSubmitted: _addTag,
        ),
      ],
    );
  }
}
```

---

## Accessibility

- **Labels:** All inputs have visible labels
- **Errors:** Errors announced immediately
- **Required fields:** Marked with asterisk
- **Focus order:** Logical tab sequence
- **Submit button:** Disabled state communicated

---

## Error Handling

### Validation Errors
- Show inline below field
- Red border on invalid field
- Clear error when user starts typing

### API Errors
- Show toast notification
- Keep form data intact
- Enable retry

### Network Errors
- Show offline indicator
- Allow save as draft (optional)
- Retry when online

---

## Unsaved Changes Warning

```dart
Future<bool> _onWillPop() async {
  if (_hasUnsavedChanges()) {
    return await showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Discard changes?'),
        content: Text('You have unsaved changes. Are you sure you want to leave?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text('Discard'),
          ),
        ],
      ),
    ) ?? false;
  }
  return true;
}
```
