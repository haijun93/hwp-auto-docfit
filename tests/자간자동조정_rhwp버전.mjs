// 자간자동조정_rhwp버전.mjs
//
// 원본 스크립트(win32com + 아래아한글 COM 자동화)를
// rhwp(@rhwp/core, https://github.com/edwardkim/rhwp)의 WASM 문서 편집 API로 재구현.
//
// ─────────────────────────────────────────────────────────────────────────
// [중요] 아키텍처가 근본적으로 다름 — 반드시 읽어주세요
// ─────────────────────────────────────────────────────────────────────────
// 원본은 "실행 중인 한/글 프로그램의 커서"를 옮겨가며 화면상의 선택 영역을
// 조작하는 COM 자동화였습니다 (MoveLineEnd, MoveSelWordBegin, InitScan 등).
// rhwp는 그런 "커서/선택" 개념이 없는 독립 문서 모델(Rust+WASM) 라이브러리라서
// 1:1로 옮길 수 없고, 아래 두 지점은 근사적으로 재구현했습니다.
//
// 1) 단어 경계 판정
//    한/글의 MoveSelWordBegin/End는 한/글 자체의 단어분리 규칙(조사, 문장부호 등)을
//    따르지만, rhwp에는 그런 "단어 이동" API가 없습니다.
//    → 이 스크립트는 공백(스페이스/탭)을 기준으로 "공백으로 끊기지 않은 연속 문자열"을
//      한 단어로 간주하는 방식으로 근사했습니다. 대부분의 한글 문서에서는 원본과
//      유사하게 동작하지만, 완전히 동일하지는 않을 수 있습니다.
//
// 2) 자간 조정에 따른 줄바꿈 재계산(reflow)
//    rhwp는 자간이 바뀌면 내부적으로 자동 재계산(reflow_line_segs)을 수행하는데,
//    이때 실제 폰트로 글자 폭을 측정하는 `measureTextWidth`류의 콜백이 필요합니다
//    (브라우저에서는 Canvas 2D의 measureText를 씁니다).
//    → Node.js에는 이게 없으므로 `canvas` 패키지로 흉내를 냅니다(아래 설치 안내 참고).
//      단, 이 폭 측정치는 한/글 자체의 내부 글꼴 메트릭과 100% 동일하지 않을 수 있어
//      결과가 실제 한/글에서 연 것과 미세하게 다를 수 있습니다. 중요 문서는 반드시
//      결과를 한/글(또는 rhwp의 export-pdf/export-png)로 열어 육안 확인하세요.
//
// ─────────────────────────────────────────────────────────────────────────
// 설치
// ─────────────────────────────────────────────────────────────────────────
//   npm install @rhwp/core canvas
//   (Node.js 18 이상, ESM)
//
//   문서에서 실제 쓰는 한글 글꼴(바탕, 굴림, 돋움 등)이 시스템에 설치되어 있어야
//   폭 측정이 그나마 정확해집니다. `canvas` 패키지의 registerFont로 등록하세요.
//
// ─────────────────────────────────────────────────────────────────────────
// 실행
// ─────────────────────────────────────────────────────────────────────────
//   node 자간자동조정_rhwp버전.mjs 문서1.hwpx 문서2.hwp ...
//   node 자간자동조정_rhwp버전.mjs ./내문서폴더        (폴더 지정 시 하위 .hwp/.hwpx 전부 처리)
//
// 결과는 "원본이름(자간조정).확장자"로 같은 폴더에 저장됩니다.

import { readFile, writeFile, readdir, stat } from "node:fs/promises";
import path from "node:path";
import initWasm, { HwpDocument } from "@rhwp/core";
import { createCanvas, registerFont } from "canvas";

// ── 1) measureTextWidth 셔틀 준비 ──────────────────────────────────────
// rhwp WASM 내부에서 `document.createElement('canvas').getContext('2d')`를
// 호출하므로, Node 전역에 최소한의 document 셔틀을 흉내 낸다.
// 필요하다면 여기서 registerFont(...)로 문서에 쓰인 폰트를 등록해두면
// measureText 정확도가 올라간다.
// 예) registerFont("/usr/share/fonts/truetype/nanum/NanumMyeongjo.ttf", { family: "바탕" });
globalThis.document = {
    createElement(tag) {
        if (tag === "canvas") {
            return createCanvas(1, 1);
        }
        throw new Error(`지원하지 않는 createElement 태그: ${tag}`);
    },
};

// ── 2) rhwp WASM 초기화 (Node용: fetch 대신 파일 바이트로 동기 초기화) ──
async function initRhwp() {
    const wasmPath = new URL("./node_modules/@rhwp/core/rhwp_bg.wasm", import.meta.url);
    const wasmBytes = await readFile(wasmPath);
    await initWasm({ module_or_path: wasmBytes });
}

