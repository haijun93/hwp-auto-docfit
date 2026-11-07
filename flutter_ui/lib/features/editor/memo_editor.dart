/// 메모 편집기 화면 조각(재사용 모듈). 제목 + 서식 도구줄 + 본문 + 자동 저장 표시('Saved') + 삭제.
///
/// 입력은 Flutter `TextField`가 그대로 받고(한글 IME 조합 포함), 서식·실행취소·평문 변환은 [EditorCore]에 맡긴다.
/// 저장 위치는 모른다: 자동 저장은 [MemoEditor.onAutoSave], 확정 저장은 쓰는 쪽(예: 노트북)이 [MemoEditorController]로 꺼내 간다.
library;

import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import 'editor_core.dart';
import 'markdown_format.dart';

/// 제목과 Markdown 본문.
class MemoDocument {
  const MemoDocument({required this.title, required this.markdown});
  final String title;
  final String markdown;

  bool get isBlank => markdown.trim().isEmpty;
}

enum MemoSaveState { saved, pending, saving, failed }

/// 편집기 밖에서 현재 내용을 읽을 때 쓴다.
class MemoEditorController {
  _MemoEditorState? _state;

  MemoDocument get document => _state?._document ?? const MemoDocument(title: '', markdown: '');
  List<PlainParagraph> get plainParagraphs => _state?._core.plainParagraphs() ?? const [];

  /// 기다리는 자동 저장이 있으면 바로 저장한다.
  Future<void> flush() async => _state?._flush();
}

class MemoEditor extends StatefulWidget {
  const MemoEditor({
    super.key,
    this.initial = const MemoDocument(title: '새 메모', markdown: ''),
    this.onAutoSave,
    this.onDelete,
    this.controller,
    this.createCore,
    this.autoSaveDelay = const Duration(milliseconds: 800),
    this.footer,
  });

  final MemoDocument initial;

  /// 내용이 바뀌고 [autoSaveDelay] 동안 멈추면 부른다. 없으면 표시만 'Saved'.
  final Future<void> Function(MemoDocument document)? onAutoSave;

  /// 휴지통(삭제)을 눌러 확인하면 부른다. 없으면 휴지통 단추를 숨긴다.
  final VoidCallback? onDelete;
  final MemoEditorController? controller;

  /// 편집 코어를 만든다. 없으면 [DartEditorCore](Rust 코어 연결 전 임시 구현).
  final EditorCore Function(String markdown)? createCore;
  final Duration autoSaveDelay;

  /// 본문 아래에 둘 위젯(예: '출처로 저장' 단추).
  final Widget? footer;

  @override
  State<MemoEditor> createState() => _MemoEditorState();
}

class _MemoEditorState extends State<MemoEditor> {
  late final EditorCore _core = (widget.createCore ?? (t) => DartEditorCore(text: t))(widget.initial.markdown);
  late final _title = TextEditingController(text: widget.initial.title);
  late final _body = TextEditingController(text: widget.initial.markdown);
  final _bodyFocus = FocusNode();
  Timer? _saveTimer;
  Timer? _groupTimer;
  MemoSaveState _save = MemoSaveState.saved;
  bool _syncing = false;

  MemoDocument get _document => MemoDocument(title: _title.text.trim(), markdown: _core.markdown);

  @override
  void initState() {
    super.initState();
    widget.controller?._state = this;
    _body.value = _core.value;
    _body.addListener(_onBodyChanged);
    _title.addListener(_scheduleSave);
  }

  @override
  void dispose() {
    if (widget.controller?._state == this) widget.controller!._state = null;
    _saveTimer?.cancel();
    _groupTimer?.cancel();
    _title.dispose();
    _body.dispose();
    _bodyFocus.dispose();
    super.dispose();
  }

  void _onBodyChanged() {
    if (_syncing) return;
    final before = _core.markdown;
    _core.updateFromInput(_body.value);
    if (_core.markdown != before) {
      // 잠시(0.7초) 멈추면 실행취소 단계를 끊는다(메모장처럼 단어·문장 단위로 되돌림).
      _groupTimer?.cancel();
      _groupTimer = Timer(const Duration(milliseconds: 700), _core.breakUndoGroup);
      _scheduleSave();
    } else {
      setState(() {}); // 커서 줄의 문단 형식 표시 갱신
    }
  }

