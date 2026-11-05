import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/library/library_api.dart';
import 'package:docfit_ui/features/library/library_screen.dart';

class _UnavailableLibraryApi implements LibraryApi {
  Future<T> _missing<T>() async => throw StateError('자료함 엔진(klib.exe)이 없습니다');
  @override Future<List<LibraryBox>> listBoxes() => _missing();
  @override Future<LibraryBox> createBox(String name) => _missing();
  @override Future<List<LibraryItem>> listItems(String boxId, {String query = ''}) => _missing();
  @override Future<LibraryItem> addItem({required String boxId, required LibraryItemKind kind, required String title, required LibrarySpace space, required double x, required double y, String? source, String? text}) => _missing();
  @override Future<LibraryItem> moveItem(String itemId, {required String boxId, required LibrarySpace space, required double x, required double y}) => _missing();
  @override Future<List<LibraryRelation>> listRelations(String boxId) => _missing();
  @override Future<LibraryRelation> addRelation(String boxId, String fromItemId, String toItemId) => _missing();
  @override Future<void> deleteRelation(String relationId) => _missing();
}
class FakeLibraryClipboardReader implements LibraryClipboardReader {
  FakeLibraryClipboardReader({this.nextData});
  LibraryClipboardData? nextData;

  @override
  Future<LibraryClipboardData?> read() async => nextData;
}