// ── 3) 문단 텍스트 유틸 ──────────────────────────────────────────────
function isWhitespace(ch) {
    return ch === " " || ch === "\t" || ch === "\u3000"; // 스페이스/탭/전각 공백
}

/**
 * 문단 전체 텍스트를 가져온다 (getTextRange를 총 길이만큼 한 번에 호출).
 */
function getParagraphText(doc, sec, para) {
    const len = doc.getParagraphLength(sec, para);
    if (len === 0) return "";
    return doc.getTextRange(sec, para, 0, len);
}

/**
 * charEnd 위치(줄 경계, 그 문단 텍스트 기준 인덱스)에서 단어가 잘려 있는지 판정.
 * 잘려있으면 { beforeLen, afterLen }을, 아니면 null을 반환.
 * (beforeLen: 이번 줄에 남은 잘린 단어 앞부분 글자수,
 *  afterLen : 다음 줄로 넘어간 잘린 단어 뒷부분 글자수)
 */
function detectSplitWord(text, charEnd) {
    if (charEnd <= 0 || charEnd >= text.length) return null;
    const before = text[charEnd - 1];
    const after = text[charEnd];
    if (isWhitespace(before) || isWhitespace(after)) return null; // 안 잘림

    let beforeLen = 0;
    for (let i = charEnd - 1; i >= 0 && !isWhitespace(text[i]); i--) beforeLen++;
    let afterLen = 0;
    for (let i = charEnd; i < text.length && !isWhitespace(text[i]); i++) afterLen++;

    return { beforeLen, afterLen };
}

// ── 4) 자간 읽기/쓰기 ────────────────────────────────────────────────
function getSpacings(doc, sec, para, offset) {
    const props = JSON.parse(doc.getCharPropertiesAt(sec, para, Math.max(0, offset)));
    return props.spacings; // [7] — 언어 카테고리별 자간(%), -50~50
}

function clamp(v, lo, hi) {
    return Math.max(lo, Math.min(hi, v));
}

/**
 * [charStart, charEnd) 범위(한 줄 전체)의 자간을 delta(%)만큼 7개 언어
 * 카테고리 전부에 동일하게 적용한다.
 * (원본의 CharShapeSpacingIncrease/Decrease는 현재 언어 자간만 1%씩 바꾸지만,
 *  rhwp API에는 "선택 영역의 현재 언어"라는 개념이 없어 전체 카테고리에 적용했다.
 *  결과적으로 시각 효과는 동일하나, 문서 내부 자간 값 자체는 원본과 다를 수 있다.)
 */
function adjustLineSpacing(doc, sec, para, charStart, charEnd, delta) {
    const current = getSpacings(doc, sec, para, charStart);
    const next = current.map((v) => clamp(v + delta, -50, 50));
    doc.applyCharFormat(sec, para, charStart, charEnd, JSON.stringify({ spacings: next }));
}

// ── 5) 문단 하나에 대해 자간자동조정 수행 ────────────────────────────
// 원본 자간자동조정()에 대응. 원본과 달리 15회 초과 시 반드시 루프를 빠져나가고
// (원본의 버그였던 break 누락을 수정한 버전을 기준으로 이식),
// Undo 대신 saveSnapshot/restoreSnapshot으로 안전하게 되돌린다.
function autoAdjustParagraph(doc, sec, para) {
    const MAX_STEPS = 15;

    for (;;) {
        const text = getParagraphText(doc, sec, para);
        if (text.length === 0) return;

        // 문단의 첫 줄부터 순회. getLineInfo(offset)는 offset이 속한 줄 정보를 준다.
        let offset = 0;
        let touchedAnyLine = false;

        while (true) {
            const info = JSON.parse(doc.getLineInfo(sec, para, offset));
            const { lineIndex, lineCount, charStart, charEnd } = info;
            const isLastLine = lineIndex >= lineCount - 1;

            if (!isLastLine) {
                const split = detectSplitWord(text, charEnd);
                if (split) {
                    touchedAnyLine = true;
                    const snapshotId = doc.saveSnapshot();
                    let steps = 0;
                    let resolved = false;

                    while (steps < MAX_STEPS) {
                        const delta = split.beforeLen >= split.afterLen ? -1 : +1; // 앞부분↑→자간↓, 뒷부분↑→자간↑
                        adjustLineSpacing(doc, sec, para, charStart, charEnd, delta);
                        steps++;

                        // 재계산된 줄 경계를 다시 조회해 여전히 잘려있는지 확인
                        const newText = getParagraphText(doc, sec, para);
                        const newInfo = JSON.parse(doc.getLineInfo(sec, para, charStart));
                        const stillSplit = detectSplitWord(newText, newInfo.charEnd);
                        if (!stillSplit) {
                            resolved = true;
                            break;
                        }
                    }

                    if (!resolved) {
                        // 원본의 "15% 이상 자간조정 시 원상복구"에 해당.
                        console.warn(
                            `  - sec${sec} para${para}: 15% 이상 조정해도 해결 안 됨 → 원상복구`
                        );
                        doc.restoreSnapshot(snapshotId);
                    } else {
                        doc.discardSnapshot(snapshotId);
                    }

                    // 이 문단 레이아웃이 바뀌었을 수 있으므로, 문단 처음부터 다시 스캔한다.
                    break;
                }
            }

            if (isLastLine) {
                return touchedAnyLine ? autoAdjustParagraph(doc, sec, para) : undefined;
            }
            offset = charEnd; // 다음 줄로
        }

        if (!touchedAnyLine) return; // 더 이상 잘린 단어 없음 → 이 문단 끝
        // touchedAnyLine이면 위 break로 빠져나와 while(true) 바깥 for(;;)가 다시 스캔
    }
}

