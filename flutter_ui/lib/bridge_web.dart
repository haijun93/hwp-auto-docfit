import 'dart:convert';
import 'dart:js_interop';

@JS('docfitCall')
external JSPromise<JSString> _invoke(JSString method, JSString arguments);

Future<Object?> callApi(String method, List<Object?> args) async {
  final response = await _invoke(method.toJS, jsonEncode(args).toJS).toDart;
  return jsonDecode(response.toDart);
}
