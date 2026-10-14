import React, { useCallback, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Tldraw, createShapeId, getSnapshot, loadSnapshot, toRichText } from 'tldraw';
import { getAssetUrlsByImport } from '@tldraw/assets/imports.vite';
import 'tldraw/tldraw.css';
import './style.css';

const assetUrls = getAssetUrlsByImport();
const templates = {
  general: {
    name: '일반 행정업무 처리',
    steps: ['접수', '검토', '결재', '시행', '완료'],
    colors: ['blue', 'blue', 'blue', 'blue', 'green'],
  },
  contract: { name: '계약 및 발주', steps: ['수요 발생', '발주 검토', '계약 방법 결정', '계약 체결', '검사·검수'] },
  direct_contract: { name: '수의계약 검토', steps: ['계약 대상 확인', '금액·사유 검토', '적정성 판단', '계약 진행'] },
  budget: { name: '예산 집행', steps: ['집행 계획', '예산 확인', '품의', '지출 원인행위', '대금 지급'] },
  subsidy: { name: '지방보조금 관리', steps: ['공모·신청', '심사', '교부 결정', '사업 수행', '정산', '사후관리'] },
  construction: { name: '공사 관리', steps: ['사업 계획', '설계', '발주', '착공', '준공 검사', '대금 지급'] },
  permit: { name: '인허가 처리', steps: ['신청 접수', '요건 검토', '보완 여부 판단', '승인·반려 결정', '결과 통보'] },
  approval: { name: '보고 및 결재', steps: ['자료 작성', '담당 검토', '팀장 검토', '부서장 결재', '시행'] },
  incident: { name: '사고·민원 대응', steps: ['상황 접수', '긴급성 판단', '초기 조치', '보고', '사후관리'] },
  complaint: { name: '민원 처리' },
};
let dirty = false;
let editGeneration = 0;

function send(message) {
  const host = window.chrome?.webview;
  if (host) host.postMessage(JSON.stringify(message));
  else window.parent?.postMessage(message, '*');
}

