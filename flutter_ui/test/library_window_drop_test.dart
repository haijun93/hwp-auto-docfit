import 'package:docfit_ui/features/library/library_api.dart';
import 'package:docfit_ui/features/library/library_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// 탐색기에서 자료함 창에 파일을 끌어 놓으면 선택한 자료함에 들어간다(사용자 보고 2026-11-07).
class _DropLibraryApi extends InMemoryLibraryApi implements LibraryDropApi {
  _DropLibraryApi() : super(initialBoxes: const [LibraryBox(id: 'box_1', name: '보고서')]);
  final watched = <bool>[];
  final pending = <String>[];

  @override
  Future<void> watchDrops(bool active) async => watched.add(active);

  @override
  Future<List<String>> takeDroppedPaths() async {
    final out = List.of(pending);
    pending.clear();
    return out;
  }
}

void main() {
  testWidgets('window file drop adds files to the selected box', (tester) async {
    tester.view.physicalSize = const Size(1400, 900);
    tester.view.devicePixelRatio = 1;
    addTearDown(tester.view.reset);
    final api = _DropLibraryApi();
    void Function()? fire;
    await tester.pumpWidget(MaterialApp(
      home: LibraryScreen(api: api, watchDropEvents: (cb) {
        fire = cb;
        return () => fire = null;
      }),
    ));
    await tester.pumpAndSettle();
    expect(api.watched, [true]);
    await tester.tap(find.text('보고서').first);
    await tester.pumpAndSettle();

    api.pending.addAll([r'C:\자료\계획.hwpx', r'C:\자료\실적.xlsx']);
    fire!();
    await tester.pumpAndSettle();
    final items = await api.listItems('box_1');
    expect(items.map((e) => e.title), containsAll(['계획.hwpx', '실적.xlsx']));
    expect(find.text('파일 2개를 자료함에 넣었습니다.'), findsOneWidget);

    await tester.pumpWidget(const SizedBox());
    expect(api.watched, [true, false]);
  });
}
