// domain5_api_client.dart
// Drop this file into your Flutter project (lib/services/)
// Add to pubspec.yaml:  http: ^1.2.0

import 'dart:convert';
import 'package:http/http.dart' as http;

class Domain5ApiClient {
  final String baseUrl;
  Domain5ApiClient({required this.baseUrl});

  // ─── Sub-test A helpers ────────────────────────────────────────────────

  /// Fetch a server-side random delay (ms) before showing the stimulus circle.
  Future<int> getTrialDelay(int trialNumber) async {
    final uri = Uri.parse('$baseUrl/api/v1/reaction-time/trial-timing')
        .replace(queryParameters: {'trial_number': '$trialNumber'});
    final res = await http.get(uri);
    _checkStatus(res);
    return (jsonDecode(res.body)['delay_ms'] as int);
  }

  /// Submit 10 RT readings and receive full analysis.
  Future<RTResult> submitReactionTime({
    required String patientId,
    required String ageGroup,
    required List<double> reactionTimesMs,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/v1/reaction-time/submit'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'patient_id': patientId,
        'age_group': ageGroup,
        'reaction_times_ms': reactionTimesMs,
      }),
    );
    _checkStatus(res);
    return RTResult.fromJson(jsonDecode(res.body));
  }

  // ─── Sub-test B helpers ────────────────────────────────────────────────

  /// Get a random digit sequence of [length] digits (2–10).
  Future<DigitSequence> getDigitSequence(int length) async {
    final uri = Uri.parse('$baseUrl/api/v1/digit-span/sequence')
        .replace(queryParameters: {'length': '$length'});
    final res = await http.get(uri);
    _checkStatus(res);
    return DigitSequence.fromJson(jsonDecode(res.body));
  }

  /// Submit forward and backward span scores.
  Future<DigitSpanResult> submitDigitSpan({
    required String patientId,
    required int forwardSpan,
    required int backwardSpan,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/v1/digit-span/submit'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'patient_id': patientId,
        'forward_span': forwardSpan,
        'backward_span': backwardSpan,
      }),
    );
    _checkStatus(res);
    return DigitSpanResult.fromJson(jsonDecode(res.body));
  }

  // ─── Combined Domain 5 ────────────────────────────────────────────────

  Future<Domain5Result> submitDomain5({
    required String patientId,
    required String ageGroup,
    required List<double> reactionTimesMs,
    required int forwardSpan,
    required int backwardSpan,
  }) async {
    final res = await http.post(
      Uri.parse('$baseUrl/api/v1/domain5/submit'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'patient_id': patientId,
        'age_group': ageGroup,
        'reaction_times_ms': reactionTimesMs,
        'forward_span': forwardSpan,
        'backward_span': backwardSpan,
      }),
    );
    _checkStatus(res);
    return Domain5Result.fromJson(jsonDecode(res.body));
  }

  void _checkStatus(http.Response res) {
    if (res.statusCode != 200) {
      throw ApiException(res.statusCode, res.body);
    }
  }
}

// ─── Data models ──────────────────────────────────────────────────────────

class Classification {
  final String severity; // 'normal' | 'watch' | 'concern' | 'critical'
  final String label;

  Classification({required this.severity, required this.label});

  factory Classification.fromJson(Map<String, dynamic> j) =>
      Classification(severity: j['severity'], label: j['label']);

  bool get isNormal  => severity == 'normal';
  bool get isWatch   => severity == 'watch';
  bool get isConcern => severity == 'concern';
  bool get isCritical => severity == 'critical';
}

class RTResult {
  final String patientId;
  final String ageGroup;
  final List<double> reactionTimesMs;
  final double medianMs;
  final double meanMs;
  final double sdMs;
  final double minMs;
  final double maxMs;
  final Classification medianClassification;
  final Classification variabilityClassification;
  final String timestamp;

  RTResult({
    required this.patientId,
    required this.ageGroup,
    required this.reactionTimesMs,
    required this.medianMs,
    required this.meanMs,
    required this.sdMs,
    required this.minMs,
    required this.maxMs,
    required this.medianClassification,
    required this.variabilityClassification,
    required this.timestamp,
  });

  factory RTResult.fromJson(Map<String, dynamic> j) => RTResult(
        patientId: j['patient_id'],
        ageGroup: j['age_group'],
        reactionTimesMs: (j['reaction_times_ms'] as List).cast<double>(),
        medianMs: (j['median_ms'] as num).toDouble(),
        meanMs: (j['mean_ms'] as num).toDouble(),
        sdMs: (j['sd_ms'] as num).toDouble(),
        minMs: (j['min_ms'] as num).toDouble(),
        maxMs: (j['max_ms'] as num).toDouble(),
        medianClassification: Classification.fromJson(j['median_classification']),
        variabilityClassification: Classification.fromJson(j['variability_classification']),
        timestamp: j['timestamp'],
      );
}

class DigitSequence {
  final int length;
  final List<int> sequence;
  final String displayString;

  DigitSequence({required this.length, required this.sequence, required this.displayString});

  factory DigitSequence.fromJson(Map<String, dynamic> j) => DigitSequence(
        length: j['length'],
        sequence: (j['sequence'] as List).cast<int>(),
        displayString: j['display_string'],
      );
}

class DigitSpanResult {
  final String patientId;
  final int forwardSpan;
  final int backwardSpan;
  final int gap;
  final Classification forwardClassification;
  final Classification backwardClassification;
  final Classification gapClassification;
  final String summary;
  final String timestamp;

  DigitSpanResult({
    required this.patientId,
    required this.forwardSpan,
    required this.backwardSpan,
    required this.gap,
    required this.forwardClassification,
    required this.backwardClassification,
    required this.gapClassification,
    required this.summary,
    required this.timestamp,
  });

  factory DigitSpanResult.fromJson(Map<String, dynamic> j) => DigitSpanResult(
        patientId: j['patient_id'],
        forwardSpan: j['forward_span'],
        backwardSpan: j['backward_span'],
        gap: j['gap'],
        forwardClassification: Classification.fromJson(j['forward_classification']),
        backwardClassification: Classification.fromJson(j['backward_classification']),
        gapClassification: Classification.fromJson(j['gap_classification']),
        summary: j['summary'],
        timestamp: j['timestamp'],
      );
}

class Domain5Result {
  final String patientId;
  final RTResult reactionTime;
  final DigitSpanResult digitSpan;
  final String domainSummary;
  final String timestamp;

  Domain5Result({
    required this.patientId,
    required this.reactionTime,
    required this.digitSpan,
    required this.domainSummary,
    required this.timestamp,
  });

  factory Domain5Result.fromJson(Map<String, dynamic> j) => Domain5Result(
        patientId: j['patient_id'],
        reactionTime: RTResult.fromJson(j['reaction_time']),
        digitSpan: DigitSpanResult.fromJson(j['digit_span']),
        domainSummary: j['domain_summary'],
        timestamp: j['timestamp'],
      );
}

class ApiException implements Exception {
  final int statusCode;
  final String body;
  ApiException(this.statusCode, this.body);

  @override
  String toString() => 'ApiException($statusCode): $body';
}
