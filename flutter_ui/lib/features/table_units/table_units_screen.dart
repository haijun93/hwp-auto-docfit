import 'dart:convert';

import 'dart:math' as math;

import 'dart:typed_data';



import 'package:flutter/material.dart';



import '../../core/api/table_units_api.dart';

import 'table_grid_preview.dart';



/// 표 템플릿 화면: 스냅샷을 보고 고른 뒤 정보단위를 조절하여 한/글에 붙여넣을 수 있게 복사.

class TableUnitsScreen extends StatefulWidget {

  const TableUnitsScreen({super.key, required this.api});



  final ApiCall api;



  @override

  State<TableUnitsScreen> createState() => _TableUnitsScreenState();

}



class _TableUnitsScreenState extends State<TableUnitsScreen> {

  late final TableUnitsApi _api;



  bool _loadingList = false;

  bool _loadingThumbnails = false;

  bool _autoThumbnailsTried = false;

  bool _loadingPreview = false;

  bool _copying = false;



  String? _errorMessage;

  String? _previewError;

  String? _copyErrorMessage;



  TableUnitsListData? _listData;

  String _selectedCategory = '전체';

  String _searchQuery = '';

  final TextEditingController _searchController = TextEditingController();



  TableTemplateInfo? _selectedTemplate;

  /// 고른 화살표(null이면 표에 있던 화살표 그대로). {kind: symbol|image, value, direction, size}
  Map<String, Object?>? _arrow;
  Map<String, Object?>? _arrowCatalog;



  int? _currentRowCount;

  int? _currentColCount;

  String _selectedFill = 'increment';

  Map<String, String> _cellTexts = {};



  TablePreview? _previewData;

  Map<String, List<CellShape>> _previewShapes = {};

  int _previewSeq = 0;



  double? _leftPaneWidth;

  final ScrollController _galleryScrollController = ScrollController();

  final ScrollController _detailScrollController = ScrollController();

  final ScrollController _categoryRibbonController = ScrollController();



  @override

  void initState() {

    super.initState();

    _api = TableUnitsApi(widget.api);

    _loadList();

  }



  @override

  void dispose() {

    _searchController.dispose();

    _galleryScrollController.dispose();

    _detailScrollController.dispose();

    _categoryRibbonController.dispose();

    super.dispose();

  }



  Future<void> _loadList() async {

    setState(() {

      _loadingList = true;

      _errorMessage = null;

    });

    try {

      final data = await _api.list();

      if (!mounted) return;

      // 그림이 없으면(서식모음이 바뀌었거나 처음) 화면을 열 때 한 번 자동으로 만든다 — 버튼을 몰라도 그림이 보이게(2026-10-23 사용자 실측).

      if (!data.thumbnailsReady &&

          !_autoThumbnailsTried &&

          data.templates.isNotEmpty) {

        _autoThumbnailsTried = true;

        WidgetsBinding.instance.addPostFrameCallback((_) {

          if (mounted) _generateThumbnails();

        });

      }

      setState(() {

        _listData = data;

        _loadingList = false;

        if (data.templates.isNotEmpty) {

          _selectTemplate(data.templates.first);

        } else {

          _selectedTemplate = null;

          _previewData = null;

          _previewShapes = {};

        }

      });

    } catch (e) {

      if (!mounted) return;

      setState(() {

        _errorMessage = '$e';

        _loadingList = false;

      });

    }

  }



  Future<void> _generateThumbnails() async {

    if (_loadingThumbnails) return;

    setState(() {

      _loadingThumbnails = true;

      _errorMessage = null;

    });

    try {

      final data = await _api.generateThumbnails();

      if (!mounted) return;

      setState(() {

        _listData = data;

        _loadingThumbnails = false;

        if (_selectedTemplate != null) {

          final matched = data.templates

              .where((t) => t.id == _selectedTemplate!.id)

              .firstOrNull;

          if (matched != null) {

            _selectedTemplate = matched;

          }

        }

      });

    } catch (e) {

      if (!mounted) return;

      setState(() {

        _errorMessage = '$e';

        _loadingThumbnails = false;

      });

    }

  }



  Future<void> _toggleFavorite(TableTemplateInfo template) async {

    final newFav = !template.favorite;



    // 즉시 UI 반영 (낙관적 갱신)

    if (_listData != null) {

      final updatedTemplates = _listData!.templates.map((t) {

        if (t.id == template.id) {

          return t.copyWith(favorite: newFav);

        }

        return t;

      }).toList();

      setState(() {

        _listData = TableUnitsListData(

          source: _listData!.source,

          thumbnailsReady: _listData!.thumbnailsReady,

          recent: _listData!.recent,

          templates: updatedTemplates,

        );

        if (_selectedTemplate?.id == template.id) {

          _selectedTemplate = _selectedTemplate!.copyWith(favorite: newFav);

        }

      });

    }



    try {

      final data = await _api.favorite(template.id, newFav);

      if (!mounted) return;

      setState(() {

        _listData = data;

        if (_selectedTemplate != null) {

          final matched = data.templates

              .where((t) => t.id == _selectedTemplate!.id)

              .firstOrNull;

          if (matched != null) {

            _selectedTemplate = matched;

          }

        }

      });

    } catch (e) {

      // 오류 시 롤백

      if (!mounted) return;

      if (_listData != null) {

        final rolledBack = _listData!.templates.map((t) {

          if (t.id == template.id) {

            return t.copyWith(favorite: !newFav);

          }

          return t;

        }).toList();

        setState(() {

          _listData = TableUnitsListData(

            source: _listData!.source,

            thumbnailsReady: _listData!.thumbnailsReady,

            recent: _listData!.recent,

            templates: rolledBack,

          );

          if (_selectedTemplate?.id == template.id) {

            _selectedTemplate = _selectedTemplate!.copyWith(favorite: !newFav);

          }

        });

      }

      ScaffoldMessenger.of(context).showSnackBar(

        SnackBar(

          content: Text('즐겨찾기 변경 실패: $e'),

          behavior: SnackBarBehavior.floating,

        ),

      );

    }

  }