  void _syncFromCore() {
    _syncing = true;
    _body.value = _core.value;
    _syncing = false;
    _scheduleSave();
  }

  void _scheduleSave() {
    _saveTimer?.cancel();
    setState(() => _save = MemoSaveState.pending);
    _saveTimer = Timer(widget.autoSaveDelay, () => unawaited(_flush()));
  }

  Future<void> _flush() async {
    _saveTimer?.cancel();
    _saveTimer = null;
    if (_save == MemoSaveState.saved) return;
    final save = widget.onAutoSave;
    if (save == null) {
      if (mounted) setState(() => _save = MemoSaveState.saved);
      return;
    }
    if (mounted) setState(() => _save = MemoSaveState.saving);
    try {
      await save(_document);
      if (mounted && _saveTimer == null) setState(() => _save = MemoSaveState.saved);
    } catch (_) {
      if (mounted) setState(() => _save = MemoSaveState.failed);
    }
  }

  void _command(EditorCommand command) {
    _core.apply(command);
    _syncFromCore();
    _bodyFocus.requestFocus();
  }

  void _undo() {
    _core.undo();
    _syncFromCore();
  }

  void _redo() {
    _core.redo();
    _syncFromCore();
  }

  Future<void> _link() async {
    final url = await showDialog<String>(context: context, builder: (_) => const _LinkDialog());
    if (url == null || url.trim().isEmpty) return;
    _core.insertLink(url);
    _syncFromCore();
    _bodyFocus.requestFocus();
  }

