import 'package:flutter/material.dart';

import '../../core/api/abbreviation_api.dart' show ApiCall;
import '../diagrams/diagram_editor_screen.dart';
import '../flows/flow_editor_screen.dart';
import '../table_sketch/table_sketch_screen.dart';
import '../table_units/table_units_screen.dart';
import 'tab_navigation_shell.dart';

/// Workspace adapter for Tab 1: Document Editor / Processing
class DocumentEditorAdapter extends StatelessWidget {
  const DocumentEditorAdapter({
    super.key,
    required this.child,
  });

  final Widget child;

  @override
  Widget build(BuildContext context) => KeyedSubtree(
        key: const ValueKey('tab-document-editor-adapter'),
        child: child,
      );
}

/// Workspace adapter for Tab 2: Table Templates
class TableTemplatesAdapter extends StatelessWidget {
  const TableTemplatesAdapter({
    super.key,
    required this.api,
  });

  final ApiCall api;

  @override
  Widget build(BuildContext context) => KeyedSubtree(
        key: const ValueKey('tab-table-templates-adapter'),
        child: TableUnitsScreen(api: api),
      );
}

/// Workspace adapter for Tab 3: Table Sketch
class TableSketchAdapter extends StatelessWidget {
  const TableSketchAdapter({
    super.key,
    required this.api,
  });

  final ApiCall api;

  @override
  Widget build(BuildContext context) => KeyedSubtree(
        key: const ValueKey('tab-table-sketch-adapter'),
        child: TableSketchScreen(api: api),
      );
}

/// Workspace adapter for Tab 4: Diagram Editor
class DiagramAdapter extends StatelessWidget {
  const DiagramAdapter({
    super.key,
    required this.api,
  });

  final ApiCall api;

  @override
  Widget build(BuildContext context) => KeyedSubtree(
        key: const ValueKey('tab-diagram-adapter'),
        child: DiagramEditorScreen(api: api),
      );
}

/// Workspace adapter for Tab 5: Mind Map / Flow Editor
class MindMapAdapter extends StatelessWidget {
  const MindMapAdapter({
    super.key,
    required this.api,
  });

  final ApiCall api;

  @override
  Widget build(BuildContext context) => KeyedSubtree(
        key: const ValueKey('tab-mindmap-adapter'),
        child: FlowEditorScreen(api: api, initialMode: 'flow'),
      );
}

/// Workspace adapter for Tab 6: File Format Conversion & Merge
class FileConversionAdapter extends StatelessWidget {
  const FileConversionAdapter({
    super.key,
    required this.child,
  });

  final Widget child;

  @override
  Widget build(BuildContext context) => KeyedSubtree(
        key: const ValueKey('tab-file-conversion-adapter'),
        child: child,
      );
}

/// Integrated 6-Tab Workspace Root Shell
class IntegratedWorkspace extends StatelessWidget {
  const IntegratedWorkspace({
    super.key,
    required this.api,
    required this.documentEditorWidget,
    required this.fileConversionWidget,
    this.initialIndex = 0,
    this.onTabChanged,
  });

  final ApiCall api;
  final Widget documentEditorWidget;
  final Widget fileConversionWidget;
  final int initialIndex;
  final ValueChanged<int>? onTabChanged;

  @override
  Widget build(BuildContext context) {
    return TabNavigationShell(
      initialIndex: initialIndex,
      onTabChanged: onTabChanged,
      documentEditor: DocumentEditorAdapter(child: documentEditorWidget),
      tableTemplates: TableTemplatesAdapter(api: api),
      tableSketch: TableSketchAdapter(api: api),
      diagram: DiagramAdapter(api: api),
      mindMap: MindMapAdapter(api: api),
      fileConversion: FileConversionAdapter(child: fileConversionWidget),
    );
  }
}