  void _selectTemplate(TableTemplateInfo template) {

    setState(() {

      _selectedTemplate = template;

      _currentRowCount = template.units.row?.count;

      _currentColCount = template.units.col?.count;

      _selectedFill = 'increment';

      _arrow = null;

      _cellTexts = {};

      _previewShapes = {};

      _copyErrorMessage = null;

    });

    _requestPreview();

  }



  Future<void> _requestPreview() async {

    if (_selectedTemplate == null) return;

    final seq = ++_previewSeq;

    setState(() {

      _loadingPreview = true;

      _previewError = null;

    });

    try {

      final payload = <String, Object?>{

        'id': _selectedTemplate!.id,

        'row_count': _currentRowCount,

        'col_count': _currentColCount,

        'fill': _selectedFill,

        if (_arrow != null) 'arrow': _arrow,

        'cell_texts': _cellTexts.isNotEmpty ? Map.from(_cellTexts) : const {},

      };



      final res = await widget.api('table_units', ['preview', payload]);

      if (!mounted || seq != _previewSeq) return;



      if (res is! Map || res['ok'] != true) {

        final err = res is Map ? res['error'] as Map? : null;

        throw ServiceApiException(

          '${err?['code'] ?? 'UNKNOWN'}',

          '${err?['message'] ?? '미리보기를 불러오지 못했습니다.'}',

          true,

        );

      }



      final data = res['data'] as Map? ?? const {};

      final preview = TablePreview.fromJson(data);



      // shapes 추출

      final extractedShapes = <String, List<CellShape>>{};

      final rawMeta = data['cell_meta'];

      if (rawMeta is List) {

        for (final rowItem in rawMeta) {

          if (rowItem is List) {

            for (final cellItem in rowItem) {

              if (cellItem is Map) {

                final r = (cellItem['row'] as num?)?.toInt();

                final c = (cellItem['col'] as num?)?.toInt();

                final rawShapes = cellItem['shapes'];

                if (r != null &&

                    c != null &&

                    rawShapes is List &&

                    rawShapes.isNotEmpty) {

                  final list = <CellShape>[];

                  for (final s in rawShapes) {

                    if (s is Map) {

                      list.add(CellShape.fromJson(s));

                    }

                  }

                  if (list.isNotEmpty) {

                    extractedShapes['$r,$c'] = list;

                  }

                }

              }

            }

          }

        }

      }



      // 범위 벗어난 입력 버리기 검사

      int prunedCount = 0;

      final keysToRemove = <String>[];

      for (final key in _cellTexts.keys) {

        final parts = key.split(',');

        if (parts.length == 2) {

          final r = int.tryParse(parts[0]);

          final c = int.tryParse(parts[1]);

          if (r != null && c != null) {

            if (r >= preview.rows || c >= preview.cols) {

              keysToRemove.add(key);

              prunedCount++;

            }

          }

        }

      }

      if (keysToRemove.isNotEmpty) {

        for (final k in keysToRemove) {

          _cellTexts.remove(k);

        }

      }



      setState(() {

        _previewData = preview;

        _previewShapes = extractedShapes;

        _loadingPreview = false;

      });



      if (prunedCount > 0 && mounted) {

        ScaffoldMessenger.of(context).showSnackBar(

          SnackBar(

            content: Text('단위 개수 변경으로 범위를 벗어난 입력 글 $prunedCount개를 정리했어요.'),

            behavior: SnackBarBehavior.floating,

            duration: const Duration(seconds: 2),

          ),

        );

      }

    } catch (e) {

      if (!mounted || seq != _previewSeq) return;

      setState(() {

        _previewError = '$e';

        _previewShapes = {};

        _loadingPreview = false;

      });

    }

  }



  Future<void> _copyTable() async {

    if (_selectedTemplate == null || _copying) return;

    setState(() {

      _copying = true;

      _copyErrorMessage = null;

    });

    try {

      final result = await _api.copy(

        _selectedTemplate!.id,

        rowCount: _currentRowCount,

        colCount: _currentColCount,

        fill: _selectedFill,

        arrow: _arrow,

        cellTexts: _cellTexts.isNotEmpty ? Map.from(_cellTexts) : null,

      );

      if (!mounted) return;

      final notice = result.activated

          ? '한/글 창을 앞으로 가져왔어요. Ctrl+V로 붙여넣으세요.'

          : '한/글 문서에서 붙여넣을 곳을 누르고 Ctrl+V 하세요.';

      ScaffoldMessenger.of(context).showSnackBar(

        SnackBar(content: Text(notice), behavior: SnackBarBehavior.floating),

      );

    } catch (e) {

      if (!mounted) return;

      setState(() {

        _copyErrorMessage = '$e';

      });

    } finally {

      if (mounted) {

        setState(() => _copying = false);

      }

    }

  }



  Future<void> _editCellText(int row, int col) async {

    final key = '$row,$col';

    final existingText = _cellTexts[key] ?? '';

    // 입력 창이 닫히는 애니메이션 동안에도 입력 상자가 그려지므로, 컨트롤러는 창 위젯이 스스로 만들고 폐기한다.

    final newText = await showDialog<String>(

      context: context,

      builder: (ctx) =>

          _CellTextDialog(row: row, col: col, initial: existingText),

    );



    if (newText != null) {

      final trimmed = newText.trim();

      setState(() {

        if (trimmed.isEmpty) {

          _cellTexts.remove(key);

        } else {

          _cellTexts[key] = trimmed;

        }

      });

      _requestPreview();

    }

  }



  Uint8List? _decodeBase64(String? base64Str) {

    if (base64Str == null || base64Str.isEmpty) return null;

    try {

      var raw = base64Str;

      final commaIndex = raw.indexOf(',');

      if (commaIndex != -1) {

        raw = raw.substring(commaIndex + 1);

      }

      raw = raw.replaceAll(RegExp(r'\s+'), '');

      return base64Decode(raw);

    } catch (_) {

      return null;

    }

  }