  Future<void> _delete() async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('메모 삭제'),
        content: const Text('이 메모를 지울까요? 되돌릴 수 없습니다.'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('취소')),
          FilledButton(
            key: const ValueKey('memo-delete-ok'),
            onPressed: () => Navigator.pop(context, true),
            child: const Text('삭제'),
          ),
        ],
      ),
    );
    if (ok == true) {
      _saveTimer?.cancel();
      _saveTimer = null;
      widget.onDelete?.call();
    }
  }

  String get _saveLabel => switch (_save) {
    MemoSaveState.saved => 'Saved',
    MemoSaveState.pending || MemoSaveState.saving => '저장 중…',
    MemoSaveState.failed => '저장 실패',
  };

  Widget _tool(String key, String tooltip, IconData icon, VoidCallback? onPressed) => IconButton(
    key: ValueKey(key),
    tooltip: tooltip,
    visualDensity: VisualDensity.compact,
    iconSize: 20,
    onPressed: onPressed,
    icon: Icon(icon),
  );

  Widget _toolbar() {
    const divider = SizedBox(height: 24, child: VerticalDivider(width: 12));
    return Wrap(
      key: const ValueKey('memo-toolbar'),
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        _tool('memo-undo', '실행취소 (Ctrl+Z)', Icons.undo, _core.canUndo ? _undo : null),
        _tool('memo-redo', '다시실행 (Ctrl+Y)', Icons.redo, _core.canRedo ? _redo : null),
        divider,
        Tooltip(
          message: '문단 형식',
          child: DropdownButton<int>(
            key: const ValueKey('memo-block-style'),
            value: _core.blockStyle,
            underline: const SizedBox.shrink(),
            isDense: true,
            items: [
              for (final e in kMemoBlockStyles.entries)
                DropdownMenuItem(key: ValueKey('memo-block-style-${e.key}'), value: e.key, child: Text(e.value)),
            ],
            onChanged: (level) {
              if (level == null) return;
              _core.setBlockStyle(level);
              _syncFromCore();
              _bodyFocus.requestFocus();
            },
          ),
        ),
        divider,
        _tool('memo-bold', '굵게 (Ctrl+B)', Icons.format_bold, () => _command(EditorCommand.bold)),
        _tool('memo-italic', '기울임 (Ctrl+I)', Icons.format_italic, () => _command(EditorCommand.italic)),
        _tool('memo-link', '링크 (Ctrl+K)', Icons.link, _link),
        divider,
        _tool('memo-code', '인라인 코드', Icons.code, () => _command(EditorCommand.inlineCode)),
        _tool('memo-code-block', '코드 블록', Icons.data_object, () => _command(EditorCommand.codeBlock)),
        divider,
        _tool('memo-bullet', '글머리 목록', Icons.format_list_bulleted, () => _command(EditorCommand.bulletList)),
        _tool('memo-numbered', '번호 목록', Icons.format_list_numbered, () => _command(EditorCommand.numberedList)),
        _tool('memo-quote', '인용', Icons.format_quote, () => _command(EditorCommand.quote)),
        _tool('memo-rule', '구분선', Icons.horizontal_rule, () => _command(EditorCommand.horizontalRule)),
        divider,
        _tool('memo-clear', '서식 지우기', Icons.format_clear, () => _command(EditorCommand.clearFormatting)),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final muted = Theme.of(context).colorScheme.onSurfaceVariant;
    return CallbackShortcuts(
      // TextField 자체 실행취소 대신 코어 이력을 쓴다(가까운 조상 단축키가 앱 기본 단축키보다 먼저 받는다).
      bindings: {
        const SingleActivator(LogicalKeyboardKey.keyZ, control: true): _undo,
        const SingleActivator(LogicalKeyboardKey.keyY, control: true): _redo,
        const SingleActivator(LogicalKeyboardKey.keyZ, control: true, shift: true): _redo,
        const SingleActivator(LogicalKeyboardKey.keyB, control: true): () => _command(EditorCommand.bold),
        const SingleActivator(LogicalKeyboardKey.keyI, control: true): () => _command(EditorCommand.italic),
        const SingleActivator(LogicalKeyboardKey.keyK, control: true): () => unawaited(_link()),
      },
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            children: [
              Expanded(
                child: TextField(
                  key: const ValueKey('memo-title'),
                  controller: _title,
                  style: Theme.of(context).textTheme.titleLarge,
                  decoration: const InputDecoration(hintText: '제목', border: InputBorder.none),
                ),
              ),
              Text(_saveLabel, key: const ValueKey('memo-status'), style: TextStyle(fontSize: 12, color: muted)),
              if (widget.onDelete != null)
                _tool('memo-delete', '메모 삭제', Icons.delete_outline, () => unawaited(_delete())),
            ],
          ),
          _toolbar(),
          const Divider(height: 1),
          Expanded(
            child: TextField(
              key: const ValueKey('memo-body'),
              controller: _body,
              focusNode: _bodyFocus,
              maxLines: null,
              expands: true,
              keyboardType: TextInputType.multiline,
              textAlignVertical: TextAlignVertical.top,
              style: const TextStyle(fontSize: 14, height: 1.5),
              decoration: const InputDecoration(
                hintText: '메모를 쓰세요. 서식은 Markdown으로 저장됩니다.',
                border: InputBorder.none,
                contentPadding: EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),
          ?widget.footer,
        ],
      ),
    );
  }
}

class _LinkDialog extends StatefulWidget {
  const _LinkDialog();

  @override
  State<_LinkDialog> createState() => _LinkDialogState();
}

class _LinkDialogState extends State<_LinkDialog> {
  final _controller = TextEditingController(text: 'https://');

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => AlertDialog(
    title: const Text('링크'),
    content: TextField(
      key: const ValueKey('memo-link-url'),
      controller: _controller,
      autofocus: true,
      decoration: const InputDecoration(labelText: '주소'),
      onSubmitted: (v) => Navigator.pop(context, v),
    ),
    actions: [
      TextButton(onPressed: () => Navigator.pop(context), child: const Text('취소')),
      FilledButton(
        key: const ValueKey('memo-link-ok'),
        onPressed: () => Navigator.pop(context, _controller.text),
        child: const Text('넣기'),
      ),
    ],
  );
}
