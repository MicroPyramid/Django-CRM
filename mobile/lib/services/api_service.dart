import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

/// API response wrapper
class ApiResponse<T> {
  final bool success;
  final T? data;
  final String? message;
  final int statusCode;

  const ApiResponse({
    required this.success,
    this.data,
    this.message,
    required this.statusCode,
  });

  @override
  String toString() => 'ApiResponse(success: $success, statusCode: $statusCode, message: $message)';
}

/// HTTP client for BottleCRM API
///
/// Handles authentication headers, organization context,
/// and provides typed request methods.
class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  final http.Client _client = http.Client();

  // Token and org getters - will be set by AuthService
  String? _accessToken;
  String? _organizationId;

  /// Set the access token (called by AuthService)
  void setAccessToken(String? token) {
    _accessToken = token;
  }

  /// Set the organization ID (called by AuthService)
  void setOrganizationId(String? orgId) {
    _organizationId = orgId;
  }

  /// Clear authentication state
  void clearAuth() {
    _accessToken = null;
    _organizationId = null;
  }

  /// Build request headers
  Map<String, String> _buildHeaders({bool requiresAuth = true}) {
    final headers = Map<String, String>.from(ApiConfig.defaultHeaders);

    if (requiresAuth && _accessToken != null) {
      headers['Authorization'] = 'Bearer $_accessToken';
    }

    if (_organizationId != null) {
      headers['X-Organization-ID'] = _organizationId!;
    }

    return headers;
  }

  /// Parse response body
  dynamic _parseResponse(http.Response response) {
    if (response.body.isEmpty) return null;

    try {
      return jsonDecode(response.body);
    } catch (e) {
      debugPrint('Failed to parse response: ${response.body}');
      return null;
    }
  }

  /// Check if response is successful
  bool _isSuccess(int statusCode) {
    return statusCode >= 200 && statusCode < 300;
  }

  /// Extract error message from response
  String _extractErrorMessage(dynamic data, int statusCode) {
    if (data == null) return 'Request failed with status $statusCode';

    if (data is Map<String, dynamic>) {
      // Check common error field names
      if (data.containsKey('detail')) return data['detail'].toString();
      if (data.containsKey('message') && data['message'] is String) {
        return data['message'].toString();
      }

      // Handle field-specific errors (Django REST format)
      if (data.containsKey('errors') && data['errors'] is Map) {
        final errors = data['errors'] as Map<String, dynamic>;
        final errorMessages = <String>[];
        for (final entry in errors.entries) {
          final fieldName = entry.key;
          final messages = entry.value;
          if (messages is List && messages.isNotEmpty) {
            // Capitalize field name
            final fieldLabel = fieldName.replaceAll('_', ' ');
            errorMessages.add('${fieldLabel[0].toUpperCase()}${fieldLabel.substring(1)}: ${messages.first}');
          }
        }
        if (errorMessages.isNotEmpty) {
          return errorMessages.join('\n');
        }
      }

      if (data.containsKey('non_field_errors')) {
        final errors = data['non_field_errors'];
        if (errors is List && errors.isNotEmpty) {
          return errors.first.toString();
        }
      }
    }

    return 'Request failed with status $statusCode';
  }

  /// Perform GET request
  Future<ApiResponse<Map<String, dynamic>>> get(
    String url, {
    bool requiresAuth = true,
    Map<String, String>? queryParams,
  }) async {
    try {
      final uri = queryParams != null
          ? Uri.parse(url).replace(queryParameters: queryParams)
          : Uri.parse(url);

      debugPrint('GET $uri');

      final response = await _client.get(
        uri,
        headers: _buildHeaders(requiresAuth: requiresAuth),
      ).timeout(ApiConfig.connectTimeout);

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      return ApiResponse(
        success: success,
        data: success ? data as Map<String, dynamic>? : null,
        message: success ? null : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('GET error: $e');
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

  /// Perform GET request returning a list
  Future<ApiResponse<List<dynamic>>> getList(
    String url, {
    bool requiresAuth = true,
    Map<String, String>? queryParams,
  }) async {
    try {
      final uri = queryParams != null
          ? Uri.parse(url).replace(queryParameters: queryParams)
          : Uri.parse(url);

      debugPrint('GET (list) $uri');

      final response = await _client.get(
        uri,
        headers: _buildHeaders(requiresAuth: requiresAuth),
      ).timeout(ApiConfig.connectTimeout);

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      return ApiResponse(
        success: success,
        data: success ? (data as List<dynamic>?) : null,
        message: success ? null : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('GET (list) error: $e');
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

  /// Perform POST request
  Future<ApiResponse<Map<String, dynamic>>> post(
    String url,
    Map<String, dynamic> body, {
    bool requiresAuth = true,
  }) async {
    try {
      debugPrint('POST $url');
      debugPrint('Body: ${jsonEncode(body)}');

      final response = await _client.post(
        Uri.parse(url),
        headers: _buildHeaders(requiresAuth: requiresAuth),
        body: jsonEncode(body),
      ).timeout(ApiConfig.connectTimeout);

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      debugPrint('Response status: ${response.statusCode}');
      if (!success) {
        debugPrint('Response body: ${response.body}');
      }

      return ApiResponse(
        success: success,
        data: success ? data as Map<String, dynamic>? : null,
        message: success ? null : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('POST error: $e');
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

  /// Perform PUT request
  Future<ApiResponse<Map<String, dynamic>>> put(
    String url,
    Map<String, dynamic> body, {
    bool requiresAuth = true,
  }) async {
    try {
      debugPrint('PUT $url');

      final response = await _client.put(
        Uri.parse(url),
        headers: _buildHeaders(requiresAuth: requiresAuth),
        body: jsonEncode(body),
      ).timeout(ApiConfig.connectTimeout);

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      return ApiResponse(
        success: success,
        data: success ? data as Map<String, dynamic>? : null,
        message: success ? null : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('PUT error: $e');
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

  /// Perform PATCH request
  Future<ApiResponse<Map<String, dynamic>>> patch(
    String url,
    Map<String, dynamic> body, {
    bool requiresAuth = true,
  }) async {
    try {
      debugPrint('PATCH $url');

      final response = await _client.patch(
        Uri.parse(url),
        headers: _buildHeaders(requiresAuth: requiresAuth),
        body: jsonEncode(body),
      ).timeout(ApiConfig.connectTimeout);

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      return ApiResponse(
        success: success,
        data: success ? data as Map<String, dynamic>? : null,
        message: success ? null : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('PATCH error: $e');
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }

  /// Perform DELETE request
  Future<ApiResponse<Map<String, dynamic>>> delete(
    String url, {
    bool requiresAuth = true,
  }) async {
    try {
      debugPrint('DELETE $url');

      final response = await _client.delete(
        Uri.parse(url),
        headers: _buildHeaders(requiresAuth: requiresAuth),
      ).timeout(ApiConfig.connectTimeout);

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      return ApiResponse(
        success: success,
        data: success ? data as Map<String, dynamic>? : null,
        message: success ? null : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('DELETE error: $e');
      return ApiResponse(
        success: false,
        message: e.toString(),
        statusCode: 0,
      );
    }
  }
}
