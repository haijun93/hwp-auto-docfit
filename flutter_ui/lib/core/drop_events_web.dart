import 'dart:js_interop';
import 'package:web/web.dart' as web;

void Function() watchDocumentDrops(void Function() callback) {
  final listener = ((web.Event event) => callback()).toJS;
  web.window.addEventListener('docfit-documents-dropped', listener);
  return () =>
      web.window.removeEventListener('docfit-documents-dropped', listener);
}
