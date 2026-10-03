const MODE_LABELS = {spacing:"자간 정리",unify:"서식 통일",format:"한 번에 적용 · 자간 조정 제외",all:"한 번에 적용"};
const $ = (id) => document.getElementById(id);
let currentStep = 1;
let returnStep = 1;
let currentMode = "spacing";
let lastState = null;
let hasRun = false;
let busy = false;

function navigate(step) {
  if (step < 1 || step > 4) return;
  currentStep = step;
  document.querySelectorAll(".step-tab").forEach((tab) => {
    const active = Number(tab.dataset.step) === step;
    tab.classList.toggle("active", active);
    tab.setAttribute("aria-selected", String(active));
    tab.tabIndex = active ? 0 : -1;
  });
  document.querySelectorAll(".page[data-page]").forEach((page) => {
    const active = Number(page.dataset.page) === step;
    page.hidden = !active;
    page.classList.toggle("active", active);
  });
  $("toolsPage").hidden = true;
  updateFooter();
  window.scrollTo({top:0,behavior:"smooth"});
}

function openTools() {
  returnStep = currentStep;
  $("toolsPage").hidden = false;
  document.querySelectorAll(".page[data-page]").forEach((page) => { page.hidden = true; });
  $("backButton").hidden = false;
  $("nextButton").hidden = true;
  $("startButton").hidden = true;
  $("nextJobButton").hidden = true;
  $("stopButton").hidden = !(lastState?.running);
  $("toolsButton").hidden = true;
  $("footerHint").textContent = "도구를 선택하면 별도 창에서 열립니다.";
  window.scrollTo({top:0,behavior:"smooth"});
}

function updateFooter() {
  const toolsOpen = !$("toolsPage").hidden;
  $("backButton").hidden = !toolsOpen;
  $("toolsButton").hidden = toolsOpen || currentStep === 3 && Boolean(lastState?.running);
  $("nextButton").hidden = toolsOpen || currentStep !== 1;
  $("nextButton").disabled = !(lastState?.count > 0);
  $("startButton").hidden = toolsOpen || !((currentStep === 2) || (currentStep === 3 && !hasRun));
  $("startButton").disabled = !(lastState?.can_start) || busy;
  $("nextJobButton").hidden = toolsOpen || currentStep !== 4;
  $("stopButton").hidden = !lastState?.running;
  const hints = {
    1: lastState?.count ? `${lastState.count}개 문서 선택됨` : "문서를 선택하거나 텍스트를 입력하세요.",
    2: "작업 유형을 선택하고 필요한 세부 설정을 확인하세요.",
    3: hasRun ? (lastState?.running ? "문서 처리 중입니다." : "진행 상태와 결과를 확인하세요.") : "작업 방식을 정했다면 여기서도 시작할 수 있어요.",
    4: "결과를 확인한 뒤 다음 작업을 시작하세요."
  };
  if (!toolsOpen) $("footerHint").textContent = hints[currentStep];
}

function renderFiles(state) {
  const list = $("fileList");
  list.replaceChildren();
  (state.files || []).forEach((file,index) => {
    const item = document.createElement("li");
    item.className = "file-item";
    const glyph = document.createElement("span");
    glyph.className = "file-glyph";
    glyph.textContent = String(file.name.split(".").pop() || "DOC").slice(0,4).toUpperCase();
    glyph.setAttribute("aria-hidden","true");
    const name = document.createElement("span");
    name.className = "file-name";
    name.textContent = file.name;
    const remove = document.createElement("button");
    remove.className = "remove-button";
    remove.type = "button";
    remove.textContent = "×";
    remove.setAttribute("aria-label",`${file.name} 제거`);
    remove.disabled = state.running;
    remove.addEventListener("click",()=>callApi("remove_file",index));
    item.append(glyph,name,remove);
    list.append(item);
  });
  $("fileSection").hidden = !state.count;
  $("fileCount").textContent = `${state.count}개`;
  $("clearFiles").disabled = state.running;
}

function renderModes(state) {
  currentMode = state.mode || currentMode;
  // 서식 적용(format)은 '한 번에 적용' 카드에서 자간 조정을 끈 것이다.
  const cardMode = currentMode === "format" ? "all" : currentMode;
  document.querySelectorAll(".mode-card").forEach((card)=>{
    const selected = card.dataset.mode === cardMode;
    card.classList.toggle("selected",selected);
    card.setAttribute("aria-checked",String(selected));
    card.disabled = Boolean(state.running);
  });
  $("resetOption").hidden = cardMode !== "spacing";
  $("resetSpacing").checked = state.reset_spacing !== false;
  $("resetSpacing").disabled = Boolean(state.running);
  $("spacingOption").hidden = cardMode !== "all";
  $("includeSpacing").checked = state.include_spacing !== false;
  $("includeSpacing").disabled = Boolean(state.running);
  $("modeSummary").textContent = MODE_LABELS[currentMode] || MODE_LABELS.spacing;
  $("defaultNote").textContent = state.default_saved
    ? "세부 설정에서 저장한 기본 구성을 사용합니다."
    : "기본 세부 구성으로 작업합니다.";
  const range = state.range || {};
  if (document.activeElement !== $("rangeStart")) $("rangeStart").value = range.start || "1";
  if (document.activeElement !== $("rangeEnd")) $("rangeEnd").value = range.end || "1";
  $("rangeBox").open = Boolean(range.enabled);
  $("rangeBox").style.pointerEvents = state.running ? "none" : "";
}

