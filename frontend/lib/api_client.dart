import 'dart:convert';

import 'package:fbuild_frontend/models.dart';
import 'package:http/http.dart' as http;

class ApiClient {
  ApiClient({http.Client? httpClient})
    : _httpClient = httpClient ?? http.Client();

  static const String _baseUrl = String.fromEnvironment('API_BASE_URL');

  final http.Client _httpClient;

  Uri _buildUri(String path) {
    if (_baseUrl.isNotEmpty) {
      final normalizedBase = _baseUrl.endsWith('/')
          ? _baseUrl.substring(0, _baseUrl.length - 1)
          : _baseUrl;
      return Uri.parse('$normalizedBase$path');
    }

    final baseOrigin = Uri.base.hasAuthority ? Uri.base.origin : '';
    return Uri.parse('$baseOrigin$path');
  }

  Future<List<Project>> listProjects() async {
    final response = await _httpClient.get(_buildUri('/api/projects'));
    _ensureSuccess(response);

    final payload = jsonDecode(response.body) as List<dynamic>;
    return payload
        .map((item) => Project.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  Future<Project> createProject(String repoUrl) async {
    final response = await _httpClient.post(
      _buildUri('/api/projects'),
      headers: const {'Content-Type': 'application/json'},
      body: jsonEncode({'repo_url': repoUrl}),
    );
    _ensureSuccess(response);

    return Project.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<BuildJob?> getCurrentBuild() async {
    final response = await _httpClient.get(_buildUri('/api/builds/current'));
    _ensureSuccess(response);

    if (response.body == 'null' || response.body.trim().isEmpty) {
      return null;
    }

    return BuildJob.fromJson(jsonDecode(response.body) as Map<String, dynamic>);
  }

  Future<List<BuildJob>> listQueuedBuilds() async {
    final response = await _httpClient.get(_buildUri('/api/builds/queue'));
    _ensureSuccess(response);

    final payload = jsonDecode(response.body) as List<dynamic>;
    return payload
        .map((item) => BuildJob.fromJson(item as Map<String, dynamic>))
        .toList(growable: false);
  }

  void _ensureSuccess(http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return;
    }
    throw ApiException(
      statusCode: response.statusCode,
      message: response.body.isEmpty ? 'Unexpected API error' : response.body,
    );
  }
}

class ApiException implements Exception {
  const ApiException({required this.statusCode, required this.message});

  final int statusCode;
  final String message;

  @override
  String toString() => 'ApiException($statusCode): $message';
}
