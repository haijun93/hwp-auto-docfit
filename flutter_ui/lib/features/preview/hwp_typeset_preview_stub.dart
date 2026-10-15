import 'package:flutter/material.dart';

/// 한/글 조판 미리보기(rhwp)는 웹 화면(WebView2)에서만 쓴다. 다른 환경에서는 기존 미리보기를 보인다.
class HwpTypesetPreview extends StatelessWidget {
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
  Widget build(BuildContext context) => fallback;
}
