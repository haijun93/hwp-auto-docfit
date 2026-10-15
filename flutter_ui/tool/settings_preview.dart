// QA 진입점: 공개 기본 자료 또는 임시 --dart-define-from-file 자료로 화면만 띄운다.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:docfit_ui/features/settings/settings_dialog.dart';

import 'preview_data.dart';

void main() {
  final data = jsonDecode(previewSettingsJson) as Map;
  Future<Object?> api(String method, List<Object?> args) async => {
    'api_version': 1,
    'ok': true,
    'data': data,
    'error': null,
  };
  runApp(
    MaterialApp(
      debugShowCheckedModeBanner: false,
      theme: ThemeData(fontFamily: 'NotoSansKR', useMaterial3: true),
      home: Scaffold(
        backgroundColor: const Color(0xff8b95a1),
        body: Builder(
          builder: (context) {
            WidgetsBinding.instance.addPostFrameCallback(
              (_) => showDialog<void>(
                context: context,
                barrierDismissible: false,
                builder: (_) => SettingsDialog(api: api),
              ),
            );
            return const SizedBox.expand();
          },
        ),
      ),
    ),
  );
}
