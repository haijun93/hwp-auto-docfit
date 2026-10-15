import 'package:flutter/material.dart';

import '../../core/api/abbreviation_api.dart';

class DiagramEditorScreen extends StatelessWidget {
  const DiagramEditorScreen({super.key, required this.api});
  final ApiCall api;

  @override
  Widget build(BuildContext context) => const Scaffold(
        body: Center(child: Text('도형 편집기는 Flutter Windows 앱에서만 사용할 수 있어요.')),
      );
}