function App() {
  const editorRef = useRef(null);
  const [name, setName] = useState('새 업무 흐름도');
  const [busy, setBusy] = useState(false);
  const applyTemplate = useCallback((key) => {
    const editor = editorRef.current;
    if (!editor) return;
    const template = templates[key];
    if (!template) return;
    editor.selectAll();
    editor.deleteShapes([...editor.getSelectedShapeIds()]);
    const width = 220;
    const height = 90;
    const gap = 70;
    const steps = key === 'complaint'
      ? [
          { label: '민원 접수', x: 100, y: 60, color: 'blue', geo: 'rectangle' },
          { label: '담당자 배정', x: 100, y: 200, color: 'blue', geo: 'rectangle' },
          { label: '내용 검토', x: 100, y: 340, color: 'orange', geo: 'diamond' },
          { label: '보완 요청', x: -250, y: 540, color: 'yellow', geo: 'rectangle' },
          { label: '보완 내용 재검토', x: -250, y: 680, color: 'blue', geo: 'rectangle' },
          { label: '처리 결과 통보', x: 450, y: 540, color: 'green', geo: 'rectangle' },
        ]
      : template.steps.map((label, index) => ({
          label, x: 100, y: 60 + index * (height + gap),
          color: template.colors?.[index] ?? (index === template.steps.length - 1 ? 'green' : 'blue'), geo: 'rectangle',
        }));
    const ids = steps.map(() => createShapeId());
    editor.createShapes(steps.map((step, index) => ({
      id: ids[index], type: 'geo', x: step.x, y: step.y,
      props: { geo: step.geo, w: width, h: height, color: step.color,
        fill: 'semi', richText: toRichText(step.label) },
    })));
    const links = key === 'complaint'
      ? [
          [0, 1], [1, 2], [2, 3, '예'], [3, 4], [4, 2], [2, 5, '아니오'],
        ]
      : template.steps.slice(1).map((_, index) => [index, index + 1]);
    const arrows = links.map(([from, to]) => ({
      id: createShapeId(),
      type: 'arrow',
      x: 0,
      y: 0,
      props: {
        start: {
          x: steps[from].x + width / 2,
          y: steps[from].y + height,
        },
        end: {
          x: steps[to].x + width / 2,
          y: steps[to].y,
        },
      },
    }));
    const labels = links.filter((link) => link[2]).map(([from, to, label]) => ({
      id: createShapeId(), type: 'text',
      x: (steps[from].x + steps[to].x) / 2 + width / 2,
      y: (steps[from].y + steps[to].y + height) / 2,
      props: { richText: toRichText(label), size: 's', color: 'black' },
    }));
    editor.createShapes([...arrows, ...labels]);
    setName(template.name);
    editor.zoomToFit({ animation: { duration: 0 } });
    send({ type: 'template_applied', template: key, name: template.name });
  }, []);

  const handleMessage = useCallback(async (message) => {
    const editor = editorRef.current;
    if (!editor || !message || typeof message !== 'object') return;
    try {
      switch (message.type) {
        case 'new':
          editor.selectAll();
          editor.deleteShapes([...editor.getSelectedShapeIds()]);
          setName('새 업무 흐름도');
          dirty = false;
          send({ type: 'dirty', value: false, generation: ++editGeneration });
          send({ type: 'document_new' });
          break;
        case 'mark_saved':
          dirty = message.generation !== editGeneration;
          send({ type: 'dirty', value: dirty, generation: editGeneration });
          break;
        case 'load':
          if (!message.snapshot || typeof message.name !== 'string') throw new Error('문서 데이터가 올바르지 않습니다.');
          loadSnapshot(editor.store, message.snapshot);
          setName(message.name);
          dirty = false;
          send({ type: 'dirty', value: false, generation: ++editGeneration });
          editor.zoomToFit({ animation: { duration: 0 } });
          send({ type: 'document_loaded', id: message.id });
          break;
        case 'apply_template':
          applyTemplate(message.template);
          break;
        case 'save': {
          const { document, session } = getSnapshot(editor.store);
          const saveName = typeof message.name === 'string' ? message.name : name;
          setName(saveName);
          send({ type: 'save_document', id: message.id ?? null, name: saveName, generation: editGeneration, snapshot: { document, session } });
          break;
        }
        case 'export_png': {
          setBusy(true);
          const ids = [...editor.getCurrentPageShapeIds()];
          if (!ids.length) throw new Error('내보낼 도형이 없습니다.');
          const { blob } = await editor.toImage(ids, { format: 'png', pixelRatio: 2, background: true });
          const bytes = new Uint8Array(await blob.arrayBuffer());
          let binary = '';
          for (let offset = 0; offset < bytes.length; offset += 0x8000) {
            binary += String.fromCharCode(...bytes.subarray(offset, offset + 0x8000));
          }
          send({ type: 'export_png', name, base64: btoa(binary) });
          setBusy(false);
          break;
        }
        case 'get_info':
          send({ type: 'diagram_info', name, shape_count: editor.getCurrentPageShapeIds().size });
          break;
        default:
          throw new Error('지원하지 않는 편집기 명령입니다.');
      }
    } catch (error) {
      setBusy(false);
      send({ type: 'editor_error', message: String(error?.message ?? error) });
    }
  }, [applyTemplate, name]);

  React.useEffect(() => {
    const receive = (event) => {
      const payload = event.data?.data ?? event.data;
      try {
        handleMessage(typeof payload === 'string' ? JSON.parse(payload) : payload);
      } catch (_) {
        send({ type: 'editor_error', message: '호스트 명령을 해석하지 못했습니다.' });
      }
    };
    window.chrome?.webview?.addEventListener('message', receive);
    window.addEventListener('message', receive);
    send({ type: 'ready', protocol_version: 1 });
    return () => {
      window.chrome?.webview?.removeEventListener('message', receive);
      window.removeEventListener('message', receive);
    };
  }, [handleMessage]);

  return <div className="editor-shell">
    <div className="editor-toolbar">
      <div className="brand"><span className="brand-mark">흐름</span><div><strong>업무 흐름도</strong><small>{name}</small></div></div>
      <div className="toolbar-actions">
        <button onClick={() => send({ type: 'request_new' })}>새 다이어그램</button>
        <button onClick={() => send({ type: 'request_list' })}>저장된 문서</button>
        <button onClick={() => send({ type: 'request_save', name })}>저장</button>
        <button onClick={() => send({ type: 'request_png' })} disabled={busy}>{busy ? 'PNG 만드는 중…' : 'PNG 내보내기'}</button>
        <select aria-label="업무 흐름도 서식" defaultValue="" onChange={(event) => {
          if (event.target.value) send({ type: 'request_template', template: event.target.value });
          event.target.value = '';
        }}>
          <option value="">예시 서식</option>
          {Object.entries(templates).map(([key, value]) => <option key={key} value={key}>{value.name}</option>)}
        </select>
      </div>
    </div>
    <div className="canvas"><Tldraw assetUrls={assetUrls} onMount={(editor) => {
      editorRef.current = editor;
      editor.zoomToFit({ animation: { duration: 0 } });
      const cleanup = editor.store.listen(() => {
        dirty = true;
        send({ type: 'dirty', value: true, generation: ++editGeneration });
      }, { source: 'user', scope: 'document' });
      send({ type: 'ready', protocol_version: 1 });
      return cleanup;
    }} /></div>
  </div>;
}

createRoot(document.getElementById('root')).render(<App />);
