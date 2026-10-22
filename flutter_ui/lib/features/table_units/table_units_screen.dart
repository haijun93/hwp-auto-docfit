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
  TableTemplateInfo? _selectedTemplate;

  int? _currentRowCount;
  int? _currentColCount;

  TablePreview? _previewData;
  int _previewSeq = 0;

  @override
  void initState() {
    super.initState();
    _api = TableUnitsApi(widget.api);
    _loadList();
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

  void _selectTemplate(TableTemplateInfo template) {
    setState(() {
      _selectedTemplate = template;
      _currentRowCount = template.units.row?.count;
      _currentColCount = template.units.col?.count;
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
      );
      if (!mounted || seq != _previewSeq) return;
      setState(() {
        _previewData = preview;
        _loadingPreview = false;
      });
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
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text(result.message),
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
    final set = <String>{'전체'};
    if (_listData != null) {
      for (final t in _listData!.templates) {
        if (t.category.isNotEmpty) {
          set.add(t.category);
        }
      }
    }
    return set.toList();
  }

  List<TableTemplateInfo> _getFilteredTemplates() {
    if (_listData == null) return const [];
    if (_selectedCategory == '전체') {
      return _listData!.templates;
    }
    return _listData!.templates
        .where((t) => t.category == _selectedCategory)
        .toList();
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
              SizedBox(height: 260, child: _buildGallery()),
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
                boxShadow: [
                  BoxShadow(
                    color: const Color(0x0a000000),
                    blurRadius: 4,
                    offset: const Offset(0, 2),
                  ),
                ],
              ),
              child: Column(
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
          if (_listData != null && !_listData!.thumbnailsReady)
            Container(
              key: const Key('thumbnailsNotice'),
              margin: const EdgeInsets.only(bottom: 12),
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              decoration: BoxDecoration(
                color: const Color(0xfffffbeb),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xfffef3c7)),
              ),
              child: Row(
                children: const [
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
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.only(bottom: 12),
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
              ? TableGridPreview(
                  rows: _previewData!.rows,
                  cols: _previewData!.cols,
                  cellMeta: _previewData!.cellMeta,
                  maxHeight: 340,
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
