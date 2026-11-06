import 'package:flutter_test/flutter_test.dart';
import 'package:docfit_ui/features/timemachine/timemachine_api.dart';

void main() {
  test('#IEeEE 접두어는 대소문자·따옴표·확장자와 관계없이 제외한다', () {
    for (final name in [
      "#IEeEE'.pptx", "#ieeee.hwpx", " '#IEeEE legacy'.pdf", '‘#IeEeE quoted’.jpg',
      '"#IEeEE".png', '\ufeff#IEeEE bom.hwpx', r'C:\문서\하위\#IEEEE.docx',
    ]) {
      expect(isExcludedTimemachineName(name), isTrue, reason: name);
    }
    for (final name in ['보고서.hwpx', 'IEeEE.hwp', 'a#IEeEE.docx', '']) {
      expect(isExcludedTimemachineName(name), isFalse, reason: name);
    }
  });
}
