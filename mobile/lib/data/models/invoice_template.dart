/// A PDF template, from `InvoiceTemplateListSerializer`.
///
/// **This model deliberately has no `templateHtml` or `templateCss` field.**
/// Those two are org-authored HTML and CSS that WeasyPrint renders into a PDF
/// server-side, and the backend keeps them off every list, detail and nested
/// response for that reason: the moment either reaches a client that renders
/// markup, a PDF setting becomes stored XSS. Only `InvoiceTemplateEditorView`
/// returns them, it is admin-only, and this app does not call it.
///
/// So the catalogue is what mobile shows: names, colours, which one is the
/// default, and booleans describing the markup rather than the markup. The
/// editor stays on the web, where a two-pane HTML editor belongs anyway.
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

  final int usedOnInvoices;
  final String? updatedBy;

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
      usedOnInvoices: json['used_on_invoices'] as int? ?? 0,
      updatedBy: json['updated_by'] as String?,
    );
  }
}
