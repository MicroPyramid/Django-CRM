/// A PDF template, from `InvoiceTemplateListSerializer`.
///
/// **This model deliberately has no `templateHtml` or `templateCss` field.**
/// Those two are org-authored HTML and CSS that WeasyPrint renders into a PDF
/// server-side, and the backend keeps them off every list, detail and nested
/// response for that reason: the moment either reaches a client that renders
/// markup, a PDF setting becomes stored XSS. Only `InvoiceTemplateEditorView`
/// returns them, it is admin-only, and this app does not call it.
///
/// That absence is what makes the phone's editor safe rather than what stops
/// it. Every other field on a template is ordinary form input, all of it is on
/// the list response, and `PUT /invoices/templates/<id>/` is partial. So the
/// phone can pre-fill from the row it already has, write the ordinary fields
/// back, and never name the two markup fields in either direction. A save from
/// here leaves whatever the web editor last stored untouched.
class InvoiceTemplate {
  const InvoiceTemplate({
    required this.id,
    this.name = '',
    this.isDefault = false,
    this.primaryColor,
    this.secondaryColor,
    this.hasLogo = false,
    this.hasCustomHtml = false,
    this.hasCustomCss = false,
    this.defaultNotes = '',
    this.defaultTerms = '',
    this.footerText = '',
    this.usedOnInvoices = 0,
    this.updatedBy,
  });

  final String id;
  final String name;
  final bool isDefault;
  final String? primaryColor;
  final String? secondaryColor;
  final bool hasLogo;

  /// Whether custom markup exists, never what it says.
  final bool hasCustomHtml;
  final bool hasCustomCss;

  /// The boilerplate a new invoice starts from. Plain text, editable here.
  final String defaultNotes;
  final String defaultTerms;
  final String footerText;

  final int usedOnInvoices;
  final String? updatedBy;

  /// The model defaults, used when a form has nothing to pre-fill from.
  static const String defaultPrimaryColor = '#3B82F6';
  static const String defaultSecondaryColor = '#1E40AF';

  factory InvoiceTemplate.fromJson(Map<String, dynamic> json) {
    return InvoiceTemplate(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      isDefault: json['is_default'] as bool? ?? false,
      primaryColor: json['primary_color'] as String?,
      secondaryColor: json['secondary_color'] as String?,
      hasLogo: json['has_logo'] as bool? ?? false,
      hasCustomHtml: json['has_custom_html'] as bool? ?? false,
      hasCustomCss: json['has_custom_css'] as bool? ?? false,
      defaultNotes: json['default_notes'] as String? ?? '',
      defaultTerms: json['default_terms'] as String? ?? '',
      footerText: json['footer_text'] as String? ?? '',
      usedOnInvoices: json['used_on_invoices'] as int? ?? 0,
      updatedBy: json['updated_by'] as String?,
    );
  }
}

/// What the form screen submits.
///
/// A separate type from [InvoiceTemplate] because the two carry different
/// things: the model holds what a template *is*, including the read-only
/// `has_custom_html` and `used_on_invoices` the list computes, while this holds
/// only the fields a person may write. Sending a model back would mean deciding
/// per field whether it is writable at the call site, which is how a read-only
/// field ends up in a payload.
class InvoiceTemplateDraft {
  const InvoiceTemplateDraft({
    required this.name,
    required this.primaryColor,
    required this.secondaryColor,
    this.defaultNotes = '',
    this.defaultTerms = '',
    this.footerText = '',
    this.isDefault,
  });

  final String name;
  final String primaryColor;
  final String secondaryColor;
  final String defaultNotes;
  final String defaultTerms;
  final String footerText;

  /// Null on an edit, where this field is deliberately not the form's to write.
  ///
  /// `is_default` is a singleton: the model clears the flag on every other
  /// template in the org inside a transaction. Carrying an off switch through
  /// an unrelated save would demote the org's current default and leave it with
  /// none, so the list owns it and both edit forms leave it out. The web's edit
  /// form does the same, for the same reason.
  final bool? isDefault;

  /// `#RRGGBB`, the only form the API accepts. Matches the regex in
  /// `_validate_hex_color` and the one in the web's `templates.js`.
  static final RegExp hexColor = RegExp(r'^#[0-9a-fA-F]{6}$');

  static bool isHexColor(String value) => hexColor.hasMatch(value.trim());

  Map<String, dynamic> toPayload() {
    return <String, dynamic>{
      'name': name.trim(),
      'primary_color': primaryColor,
      'secondary_color': secondaryColor,
      'default_notes': defaultNotes,
      'default_terms': defaultTerms,
      'footer_text': footerText,
      if (isDefault != null) 'is_default': isDefault,
    };
  }

  /// The same payload as multipart fields, for the calls that carry a logo.
  ///
  /// `http.MultipartRequest.fields` is `Map<String, String>`, so `is_default`
  /// arrives as "true" or "false". DRF's `BooleanField` reads both, and it is
  /// the same spelling the web sends through `FormData`.
  Map<String, String> toMultipartFields() {
    return toPayload().map((key, value) => MapEntry(key, '$value'));
  }
}
