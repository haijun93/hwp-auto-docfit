import 'package:docfit_ui/core/api/table_units_api.dart';
import 'package:docfit_ui/features/table_units/table_template_order.dart';
import 'package:flutter_test/flutter_test.dart';

TableTemplateInfo t(
  String id,
  String category,
  String name, {
  bool favorite = false,
}) => TableTemplateInfo(
  id: id,
  category: category,
  name: name,
  rows: 1,
  cols: 1,
  favorite: favorite,
  units: const TableUnits(),
);

List<String> ids(List<TableTemplateInfo> list) => [for (final x in list) x.id];

void main() {
  final templates = [
    t('a', '표(가로)', '표(가로) · 모양 1'),
    t('l1', '라벨 서식', '라벨 서식 · 모양 1', favorite: true),
    t('b', '현황표(가로)', '현황표(가로) · 모양 1', favorite: true),
    t('l2', '라벨 서식', '라벨 서식 · 모양 2'),
    t('c', '서식', '모양 1 서식', favorite: true),
  ];

  test('라벨 서식 분류 판정은 띄어쓰기를 무시한다', () {
    expect(isLastCategory('라벨 서식'), isTrue);
    expect(isLastCategory('라벨서식'), isTrue);
    expect(isLastCategory('표(가로)'), isFalse);
  });

  test('검색 정확도 순서: 이름 같음 < 이름 시작 < 이름 포함 < 분류', () {
    final list = [
      t('cat', '모양 1', '다른 표'),
      t('contains', '가', '표 모양 1'),
      t('starts', '가', '모양 1 표'),
      t('exact', '가', '모양 1'),
    ];
    expect(ids(rankTemplateSearch(list, '모양 1')), [
      'exact',
      'starts',
      'contains',
      'cat',
    ]);
    expect(templateSearchRank(list.first, '없는말'), isNull);
  });

  test('같은 정확도면 라벨 서식이 뒤, 나머지는 원래 순서', () {
    // '모양 1'은 a·l1·b 모두 이름 포함(2), c는 이름 시작(1).
    expect(ids(rankTemplateSearch(templates, '모양 1')), ['c', 'a', 'b', 'l1']);
    expect(ids(rankTemplateSearch(templates, '모양')), [
      'c',
      'a',
      'b',
      'l1',
      'l2',
    ]);
    // 라벨 서식이 더 정확하면 앞에 둔다(정확도가 먼저).
    expect(ids(rankTemplateSearch(templates, '라벨서식 · 모양 2')), ['l2']);
    expect(ids(rankTemplateSearch(templates, '라벨')).first, 'l1');
  });

  test('즐겨찾기는 사용자가 누른 순서 그대로, 라벨 서식도 뒤로 보내지 않는다', () {
    expect(ids(orderedFavorites(templates, ['l1', 'c', 'b'])), [
      'l1',
      'c',
      'b',
    ]);
    // 순서 정보가 없는 즐겨찾기는 뒤에 원래 순서로, 해제된 id는 무시.
    expect(ids(orderedFavorites(templates, ['c', 'a'])), ['c', 'l1', 'b']);
  });

  test('최근 사용은 최근 순서 그대로, 검색은 거르기만 한다', () {
    final recent = orderedRecent(templates, ['l2', 'missing', 'a', 'c']);
    expect(ids(recent), ['l2', 'a', 'c']);
    // c(이름이 '서식'으로 끝남)가 l2(분류가 라벨 서식)보다 정확해도 최근 순서를 지킨다.
    expect(ids(filterTemplateSearch(recent, '서식')), ['l2', 'c']);
  });
}
