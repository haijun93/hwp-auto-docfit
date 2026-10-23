import 'package:flutter/material.dart';

import '../../core/api/public_language_api.dart';

/// 공공언어 교정 제외어 관리 화면 (T12).
class ExclusionManagerScreen extends StatefulWidget {
  const ExclusionManagerScreen({
    super.key,
    required this.api,
  });

  final ApiCall api;

  @override
  State<ExclusionManagerScreen> createState() => _ExclusionManagerScreenState();
}

class _ExclusionManagerScreenState extends State<ExclusionManagerScreen> {
  late final PublicLanguageApi _api;
  final TextEditingController _inputController = TextEditingController();

  List<String> _exclusions = [];
  bool _loading = false;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _api = PublicLanguageApi(widget.api);
    _loadExclusions();
  }

  @override
  void dispose() {
    _inputController.dispose();
    super.dispose();
  }

  Future<void> _loadExclusions() async {
    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      final list = await _api.listExclusions();
      if (!mounted) return;
      setState(() {
        _exclusions = list;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = '$e';
        _loading = false;
      });
    }
  }

  Future<void> _addExclusion() async {
    final text = _inputController.text.trim();
    if (text.isEmpty) return;

    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      final list = await _api.addExclusions([text]);
      if (!mounted) return;
      _inputController.clear();
      setState(() {
        _exclusions = list;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = '$e';
        _loading = false;
      });
    }
  }

  Future<void> _deleteExclusion(int index) async {
    if (index < 0 || index >= _exclusions.length) return;
    final word = _exclusions[index];

    setState(() {
      _loading = true;
      _errorMessage = null;
    });
    try {
      final list = await _api.deleteExclusions([word]);
      if (!mounted) return;
      setState(() {
        _exclusions = list;
        _loading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _errorMessage = '$e';
        _loading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('교정 제외어 관리'),
      ),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              const Text(
                '등록된 제외어는 공공언어 검토 및 교정 대상에서 제외됩니다.',
                style: TextStyle(fontSize: 13, color: Color(0xff64748b)),
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Expanded(
                    child: TextField(
                      key: const Key('exclusionInput'),
                      controller: _inputController,
                      decoration: const InputDecoration(
                        labelText: '제외할 단어 입력',
                        hintText: '예: 금번, 익일',
                        border: OutlineInputBorder(),
                        isDense: true,
                      ),
                      onSubmitted: (_) => _addExclusion(),
                    ),
                  ),
                  const SizedBox(width: 8),
                  FilledButton.icon(
                    key: const Key('exclusionAdd'),
                    onPressed: _loading ? null : _addExclusion,
                    icon: const Icon(Icons.add, size: 18),
                    label: const Text('추가'),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              if (_loading) const LinearProgressIndicator(),
              if (_errorMessage != null)
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 8),
                  child: Text(
                    _errorMessage!,
                    style: const TextStyle(color: Colors.red, fontSize: 13),
                  ),
                ),
              const SizedBox(height: 8),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '제외어 목록 (${_exclusions.length}개)',
                    style: const TextStyle(
                      fontWeight: FontWeight.w700,
                      fontSize: 14,
                    ),
                  ),
                  IconButton(
                    tooltip: '새로고침',
                    icon: const Icon(Icons.refresh, size: 18),
                    onPressed: _loading ? null : _loadExclusions,
                  ),
                ],
              ),
              const Divider(),
              Expanded(
                child: _exclusions.isEmpty
                    ? Center(
                        child: Text(
                          _loading ? '불러오는 중...' : '등록된 제외어가 없습니다.',
                          style: const TextStyle(color: Color(0xff8b98ad)),
                        ),
                      )
                    : ListView.separated(
                        itemCount: _exclusions.length,
                        separatorBuilder: (_, _) => const Divider(height: 1),
                        itemBuilder: (context, i) {
                          final word = _exclusions[i];
                          return ListTile(
                            dense: true,
                            contentPadding:
                                const EdgeInsets.symmetric(horizontal: 8),
                            title: Text(
                              word,
                              style: const TextStyle(fontSize: 14),
                            ),
                            trailing: IconButton(
                              key: Key('exclusionDelete_$i'),
                              tooltip: '제외어 삭제',
                              icon: const Icon(
                                Icons.delete_outline,
                                color: Colors.redAccent,
                                size: 20,
                              ),
                              onPressed:
                                  _loading ? null : () => _deleteExclusion(i),
                            ),
                          );
                        },
                      ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
