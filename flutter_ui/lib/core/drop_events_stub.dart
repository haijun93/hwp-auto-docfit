void Function() watchDocumentDrops(void Function() callback) => () {};

/// 창 이벤트 듣기(웹에서만). 시험·데스크톱에서는 아무것도 하지 않는다.
void Function() watchWindowEvent(String name, void Function() callback) =>
    () {};