function renderFlow(state) {
  const progress = state.progress || {};
  const steps = progress.steps || ["열기","서식","자간","줄 병합","페이지 배치","저장"];
  const visited = new Set(progress.visited || []);
  const list = $("flowchart");
  list.replaceChildren();
  steps.forEach((label,index)=>{
    const li = document.createElement("li");
    const stateName = label === progress.active
      ? (progress.outcome === "완료" ? "done" : progress.outcome === "오류" ? "error" : "active")
      : visited.has(label) ? "done" : "";
    li.className = `flow-node ${stateName}`.trim();
    li.setAttribute("aria-current",stateName === "active" ? "step" : "false");
    const node = document.createElement("span");
    node.className = "node-icon";
    node.textContent = stateName === "done" ? "✓" : String(index+1);
    const text = document.createElement("b");
    text.textContent = label;
    li.append(node,text);
    list.append(li);
  });
  const active = progress.active || "작업 준비";
  $("currentStage").textContent = active;
  $("progressDetail").textContent = progress.detail || (hasRun ? "작업 상태가 실시간으로 갱신됩니다." : "작업을 시작하기 전입니다.");
  $("progressStatus").textContent = state.status || (state.running ? `${active} 작업 중` : hasRun ? "작업이 끝났습니다." : "작업 방식 선택 후 정리를 시작하세요.");
  $("workingIndicator").hidden = !state.running;
  $("progressHint").textContent = state.running
    ? `${state.count}개 문서 중 처리 중입니다. 다른 단계 탭을 눌러 이동할 수 있습니다.`
    : hasRun ? "작업 결과는 결과 탭에서 확인할 수 있습니다." : "작업 방식 선택 후 정리를 시작하면 실제 처리 단계가 표시됩니다.";
}

function renderResults(state) {
  const results = state.results || [];
  const list = $("resultList");
  list.replaceChildren();
  results.forEach((result)=>{
    const row = document.createElement("li");
    row.className = "file-item";
    const glyph = document.createElement("span");
    glyph.className = "file-glyph";
    glyph.textContent = "HWPX";
    const name = document.createElement("span");
    name.className = "file-name";
    name.textContent = result.name;
    row.append(glyph,name);
    list.append(row);
  });
  const complete = /^처리 완료/.test(state.status || "");
  const stopped = /중단/.test(state.status || "");
  const hasResult = results.length > 0;
  $("resultSection").hidden = !hasResult;
  $("resultStatus").textContent = complete ? "문서 정리가 완료되었습니다." : stopped ? "작업이 중단되었습니다." : hasRun ? "작업이 끝났습니다." : "아직 작업 결과가 없습니다.";
  $("resultCount").textContent = hasResult ? `저장된 결과 ${results.length}개` : hasRun ? (state.status || "저장된 결과가 없습니다.") : "작업을 마치면 여기에 결과가 표시됩니다.";
  $("resultTitle").textContent = complete ? "정리가 끝났습니다." : stopped ? "작업이 멈췄습니다." : "결과를 확인하세요.";
  $("resultSubtitle").textContent = hasRun ? "결과를 확인하고 다음 작업을 선택하세요." : "처리를 시작하면 결과가 여기에 표시됩니다.";
  $("resultIcon").textContent = complete ? "✓" : stopped ? "Ⅱ" : hasRun ? "!" : "·";
  $("resultIcon").className = complete ? "success" : stopped || hasRun ? "attention" : "neutral";
  $("openResults").disabled = !hasResult;
}

function render(state) {
  if (!state) return;
  lastState = state;
  $("version").textContent = state.version || "알파";
  renderFiles(state);
  renderModes(state);
  renderFlow(state);
  renderResults(state);
  document.querySelectorAll(".step-tab").forEach((tab)=>{
    const num = Number(tab.dataset.step);
    tab.classList.toggle("complete",(num===1 && state.count>0) || (num===2 && hasRun) || (num===3 && hasRun && !state.running));
  });
  updateFooter();
  if (hasRun && !state.running && currentStep === 3 && /처리 완료|중단/.test(state.status || "")) navigate(4);
}