  List<String> _getCategories() {

    final rawCats = <String>{};

    if (_listData != null) {

      for (final t in _listData!.templates) {

        if (t.category.isNotEmpty &&

            t.category != '전체' &&

            t.category != '즐겨찾기' &&

            t.category != '최근 사용') {

          rawCats.add(t.category);

        }

      }

    }

    return ['즐겨찾기', '최근 사용', '전체', ...rawCats];

  }



  List<TableTemplateInfo> _getFilteredTemplates() {

    if (_listData == null) return const [];

    List<TableTemplateInfo> list;



    if (_selectedCategory == '즐겨찾기') {

      list = _listData!.templates.where((t) => t.favorite).toList();

    } else if (_selectedCategory == '최근 사용') {

      final map = {for (final t in _listData!.templates) t.id: t};

      list = [];

      for (final id in _listData!.recent) {

        if (map.containsKey(id)) {

          list.add(map[id]!);

        }

      }

    } else if (_selectedCategory == '전체') {

      list = _listData!.templates;

    } else {

      list = _listData!.templates

          .where((t) => t.category == _selectedCategory)

          .toList();

    }



    final query = _searchQuery.trim().toLowerCase();

    if (query.isNotEmpty) {

      list = list.where((t) {

        final nameMatch = t.name.toLowerCase().contains(query);

        final catMatch = t.category.toLowerCase().contains(query);

        return nameMatch || catMatch;

      }).toList();

    }



    return list;

  }



  @override

  Widget build(BuildContext context) {

    return Scaffold(

      appBar: AppBar(

        title: const Text('표 템플릿'),

        actions: [

          if (_loadingThumbnails)

            const Padding(

              padding: EdgeInsets.symmetric(horizontal: 16),

              child: Center(

                child: SizedBox(

                  width: 20,

                  height: 20,

                  child: CircularProgressIndicator(strokeWidth: 2),

                ),

              ),

            )

          else

            TextButton.icon(

              key: const Key('btnGenerateThumbnails'),

              icon: const Icon(Icons.photo_camera_outlined, size: 18),

              label: const Text('스냅샷 새로 만들기'),

              onPressed: (_loadingList || _loadingThumbnails)

                  ? null

                  : _generateThumbnails,

            ),

          const SizedBox(width: 8),

        ],

      ),

      body: _buildBody(),

    );

  }



  Widget _buildBody() {

    if (_loadingList) {

      return const Center(child: CircularProgressIndicator());

    }



    if (_errorMessage != null) {

      return Center(

        child: Padding(

          padding: const EdgeInsets.all(24),

          child: Column(

            mainAxisSize: MainAxisSize.min,

            children: [

              Text(

                _errorMessage!,

                key: const Key('errorMessage'),

                style: const TextStyle(color: Color(0xfff04452), fontSize: 15),

                textAlign: TextAlign.center,

              ),

              const SizedBox(height: 16),

              FilledButton(onPressed: _loadList, child: const Text('다시 시도')),

            ],

          ),

        ),

      );

    }



    return LayoutBuilder(

      builder: (context, constraints) {

        final isWide = constraints.maxWidth >= 760;



        if (isWide) {

          final maxLeft = (constraints.maxWidth - 280.0).clamp(220.0, constraints.maxWidth);

          final defaultLeft = math.min(460.0, constraints.maxWidth * 0.42).clamp(240.0, maxLeft);

          final leftWidth = (_leftPaneWidth ?? defaultLeft).clamp(220.0, maxLeft);



          return Row(

            crossAxisAlignment: CrossAxisAlignment.stretch,

            children: [

              SizedBox(

                width: leftWidth,

                child: _buildGallery(),

              ),

              MouseRegion(

                cursor: SystemMouseCursors.resizeColumn,

                child: GestureDetector(

                  behavior: HitTestBehavior.translucent,

                  onHorizontalDragUpdate: (details) {

                    setState(() {

                      _leftPaneWidth = (leftWidth + details.delta.dx).clamp(220.0, maxLeft);

                    });

                  },

                  onDoubleTap: () {

                    setState(() {

                      _leftPaneWidth = defaultLeft;

                    });

                  },

                  child: Container(

                    width: 10,

                    color: const Color(0xfff8fafc),

                    child: Stack(

                      alignment: Alignment.center,

                      children: [

                        Container(

                          width: 1,

                          color: const Color(0xffcbd5e1),

                        ),

                        Container(

                          width: 4,

                          height: 36,

                          decoration: BoxDecoration(

                            color: const Color(0xff94a3b8),

                            borderRadius: BorderRadius.circular(2),

                          ),

                        ),

                      ],

                    ),

                  ),

                ),

              ),

              Expanded(

                child: Scrollbar(

                  controller: _detailScrollController,

                  thumbVisibility: true,

                  child: SingleChildScrollView(

                    controller: _detailScrollController,

                    padding: const EdgeInsets.all(24),

                    child: _buildDetail(),

                  ),

                ),

              ),

            ],

          );

        } else {

          return Scrollbar(

            child: SingleChildScrollView(

              child: Column(

                crossAxisAlignment: CrossAxisAlignment.stretch,

                children: [

                  _buildGallery(shrinkWrap: true),

                  const Divider(

                    height: 1,

                    thickness: 1,

                    color: Color(0xffe2e8f0),

                  ),

                  Padding(

                    padding: const EdgeInsets.all(16),

                    child: _buildDetail(),

                  ),

                ],

              ),

            ),

          );

        }

      },

    );

  }



