import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';

class FlowEditorScreen extends StatelessWidget {
  const FlowEditorScreen({super.key, required this.api});
  final ApiCall api;
  @override
  Widget build(BuildContext context) =>
      const Scaffold(body: Center(child: Text('이 환경에서는 흐름도 편집기를 지원하지 않아요.')));
}