async function callApi(method,...args) {
  if (!window.pywebview?.api) return null;
  try {
    const result = await window.pywebview.api[method](...args);
    if (result && typeof result === "object" && "files" in result) render(result);
    return result;
  } catch (error) {
    $("footerHint").textContent = error?.message || "요청을 처리하지 못했습니다.";
    return null;
  }
}

async function startJob() {
  if (busy || !lastState?.can_start) return;
  busy = true;
  hasRun = true;
  navigate(3);
  updateFooter();
  const result = await callApi("start",currentMode,$("rangeBox").open,$("rangeStart").value,$("rangeEnd").value);
  busy = false;
  if (result?.running) navigate(3);
  updateFooter();
}

async function nextJob() {
  if (lastState?.running) return;
  const state = await callApi("next_job");
  if (state) {
    hasRun = false;
    currentMode = state.mode || "spacing";
    navigate(1);
  }
}

document.querySelectorAll(".step-tab").forEach((tab)=>{
  tab.addEventListener("click",()=>navigate(Number(tab.dataset.step)));
  tab.addEventListener("keydown",(event)=>{
    const tabs = [...document.querySelectorAll(".step-tab")];
    const index = tabs.indexOf(tab);
    let next = null;
    if (event.key === "ArrowRight") next = tabs[(index+1)%tabs.length];
    if (event.key === "ArrowLeft") next = tabs[(index-1+tabs.length)%tabs.length];
    if (event.key === "Home") next = tabs[0];
    if (event.key === "End") next = tabs[tabs.length-1];
    if (next) { event.preventDefault(); navigate(Number(next.dataset.step)); next.focus(); }
  });
});
$("addFiles").addEventListener("click",()=>callApi("add_files"));
$("addFolder").addEventListener("click",()=>callApi("add_folder"));
$("textInput").addEventListener("click",()=>callApi("text_input"));
$("clearFiles").addEventListener("click",()=>callApi("clear_files"));
$("settingsButton").addEventListener("click",()=>callApi("open_settings"));
$("stagesButton").addEventListener("click",()=>callApi("open_stages"));
$("logButton").addEventListener("click",()=>callApi("open_log"));
$("openResults").addEventListener("click",()=>callApi("open_results"));
$("stopButton").addEventListener("click",()=>callApi("stop"));
$("nextButton").addEventListener("click",()=>navigate(2));
$("startButton").addEventListener("click",startJob);
$("nextJobButton").addEventListener("click",nextJob);
$("toolsButton").addEventListener("click",openTools);
$("backButton").addEventListener("click",()=>navigate(returnStep));
document.querySelectorAll(".mode-card").forEach((card)=>card.addEventListener("click",async()=>{
  currentMode = card.dataset.mode;
  render({...lastState,mode:currentMode});
  await callApi("set_mode",currentMode);
}));
$("includeSpacing").addEventListener("change",()=>callApi("set_include_spacing",$("includeSpacing").checked));
$("resetSpacing").addEventListener("change",()=>callApi("set_reset_spacing",$("resetSpacing").checked));

$("rangeBox").addEventListener("toggle",()=>{
  if (window.pywebview?.api && !lastState?.running) callApi("set_range",$("rangeBox").open,$("rangeStart").value,$("rangeEnd").value);
});
for (const id of ["rangeStart","rangeEnd"]) $(id).addEventListener("change",()=>{
  if ($("rangeBox").open) callApi("set_range",true,$("rangeStart").value,$("rangeEnd").value);
});
document.querySelectorAll("[data-tool]").forEach((button)=>button.addEventListener("click",async()=>{
  await callApi("run_tool",button.dataset.tool);
}));

const dropArea = $("dropArea");
for (const eventName of ["dragenter","dragover"]) dropArea.addEventListener(eventName,(event)=>{
  event.preventDefault();
  dropArea.classList.add("dragging");
});
for (const eventName of ["dragleave","drop"]) dropArea.addEventListener(eventName,(event)=>{
  event.preventDefault();
  dropArea.classList.remove("dragging");
});
dropArea.addEventListener("keydown",(event)=>{
  if (event.key === "Enter" || event.key === " ") { event.preventDefault(); callApi("add_files"); }
});
document.addEventListener("dragover",(event)=>event.preventDefault());
document.addEventListener("drop",(event)=>event.preventDefault());

async function sync() {
  if (!window.pywebview?.api) return;
  try { render(await window.pywebview.api.get_state()); }
  catch (_) { $("footerHint").textContent = "앱 상태를 확인할 수 없습니다."; }
}
window.addEventListener("pywebviewready",()=>{sync();window.setInterval(sync,650);});