  Widget _buildGallery({bool shrinkWrap = false}) {

    final categories = _getCategories();

    final templates = _getFilteredTemplates();



    final headerSliver = SliverToBoxAdapter(

      child: Padding(

        padding: const EdgeInsets.fromLTRB(16, 10, 16, 6),

        child: Column(

          crossAxisAlignment: CrossAxisAlignment.stretch,

          children: [

            // 1. 전폭 검색 바 (불필요한 중복 드롭다운 제거로 검색 편의성 극대화)

            SizedBox(

              height: 36,

              child: TextField(

                key: const Key('searchTextField'),

                controller: _searchController,

                decoration: InputDecoration(

                  contentPadding: const EdgeInsets.symmetric(horizontal: 12),

                  hintText: '이름 또는 분류 검색 (예: 일정표, 부연설명)',

                  hintStyle: const TextStyle(

                    fontSize: 12,

                    color: Color(0xff94a3b8),

                  ),

                  prefixIcon: const Icon(

                    Icons.search,

                    size: 16,

                    color: Color(0xff64748b),

                  ),

                  suffixIcon: _searchQuery.isNotEmpty

                      ? IconButton(

                          icon: const Icon(Icons.clear, size: 14),

                          padding: EdgeInsets.zero,

                          onPressed: () {

                            _searchController.clear();

                            setState(() => _searchQuery = '');

                          },

                        )

                      : null,

                  filled: true,

                  fillColor: const Color(0xfff1f5f9),

                  border: OutlineInputBorder(

                    borderRadius: BorderRadius.circular(8),

                    borderSide: BorderSide.none,

                  ),

                ),

                style: const TextStyle(fontSize: 12.5),

                onChanged: (val) {

                  setState(() => _searchQuery = val);

                },

              ),

            ),

            const SizedBox(height: 6),

            // 2. PPT 스타일 가로 1줄 분류 리본 (SingleChildScrollView horizontal with < > scroll buttons)

            Container(

              height: 36,

              padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 3),

              decoration: BoxDecoration(

                color: const Color(0xfff8fafc),

                borderRadius: BorderRadius.circular(8),

                border: Border.all(color: const Color(0xffe2e8f0)),

              ),

              child: Row(

                children: [

                  // 좌측 스크롤 화살표

                  InkWell(

                    key: const Key('btnCategoryRibbonLeft'),

                    borderRadius: BorderRadius.circular(4),

                    onTap: () {

                      if (_categoryRibbonController.hasClients) {

                        _categoryRibbonController.animateTo(

                          math.max(0.0, _categoryRibbonController.offset - 160),

                          duration: const Duration(milliseconds: 200),

                          curve: Curves.easeOut,

                        );

                      }

                    },

                    child: const SizedBox(

                      width: 22,

                      height: 28,

                      child: Icon(

                        Icons.chevron_left,

                        size: 16,

                        color: Color(0xff64748b),

                      ),

                    ),

                  ),

                  const SizedBox(width: 2),

                  // 가로 1줄 스크롤 칩 리스트

                  Expanded(

                    child: SingleChildScrollView(

                      controller: _categoryRibbonController,

                      scrollDirection: Axis.horizontal,

                      physics: const BouncingScrollPhysics(),

                      child: Row(

                        mainAxisSize: MainAxisSize.min,

                        children: categories.map((cat) {

                          final isSelected = _selectedCategory == cat;

                          return Padding(

                            padding: const EdgeInsets.symmetric(horizontal: 2),

                            child: Material(

                              key: Key('categoryChip_$cat'),

                              color: isSelected

                                  ? const Color(0xff2563eb)

                                  : Colors.white,

                              shape: RoundedRectangleBorder(

                                borderRadius: BorderRadius.circular(6),

                                side: BorderSide(

                                  color: isSelected

                                      ? const Color(0xff2563eb)

                                      : const Color(0xffcbd5e1),

                                ),

                              ),

                              child: InkWell(

                                borderRadius: BorderRadius.circular(6),

                                onTap: () {

                                  setState(() => _selectedCategory = cat);

                                },

                                child: Container(

                                  height: 28,

                                  padding: const EdgeInsets.symmetric(horizontal: 8),

                                  child: Row(

                                    mainAxisSize: MainAxisSize.min,

                                    mainAxisAlignment: MainAxisAlignment.center,

                                    crossAxisAlignment: CrossAxisAlignment.center,

                                    children: [

                                      if (isSelected) ...[

                                        const Icon(

                                          Icons.check,

                                          size: 12,

                                          color: Colors.white,

                                        ),

                                        const SizedBox(width: 3),

                                      ] else if (cat == '즐겨찾기') ...[

                                        const Icon(

                                          Icons.star,

                                          size: 12,

                                          color: Color(0xffeab308),

                                        ),

                                        const SizedBox(width: 3),

                                      ] else if (cat == '최근 사용') ...[

                                        const Icon(

                                          Icons.history,

                                          size: 12,

                                          color: Color(0xff64748b),

                                        ),

                                        const SizedBox(width: 3),

                                      ],

                                      Text(

                                        cat,

                                        maxLines: 1,

                                        style: TextStyle(

                                          fontSize: 11,

                                          height: 1.0,

                                          color: isSelected

                                              ? Colors.white

                                              : const Color(0xff334155),

                                          fontWeight: isSelected

                                              ? FontWeight.w700

                                              : FontWeight.w500,

                                        ),

                                      ),

                                    ],

                                  ),

                                ),

                              ),

                            ),

                          );

                        }).toList(),

                      ),

                    ),

                  ),

                  const SizedBox(width: 2),

                  // 우측 스크롤 화살표

                  InkWell(

                    key: const Key('btnCategoryRibbonRight'),

                    borderRadius: BorderRadius.circular(4),

                    onTap: () {

                      if (_categoryRibbonController.hasClients) {

                        _categoryRibbonController.animateTo(

                          _categoryRibbonController.offset + 160,

                          duration: const Duration(milliseconds: 200),

                          curve: Curves.easeOut,

                        );

                      }

                    },

                    child: const SizedBox(

                      width: 22,

                      height: 28,

                      child: Icon(

                        Icons.chevron_right,

                        size: 16,

                        color: Color(0xff64748b),

                      ),

                    ),

                  ),

                ],

              ),

            ),

            const SizedBox(height: 6),

            // 서식 개수 및 현재 분류 상태 표시줄

            Row(

              children: [

                Text(

                  '$_selectedCategory 서식',

                  style: const TextStyle(

                    fontSize: 12,

                    fontWeight: FontWeight.bold,

                    color: Color(0xff475569),

                  ),

                ),

                const SizedBox(width: 6),

                Container(

                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),

                  decoration: BoxDecoration(

                    color: const Color(0xffe2e8f0),

                    borderRadius: BorderRadius.circular(10),

                  ),

                  child: Text(

                    '${templates.length}개',

                    style: const TextStyle(

                      fontSize: 10.5,

                      fontWeight: FontWeight.w700,

                      color: Color(0xff334155),

                    ),

                  ),

                ),

              ],

            ),

          ],

        ),

      ),

    );



    final Widget bodySliver;

    if (templates.isEmpty) {

      bodySliver = const SliverToBoxAdapter(

        child: Center(

          child: Padding(

            padding: EdgeInsets.symmetric(vertical: 40),

            child: Text(

              '표 템플릿이 없습니다.',

              style: TextStyle(color: Color(0xff8b95a1)),

            ),

          ),

        ),

      );

    } else {

      bodySliver = SliverPadding(

        padding: const EdgeInsets.fromLTRB(16, 4, 16, 20),

        sliver: SliverGrid(

          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(

            crossAxisCount: 2,

            crossAxisSpacing: 10,

            mainAxisSpacing: 10,

            childAspectRatio: 0.82,

          ),

          delegate: SliverChildBuilderDelegate(

            (context, index) {

              final template = templates[index];

              final isSelected = _selectedTemplate?.id == template.id;

              final imageBytes = _decodeBase64(template.thumbnail);



              return GestureDetector(

                key: Key('templateCard_${template.id}'),

                onTap: () => _selectTemplate(template),

                child: AnimatedContainer(

                  duration: const Duration(milliseconds: 150),

                  decoration: BoxDecoration(

                    color: isSelected ? const Color(0xffedf3ff) : Colors.white,

                    borderRadius: BorderRadius.circular(10),

                    border: Border.all(

                      color: isSelected

                          ? const Color(0xff2563eb)

                          : const Color(0xffe2e8f0),

                      width: isSelected ? 2 : 1,

                    ),

                    boxShadow: const [

                      BoxShadow(

                        color: Color(0x0a000000),

                        blurRadius: 4,

                        offset: Offset(0, 2),

                      ),

                    ],

                  ),

                  child: Stack(

                    children: [

                      Column(

                        crossAxisAlignment: CrossAxisAlignment.stretch,

                        children: [

                          Expanded(

                            child: Container(

                              decoration: const BoxDecoration(

                                color: Color(0xfff8fafc),

                                borderRadius: BorderRadius.vertical(

                                  top: Radius.circular(8),

                                ),

                              ),

                              alignment: Alignment.center,

                              child: imageBytes != null

                                  ? Image.memory(imageBytes, fit: BoxFit.contain)

                                  : const Icon(

                                      Icons.table_chart_outlined,

                                      size: 36,

                                      color: Color(0xff94a3b8),

                                    ),

                            ),

                          ),

                          Padding(

                            padding: const EdgeInsets.all(8),

                            child: Column(

                              crossAxisAlignment: CrossAxisAlignment.start,

                              children: [

                                Text(

                                  template.name,

                                  style: const TextStyle(

                                    fontSize: 13,

                                    fontWeight: FontWeight.bold,

                                    color: Color(0xff1e293b),

                                  ),

                                  maxLines: 1,

                                  overflow: TextOverflow.ellipsis,

                                ),

                                const SizedBox(height: 4),

                                _buildUnitBadge(template),

                              ],

                            ),

                          ),

                        ],

                      ),

                      Positioned(

                        top: 2,

                        right: 2,

                        child: IconButton(

                          key: Key('btnFavorite_${template.id}'),

                          icon: Icon(

                            template.favorite ? Icons.star : Icons.star_border,

                            color: template.favorite

                                ? const Color(0xfff59e0b)

                                : const Color(0xff94a3b8),

                            size: 20,

                          ),

                          padding: EdgeInsets.zero,

                          constraints: const BoxConstraints(

                            minWidth: 32,

                            minHeight: 32,

                          ),

                          onPressed: () => _toggleFavorite(template),

                          tooltip: template.favorite ? '즐겨찾기 해제' : '즐겨찾기 추가',

                        ),

                      ),

                    ],

                  ),

                ),

              );

            },

            childCount: templates.length,

          ),

        ),

      );

    }



    if (shrinkWrap) {

      return CustomScrollView(

        shrinkWrap: true,

        physics: const NeverScrollableScrollPhysics(),

        slivers: [headerSliver, bodySliver],

      );

    }



    return Scrollbar(

      controller: _galleryScrollController,

      thumbVisibility: true,

      child: CustomScrollView(

        controller: _galleryScrollController,

        physics: const AlwaysScrollableScrollPhysics(),

        slivers: [headerSliver, bodySliver],

      ),

    );

  }



  Widget _buildUnitBadge(TableTemplateInfo template) {

    if (template.units.isFixed) {

      return Container(

        padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),

        decoration: BoxDecoration(

          color: const Color(0xfff1f5f9),

          borderRadius: BorderRadius.circular(4),

        ),

        child: const Text(

          '고정 표',

          style: TextStyle(

            fontSize: 11,

            color: Color(0xff64748b),

            fontWeight: FontWeight.w500,

          ),

        ),

      );

    }



    final parts = <String>[];

    if (template.units.row != null) {

      parts.add('행 ${template.units.row!.count}개');

    }

    if (template.units.col != null) {

      parts.add('열 ${template.units.col!.count}개');

    }

    final label = parts.join(' · ');



    return Container(

      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),

      decoration: BoxDecoration(

        color: const Color(0xffeff6ff),

        borderRadius: BorderRadius.circular(4),

      ),

      child: Text(

        '정보단위 $label',

        style: const TextStyle(

          fontSize: 11,

          color: Color(0xff2563eb),

          fontWeight: FontWeight.w600,

        ),

        maxLines: 1,

        overflow: TextOverflow.ellipsis,

      ),

    );

  }



  Widget _buildDetail() {

    final template = _selectedTemplate;

    if (template == null) {

      return const Center(

        child: Padding(

          padding: EdgeInsets.symmetric(vertical: 40),

          child: Text(

            '선택된 템플릿이 없습니다.',

            style: TextStyle(color: Color(0xff8b95a1)),

          ),

        ),

      );

    }



    return Column(

      crossAxisAlignment: CrossAxisAlignment.stretch,

      children: [

        Row(

          crossAxisAlignment: CrossAxisAlignment.center,

          children: [

            Expanded(

              child: Column(

                crossAxisAlignment: CrossAxisAlignment.start,

                children: [

                  Text(

                    template.name,

                    style: const TextStyle(

                      fontSize: 20,

                      fontWeight: FontWeight.bold,

                      color: Color(0xff1e293b),

                    ),

                  ),

                  const SizedBox(height: 4),

                  Text(

                    '${template.category} · 기본 ${template.rows}행 × ${template.cols}열',

                    style: const TextStyle(

                      fontSize: 13,

                      color: Color(0xff64748b),

                    ),

                  ),

                ],

              ),

            ),

            const SizedBox(width: 8),

            FilledButton.icon(

              key: const Key('btnTopCopyTable'),

              icon: _copying

                  ? const SizedBox(

                      width: 16,

                      height: 16,

                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),

                    )

                  : const Icon(Icons.content_copy_rounded, size: 16),

              label: Text(

                _copying ? '복사 중…' : '한/글로 복사 (Ctrl+V)',

                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold),

              ),

              style: FilledButton.styleFrom(

                backgroundColor: const Color(0xff2563eb),

                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),

              ),

              onPressed: (_loadingPreview || _copying) ? null : _copyTable,

            ),

                        if (_cellTexts.isNotEmpty)

              OutlinedButton.icon(

                key: const Key('btnClearCellTexts'),

                icon: const Icon(Icons.clear_all, size: 16),

                label: const Text('입력한 글 모두 지우기'),

                style: OutlinedButton.styleFrom(

                  foregroundColor: const Color(0xffef4444),

                  side: const BorderSide(color: Color(0xfffecaca)),

                  padding: const EdgeInsets.symmetric(

                    horizontal: 10,

                    vertical: 6,

                  ),

                  visualDensity: VisualDensity.compact,

                ),

                onPressed: () {

                  setState(() => _cellTexts.clear());

                  _requestPreview();

                },

              ),

          ],

        ),

        const SizedBox(height: 16),

        Container(

          key: const Key('tableGridPreview'),

          constraints: const BoxConstraints(minHeight: 180),

          padding: const EdgeInsets.all(16),

          decoration: BoxDecoration(

            color: const Color(0xfff8fafc),

            borderRadius: BorderRadius.circular(12),

            border: Border.all(color: const Color(0xffe2e8f0)),

          ),

          child: _loadingPreview

              ? const SizedBox(

                  height: 160,

                  child: Center(child: CircularProgressIndicator()),

                )

              : _previewError != null

              ? SizedBox(

                  height: 160,

                  child: Center(

                    child: Text(

                      _previewError!,

                      style: const TextStyle(color: Color(0xfff04452)),

                    ),

                  ),

                )

              : _previewData != null

              ? Column(

                  children: [

                    TableGridPreview(

                      rows: _previewData!.rows,

                      cols: _previewData!.cols,

                      cellMeta: _previewData!.cellMeta,

                      shapes: _previewShapes,

                      maxHeight: 340,

                      onCellTap: (r, c) => _editCellText(r, c),

                      editedCellKeys: _cellTexts.keys.toSet(),

                    ),

                    const SizedBox(height: 8),

                    const Text(

                      '칸을 누르면 글을 직접 입력할 수 있어요.',

                      style: TextStyle(fontSize: 11, color: Color(0xff94a3b8)),

                    ),

                  ],

                )

              : const SizedBox.shrink(),

        ),

        const SizedBox(height: 20),

        if (template.units.isFixed)

          Container(

            key: const Key('fixedTableNotice'),

            padding: const EdgeInsets.all(14),

            decoration: BoxDecoration(

              color: const Color(0xfff1f5f9),

              borderRadius: BorderRadius.circular(8),

              border: Border.all(color: const Color(0xffe2e8f0)),

            ),

            child: const Row(

              children: [

                Icon(Icons.info_outline, size: 18, color: Color(0xff64748b)),

                SizedBox(width: 8),

                Expanded(

                  child: Text(

                    '이 표는 정보단위 조절 없이 그대로 복사해요',

                    style: TextStyle(

                      fontSize: 14,

                      color: Color(0xff334155),

                      fontWeight: FontWeight.w500,

                    ),

                  ),

                ),

              ],

            ),

          )

        else ...[

          if (template.units.row != null)

            _buildStepper(

              axisLabel: '행 단위',

              count: _currentRowCount ?? template.units.row!.count,

              min: template.units.row!.min,

              max: template.units.row!.max,

              minusKey: const Key('btnRowMinus'),

              plusKey: const Key('btnRowPlus'),

              onMinus: () {

                final cur = _currentRowCount ?? template.units.row!.count;

                if (cur > template.units.row!.min) {

                  setState(() => _currentRowCount = cur - 1);

                  _requestPreview();

                }

              },

              onPlus: () {

                final cur = _currentRowCount ?? template.units.row!.count;

                if (cur < template.units.row!.max) {

                  setState(() => _currentRowCount = cur + 1);

                  _requestPreview();

                }

              },

            ),

          if (template.units.col != null) ...[

            const SizedBox(height: 10),

            _buildStepper(

              axisLabel: '열 단위',

              count: _currentColCount ?? template.units.col!.count,

              min: template.units.col!.min,

              max: template.units.col!.max,

              minusKey: const Key('btnColMinus'),

              plusKey: const Key('btnColPlus'),

              onMinus: () {

                final cur = _currentColCount ?? template.units.col!.count;

                if (cur > template.units.col!.min) {

                  setState(() => _currentColCount = cur - 1);

                  _requestPreview();

                }

              },

              onPlus: () {

                final cur = _currentColCount ?? template.units.col!.count;

                if (cur < template.units.col!.max) {

                  setState(() => _currentColCount = cur + 1);

                  _requestPreview();

                }

              },

            ),

            const SizedBox(height: 4),

            const Text(

              '열 단위를 늘려도 표 전체 폭은 그대로라 칸이 좁아져요. 긴 글은 붙여넣은 뒤 다듬어 주세요.',

              key: Key('colWidthNotice'),

              style: TextStyle(fontSize: 12, color: Colors.black54),

            ),

          ],

          const SizedBox(height: 14),

          // 3. 글 처리 방식 (fill)

          _buildFillSelector(),

        ],

        if ((_selectedTemplate?.arrows ?? 0) > 0) ...[
          const SizedBox(height: 14),
          _buildArrowSelector(),
        ],

        const SizedBox(height: 24),

        SizedBox(

          height: 48,

          child: FilledButton.icon(

            key: const Key('btnCopyTable'),

            icon: _copying

                ? const SizedBox(

                    width: 18,

                    height: 18,

                    child: CircularProgressIndicator(

                      strokeWidth: 2,

                      color: Colors.white,

                    ),

                  )

                : const Icon(Icons.copy_rounded, size: 20),

            label: Text(

              _copying ? '복사 중…' : '한/글에 붙여넣기용 복사',

              style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),

            ),

            onPressed: (_loadingPreview || _copying) ? null : _copyTable,

          ),

        ),

        if (_copyErrorMessage != null)

          Padding(

            padding: const EdgeInsets.only(top: 8),

            child: Text(

              _copyErrorMessage!,

              key: const Key('copyErrorMessage'),

              style: const TextStyle(

                color: Color(0xfff04452),

                fontSize: 13,

                fontWeight: FontWeight.w500,

              ),

            ),

          ),

      ],

    );

  }



  Future<void> _loadArrowCatalog() async {
    if (_arrowCatalog != null) return;
    try {
      final data = await _api.arrows();
      if (mounted) setState(() => _arrowCatalog = data);
    } catch (_) {}
  }

  void _chooseArrow(Map<String, Object?>? arrow) {
    setState(() => _arrow = arrow);
    _requestPreview();
  }

  /// 칸 사이 화살표 종류 고르기(2.0.6): 기호 화살표·공문서용 그림 화살표, 그림은 방향·크기도 고른다.
  Widget _buildArrowSelector() {
    _loadArrowCatalog();
    final catalog = _arrowCatalog;
    final symbols = (catalog?['symbols'] as List?)?.cast<Object?>() ?? const [];
    final images = (catalog?['images'] as List?)?.cast<Object?>() ?? const [];
    final kind = _arrow?['kind'];
    final value = _arrow?['value'];
    Widget box({required Key key, required bool selected, required VoidCallback onTap, required Widget child,
        double width = 40, double height = 40, String? tooltip}) {
      final tile = InkWell(
        key: key,
        onTap: onTap,
        borderRadius: BorderRadius.circular(6),
        child: Container(
          width: width,
          height: height,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: selected ? const Color(0xffdbeafe) : Colors.white,
            borderRadius: BorderRadius.circular(6),
            border: Border.all(
              color: selected ? const Color(0xff2563eb) : const Color(0xffcbd5e1),
              width: selected ? 2 : 1,
            ),
          ),
          child: child,
        ),
      );
      return tooltip == null ? tile : Tooltip(message: tooltip, child: tile);
    }

    Map<String, Object?> imageArrow(String style) => {
      'kind': 'image',
      'value': style,
      'direction': _arrow?['direction'] ?? 'auto',
      'size': _arrow?['size'] ?? 'medium',
    };
    return Container(
      key: const Key('arrowSelector'),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xffe2e8f0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Expanded(
                child: Text(
                  '화살표 모양',
                  style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Color(0xff334155)),
                ),
              ),
              TextButton(
                key: const Key('arrowReset'),
                onPressed: _arrow == null ? null : () => _chooseArrow(null),
                child: const Text('원래 화살표'),
              ),
            ],
          ),
          const SizedBox(height: 6),
          const Text('기호 화살표', style: TextStyle(fontSize: 12, color: Color(0xff64748b))),
          const SizedBox(height: 6),
          Wrap(
            spacing: 6,
            runSpacing: 6,
            children: [
              for (final symbol in symbols)
                box(
                  key: Key('arrowSymbol_$symbol'),
                  selected: kind == 'symbol' && value == symbol,
                  onTap: () => _chooseArrow({'kind': 'symbol', 'value': '$symbol'}),
                  child: Text('$symbol', style: const TextStyle(fontSize: 20, color: Color(0xff0f172a))),
                ),
            ],
          ),
          const SizedBox(height: 12),
          const Text('공문서용 그림 화살표', style: TextStyle(fontSize: 12, color: Color(0xff64748b))),
          const SizedBox(height: 6),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              for (final item in images.whereType<Map>())
                Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    box(
                      key: Key('arrowImage_${item['value']}'),
                      width: 64,
                      height: 52,
                      tooltip: '${item['label']}',
                      selected: kind == 'image' && value == item['value'],
                      onTap: () => _chooseArrow(imageArrow('${item['value']}')),
                      child: Padding(
                        padding: const EdgeInsets.all(6),
                        child: Image.memory(
                          UriData.parse('${item['src']}').contentAsBytes(),
                          fit: BoxFit.contain,
                        ),
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text('${item['label']}', style: const TextStyle(fontSize: 11, color: Color(0xff475569))),
                  ],
                ),
            ],
          ),
          if (kind == 'image') ...[
            const SizedBox(height: 12),
            Wrap(
              spacing: 16,
              runSpacing: 8,
              crossAxisAlignment: WrapCrossAlignment.center,
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('방향  ', style: TextStyle(fontSize: 13)),
                    DropdownButton<String>(
                      key: const Key('arrowDirection'),
                      value: '${_arrow?['direction'] ?? 'auto'}',
                      items: [
                        for (final pair in ((catalog?['directions'] as List?) ?? const []).whereType<List>())
                          DropdownMenuItem(value: '${pair[0]}', child: Text('${pair[1]}')),
                      ],
                      onChanged: (v) => _chooseArrow({..._arrow!, 'direction': v}),
                    ),
                  ],
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Text('크기  ', style: TextStyle(fontSize: 13)),
                    for (final pair in ((catalog?['sizes'] as List?) ?? const []).whereType<List>())
                      Padding(
                        padding: const EdgeInsets.only(right: 6),
                        child: ChoiceChip(
                          key: Key('arrowSize_${pair[0]}'),
                          label: Text('${pair[1]}'),
                          selected: (_arrow?['size'] ?? 'medium') == pair[0],
                          onSelected: (_) => _chooseArrow({..._arrow!, 'size': '${pair[0]}'}),
                        ),
                      ),
                  ],
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildFillSelector() {

    return Container(

      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),

      decoration: BoxDecoration(

        color: Colors.white,

        borderRadius: BorderRadius.circular(8),

        border: Border.all(color: const Color(0xffe2e8f0)),

      ),

      child: Column(

        crossAxisAlignment: CrossAxisAlignment.start,

        children: [

          const Text(

            '늘린 칸 글 처리',

            style: TextStyle(

              fontSize: 14,

              fontWeight: FontWeight.w600,

              color: Color(0xff334155),

            ),

          ),

          const SizedBox(height: 8),

          Wrap(

            spacing: 8,

            runSpacing: 6,

            children: [

              ChoiceChip(

                key: const Key('fillOption_increment'),

                label: const Text('번호 이어서(기본)'),

                selected: _selectedFill == 'increment',

                onSelected: (selected) {

                  if (selected && _selectedFill != 'increment') {

                    setState(() => _selectedFill = 'increment');

                    _requestPreview();

                  }

                },

              ),

              ChoiceChip(

                key: const Key('fillOption_blank'),

                label: const Text('비우기'),

                selected: _selectedFill == 'blank',

                onSelected: (selected) {

                  if (selected && _selectedFill != 'blank') {

                    setState(() => _selectedFill = 'blank');

                    _requestPreview();

                  }

                },

              ),

              ChoiceChip(

                key: const Key('fillOption_copy'),

                label: const Text('그대로'),

                selected: _selectedFill == 'copy',

                onSelected: (selected) {

                  if (selected && _selectedFill != 'copy') {

                    setState(() => _selectedFill = 'copy');

                    _requestPreview();

                  }

                },

              ),

            ],

          ),

        ],

      ),

    );

  }



  Widget _buildStepper({

    required String axisLabel,

    required int count,

    required int min,

    required int max,

    required Key minusKey,

    required Key plusKey,

    required VoidCallback onMinus,

    required VoidCallback onPlus,

  }) {

    final canMinus = count > min && !_loadingPreview;

    final canPlus = count < max && !_loadingPreview;



    return Container(

      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),

      decoration: BoxDecoration(

        color: Colors.white,

        borderRadius: BorderRadius.circular(8),

        border: Border.all(color: const Color(0xffe2e8f0)),

      ),

      child: Row(

        children: [

          Expanded(

            child: Text(

              '$axisLabel $count개',

              style: const TextStyle(

                fontSize: 15,

                fontWeight: FontWeight.w600,

                color: Color(0xff1e293b),

              ),

            ),

          ),

          IconButton.filledTonal(

            key: minusKey,

            icon: const Icon(Icons.remove, size: 18),

            onPressed: canMinus ? onMinus : null,

          ),

          const SizedBox(width: 8),

          IconButton.filledTonal(

            key: plusKey,

            icon: const Icon(Icons.add, size: 18),

            onPressed: canPlus ? onPlus : null,

          ),

        ],

      ),

    );

  }

}



class _CellTextDialog extends StatefulWidget {

  const _CellTextDialog({

    required this.row,

    required this.col,

    required this.initial,

  });

  final int row, col;

  final String initial;

  @override

  State<_CellTextDialog> createState() => _CellTextDialogState();

}



class _CellTextDialogState extends State<_CellTextDialog> {

  late final TextEditingController controller = TextEditingController(

    text: widget.initial,

  );



  @override

  void dispose() {

    controller.dispose();

    super.dispose();

  }



  @override

  Widget build(BuildContext context) => AlertDialog(

    title: Text('칸 글 입력 (${widget.row}행 ${widget.col}열)'),

    content: TextField(

      key: const Key('cellTextInputField'),

      controller: controller,

      maxLines: 4,

      autofocus: true,

      decoration: const InputDecoration(

        border: OutlineInputBorder(),

        hintText: '이 칸에 들어갈 글을 적어주세요.',

      ),

    ),

    actions: [

      TextButton(

        onPressed: () => Navigator.of(context).pop(null),

        child: const Text('취소'),

      ),

      FilledButton(

        key: const Key('btnSaveCellText'),

        onPressed: () => Navigator.of(context).pop(controller.text),

        child: const Text('확인'),

      ),

    ],

  );

}

