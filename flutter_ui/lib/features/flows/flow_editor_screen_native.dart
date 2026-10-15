import 'package:flutter/material.dart';
import '../../core/api/abbreviation_api.dart';
import '../diagrams/diagram_editor_screen_native.dart';

class FlowEditorScreen extends StatelessWidget {
  const FlowEditorScreen({super.key, required this.api});
  final ApiCall api;
  @override
  Widget build(BuildContext context) =>
      DiagramEditorScreen(api: api, useTldraw: false);
}
