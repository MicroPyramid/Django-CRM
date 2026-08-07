/// A catalogue product, from `invoices.serializer.ProductSerializer`.
///
/// The catalogue is org-wide shared config: every member reads it (they need
/// it to build line items) and only an admin may change it. `ProductListView`
/// enforces that on the write, so the client hiding the button is UX and not
/// a guard. Invoice templates take the same shape.
class Product {
  const Product({
    required this.id,
    this.name = '',
    this.description,
    this.sku,
    this.price = 0,
    this.currency,
    this.category,
    this.isActive = true,
    this.usedOn = 0,
  });

  final String id;
  final String name;
  final String? description;
  final String? sku;
  final double price;
  final String? currency;
  final String? category;
  final bool isActive;

  /// Distinct invoices this product is a line item on. Line items denormalise
  /// their own name and price, so retiring a product never rewrites history,
  /// and this count is why a retired one is still worth listing.
  final int usedOn;

  factory Product.fromJson(Map<String, dynamic> json) {
    return Product(
      id: json['id']?.toString() ?? '',
      name: json['name'] as String? ?? '',
      description: json['description'] as String?,
      sku: json['sku'] as String?,
      price: _num(json['price']),
      currency: json['currency'] as String?,
      category: json['category'] as String?,
      isActive: json['is_active'] as bool? ?? true,
      usedOn: json['used_on'] as int? ?? 0,
    );
  }

  /// Only the fields `ProductCreateSerializer` accepts. `org` is derived from
  /// the caller's profile server-side and must never be sent.
  Map<String, dynamic> toPayload() {
    return {
      'name': name,
      if (description != null) 'description': description,
      if (sku != null) 'sku': sku,
      'price': price.toStringAsFixed(2),
      if (currency != null) 'currency': currency,
      if (category != null) 'category': category,
      'is_active': isActive,
    };
  }
}

double _num(dynamic value) {
  if (value is num) return value.toDouble();
  return double.tryParse(value?.toString() ?? '') ?? 0;
}
