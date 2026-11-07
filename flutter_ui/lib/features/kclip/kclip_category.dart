/// 몽땅클립보드 분류 규칙(관리창용). `kagent/src/category.rs`의 `classify`와 같은 규칙을 Dart로 옮겼다.
///
/// 규칙 표(확장자·프로그램·서식 이름)와 판별 사례는 `tests/fixtures/kclip_category_rules.json`
/// 한곳에 두고, Rust 시험과 Dart 시험(`test/kclip_category_test.dart`)이 같은 파일을 읽어
/// 두 쪽의 표와 결과가 같은지 확인한다. 규칙을 바꿀 때는 세 곳을 함께 고친다.
///
/// 요약: 분류는 겹칠 수 있고 "전체"에는 항상 속한다.
/// - 화면캡처: kind=image 이면서 source=="screenshot" 또는 미리보기가 "캡처 · "로 시작(그림에도 속함)
/// - 그림: kind=image, 또는 파일 항목에 그림 확장자 파일이 있음
/// - 문서: 파일 항목에 문서 확장자 파일이 있음, 또는 글 항목이 문서 프로그램에서 왔거나 문서 서식을 가짐
/// - 파일/폴더: 파일 항목의 경로 중 폴더가 아닌 것이 있으면 파일, 폴더가 있으면 폴더
/// - 웹: 출처 주소 저장됨, 미리보기에 " · 웹 · ", 글 전체가 http(s) 주소 한 개, 브라우저의 HTML 서식 글
library;

/// 분류 단추 이름(순서 = Rust `Category::ALL`).
const kclipCategories = ['전체', '문서', '그림', '파일', '폴더', '웹', '화면캡처'];

/// 검색 칸 이름(빠른 목록과 같음).
const kclipSearchLabel = '키워드검색';

const kclipDocExts = [
  'hwp', 'hwpx', 'hml', 'hwt', 'doc', 'docx', 'dot', 'dotx', 'docm', 'xls', 'xlsx', 'xlsm', 'xlsb', 'csv',
  'ppt', 'pptx', 'pps', 'ppsx', 'pdf', 'txt', 'rtf', 'md', 'odt', 'ods', 'odp', 'one', 'gul', 'show', 'cell',
  'xps', 'epub',
];
const kclipImageExts = [
  'png', 'jpg', 'jpeg', 'jpe', 'gif', 'bmp', 'webp', 'tif', 'tiff', 'ico', 'svg', 'heic', 'heif', 'avif',
];
const kclipDocPrograms = [
  'hwp.exe', 'hwpviewer.exe', 'hword.exe', 'hcell.exe', 'hshow.exe', 'winword.exe', 'excel.exe', 'powerpnt.exe',
  'onenote.exe', 'soffice.exe', 'soffice.bin', 'swriter.exe', 'scalc.exe', 'simpress.exe', 'acrobat.exe',
  'acrord32.exe', 'acrord64.exe', 'foxitreader.exe', 'foxitpdfreader.exe', 'wordpad.exe', 'hancomoffice.exe',
];
const kclipBrowsers = [
  'chrome.exe', 'msedge.exe', 'firefox.exe', 'whale.exe', 'brave.exe', 'opera.exe', 'vivaldi.exe',
  'iexplore.exe', 'safari',
];
const kclipDocFormats = [
  'hwp character shape', 'hwp native', 'hwp format', 'hwp paragraph shape', 'rich text format',
  'xml spreadsheet', 'biff8', 'biff12', 'csv',
];

/// 분류에 필요한 항목 정보(Rust `Entry`와 같은 칸).
class KClipEntry {
  const KClipEntry({
    required this.kind,
    this.preview = '',
    this.source = '',
    this.formats = const [],
    this.paths = const [],
    this.webUrl,
    this.text = '',
  });

  /// "text" | "image" | "files"
  final String kind;
  final String preview;

  /// 소문자 프로그램 파일 이름, 화면 캡처는 "screenshot".
  final String source;
  final List<String> formats;
  final List<String> paths;
  final String? webUrl;

  /// 글 항목 본문(주소 판별용).
  final String text;

