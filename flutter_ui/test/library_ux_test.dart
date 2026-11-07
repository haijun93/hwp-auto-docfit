import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:docfit_ui/features/library/library_api.dart';
import 'package:docfit_ui/features/library/library_layout.dart';
import 'package:docfit_ui/features/library/library_screen.dart';

/// 실제로 파일을 열지 않는 가짜 실행기.
class _FakeOpener implements LibraryOpenApi {
  _FakeOpener([this.respond]);
  final LibraryOpenResult Function(String source, bool confirmed)? respond;
  final calls = <({String? itemId, LibraryItemKind kind, String source, bool confirmed})>[];

  @override
  Future<LibraryOpenResult> openItem({String? itemId, required LibraryItemKind kind, required String source, bool confirmed = false}) async {
    calls.add((itemId: itemId, kind: kind, source: source, confirmed: confirmed));
    return respond?.call(source, confirmed) ?? const LibraryOpenResult(ok: true);
  }
}

/// [failOnMove]번째 moveItem 호출에서 실패하는 API(일괄 이동 되돌리기 시험).
class _FlakyMoveApi extends InMemoryLibraryApi {
  int moves = 0;
  int? failOnMove;

  @override
  Future<LibraryItem> moveItem(String itemId, {required String boxId, required LibrarySpace space, required double x, required double y}) {
    moves++;
    if (failOnMove != null && moves == failOnMove) throw StateError('저장 실패');
    return super.moveItem(itemId, boxId: boxId, space: space, x: x, y: y);
  }
}

Future<void> _pumpScreen(WidgetTester tester, LibraryApi api, {LibraryOpenApi? opener, Size size = const Size(1400, 900)}) async {
  tester.view.physicalSize = size;
  tester.view.devicePixelRatio = 1;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(MaterialApp(home: LibraryScreen(api: api, openApi: opener)));
  await tester.pumpAndSettle();
}

Finder _card(String id) => find.byKey(ValueKey('libraryItem-$id'));

Future<void> _doubleTap(WidgetTester tester, Finder finder) async {
  await tester.tap(finder);
  await tester.pump(const Duration(milliseconds: 60));
  await tester.tap(finder);
  await tester.pumpAndSettle();
}

Future<void> _tap(WidgetTester tester, Finder finder, {bool ctrl = false}) async {
  if (ctrl) await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
  await tester.tap(finder);
  await tester.pump(const Duration(milliseconds: 400)); // 더블클릭 대기 시간
  if (ctrl) await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
  await tester.pumpAndSettle();
}

void _expectNoOverlap(WidgetTester tester, Iterable<String> ids) {
  final rects = [for (final id in ids) tester.getRect(_card(id))];
  for (var i = 0; i < rects.length; i++) {
    for (var j = i + 1; j < rects.length; j++) {
      expect(rects[i].overlaps(rects[j]), isFalse, reason: '카드 $i와 $j가 겹칩니다: ${rects[i]} ${rects[j]}');
    }
  }
}

