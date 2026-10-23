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

  int? _currentRowCount;
  int? _currentColCount;
  String _selectedFill = 'increment';
  Map<String, String> _cellTexts = {};

  TablePreview? _previewData;
  int _previewSeq = 0;

  @override
  void initState() {
    super.initState();
    _api = TableUnitsApi(widget.api);
    _loadList();
  }

  @override
  void dispose() {
    _searchController.dispose();
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
      setState(() {
        _listData = data;
        _loadingList = false;
        if (data.templates.isNotEmpty) {
          _selectTemplate(data.templates.first);
        } else {
          _selectedTemplate = null;
          _previewData = null;
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
            _selectedTemplate =
                _selectedTemplate!.copyWith(favorite: !newFav);
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
      _cellTexts = {};
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
      final preview = await _api.preview(
        _selectedTemplate!.id,
        rowCount: _currentRowCount,
        colCount: _currentColCount,
        fill: _selectedFill,
        cellTexts: _cellTexts.isNotEmpty ? Map.from(_cellTexts) : null,
      );
      if (!mounted || seq != _previewSeq) return;

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
        cellTexts: _cellTexts.isNotEmpty ? Map.from(_cellTexts) : null,
      );
      if (!mounted) return;
      final notice = result.activated
          ? '한/글 창을 앞으로 가져왔어요. Ctrl+V로 붙여넣으세요.'
          : '한/글 문서에서 붙여넣을 곳을 누르고 Ctrl+V 하세요.';
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(notice),
          behavior: SnackBarBehavior.floating,
        ),
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
    final controller = TextEditingController(text: existingText);

    final newText = await showDialog<String>(
      context: context,
      builder: (ctx) {
        return AlertDialog(
          title: Text('칸 글 입력 ($row행 $col열)'),
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
              onPressed: () => Navigator.of(ctx).pop(null),
              child: const Text('취소'),
            ),
            FilledButton(
              key: const Key('btnSaveCellText'),
              onPressed: () => Navigator.of(ctx).pop(controller.text),
              child: const Text('확인'),
            ),
          ],
        );
      },
    );

    controller.dispose();

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
          return Row(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(
                width: math.min(460, constraints.maxWidth * 0.42),
                child: _buildGallery(),
              ),
              const VerticalDivider(
                width: 1,
                thickness: 1,
                color: Color(0xffe2e8f0),
              ),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(24),
                  child: _buildDetail(),
                ),
              ),
            ],
          );
        } else {
          return Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              SizedBox(height: 320, child: _buildGallery()),
              const Divider(height: 1, thickness: 1, color: Color(0xffe2e8f0)),
              Expanded(
                child: SingleChildScrollView(
                  padding: const EdgeInsets.all(16),
                  child: _buildDetail(),
                ),
              ),
            ],
          );
        }
      },
    );
  }

  Widget _buildGallery({bool shrinkWrap = false}) {
    final categories = _getCategories();
    final templates = _getFilteredTemplates();

    final Widget grid;
    if (templates.isEmpty) {
      grid = const Center(
        child: Padding(
          padding: EdgeInsets.symmetric(vertical: 40),
          child: Text(
            '표 템플릿이 없습니다.',
            style: TextStyle(color: Color(0xff8b95a1)),
          ),
        ),
      );
    } else {
      grid = GridView.builder(
        shrinkWrap: shrinkWrap,
        physics: shrinkWrap
            ? const NeverScrollableScrollPhysics()
            : const AlwaysScrollableScrollPhysics(),
        itemCount: templates.length,
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          crossAxisSpacing: 10,
          mainAxisSpacing: 10,
          childAspectRatio: 0.82,
        ),
        itemBuilder: (context, index) {
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
      );
    }

    return Padding(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          // 1. 검색창
          SizedBox(
            height: 40,
            child: TextField(
              key: const Key('searchTextField'),
              controller: _searchController,
              decoration: InputDecoration(
                contentPadding: const EdgeInsets.symmetric(horizontal: 12),
                hintText: '이름 또는 분류 검색',
                hintStyle: const TextStyle(fontSize: 13, color: Color(0xff94a3b8)),
                prefixIcon: const Icon(Icons.search, size: 18, color: Color(0xff64748b)),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, size: 16),
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
              style: const TextStyle(fontSize: 13),
              onChanged: (val) {
                setState(() => _searchQuery = val);
              },
            ),
          ),
          const SizedBox(height: 10),

          // 스냅샷 생성 안내
          if (_listData != null && !_listData!.thumbnailsReady)
            Container(
              key: const Key('thumbnailsNotice'),
              margin: const EdgeInsets.only(bottom: 10),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xfffffbeb),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xfffef3c7)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.info_outline, size: 16, color: Color(0xffd97706)),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      '한/글로 실제 모양 그림을 만들 수 있어요',
                      style: TextStyle(
                        fontSize: 12,
                        color: Color(0xff92400e),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                ],
              ),
            ),

          // 2. 분류 칩
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.only(bottom: 10),
            child: Row(
              children: categories.map((cat) {
                final selected = _selectedCategory == cat;
                return Padding(
                  padding: const EdgeInsets.only(right: 6),
                  child: ChoiceChip(
                    key: Key('categoryChip_$cat'),
                    label: Text(cat),
                    selected: selected,
                    onSelected: (val) {
                      if (val) {
                        setState(() => _selectedCategory = cat);
                      }
                    },
                  ),
                );
              }).toList(),
            ),
          ),

          if (shrinkWrap) grid else Expanded(child: grid),
        ],
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
            if (_cellTexts.isNotEmpty)
              OutlinedButton.icon(
                key: const Key('btnClearCellTexts'),
                icon: const Icon(Icons.clear_all, size: 16),
                label: const Text('입력한 글 모두 지우기'),
                style: OutlinedButton.styleFrom(
                  foregroundColor: const Color(0xffef4444),
                  side: const BorderSide(color: Color(0xfffecaca)),
                  padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
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