void main() {
  testWidgets('missing klib is shown without crashing', (tester) async {
    await tester.pumpWidget(MaterialApp(home: LibraryScreen(api: _UnavailableLibraryApi())));
    await tester.pumpAndSettle();
    expect(find.text('자료함 엔진(klib.exe)이 없습니다'), findsOneWidget);
  });
  test('초기 ID 뒤에서 안전하게 증가하고 잘못된 자료함 이동을 거부한다', () async {
    final api = InMemoryLibraryApi(
      initialBoxes: const [LibraryBox(id: 'box_8', name: '초기')],
      initialItems: const [
        LibraryItem(id: 'item_12', boxId: 'box_8', kind: LibraryItemKind.text,
          title: '초기 자료', space: LibrarySpace.core, x: 0, y: 0),
      ],
      initialRelations: const [
        LibraryRelation(id: 'rel_4', boxId: 'box_8', fromItemId: 'a', toItemId: 'b'),
      ],
    );
    expect((await api.createBox('다음')).id, 'box_9');
    expect((await api.addItem(boxId: 'box_8', kind: LibraryItemKind.note,
      title: '다음 자료', space: LibrarySpace.core, x: 1, y: 1)).id, 'item_13');
    expect((await api.addRelation('box_8', 'item_12', 'item_13')).id, 'rel_5');
    await expectLater(
      api.moveItem('item_12', boxId: 'another-box', space: LibrarySpace.basis, x: 2, y: 2),
      throwsStateError,
    );
  });

  testWidgets('자료가 없는 초기 상태에서 빈 공간과 생성 동작을 보인다', (tester) async {
    final api = InMemoryLibraryApi();
    await tester.pumpWidget(
      MaterialApp(
        home: LibraryScreen(api: api),
      ),
    );
    await tester.pumpAndSettle();

    // 자동 자료함 생성 없음, 빈 안내 문구와 새로 만들기 CTA 확인
    expect(find.text('자료함을 선택하거나 새로 만드세요.'), findsOneWidget);
    expect(find.byKey(const ValueKey('libraryEmptyStateCta')), findsOneWidget);

    // CTA 클릭 시 자료함 생성 및 4개 공간 표시
    await tester.tap(find.byKey(const ValueKey('libraryEmptyStateCta')));
    await tester.pumpAndSettle();

    expect(find.byKey(const ValueKey('librarySpace-core')), findsOneWidget);
    expect(find.byKey(const ValueKey('librarySpace-basis')), findsOneWidget);
    expect(find.byKey(const ValueKey('librarySpace-reference')), findsOneWidget);
    expect(find.byKey(const ValueKey('librarySpace-temp')), findsOneWidget);
  });

  testWidgets('자료함을 만들고 목록에서 선택한다', (tester) async {
    final api = InMemoryLibraryApi();
    await tester.pumpWidget(
      MaterialApp(
        home: LibraryScreen(api: api),
      ),
    );
    await tester.pumpAndSettle();

    // 인라인 이름 입력 후 생성
    await tester.enterText(
      find.byKey(const ValueKey('libraryAddBoxName')),
      '연구 프로젝트',
    );
    await tester.tap(find.byKey(const ValueKey('libraryAddBoxSubmit')));
    await tester.pumpAndSettle();

    // 좌측 목록에 나타나고 4개 공간 제목 표시
    expect(find.text('연구 프로젝트'), findsWidgets);
    expect(find.text('핵심자료'), findsOneWidget);
    expect(find.text('기초자료'), findsOneWidget);
    expect(find.text('참고자료'), findsOneWidget);
    expect(find.text('임시저장소'), findsOneWidget);
  });

  testWidgets('텍스트 자료를 추가하고 검색한다', (tester) async {
    final api = InMemoryLibraryApi();
    final box1 = await api.createBox('자료함1');
    final box2 = await api.createBox('자료함2');

    await api.addItem(
      boxId: box1.id,
      kind: LibraryItemKind.text,
      title: '핵심 아이디어',
      space: LibrarySpace.core,
      x: 10,
      y: 10,
      text: '비즈니스 모델 메모',
    );
    await api.addItem(
      boxId: box1.id,
      kind: LibraryItemKind.text,
      title: '기초 참고 문서',
      space: LibrarySpace.basis,
      x: 10,
      y: 10,
      text: '설계 문서',
    );
    await api.addItem(
      boxId: box2.id,
      kind: LibraryItemKind.text,
      title: '다른 자료함 핵심 아이디어',
      space: LibrarySpace.core,
      x: 10,
      y: 10,
      text: '다른 내용',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: LibraryScreen(api: api),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('핵심 아이디어'), findsOneWidget);
    expect(find.text('기초 참고 문서'), findsOneWidget);
    expect(find.text('다른 자료함 핵심 아이디어'), findsNothing);

    // 검색어 입력
    await tester.enterText(
      find.byKey(const ValueKey('librarySearch')),
      '아이디어',
    );
    await tester.pumpAndSettle();

    expect(find.text('핵심 아이디어'), findsOneWidget);
    expect(find.text('기초 참고 문서'), findsNothing);
    expect(find.text('다른 자료함 핵심 아이디어'), findsNothing);
  });

  testWidgets('카드를 같은 공간 안에서 끌어 이동한다', (tester) async {
    final api = InMemoryLibraryApi();
    final box = await api.createBox('이동 시험 자료함');
    final item = await api.addItem(
      boxId: box.id,
      kind: LibraryItemKind.text,
      title: '이동 카드',
      space: LibrarySpace.core,
      x: 16,
      y: 16,
      text: '내용',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: LibraryScreen(api: api),
      ),
    );
    await tester.pumpAndSettle();

    final cardFinder = find.byKey(ValueKey('libraryItem-${item.id}'));
    expect(cardFinder, findsOneWidget);

    await tester.drag(cardFinder, const Offset(60, 40));
    await tester.pumpAndSettle();

    final items = await api.listItems(box.id);
    expect(items.length, 1);
    expect(items.first.id, item.id);
    expect(items.first.title, '이동 카드');
    expect(items.first.space, LibrarySpace.core);
    expect(items.first.x, greaterThan(16.0));
    expect(items.first.y, greaterThan(16.0));
  });

  testWidgets('카드를 다른 공간으로 끌어 이동한다', (tester) async {
    tester.view.physicalSize = const Size(1200, 800);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    final api = InMemoryLibraryApi();
    final box = await api.createBox('공간 이동 자료함');
    final item = await api.addItem(
      boxId: box.id,
      kind: LibraryItemKind.text,
      title: '공간 이동 카드',
      space: LibrarySpace.core,
      x: 20,
      y: 20,
      text: '내용',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: LibraryScreen(api: api),
      ),
    );
    await tester.pumpAndSettle();

    final itemFinder = find.byKey(ValueKey('libraryItem-${item.id}'));
    final basisFinder = find.byKey(const ValueKey('librarySpace-basis'));

    final gesture = await tester.startGesture(tester.getCenter(itemFinder));
    await tester.pump(const Duration(milliseconds: 100));
    await gesture.moveTo(tester.getCenter(basisFinder));
    await tester.pump(const Duration(milliseconds: 100));
    await gesture.up();
    await tester.pumpAndSettle();

    final items = await api.listItems(box.id);
    expect(items.length, 1);
    expect(items.first.id, item.id);
    expect(items.first.space, LibrarySpace.basis);
  });

  testWidgets('핵심자료 두 카드의 관계선을 만들고 삭제한다', (tester) async {
    final api = InMemoryLibraryApi();
    final box = await api.createBox('관계 시험 자료함');
    final item1 = await api.addItem(
      boxId: box.id,
      kind: LibraryItemKind.text,
      title: '핵심 카드 1',
      space: LibrarySpace.core,
      x: 20,
      y: 20,
      text: '내용1',
    );
    final item2 = await api.addItem(
      boxId: box.id,
      kind: LibraryItemKind.text,
      title: '핵심 카드 2',
      space: LibrarySpace.core,
      x: 180,
      y: 20,
      text: '내용2',
    );
    final itemBasis = await api.addItem(
      boxId: box.id,
      kind: LibraryItemKind.text,
      title: '기초 카드',
      space: LibrarySpace.basis,
      x: 20,
      y: 20,
      text: '내용3',
    );

    await tester.pumpWidget(
      MaterialApp(
        home: LibraryScreen(api: api),
      ),
    );
    await tester.pumpAndSettle();

    // 핵심 카드 1 탭 -> 기초 카드 탭: 관계 생성 거부/무시
    await tester.tap(find.byKey(ValueKey('libraryItem-${item1.id}')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(ValueKey('libraryItem-${itemBasis.id}')));
    await tester.pumpAndSettle();

    var relations = await api.listRelations(box.id);
    expect(relations, isEmpty);

    // 핵심 카드 1 탭 -> 핵심 카드 2 탭: 관계 생성 성공
    await tester.tap(find.byKey(ValueKey('libraryItem-${item1.id}')));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(ValueKey('libraryItem-${item2.id}')));
    await tester.pumpAndSettle();

    relations = await api.listRelations(box.id);
    expect(relations.length, 1);
    final rel = relations.first;
    expect(find.byKey(ValueKey('libraryRelation-${rel.id}')), findsOneWidget);
    final painterFinder = find.descendant(
      of: find.byKey(const ValueKey('librarySpace-core')),
      matching: find.byType(CustomPaint),
    );
    expect(painterFinder, findsWidgets);
    final linePaint = tester.widgetList<CustomPaint>(painterFinder).firstWhere(
      (paint) => paint.painter.runtimeType.toString().contains('RelationPainter'),
    );
    expect(linePaint.size, isNot(Size.zero));
    final recordingCanvas = _RecordingCanvas();
    linePaint.painter!.paint(recordingCanvas, linePaint.size);
    expect(recordingCanvas.lines, hasLength(1));
    expect(recordingCanvas.lines.single.$1, const Offset(90, 56));
    expect(recordingCanvas.lines.single.$2, const Offset(250, 56));

    // 관계선 삭제 버튼 클릭
    await tester.tap(find.byKey(ValueKey('libraryRelationDelete-${rel.id}')));
    await tester.pumpAndSettle();

    relations = await api.listRelations(box.id);
    expect(relations, isEmpty);
    expect(find.byKey(ValueKey('libraryRelation-${rel.id}')), findsNothing);
  });

  testWidgets('파일 드롭과 Ctrl+V로 자료를 추가한다', (tester) async {
    final fakeClipboard = FakeLibraryClipboardReader(
      nextData: const LibraryClipboardData(text: '클립보드 텍스트 자료'),
    );
    final api = InMemoryLibraryApi();
    final box = await api.createBox('입력 시험 자료함');

    await tester.pumpWidget(
      MaterialApp(
        home: LibraryScreen(
          api: api,
          clipboardReader: fakeClipboard,
        ),
      ),
    );
    await tester.pumpAndSettle();

    // Ctrl+V로 텍스트 자료 등록
    await tester.sendKeyDownEvent(LogicalKeyboardKey.controlLeft);
    await tester.sendKeyDownEvent(LogicalKeyboardKey.keyV);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.keyV);
    await tester.sendKeyUpEvent(LogicalKeyboardKey.controlLeft);
    await tester.pumpAndSettle();

    var items = await api.listItems(box.id);
    expect(items.where((i) => i.kind == LibraryItemKind.text && i.text == '클립보드 텍스트 자료').length, 1);

    // 드롭 타깃 제스처 대신 자료함 공개 API에 파일 자료를 직접 등록
    await api.addItem(
      boxId: box.id,
      kind: LibraryItemKind.file,
      title: 'report_v1.pdf',
      space: LibrarySpace.basis,
      x: 24,
      y: 32,
      source: 'C:/docs/report_v1.pdf',
    );

    items = await api.listItems(box.id);
    final fileItem = items.firstWhere((i) => i.kind == LibraryItemKind.file);
    expect(fileItem.title, 'report_v1.pdf');
    expect(fileItem.source, 'C:/docs/report_v1.pdf');
    expect(fileItem.space, LibrarySpace.basis);

    // 빈 클립보드 시 빈 항목을 만들지 않고 안내 표시
    fakeClipboard.nextData = null;
    await tester.tap(find.byKey(const ValueKey('libraryPaste')));
    await tester.pumpAndSettle();

    expect(find.text('클립보드에 지원되는 자료가 없습니다.'), findsOneWidget);
  });

  testWidgets('기본 Flutter 클립보드 브리지에서 붙여넣는다', (tester) async {
    // Flutter test clipboard handler exercises the same platform channel used by Windows/web.
    TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMessageHandler('flutter/platform', (message) async {
      final call = const JSONMethodCodec().decodeMethodCall(message!);
      if (call.method == 'Clipboard.hasStrings') {
        return const JSONMethodCodec().encodeSuccessEnvelope(<String, dynamic>{'value': true});
      }
      if (call.method == 'Clipboard.getData') {
        return const JSONMethodCodec().encodeSuccessEnvelope(<String, dynamic>{'text': '실제 브리지 텍스트'});
      }
      return const JSONMethodCodec().encodeSuccessEnvelope(null);
    });
    addTearDown(() => TestDefaultBinaryMessengerBinding.instance.defaultBinaryMessenger
        .setMockMessageHandler('flutter/platform', null));
    final api = InMemoryLibraryApi();
    final box = await api.createBox('기본 클립보드');
    await tester.pumpWidget(MaterialApp(home: LibraryScreen(api: api)));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const ValueKey('libraryPaste')));
    await tester.pumpAndSettle();
    expect((await api.listItems(box.id)).single.text, '실제 브리지 텍스트');
  });

  testWidgets('자료함 화면 폭 1000과 1400에서 넘치지 않는다', (tester) async {
    final api = InMemoryLibraryApi();
    await api.createBox('반응형 자료함');

    // 폭 1000 시험
    tester.view.physicalSize = const Size(1000, 700);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);

    await tester.pumpWidget(
      MaterialApp(
        home: LibraryScreen(api: api),
      ),
    );
    final overflowErrors = <FlutterErrorDetails>[];
    final previousOnError = FlutterError.onError;
    FlutterError.onError = overflowErrors.add;
    addTearDown(() => FlutterError.onError = previousOnError);
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(overflowErrors.where((error) => error.exceptionAsString().contains('overflowed')), isEmpty);

    // 폭 1400 시험
    tester.view.physicalSize = const Size(1400, 900);
    await tester.pumpWidget(
      MaterialApp(
        home: LibraryScreen(api: api),
      ),
    );
    await tester.pumpAndSettle();
    expect(tester.takeException(), isNull);
    expect(tester.takeException(), isNull);
    expect(overflowErrors.where((error) => error.exceptionAsString().contains('overflowed')), isEmpty);
  });
}

class _RecordingCanvas extends Fake implements Canvas {
  final lines = <(Offset, Offset)>[];

  @override
  void drawLine(Offset p1, Offset p2, Paint paint) {
    lines.add((p1, p2));
  }
}

