import 'dart:async';

import 'abbreviation_api.dart' show ApiCall, ServiceApiException;

export 'abbreviation_api.dart' show ApiCall, ServiceApiException;

/// 공공언어 검토 표현의 본문 위치 (구역 및 XML 문단 순번).
class PublicLanguageLocation {
  const PublicLanguageLocation({
    required this.section,
    required this.paragraph,
    this.page,
  });

  final String section;
  final int paragraph;
  final int? page;

  factory PublicLanguageLocation.fromJson(Map<dynamic, dynamic> json) =>
      PublicLanguageLocation(
        section: '${json['section'] ?? ''}',
        paragraph: (json['paragraph'] as num?)?.toInt() ?? 0,
        page: (json['page'] as num?)?.toInt(),
      );

  Map<String, dynamic> toJson() => {
    'section': section,
    'paragraph': paragraph,
    if (page != null) 'page': page,
  };
}

/// 공공언어 검토 검출 항목 (검토별·문서별·규칙별 표현 묶음).
class PublicLanguageIssue {
  const PublicLanguageIssue({
    required this.id,
    required this.sourcePath,
    required this.ruleId,
    required this.category,
    required this.source,
    required this.suggestion,
    required this.reason,
    required this.count,
    required this.examples,
    required this.locations,
  });

  final String id;
  final String sourcePath;
  final String ruleId;
  final String category;
  final String source;
  final String suggestion;
  final String reason;
  final int count;
  final List<String> examples;
  final List<PublicLanguageLocation> locations;

  factory PublicLanguageIssue.fromJson(Map<dynamic, dynamic> json) =>
      PublicLanguageIssue(
        id: '${json['id'] ?? ''}',
        sourcePath: '${json['source_path'] ?? ''}',
        ruleId: '${json['rule_id'] ?? ''}',
        category: '${json['category'] ?? ''}',
        source: '${json['source'] ?? ''}',
        suggestion: '${json['suggestion'] ?? ''}',
        reason: '${json['reason'] ?? ''}',
        count: (json['count'] as num?)?.toInt() ?? 1,
        examples: [
          for (final ex in (json['examples'] as List? ?? [])) '$ex',
        ],
        locations: [
          for (final loc in (json['locations'] as List? ?? []))
            if (loc is Map) PublicLanguageLocation.fromJson(loc),
        ],
      );
}

/// 공공언어 검토 완료 결과.
class PublicLanguageReviewResult {
  const PublicLanguageReviewResult({
    required this.reviewId,
    required this.issues,
    this.errors = const [],
  });

  final String reviewId;
  final List<PublicLanguageIssue> issues;
  final List<Map<String, dynamic>> errors;

  factory PublicLanguageReviewResult.fromJson(Map<dynamic, dynamic> json) =>
      PublicLanguageReviewResult(
        reviewId: '${json['review_id'] ?? ''}',
        issues: [
          for (final issue in (json['issues'] as List? ?? []))
            if (issue is Map) PublicLanguageIssue.fromJson(issue),
        ],
        errors: [
          for (final err in (json['errors'] as List? ?? []))
            if (err is Map) err.cast<String, dynamic>(),
        ],
      );
}

/// 개별 문서 교정 적용 결과.
class PublicLanguageApplyItemResult {
  const PublicLanguageApplyItemResult({
    required this.source,
    required this.path,
    required this.changes,
  });

  final String source;
  final String path;
  final int changes;

  factory PublicLanguageApplyItemResult.fromJson(Map<dynamic, dynamic> json) =>
      PublicLanguageApplyItemResult(
        source: '${json['source'] ?? ''}',
        path: '${json['path'] ?? ''}',
        changes: (json['changes'] as num?)?.toInt() ?? 0,
      );
}

/// 공공언어 교정 사본 생성 완료 결과.
class PublicLanguageApplyResult {
  const PublicLanguageApplyResult({
    required this.results,
    this.errors = const [],
  });

  final List<PublicLanguageApplyItemResult> results;
  final List<Map<String, dynamic>> errors;

  factory PublicLanguageApplyResult.fromJson(Map<dynamic, dynamic> json) =>
      PublicLanguageApplyResult(
        results: [
          for (final res in (json['results'] as List? ?? []))
            if (res is Map) PublicLanguageApplyItemResult.fromJson(res),
        ],
        errors: [
          for (final err in (json['errors'] as List? ?? []))
            if (err is Map) err.cast<String, dynamic>(),
        ],
      );
}

