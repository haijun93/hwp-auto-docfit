import 'dart:async';
import 'dart:convert';
import 'dart:js_interop';
import 'dart:ui_web' as ui_web;

import 'package:flutter/material.dart';
import 'package:web/web.dart' as web;

import '../settings/kiosk_theme.dart';

/// 한/글 조판 미리보기: rhwp(@rhwp/core, MIT) WASM 조판 엔진이 명세를 실제 HWP 문서로 만들어
/// 한/글처럼 줄을 나누고 정렬한 결과를 보인다(assets/hwp_preview). 같은 출처 iframe + postMessage.
/// 엔진을 불러오지 못하면 [fallback](기존 Flutter 미리보기)을 보인다.
class HwpTypesetPreview extends StatefulWidget {
  const HwpTypesetPreview({
    super.key,
    required this.spec,
    required this.fallback,
    this.minHeight = 120,
    this.maxHeight = 640,
  });

  final Map<String, Object?> spec;
  final Widget fallback;
  final double minHeight;
  final double maxHeight;

  @override
  State<HwpTypesetPreview> createState() => _HwpTypesetPreviewState();
}

class _HwpTypesetPreviewState extends State<HwpTypesetPreview> {
  late final String viewType;
  late final web.HTMLIFrameElement frame;
  late final JSFunction listener;
  bool ready = false, failed = false;
  double? height;
  List<Object?> lines = const [];
  int requestId = 0;
  String sent = '';
  Timer? debounce;

  @override
  void initState() {
    super.initState();
    viewType =
        'docfit-hwp-preview-${DateTime.now().microsecondsSinceEpoch}-$hashCode';
    frame = web.HTMLIFrameElement()
      ..src = Uri.base
          .resolve('assets/assets/hwp_preview/index.html')
          .toString()
      ..title = '한/글 조판 미리보기'
      ..setAttribute('sandbox', 'allow-scripts allow-same-origin')
      ..style.border = '0'
      ..style.width = '100%'
      ..style.height = '100%';
    ui_web.platformViewRegistry.registerViewFactory(viewType, (_) => frame);
    listener = ((web.MessageEvent event) {
      if (event.origin != web.window.location.origin ||
          event.source != frame.contentWindow) {
        return;
      }
      final data = event.data.dartify();
      if (data is! Map || !mounted) return;
      switch (data['type']) {
        case 'ready':
          setState(() => ready = true);
          _send(force: true);
        case 'rendered':
          if (data['requestId'] == requestId) {
            setState(() {
              height = (data['height'] as num?)?.toDouble();
              lines = data['lines'] as List? ?? const [];
            });
          }
        case 'preview_error':
          setState(() => failed = true);
      }
    }).toJS;
    web.window.addEventListener('message', listener);
  }

  void _send({bool force = false}) {
    if (!ready) return;
    final encoded = jsonEncode(widget.spec);
    if (!force && encoded == sent) return;
    sent = encoded;
    requestId++;
    frame.contentWindow?.postMessage(
      {'type': 'render', 'requestId': requestId, 'spec': widget.spec}.jsify(),
      web.window.location.origin.toJS,
    );
  }

  @override
  void didUpdateWidget(HwpTypesetPreview oldWidget) {
    super.didUpdateWidget(oldWidget);
    // 값을 빠르게 바꿀 때는 마지막 값만 그린다.
    debounce?.cancel();
    debounce = Timer(const Duration(milliseconds: 180), _send);
  }

  @override
  void dispose() {
    debounce?.cancel();
    web.window.removeEventListener('message', listener);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (failed) return widget.fallback;
    final shown = (height ?? widget.minHeight)
        .clamp(widget.minHeight, widget.maxHeight)
        .toDouble();
    final counted = lines.whereType<num>().toList();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          height: shown,
          decoration: BoxDecoration(
            color: Colors.white,
            border: Border.all(color: Kiosk.line),
            borderRadius: BorderRadius.circular(12),
          ),
          clipBehavior: Clip.antiAlias,
          child: Stack(
            children: [
              HtmlElementView(viewType: viewType),
              if (!ready || height == null)
                const Center(
                  child: Text('한/글 조판 엔진을 준비하고 있어요…', style: Kiosk.caption),
                ),
            ],
          ),
        ),
        const SizedBox(height: 6),
        Text(
          counted.isEmpty
              ? '한/글과 같은 방식(rhwp 조판 엔진)으로 줄을 나눈 결과예요.'
              : '한/글과 같은 방식(rhwp 조판 엔진)으로 줄을 나눈 결과예요 · 문단별 줄 수 ${counted.map((n) => n.toInt()).join('·')}',
          style: Kiosk.caption,
        ),
      ],
    );
  }
}
