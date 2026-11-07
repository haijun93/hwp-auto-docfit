import '../../core/api/table_units_api.dart';

/// 목록 맨 뒤에 둘 분류(백엔드 `TEMPLATE_LAST_CATEGORIES`와 같은 규칙, 띄어쓰기 무시).
const tableTemplateLastCategories = ['라벨 서식'];

String _compact(String value) =>
    value.replaceAll(RegExp(r'\s+'), '').toLowerCase();

bool isLastCategory(String category) {
  final name = _compact(category);
  return tableTemplateLastCategories.any((last) => _compact(last) == name);
}

/// 검색어와 얼마나 맞는지(작을수록 정확). 맞지 않으면 null.
///
/// 0 이름이 같음 · 1 이름이 검색어로 시작 · 2 이름에 포함 · 3 분류가 같음 · 4 분류에 포함.
/// 띄어쓰기와 대소문자는 무시한다('라벨서식'으로도 '라벨 서식'을 찾는다).
int? templateSearchRank(TableTemplateInfo template, String query) {
  final q = _compact(query);
  if (q.isEmpty) return 0;
  final name = _compact(template.name);
  final category = _compact(template.category);
  if (name == q) return 0;
  if (name.startsWith(q)) return 1;
  if (name.contains(q)) return 2;
  if (category == q) return 3;
  if (category.contains(q)) return 4;
  return null;
}

/// 검색 결과: 정확도 순서를 지키고, 같은 정도면 라벨 서식을 뒤로, 그다음은 원래 순서(안정 정렬).
List<TableTemplateInfo> rankTemplateSearch(
  List<TableTemplateInfo> templates,
  String query,
) {
  final scored = <(int, int, int, TableTemplateInfo)>[];
  for (var i = 0; i < templates.length; i++) {
    final rank = templateSearchRank(templates[i], query);
    if (rank == null) continue;
    scored.add((rank, isLastCategory(templates[i].category) ? 1 : 0, i, templates[i]));
  }
  scored.sort((a, b) {
    if (a.$1 != b.$1) return a.$1.compareTo(b.$1);
    if (a.$2 != b.$2) return a.$2.compareTo(b.$2);
    return a.$3.compareTo(b.$3);
  });
  return [for (final item in scored) item.$4];
}

/// 검색어로 거르기만 하고 순서는 그대로(즐겨찾기·최근 사용은 사용자 순서를 지킨다).
List<TableTemplateInfo> filterTemplateSearch(
  List<TableTemplateInfo> templates,
  String query,
) =>
    [for (final t in templates) if (templateSearchRank(t, query) != null) t];

/// 즐겨찾기 칩 목록: 사용자가 별표를 누른 순서(`favorites`) 그대로. 순서 정보가 없는 즐겨찾기는 뒤에 원래 순서로.
List<TableTemplateInfo> orderedFavorites(
  List<TableTemplateInfo> templates,
  List<String> favoriteOrder,
) {
  final byId = {for (final t in templates) t.id: t};
  final result = <TableTemplateInfo>[];
  final seen = <String>{};
  for (final id in favoriteOrder) {
    final template = byId[id];
    if (template != null && template.favorite && seen.add(id)) {
      result.add(template);
    }
  }
  for (final t in templates) {
    if (t.favorite && seen.add(t.id)) result.add(t);
  }
  return result;
}

/// 최근 사용 칩 목록: 최근에 쓴 순서 그대로.
List<TableTemplateInfo> orderedRecent(
  List<TableTemplateInfo> templates,
  List<String> recent,
) {
  final byId = {for (final t in templates) t.id: t};
  return [
    for (final id in recent)
      if (byId[id] != null) byId[id]!,
  ];
}