/// 공공언어 검토·교정 작업 진행 정보.
class PublicLanguageJobProgress {
  const PublicLanguageJobProgress({
    required this.stage,
    required this.percent,
    this.file = 0,
    this.total = 0,
    this.source = '',
  });

  final String stage;
  final double percent;
  final int file;
  final int total;
  final String source;

  factory PublicLanguageJobProgress.fromJson(Map<dynamic, dynamic> json) =>
      PublicLanguageJobProgress(
        stage: '${json['stage'] ?? ''}',
        percent: (json['percent'] as num?)?.toDouble() ?? 0.0,
        file: (json['file'] as num?)?.toInt() ?? 0,
        total: (json['total'] as num?)?.toInt() ?? 0,
        source: '${json['source'] ?? ''}',
      );
}

/// 공공언어 검토·교정 제외어 백엔드 API 클라이언트.
class PublicLanguageApi {
  const PublicLanguageApi(this.call);

  final ApiCall call;

  Future<Map<String, Object?>> _request(
    String method,
    List<Object?> args,
  ) async {
    final response = await call(method, args);
    if (response is! Map || response['api_version'] != 1) {
      throw const ServiceApiException(
        'API_VERSION',
        '앱 연결과 버전을 확인해 주세요.',
        true,
      );
    }
    if (response['ok'] != true) {
      final error = response['error'] as Map? ?? {};
      throw ServiceApiException(
        '${error['code'] ?? 'UNKNOWN'}',
        '${error['message'] ?? '공공언어 작업을 완료하지 못했어요.'}',
        error['recoverable'] == true,
      );
    }
    final data = response['data'];
    if (data is Map) {
      return data.cast<String, Object?>();
    }
    return const {};
  }

  /// 공공언어 검토 시작.
  /// sources 생략 시 백엔드 앱에 추가된 문서 목록 사용.
  Future<String> startReview({List<String>? sources}) async {
    final payload = <String, Object?>{
      if (sources != null) 'sources': sources,
    };
    final data = await _request('public_language', ['start', payload]);
    final jobId = '${data['job_id'] ?? ''}';
    if (jobId.isEmpty) {
      throw const ServiceApiException(
        'JOB_NOT_STARTED',
        '검토 작업을 시작하지 못했습니다.',
        true,
      );
    }
    return jobId;
  }

  /// 선택 항목 교정 사본 생성 시작.
  Future<String> applyReview(String reviewId, List<String> issueIds) async {
    final payload = <String, Object?>{
      'review_id': reviewId,
      'ids': issueIds,
    };
    final data = await _request('public_language', ['apply', payload]);
    final jobId = '${data['job_id'] ?? ''}';
    if (jobId.isEmpty) {
      throw const ServiceApiException(
        'JOB_NOT_STARTED',
        '교정 작업을 시작하지 못했습니다.',
        true,
      );
    }
    return jobId;
  }

  /// 작업 취소 요청.
  Future<void> cancelJob(String jobId) async {
    await call('cancel_job', [jobId]);
  }

  /// 작업 사건 조회 (jobs 프로토콜).
  Future<Map<String, dynamic>> getEvents({
    int afterSeq = 0,
    int max = 200,
  }) async {
    final res = await call('get_events', [afterSeq, max]);
    if (res is Map) {
      return res.cast<String, dynamic>();
    }
    return const {};
  }

  /// 교정 제외어 목록 조회.
  Future<List<String>> listExclusions() async {
    final data = await _request('proofreading_exclusions', ['list', const {}]);
    final list = data['expressions'] as List? ?? [];
    return list.map((e) => '$e').toList();
  }

  /// 교정 제외어 추가.
  Future<List<String>> addExclusions(List<String> expressions) async {
    final data = await _request('proofreading_exclusions', [
      'add',
      {'expressions': expressions},
    ]);
    final list = data['expressions'] as List? ?? [];
    return list.map((e) => '$e').toList();
  }

  /// 교정 제외어 삭제.
  Future<List<String>> deleteExclusions(List<String> expressions) async {
    final data = await _request('proofreading_exclusions', [
      'delete',
      {'expressions': expressions},
    ]);
    final list = data['expressions'] as List? ?? [];
    return list.map((e) => '$e').toList();
  }
}
