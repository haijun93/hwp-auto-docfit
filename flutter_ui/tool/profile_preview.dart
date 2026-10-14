// QA 전용 진입점: 실제 서식 분석 자료(scripts/preview_settings.py --profile)로 서식 세부 편집 화면만 띄운다.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:docfit_ui/features/formats/profile_editor.dart';

import 'settings_preview_data.dart';

void main() {
  final data = jsonDecode(previewSettingsJson) as Map;
  Future<Object?> api(String method, List<Object?> args) async => {'ok': true, 'data': data};
  runApp(MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: ThemeData(fontFamily: 'NotoSansKR', useMaterial3: true),
    home: Scaffold(
      backgroundColor: const Color(0xff8b95a1),
      body: Builder(builder: (context) {
        WidgetsBinding.instance.addPostFrameCallback((_) => showDialog<void>(
            context: context, barrierDismissible: false,
            builder: (_) => ProfileEditor(api: api, identifier: 'preview')));
        return const SizedBox.expand();
      }),
    ),
  ));
}
