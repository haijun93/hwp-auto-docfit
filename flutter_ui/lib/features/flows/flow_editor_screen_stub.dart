import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';

class FlowEditorScreen extends StatelessWidget {
  const FlowEditorScreen({super.key, required this.api, this.initialMode = 'diagram', this.isModal = true});
  final ApiCall api;
  final String initialMode;
  final bool isModal;
  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Center(child: Text('이 환경에서는 다이어그램·마인드맵 편집기를 지원하지 않아요.')));
}