void main() {
  group('배치 규칙(LibraryLayout)', () {
    test('빈 자리는 그대로, 겹치면 가장 가까운 빈 칸', () {
      final occupied = [LibraryLayout.rectAt(const Offset(16, 16))];
      expect(LibraryLayout.freeSlot(const Offset(300, 200), occupied), const Offset(300, 200));
      final moved = LibraryLayout.freeSlot(const Offset(30, 20), occupied, width: 600);
      expect(LibraryLayout.rectAt(moved).overlaps(occupied.single), isFalse);
      expect((moved - const Offset(30, 20)).distance, lessThan(200));
    });

    test('같은 좌표에 쌓인 카드를 모두 떼어 놓고 폭을 넘지 않는다', () {
      final items = [
        for (var i = 0; i < 9; i++)
          LibraryItem(id: 'item_$i', boxId: 'b', kind: LibraryItemKind.file, title: '붙임$i', space: LibrarySpace.reference, x: 900, y: 40),
      ];
      final positions = LibraryLayout.resolve(items, width: 420);
      expect(LibraryLayout.hasOverlap(positions.values), isFalse);
      for (final p in positions.values) {
        expect(p.dx + LibraryLayout.cardWidth, lessThanOrEqualTo(420));
      }
    });

    test('정리(격자)는 정렬 기준대로 채운다', () {
      final items = [
        const LibraryItem(id: 'item_2', boxId: 'b', kind: LibraryItemKind.text, title: '나', space: LibrarySpace.core, x: 0, y: 0),
        const LibraryItem(id: 'item_1', boxId: 'b', kind: LibraryItemKind.file, title: '다', space: LibrarySpace.core, x: 0, y: 0),
        const LibraryItem(id: 'item_3', boxId: 'b', kind: LibraryItemKind.folder, title: '가', space: LibrarySpace.core, x: 0, y: 0),
      ];
      expect(sortForArrange(items, LibraryArrangeOrder.added).map((i) => i.id), ['item_1', 'item_2', 'item_3']);
      expect(sortForArrange(items, LibraryArrangeOrder.name).map((i) => i.title), ['가', '나', '다']);
      expect(sortForArrange(items, LibraryArrangeOrder.kind).map((i) => i.kind),
          [LibraryItemKind.file, LibraryItemKind.folder, LibraryItemKind.text]);
      final grid = LibraryLayout.grid(items, width: 320);
      expect(LibraryLayout.hasOverlap(grid.values), isFalse);
      expect(grid.values.map((p) => p.dx).toSet().length, 2); // 폭 320에는 2열
    });
  });

  group('더블클릭 열기', () {
    testWidgets('4개 영역 모두 연결 앱으로 열고 성공하면 대화상자를 띄우지 않는다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('열기');
      final ids = <String>[];
      for (final space in LibrarySpace.values) {
        ids.add((await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: '${space.name}.hwpx', space: space, x: 16, y: 16, source: 'C:/자료/${space.name}.hwpx')).id);
      }
      final link = await api.addItem(boxId: box.id, kind: LibraryItemKind.link, title: '누리집', space: LibrarySpace.temp, x: 200, y: 16, source: 'https://example.com');
      final folder = await api.addItem(boxId: box.id, kind: LibraryItemKind.folder, title: '폴더', space: LibrarySpace.basis, x: 200, y: 16, source: 'C:/자료');
      final opener = _FakeOpener();
      await _pumpScreen(tester, api, opener: opener);
      for (final id in [...ids, link.id, folder.id]) {
        await _doubleTap(tester, _card(id));
      }
      expect(opener.calls.map((c) => c.itemId), [...ids, link.id, folder.id]);
      expect(opener.calls[4].kind, LibraryItemKind.link);
      expect(opener.calls[5].kind, LibraryItemKind.folder);
      expect(find.byKey(const ValueKey('libraryOpenFailed')), findsNothing);
      expect(find.text('자료 위치'), findsNothing);
    });

    testWidgets('원본이 없으면 이유와 경로를 보이고 경로를 복사할 수 있다', (tester) async {
      String? copied;
      tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, (call) async {
        if (call.method == 'Clipboard.setData') copied = (call.arguments as Map)['text'] as String?;
        return null;
      });
      addTearDown(() => tester.binding.defaultBinaryMessenger.setMockMethodCallHandler(SystemChannels.platform, null));
      final api = InMemoryLibraryApi();
      final box = await api.createBox('원본 없음');
      final item = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: '붙임1.pdf', space: LibrarySpace.reference, x: 16, y: 16, source: 'C:/옮겨짐/붙임1.pdf');
      final opener = _FakeOpener((_, _) => const LibraryOpenResult(ok: false, code: 'SOURCE_MISSING', message: 'x'));
      await _pumpScreen(tester, api, opener: opener);
      await _doubleTap(tester, _card(item.id));
      expect(find.byKey(const ValueKey('libraryOpenFailed')), findsOneWidget);
      expect(find.textContaining('원본 파일을 찾을 수 없습니다'), findsOneWidget);
      expect(find.text('C:/옮겨짐/붙임1.pdf'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('libraryOpenFailedCopyPath')));
      await tester.pumpAndSettle();
      expect(copied, 'C:/옮겨짐/붙임1.pdf');
      expect(find.byKey(const ValueKey('libraryOpenFailed')), findsNothing);
    });

    testWidgets('실행 파일은 확인한 뒤에만 열고, 취소하면 열지 않는다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('실행 파일');
      final item = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'setup.exe', space: LibrarySpace.temp, x: 16, y: 16, source: 'C:/받은 파일/setup.exe');
      final opener = _FakeOpener();
      await _pumpScreen(tester, api, opener: opener);
      await _doubleTap(tester, _card(item.id));
      expect(find.byKey(const ValueKey('libraryConfirmRiskyOpen')), findsOneWidget);
      await tester.tap(find.text('취소'));
      await tester.pumpAndSettle();
      expect(opener.calls, isEmpty);
      await _doubleTap(tester, _card(item.id));
      await tester.tap(find.byKey(const ValueKey('libraryConfirmRiskyOpenYes')));
      await tester.pumpAndSettle();
      expect(opener.calls.single.confirmed, isTrue);
    });

    testWidgets('텍스트 자료는 메모 편집기로 열고 실행기를 부르지 않는다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('텍스트');
      final item = await api.addItem(boxId: box.id, kind: LibraryItemKind.text, title: '메모', space: LibrarySpace.core, x: 16, y: 16, text: '회의 메모 본문');
      final opener = _FakeOpener();
      await _pumpScreen(tester, api, opener: opener);
      await _doubleTap(tester, _card(item.id));
      expect(find.byKey(const ValueKey('libraryMemoPage')), findsOneWidget);
      expect(find.text('회의 메모 본문'), findsOneWidget);
      expect(opener.calls, isEmpty);
    });

    test('BridgeLibraryApi.openItem은 open_item 명령을 보내고 실패 코드를 돌려준다', () async {
      final sent = <Object?>[];
      final api = BridgeLibraryApi((method, args) async {
        sent.add(args.single);
        return {'ok': false, 'code': 'NO_APP', 'message': '연결된 앱 없음'};
      });
      final result = await api.openItem(itemId: '12', kind: LibraryItemKind.file, source: 'C:/a.xyz');
      expect(sent.single, {'cmd': 'open_item', 'item_id': 12, 'kind': 'file', 'source_path': 'C:/a.xyz', 'confirmed': false});
      expect(result.ok, isFalse);
      expect(result.code, 'NO_APP');
    });
  });

  group('여러 개 선택', () {
    testWidgets('Ctrl+클릭으로 여러 개를 고르고 다른 영역으로 한꺼번에 옮긴다(관계선은 만들지 않는다)', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('선택');
      final a = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'A', space: LibrarySpace.core, x: 16, y: 16, source: 'C:/a.pdf');
      final b = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'B', space: LibrarySpace.core, x: 166, y: 16, source: 'C:/b.pdf');
      final c = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'C', space: LibrarySpace.reference, x: 16, y: 16, source: 'C:/c.pdf');
      await _pumpScreen(tester, api);
      await _tap(tester, _card(a.id));
      await _tap(tester, _card(b.id), ctrl: true);
      await _tap(tester, _card(c.id), ctrl: true);
      expect(find.text('3개 선택'), findsOneWidget);
      expect(await api.listRelations(box.id), isEmpty);
      // Ctrl+클릭을 다시 하면 해제
      await _tap(tester, _card(c.id), ctrl: true);
      expect(find.text('2개 선택'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('librarySelectionMove')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('librarySelectionMove-reference')));
      await tester.pumpAndSettle();
      final items = await api.listItems(box.id);
      expect(items.every((i) => i.space == LibrarySpace.reference), isTrue);
      expect(LibraryLayout.hasOverlap(items.map((i) => Offset(i.x, i.y))), isFalse);
      _expectNoOverlap(tester, [a.id, b.id, c.id]);
    });

    testWidgets('빈 곳 클릭·Esc는 선택을 풀고 Ctrl+A는 현재 영역을 모두 고른다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('키보드');
      final a = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'A', space: LibrarySpace.basis, x: 16, y: 16, source: 'C:/a.pdf');
      await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'B', space: LibrarySpace.basis, x: 166, y: 16, source: 'C:/b.pdf');
      await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'C', space: LibrarySpace.core, x: 16, y: 16, source: 'C:/c.pdf');
      await _pumpScreen(tester, api);
      await _tap(tester, _card(a.id));
      expect(find.text('1개 선택'), findsOneWidget);
      await tester.sendKeyEvent(LogicalKeyboardKey.escape);
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('librarySelectionBar')), findsNothing);
      await _tap(tester, _card(a.id));
      await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
      await tester.sendKeyEvent(LogicalKeyboardKey.keyA);
      await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
      await tester.pumpAndSettle();
      expect(find.text('2개 선택'), findsOneWidget);
      await tester.tapAt(tester.getBottomRight(find.byKey(const ValueKey('libraryBackground-basis'))) - const Offset(10, 10));
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('librarySelectionBar')), findsNothing);
    });

    testWidgets('Delete는 개수를 보여 확인한 뒤 한꺼번에 삭제한다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('삭제');
      final a = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'A', space: LibrarySpace.temp, x: 16, y: 16, source: 'C:/a.pdf');
      final b = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'B', space: LibrarySpace.temp, x: 166, y: 16, source: 'C:/b.pdf');
      await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: '남김', space: LibrarySpace.temp, x: 16, y: 96, source: 'C:/c.pdf');
      await _pumpScreen(tester, api);
      await _tap(tester, _card(a.id));
      await _tap(tester, _card(b.id), ctrl: true);
      await tester.sendKeyEvent(LogicalKeyboardKey.delete);
      await tester.pumpAndSettle();
      expect(find.byKey(const ValueKey('libraryConfirmBatchDelete')), findsOneWidget);
      expect(find.textContaining('2개를 자료함에서 삭제할까요'), findsOneWidget);
      await tester.tap(find.byKey(const ValueKey('libraryConfirmBatchDeleteYes')));
      await tester.pumpAndSettle();
      expect((await api.listItems(box.id)).map((i) => i.title), ['남김']);
    });

    testWidgets('다른 자료함으로 복사하면 원본 등록은 남고 겹치지 않게 놓인다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('보내는 곳');
      final other = await api.createBox('받는 곳');
      await api.addItem(boxId: other.id, kind: LibraryItemKind.file, title: '기존', space: LibrarySpace.core, x: 16, y: 16, source: 'C:/old.pdf');
      final a = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'A', space: LibrarySpace.basis, x: 16, y: 16, source: 'C:/a.pdf');
      final b = await api.addItem(boxId: box.id, kind: LibraryItemKind.link, title: 'B', space: LibrarySpace.basis, x: 166, y: 16, source: 'https://example.com');
      await _pumpScreen(tester, api);
      await _tap(tester, _card(a.id));
      await _tap(tester, _card(b.id), ctrl: true);
      await tester.tap(find.byKey(const ValueKey('librarySelectionTransfer')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('libraryTransferBox')));
      await tester.pumpAndSettle();
      await tester.tap(find.text('받는 곳').last);
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('libraryTransferCopy')));
      await tester.pumpAndSettle();
      expect((await api.listItems(box.id)).length, 2);
      final copied = await api.listItems(other.id);
      expect(copied.map((i) => i.title).toSet(), {'기존', 'A', 'B'});
      expect(copied.every((i) => i.space == LibrarySpace.core), isTrue);
      expect(LibraryLayout.hasOverlap(copied.map((i) => Offset(i.x, i.y))), isFalse);
      expect(find.textContaining('2개를'), findsOneWidget);
    });

    testWidgets('여러 개를 끌면 선택 전체가 상대 위치를 지키며 함께 옮겨진다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('함께 끌기');
      final a = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'A', space: LibrarySpace.core, x: 16, y: 16, source: 'C:/a.pdf');
      final b = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'B', space: LibrarySpace.core, x: 166, y: 16, source: 'C:/b.pdf');
      await _pumpScreen(tester, api);
      await _tap(tester, _card(a.id));
      await _tap(tester, _card(b.id), ctrl: true);
      await tester.drag(_card(a.id), const Offset(0, 120));
      await tester.pumpAndSettle();
      final items = {for (final i in await api.listItems(box.id)) i.id: i};
      expect(items[a.id]!.y, greaterThan(100));
      expect(items[b.id]!.y, items[a.id]!.y);
      expect(items[b.id]!.x - items[a.id]!.x, 150);
    });

    testWidgets('일괄 이동 중 하나가 실패하면 처음 상태로 되돌린다', (tester) async {
      final api = _FlakyMoveApi();
      final box = await api.createBox('되돌리기');
      final a = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'A', space: LibrarySpace.core, x: 16, y: 16, source: 'C:/a.pdf');
      final b = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'B', space: LibrarySpace.core, x: 166, y: 16, source: 'C:/b.pdf');
      await _pumpScreen(tester, api);
      await _tap(tester, _card(a.id));
      await _tap(tester, _card(b.id), ctrl: true);
      api.failOnMove = api.moves + 2;
      await tester.tap(find.byKey(const ValueKey('librarySelectionMove')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('librarySelectionMove-temp')));
      await tester.pumpAndSettle();
      expect((await api.listItems(box.id)).every((i) => i.space == LibrarySpace.core), isTrue);
      expect(find.textContaining('처음 상태로 되돌렸습니다'), findsOneWidget);
    });
  });

  group('겹침 방지', () {
    testWidgets('겹쳐 저장된 자료함은 열 때 정리해 저장하고 화면에서도 겹치지 않는다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('겹침');
      final ids = [
        for (final name in ['붙임1', '붙임2', '붙임4'])
          (await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: name, space: LibrarySpace.reference, x: 20, y: 30, source: 'C:/$name.pdf')).id,
      ];
      await _pumpScreen(tester, api);
      final stored = await api.listItems(box.id);
      expect(LibraryLayout.hasOverlap(stored.map((i) => Offset(i.x, i.y))), isFalse);
      expect(stored.first.x, 20); // 처음 놓은 카드는 그 자리를 지킨다
      _expectNoOverlap(tester, ids);
    });

    testWidgets('같은 자리에 끌어 놓으면 가까운 빈 칸으로 놓인다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('끌어 놓기');
      final a = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'A', space: LibrarySpace.core, x: 16, y: 16, source: 'C:/a.pdf');
      final b = await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: 'B', space: LibrarySpace.core, x: 16, y: 200, source: 'C:/b.pdf');
      await _pumpScreen(tester, api);
      await tester.drag(_card(b.id), const Offset(10, -180));
      await tester.pumpAndSettle();
      final items = {for (final i in await api.listItems(box.id)) i.id: i};
      expect(items[a.id]!.x, 16);
      expect(items[a.id]!.y, 16);
      expect(LibraryLayout.hasOverlap(items.values.map((i) => Offset(i.x, i.y))), isFalse);
      expect(items[b.id]!.y, lessThan(200));
      _expectNoOverlap(tester, [a.id, b.id]);
    });

    testWidgets('창이 좁아져도 카드가 가장자리에 몰려 겹치지 않고 세로로 스크롤된다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('좁은 창');
      final ids = [
        for (var i = 0; i < 8; i++)
          (await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: '자료$i', space: LibrarySpace.temp, x: 16.0 + 150 * i, y: 16, source: 'C:/$i.pdf')).id,
      ];
      await _pumpScreen(tester, api, size: const Size(1000, 700));
      expect(tester.takeException(), isNull);
      final quadrant = tester.getRect(find.byKey(const ValueKey('libraryScroll-temp')));
      for (final id in ids.take(2)) {
        final rect = tester.getRect(_card(id));
        expect(rect.left, greaterThanOrEqualTo(quadrant.left));
        expect(rect.right, lessThanOrEqualTo(quadrant.right + 0.5));
      }
      final scrollable = tester.state<ScrollableState>(find.descendant(of: find.byKey(const ValueKey('libraryScroll-temp')), matching: find.byType(Scrollable)));
      expect(scrollable.position.maxScrollExtent, greaterThan(0));
      final stored = await api.listItems(box.id);
      expect(stored.map((i) => i.x).toList(), [for (var i = 0; i < 8; i++) 16.0 + 150 * i]); // 저장 좌표는 그대로
      _expectNoOverlap(tester, ids);
    });

    testWidgets('정리 단추는 이름순 격자로 다시 놓는다', (tester) async {
      final api = InMemoryLibraryApi();
      final box = await api.createBox('정리');
      await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: '나', space: LibrarySpace.basis, x: 300, y: 200, source: 'C:/b.pdf');
      await api.addItem(boxId: box.id, kind: LibraryItemKind.file, title: '가', space: LibrarySpace.basis, x: 16, y: 300, source: 'C:/a.pdf');
      await _pumpScreen(tester, api);
      await tester.tap(find.byKey(const ValueKey('libraryArrange-basis')));
      await tester.pumpAndSettle();
      await tester.tap(find.byKey(const ValueKey('libraryArrangeName')));
      await tester.pumpAndSettle();
      final byTitle = {for (final i in await api.listItems(box.id)) i.title: Offset(i.x, i.y)};
      expect(byTitle['가'], const Offset(16, 16));
      expect(byTitle['나'], const Offset(166, 16));
    });
  });
}
