window.docfitCall = async function(method, argumentsJson) {
  const api = window.pywebview && window.pywebview.api;
  if (!api || typeof api[method] !== 'function') throw new Error('앱 연결을 기다리고 있습니다.');
  return JSON.stringify(await api[method](...JSON.parse(argumentsJson)));
};
window.addEventListener('flutter-first-frame', () => document.getElementById('loading')?.remove());