  /// 에이전트 목록 항목(Map)에서 만든다. 에이전트가 주는 칸(id·kind·preview…)만 있으면
  /// 글 본문은 미리보기로, 파일 경로는 미리보기의 파일 이름 목록("파일 N개: a, b …")으로 대신한다.
  factory KClipEntry.fromItem(Map item) {
    final kind = '${item['kind'] ?? ''}';
    final preview = '${item['preview'] ?? ''}';
    List<String> list(Object? v) => v is List ? [for (final x in v) '$x'] : const [];
    final url = item['web_url'];
    var paths = list(item['paths']);
    if (paths.isEmpty && kind == 'files') paths = _namesFromPreview(preview);
    return KClipEntry(
      kind: kind,
      preview: preview,
      source: '${item['source'] ?? ''}',
      formats: list(item['formats']),
      paths: paths,
      webUrl: url is String && url.isNotEmpty ? url : null,
      text: item['text'] is String ? item['text'] as String : (kind == 'text' ? preview : ''),
    );
  }

  /// "파일 2개: 1.hwpx, 2.pdf · 서식 …"에서 파일 이름들을 꺼낸다(최대 3개, 이름 안의 ", "는 구분 못 함).
  static List<String> _namesFromPreview(String preview) {
    final m = RegExp(r'^파일 \d+개: (.*)$').firstMatch(preview);
    if (m == null) return const [];
    var rest = m.group(1)!;
    final mark = rest.indexOf(' · ');
    if (mark >= 0) rest = rest.substring(0, mark);
    if (rest.endsWith(' …')) rest = rest.substring(0, rest.length - 2);
    return [for (final n in rest.split(', ')) if (n.isNotEmpty) n];
  }
}

/// 폴더 여부를 알려 주는 함수(참=폴더, 거짓=파일, null=모름 → 경로 모양으로 추정).
typedef KClipIsDir = bool? Function(String path);

bool? _unknown(String _) => null;

String _fileName(String path) {
  var end = path.length;
  while (end > 0 && (path[end - 1] == '\\' || path[end - 1] == '/')) {
    end--;
  }
  final trimmed = path.substring(0, end);
  final cut = trimmed.lastIndexOf(RegExp(r'[\\/]'));
  return cut < 0 ? trimmed : trimmed.substring(cut + 1);
}

/// 소문자 확장자(없거나 점으로만 시작·끝나면 null).
String? kclipExtension(String path) {
  final name = _fileName(path);
  final dot = name.lastIndexOf('.');
  if (dot <= 0 || dot + 1 == name.length) return null;
  return name.substring(dot + 1).toLowerCase();
}

bool _guessIsDir(String path) {
  if (path.endsWith('\\') || path.endsWith('/')) return true;
  // Rust는 바이트 길이 2("C:")로 본다 → 첫 글자가 ASCII일 때만 같다.
  if (path.length == 2 && path.codeUnitAt(0) < 0x80 && path[1] == ':') return true;
  return kclipExtension(path) == null;
}

bool _isSingleWebUrl(String text) {
  final t = text.trim();
  return (t.startsWith('http://') || t.startsWith('https://')) && t.length > 8 && !t.contains(RegExp(r'\s'));
}

/// 항목이 속한 분류를 [kclipCategories] 순서로 돌려준다.
List<String> kclipClassify(KClipEntry entry, {KClipIsDir isDir = _unknown}) {
  final set = <String>{'전체'};
  final source = entry.source.toLowerCase();
  bool hasFormat(List<String> names) => entry.formats.any((f) => names.contains(f.toLowerCase()));
  switch (entry.kind) {
    case 'image':
      set.add('그림');
      if (source == 'screenshot' || entry.preview.startsWith('캡처 · ')) set.add('화면캡처');
    case 'files':
      for (final path in entry.paths) {
        if (isDir(path) ?? _guessIsDir(path)) {
          set.add('폴더');
        } else {
          set.add('파일');
          final ext = kclipExtension(path);
          if (kclipDocExts.contains(ext)) {
            set.add('문서');
          } else if (kclipImageExts.contains(ext)) {
            set.add('그림');
          }
        }
      }
    case 'text':
      if (kclipDocPrograms.contains(source) || hasFormat(kclipDocFormats)) set.add('문서');
      if (_isSingleWebUrl(entry.text) || (kclipBrowsers.contains(source) && hasFormat(const ['html format']))) {
        set.add('웹');
      }
  }
  if (entry.webUrl != null || entry.preview.contains(' · 웹 · ')) set.add('웹');
  return [for (final c in kclipCategories) if (set.contains(c)) c];
}

/// 에이전트 목록 항목이 [category]에 속하는지.
bool kclipItemIn(Map item, String category, {KClipIsDir? isDir}) {
  if (category == '전체') return true;
  final known = item['is_folder'];
  final lookup = isDir ?? (known is bool ? (_) => known : _unknown);
  return kclipClassify(KClipEntry.fromItem(item), isDir: lookup).contains(category);
}
