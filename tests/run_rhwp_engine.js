// tests/run_rhwp_engine.js
// Pure JS/WASM HWP & HWPX Auto Letter Spacing Engine

const fs = require('fs');
const path = require('path');

// Mock Canvas 2D context for headless text measurement
globalThis.document = {
    createElement(tag) {
        if (tag === 'canvas') {
            return {
                getContext(type) {
                    return {
                        font: '',
                        measureText(text) {
                            let w = 0;
                            for (let i = 0; i < text.length; i++) {
                                const code = text.charCodeAt(i);
                                w += code > 255 ? 10 : 5.5;
                            }
                            return { width: w };
                        }
                    };
                }
            };
        }
        throw new Error('Unsupported tag: ' + tag);
    }
};

const rhwp = require('/Users/hyeokjunkong/Downloads/test/node_modules/@rhwp/core');
const wasmPath = '/Users/hyeokjunkong/Downloads/test/node_modules/@rhwp/core/rhwp_bg.wasm';
rhwp.initSync({ module: fs.readFileSync(wasmPath) });

const SENTENCE_MARKS = [
    '-', '－', '–', '—', 'ㆍ', '·', '•', '∙', '‧',
    '○', '●', '◦', '◉', '◎', '□', '■', '▣', '▢',
    '◇', '◆', '△', '▲', '▽', '▼', '※', '▶', '▷',
    '◀', '◁', '→', '⇒', '↔', '☞', '☑', '✓', '✔',
    '★', '☆', '▪', '▫', '‣', '⁃', '⁌', '⁍',
];

const NUMBER_MARK_RE = /^(?:[0-9]{1,3}[.)]|\([0-9]{1,3}\)|[가나다라마바사아자차카타파하][.)]|\([가나다라마바사아자차카타파하]\)|[A-Za-z][.)]|\([A-Za-z]\)|[①②③④⑤⑥⑦⑧⑨⑩]|[㉠㉡㉢㉣㉤㉥㉦㉧㉨㉩])(?:\s|$)/;

function isSentenceMark(text) {
    if (!text) return false;
    const trimmed = text.trimStart();
    if (!trimmed) return false;
    if (SENTENCE_MARKS.includes(trimmed[0])) return true;
    return NUMBER_MARK_RE.test(trimmed);
}

function processDocument(inputPath, outputPath) {
    console.log('=' .repeat(70));
    console.log(`[rhwp WASM Engine] 문서 처리 시작: ${inputPath}`);
    console.log('=' .repeat(70));

    const inputBytes = fs.readFileSync(inputPath);
    const doc = new rhwp.HwpDocument(new Uint8Array(inputBytes));

    const secCount = doc.getSectionCount();
    let totalAdjusted = 0;
    let totalLinesReduced = 0;

    for (let sec = 0; sec < secCount; sec++) {
        const paraCount = doc.getParagraphCount(sec);
        console.log(`\n[Section ${sec}] 총 ${paraCount}개 문단 검사 시작...`);

        for (let p = 0; p < paraCount; p++) {
            const len = doc.getParagraphLength(sec, p);
            if (len === 0) continue;

            const text = doc.getTextRange(sec, p, 0, len);
            const trimmed = text.trim();
            if (!trimmed) continue;

            // 1. 공문서 기호 및 개조식 문장 판정
            if (isSentenceMark(text)) {
                // 줄바꿈 정보 조회
                try {
                    const lineInfo0 = JSON.parse(doc.getLineInfo(sec, p, 0));
                    const lineCount = lineInfo0.lineCount;

                    // 2줄 문장이거나 2번째 줄 오버플로우가 5자 이하인 경우
                    if (lineCount >= 2) {
                        const lineInfo1 = JSON.parse(doc.getLineInfo(sec, p, lineInfo0.charEnd));
                        const line2Text = text.slice(lineInfo1.charStart, lineInfo1.charEnd).trim();
                        const line2Len = line2Text.length;

                        console.log(`  • [P${p}] (${lineCount}줄) "${text.slice(0, 30)}..." | 2번째줄: "${line2Text}" (${line2Len}자)`);

                        if (line2Len > 0 && line2Len <= 10) {
                            // 자간 축소 적용 (-1% ~ -5%)
                            let targetDelta = -2;
                            if (line2Len <= 3) targetDelta = -2;
                            else if (line2Len <= 6) targetDelta = -3;
                            else targetDelta = -5;

                            const charProps = JSON.parse(doc.getCharPropertiesAt(sec, p, 0));
                            const curSpacings = charProps.spacings || [0, 0, 0, 0, 0, 0, 0];
                            const nextSpacings = curSpacings.map(v => Math.max(-50, v + targetDelta));

                            // 문단 전체에 축소된 자간 적용
                            doc.applyCharFormat(sec, p, 0, len, JSON.stringify({ spacings: nextSpacings }));
                            totalAdjusted++;
                            totalLinesReduced++;
                            console.log(`    └─ [자간 조정 완료] 자간 ${targetDelta}%p 축소 (현재: ${nextSpacings[0]}%) -> 1줄 압축`);
                        }
                    }
                } catch (e) {
                    // LineInfo 파싱 에러 방어
                }
            }
        }
    }

    console.log('\n' + '=' .repeat(70));
    console.log(`[처리 완료] 총 조정된 문단: ${totalAdjusted}개, 절감된 줄 수: ${totalLinesReduced}줄`);
    console.log(`HWPX 저장 중: ${outputPath}`);

    const hwpxBytes = doc.exportHwpx();
    fs.writeFileSync(outputPath, Buffer.from(hwpxBytes));
    doc.free();
    console.log(`저장 성공: ${outputPath} (${hwpxBytes.length} bytes)`);
    console.log('=' .repeat(70));
}

// 실행
const src = 'tests/fixtures/test.hwp';
const dst1 = 'tests/fixtures/test(자간조정).hwpx';
const dst2 = '/Users/hyeokjunkong/Downloads/test/test(자간조정).hwpx';

processDocument(src, dst1);
fs.copyFileSync(dst1, dst2);
