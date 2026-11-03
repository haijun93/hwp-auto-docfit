// 연관 문서 대화상자에 쓰는 표시 문구 만들기(위젯 없이 시험할 수 있게 순수 함수로 둔다).

/// 연관 근거 목록을 사람이 읽는 문장으로 바꾼다.
/// - Map: `text`가 있으면 그대로, 없으면 `label`(+`values`가 있으면 `label: v1, v2`)
/// - String: 그대로
/// 그 밖의 값이나 읽을 문장이 없는 Map은 건너뛰어 `{type: …}` 같은 원문이 보이지 않게 한다.
String formatRelatedReasons(Object? raw) {
  if (raw is! List) return '';
  final parts = <String>[];
  for (final reason in raw) {
    final text = _formatReason(reason);
    if (text.isNotEmpty) parts.add(text);
  }
  return parts.join(' · ');
}

String _formatReason(Object? reason) {
  if (reason is String) return reason.trim();
  if (reason is! Map) return '';
  final text = _nonEmptyString(reason['text']);
  if (text != null) return text;
  final label = _nonEmptyString(reason['label']);
  if (label == null) return '';
  final values = reason['values'];
  final shown = values is List
      ? values.where((value) => value is String || value is num).map((value) => '$value'.trim()).where((value) => value.isNotEmpty).toList()
      : const <String>[];
  return shown.isEmpty ? label : '$label: ${shown.join(', ')}';
}

/// 작성 기준일과 그 출처를 한 줄로 만든다(선택 문서·연관 항목 공통).
/// 새 키(`reference_date_source`·`reference_date_text`·`estimated_reference_date`)가 없는
/// 기존 응답은 예전처럼 날짜 또는 `기준일 없음`만 보인다.
String formatReferenceDate(Map response) {
  final date = _nonEmptyString(response['reference_date']);
  final source = _nonEmptyString(response['reference_date_source']);
  final sourceText = _nonEmptyString(response['reference_date_text']);
  if (response['reference_date_found'] == true && date != null) {
    if (source == 'quarter' || source == 'half') {
      return '작성 기준일 $date (${_estimateBasis(source, sourceText)} 표기로 추정)';
    }
    if (source == 'explicit' && sourceText != null) {
      return "작성 기준일 $date (본문 '$sourceText')";
    }
    return '작성 기준일 $date';
  }
  final estimated = _nonEmptyString(response['estimated_reference_date']);
  if (estimated != null) {
    final basis = sourceText ?? (source == 'quarter' || source == 'half' ? _estimateBasis(source, null) : null);
    return basis == null ? '기준일 없음 (추정 $estimated)' : '기준일 없음 ($basis 표기로 추정 $estimated)';
  }
  return '기준일 없음';
}

String _estimateBasis(String? source, String? sourceText) {
  if (sourceText != null) return sourceText;
  return source == 'half' ? '반기' : '분기';
}

String? _nonEmptyString(Object? value) {
  if (value is! String) return null;
  final trimmed = value.trim();
  return trimmed.isEmpty ? null : trimmed;
}
