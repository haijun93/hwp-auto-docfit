"""DeepSeek-R1 (MacBook Air 192.168.0.3) 전담 작업 클라이언트.
http.client를 사용하여 Semgrep 보안 감사(dynamic-urllib-use-detected)를 100% 준수합니다.

전담 업무:
1. TODO 96: 원문자/항목 기호 후 콜론(:) 들여쓰기/내어쓰기 정합성 및 엣지 케이스 규칙 생성
2. TODO 164~168: 흐름도 다이어그램 실제 한글 도형 클립보드(hp:rect, hp:ellipse, hp:connectLine) 연결점 검증
3. 공공 행정 준말(Abbreviation) 및 관용구 사전 유효성 필터링
"""
import http.client
import json
import os
import sys

AIR_HOST = "192.168.0.3"
AIR_PORT = 11434
GENERATE_PATH = "/api/generate"

TODO_96_PROMPT = """당신은 HWP 문서 조판 엔진 최고 전문가(DeepSeek-R1)입니다.
금일 과제 TODO 96: 원문자(①, ②, ③, ④ 등) 및 항목 기호(1., 가., 1)) 뒤에 콜론(:)이 오는 경우,
콜론 다음 줄바꿈(wrapping) 텍스트의 들여쓰기(hanging indent)를 콜론 뒤 공백 위치에 정확히 정렬시키는
조판 메트릭스 및 정규식 규칙을 수립해야 합니다.

1. 원문자/항목 기호 + 콜론 패턴 매칭 정규식 (예: ^([①-⑳]|[0-9]+\\.|[가-힣]\\.)\\s*([^:]+):\\s*)
2. 콜론 위치까지의 폭(width) 계산 알고리즘 (한글 전각 문자 1000 HWP단위, 반각 영숫자/기호 단위)
3. 2줄 이상 감싸질 때 본문 첫 글자가 콜론 뒤 공백과 수직 일치되도록 하는 HWPX <hp:para> 들여쓰기 수치 산출식
4. 실제 공공 서식 엣지 케이스 5가지와 기대되는 들여쓰기 pt 값

상세하고 엄밀한 CoT 추론 과정과 최종 권장 알고리즘을 작성해 주세요.
"""

def call_deepseek_air(prompt, task_name="TODO_96", output_path=None):
    print(f"[*] Connecting to DeepSeek-Air ({AIR_HOST}:{AIR_PORT})...")
    payload = json.dumps({
        "model": "deepseek-r1:7b",
        "prompt": prompt,
        "stream": False,
        "keep_alive": "60m"
    }).encode("utf-8")
    
    conn = http.client.HTTPConnection(AIR_HOST, AIR_PORT, timeout=300)
    conn.request("POST", GENERATE_PATH, body=payload, headers={"Content-Type": "application/json"})
    resp = conn.getresponse()
    if resp.status != 200:
        raise RuntimeError(f"HTTP {resp.status}: {resp.reason}")
    data = json.loads(resp.read().decode("utf-8"))
    conn.close()
    
    response_text = data.get("response", "")
    print(f"[+] Response received from DeepSeek-Air: {len(response_text)} characters")
    
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(response_text)
        print(f"[+] Saved output to {output_path}")
    return response_text

if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else r"C:\HWP_AUTODOCFIT\v1803\v2\docs\DEEPSEEK_AIR_TODO96_SOLUTION.md"
    call_deepseek_air(TODO_96_PROMPT, task_name="TODO_96", output_path=out)

