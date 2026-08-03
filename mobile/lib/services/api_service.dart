import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';

/// Callback invoked when an authenticated request gets a 401, should hit the
/// refresh endpoint and update the ApiService's access token, returning true
/// if the new token is ready and the original request can be retried.
typedef RefreshTokenCallback = Future<bool> Function();

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
  String toString() =>
      'ApiResponse(success: $success, statusCode: $statusCode, message: $message)';
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

  // Refresh wiring. AuthService registers `refreshAccessToken` here during
  // initialize(); `_refreshInFlight` coalesces concurrent refresh attempts so
  // a burst of expired-token requests only fires one network call to the
  // refresh endpoint.
  RefreshTokenCallback? _refreshCallback;
  Future<bool>? _refreshInFlight;

  /// Set the access token (called by AuthService)
  void setAccessToken(String? token) {
    _accessToken = token;
  }

  /// Set the organization ID (called by AuthService)
  void setOrganizationId(String? orgId) {
    _organizationId = orgId;
  }

  /// Register the refresh-token callback (called once by AuthService.initialize).
  /// Passing null disables auto-refresh.
  void setRefreshCallback(RefreshTokenCallback? callback) {
    _refreshCallback = callback;
  }

  /// Clear authentication state
  void clearAuth() {
    _accessToken = null;
    _organizationId = null;
  }

  /// Run the registered refresh callback at most once per concurrent burst.
  /// Returns true if the access token was refreshed and the caller should
  /// retry the original request.
  Future<bool> _refreshAccessToken() async {
    final cb = _refreshCallback;
    if (cb == null) return false;
    final existing = _refreshInFlight;
    if (existing != null) return existing;
    final fut = cb();
    _refreshInFlight = fut;
    try {
      return await fut;
    } finally {
      _refreshInFlight = null;
    }
  }

  /// Send an HTTP request and transparently retry once on 401 after refreshing
  /// the access token. The `send` closure must be safe to invoke twice, every
  /// caller below builds a fresh request inside it.
  Future<http.Response> _sendWithRetry({
    required bool requiresAuth,
    required Future<http.Response> Function(Map<String, String> headers) send,
  }) async {
    var response = await send(_buildHeaders(requiresAuth: requiresAuth))
        .timeout(ApiConfig.connectTimeout);

    if (requiresAuth &&
        response.statusCode == 401 &&
        _accessToken != null &&
        _refreshCallback != null) {
      final refreshed = await _refreshAccessToken();
      if (refreshed) {
        response = await send(_buildHeaders(requiresAuth: requiresAuth))
            .timeout(ApiConfig.connectTimeout);
      }
    }
    return response;
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

      // Handle backend-shaped errors. The Django views use two flavors:
      //   {"errors": "plain string"}: top-level error message
      //   {"errors": {"field": ["msg", ...]}}: DRF field-level errors
      if (data.containsKey('errors')) {
        final errors = data['errors'];
        if (errors is String && errors.isNotEmpty) return errors;
        if (errors is Map) {
          final errorMessages = <String>[];
          for (final entry in errors.entries) {
            final fieldName = entry.key.toString();
            final messages = entry.value;
            final fieldLabel = fieldName.replaceAll('_', ' ');
            final cap = fieldLabel.isEmpty
                ? fieldLabel
                : '${fieldLabel[0].toUpperCase()}${fieldLabel.substring(1)}';
            if (messages is List && messages.isNotEmpty) {
              errorMessages.add('$cap: ${messages.first}');
            } else if (messages is String && messages.isNotEmpty) {
              errorMessages.add('$cap: $messages');
            }
          }
          if (errorMessages.isNotEmpty) return errorMessages.join('\n');
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

      final response = await _sendWithRetry(
        requiresAuth: requiresAuth,
        send: (headers) => _client.get(uri, headers: headers),
      );

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      return ApiResponse(
        success: success,
        data: success ? data as Map<String, dynamic>? : null,
        message: success
            ? null
            : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('GET error: $e');
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
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

      final response = await _sendWithRetry(
        requiresAuth: requiresAuth,
        send: (headers) => _client.get(uri, headers: headers),
      );

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      return ApiResponse(
        success: success,
        data: success ? (data as List<dynamic>?) : null,
        message: success
            ? null
            : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('GET (list) error: $e');
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
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

      final uri = Uri.parse(url);
      final encoded = jsonEncode(body);
      final response = await _sendWithRetry(
        requiresAuth: requiresAuth,
        send: (headers) => _client.post(uri, headers: headers, body: encoded),
      );

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      debugPrint('Response status: ${response.statusCode}');
      if (!success) {
        debugPrint('Response body: ${response.body}');
      }

      return ApiResponse(
        success: success,
        // Preserve the parsed body on failure too so callers can read
        // structured error fields (e.g. validation `errors` map, 409 conflict
        // payloads like {running_case_id}). Callers must still check
        // `success` before treating the data as a happy-path payload.
        data: data is Map<String, dynamic> ? data : null,
        message: success
            ? null
            : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('POST error: $e');
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
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

      final uri = Uri.parse(url);
      final encoded = jsonEncode(body);
      final response = await _sendWithRetry(
        requiresAuth: requiresAuth,
        send: (headers) => _client.put(uri, headers: headers, body: encoded),
      );

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      return ApiResponse(
        success: success,
        // Preserve the parsed body on failure too. See POST for rationale.
        data: data is Map<String, dynamic> ? data : null,
        message: success
            ? null
            : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('PUT error: $e');
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
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

      final uri = Uri.parse(url);
      final encoded = jsonEncode(body);
      final response = await _sendWithRetry(
        requiresAuth: requiresAuth,
        send: (headers) => _client.patch(uri, headers: headers, body: encoded),
      );

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      return ApiResponse(
        success: success,
        data: success ? data as Map<String, dynamic>? : null,
        message: success
            ? null
            : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('PATCH error: $e');
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }

  /// Perform DELETE request
  Future<ApiResponse<Map<String, dynamic>>> delete(
    String url, {
    bool requiresAuth = true,
  }) async {
    try {
      debugPrint('DELETE $url');

      final uri = Uri.parse(url);
      final response = await _sendWithRetry(
        requiresAuth: requiresAuth,
        send: (headers) => _client.delete(uri, headers: headers),
      );

      final data = _parseResponse(response);
      final success = _isSuccess(response.statusCode);

      return ApiResponse(
        success: success,
        data: success ? data as Map<String, dynamic>? : null,
        message: success
            ? null
            : _extractErrorMessage(data, response.statusCode),
        statusCode: response.statusCode,
      );
    } catch (e) {
      debugPrint('DELETE error: $e');
      return ApiResponse(success: false, message: e.toString(), statusCode: 0);
    }
  }
}
