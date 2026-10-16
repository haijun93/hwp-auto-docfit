import 'package:flutter/material.dart';

/// 토스 키오스크 느낌의 설정 화면 색·간격 규칙.
/// 큰 글자, 넉넉한 여백, 둥근 카드, 한 가지 강조색(파랑)만 쓴다.
class Kiosk {
  static const blue = Color(0xff3182f6);
  static const blueSoft = Color(0xffe8f3ff);
  static const ink = Color(0xff191f28);
  static const sub = Color(0xff4e5968);
  static const faint = Color(0xff8b95a1);
  static const line = Color(0xffe5e8eb);
  static const canvas = Color(0xfff2f4f6);
  static const card = Colors.white;
  static const green = Color(0xff03b26c);
  static const red = Color(0xfff04452);
  static const radius = 20.0;

  static const title = TextStyle(
    fontSize: 22,
    fontWeight: FontWeight.w700,
    color: ink,
    height: 1.35,
  );
  static const cardTitle = TextStyle(
    fontSize: 18,
    fontWeight: FontWeight.w700,
    color: ink,
    height: 1.35,
  );
  static const body = TextStyle(fontSize: 15, color: sub, height: 1.5);
  static const caption = TextStyle(fontSize: 13, color: faint, height: 1.4);

  static BoxDecoration cardBox({bool selected = false}) => BoxDecoration(
    color: card,
    borderRadius: BorderRadius.circular(radius),
    border: Border.all(color: selected ? blue : line, width: selected ? 2 : 1),
  );
}

/// 큼직한 파란 기본 버튼(키오스크의 '다음' 버튼).
class KioskPrimaryButton extends StatelessWidget {
  const KioskPrimaryButton({
    super.key,
    required this.label,
    required this.onPressed,
  });
  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => FilledButton(
    style: FilledButton.styleFrom(
      backgroundColor: Kiosk.blue,
      disabledBackgroundColor: const Color(0xffd1d6db),
      minimumSize: const Size(160, 52),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
    ),
    onPressed: onPressed,
    child: Text(label),
  );
}

/// 회색 보조 버튼.
class KioskSecondaryButton extends StatelessWidget {
  const KioskSecondaryButton({
    super.key,
    required this.label,
    required this.onPressed,
  });
  final String label;
  final VoidCallback? onPressed;

  @override
  Widget build(BuildContext context) => TextButton(
    style: TextButton.styleFrom(
      backgroundColor: const Color(0xfff2f4f6),
      foregroundColor: Kiosk.sub,
      minimumSize: const Size(110, 52),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
      textStyle: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600),
    ),
    onPressed: onPressed,
    child: Text(label),
  );
}