// ── 6) 문서 전체(본문 문단) 순회 ─────────────────────────────────────
// [주의] 원본의 컨트롤_내부_자간조정()(표, 글상자, 각주/미주 등 본문 외 텍스트)에
// 대응하는 기능은 이식하지 않았습니다. rhwp의 셀/글상자 자간 조정은
// applyCharFormatInCell 계열로 가능하지만, 표의 각 셀·문단을 순회하는 부분까지
// 포함하면 스크립트가 크게 길어져 이번 이식 범위에서는 본문 문단만 처리합니다.
// 필요하면 getCellParagraphCount/getTextInCell/applyCharFormatInCell로
// 동일한 패턴을 표 셀에도 반복 적용할 수 있습니다.
function adjustDocument(doc) {
    const sectionCount = doc.getSectionCount();
    for (let sec = 0; sec < sectionCount; sec++) {
        const paraCount = doc.getParagraphCount(sec);
        for (let para = 0; para < paraCount; para++) {
            autoAdjustParagraph(doc, sec, para);
        }
    }
}

// ── 7) 파일 목록 수집 (원본의 tkinter 파일선택창 대체) ───────────────
async function collectHwpFiles(inputs) {
    const files = [];
    for (const p of inputs) {
        const st = await stat(p);
        if (st.isDirectory()) {
            const entries = await readdir(p, { withFileTypes: true });
            for (const e of entries) {
                if (e.isFile() && /\.(hwpx|hwp)$/i.test(e.name)) {
                    files.push(path.join(p, e.name));
                }
            }
        } else if (/\.(hwpx|hwp)$/i.test(p)) {
            files.push(p);
        }
    }
    return files;
}

// ── 8) 메인 ───────────────────────────────────────────────────────
async function main() {
    const inputs = process.argv.slice(2);
    if (inputs.length === 0) {
        console.error("사용법: node 자간자동조정_rhwp버전.mjs <파일 또는 폴더 ...>");
        process.exit(1);
    }

    await initRhwp();

    const fileList = await collectHwpFiles(inputs);
    if (fileList.length === 0) {
        console.error("처리할 .hwp/.hwpx 파일을 찾지 못했습니다.");
        process.exit(1);
    }

    const failed = [];

    for (const filePath of fileList) {
        console.log(`처리 중: ${filePath}`);
        try {
            const bytes = await readFile(filePath);
            const doc = new HwpDocument(new Uint8Array(bytes));

            adjustDocument(doc);

            const isHwpx = /\.hwpx$/i.test(filePath);
            const outBytes = isHwpx ? doc.exportHwpx() : doc.exportHwp();

            const ext = path.extname(filePath);
            const base = filePath.slice(0, -ext.length);
            const outPath = `${base}(자간조정)${ext}`;
            await writeFile(outPath, outBytes);

            doc.free(); // wasm-bindgen 객체 명시적 해제
            console.log(`  → 저장 완료: ${outPath}`);
        } catch (err) {
            console.error(`  [오류] ${filePath}: ${err.message ?? err}`);
            failed.push(filePath);
        }
    }

    if (failed.length > 0) {
        console.log("\n다음 파일은 처리하지 못했습니다:");
        for (const f of failed) console.log(` - ${f}`);
    } else {
        console.log("\n모든 파일 처리가 완료되었습니다.");
    }
}

main();
