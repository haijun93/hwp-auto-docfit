// QA 진입점: 공개 기본 자료 또는 임시 --dart-define-from-file 자료로 화면만 띄운다.
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:docfit_ui/features/formats/profile_editor.dart';

import 'preview_data.dart';

void main() {
  final data = jsonDecode(previewProfileJson) as Map;
  Future<Object?> api(String method, List<Object?> args) async => {
    'ok': true,
    'data': data,
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
                builder: (_) => ProfileEditor(api: api, identifier: 'preview'),
              ),
            );
            return const SizedBox.expand();
          },
        ),
      ),
    ),
  );
}
