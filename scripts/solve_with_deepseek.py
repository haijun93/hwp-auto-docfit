"""DeepSeek-R1 조판 수학 및 정밀 알고리즘 검증 도구.
http.client를 사용하여 Semgrep 보안 감사(dynamic-urllib-use-detected)를 100% 준수합니다.
"""
import http.client
import json
import os
import time

HOST = "192.168.0.4"
PORT = 11434
PATH = "/api/generate"
OUTPUT_FILE = r"C:\HWP_AUTODOCFIT\v1803\v2\docs\DEEPSEEK_ALGORITHM_SOLUTION.md"

PROMPT = """당신은 HWP 문서 조판 및 글꼴 메트릭스 알고리즘 최고 전문가(DeepSeek-R1)입니다."""

def main():
    payload = json.dumps({
        "model": "deepseek-r1:7b",
        "prompt": PROMPT,
        "stream": False,
        "keep_alive": "60m"
    }).encode("utf-8")
    
    conn = http.client.HTTPConnection(HOST, PORT, timeout=120)
    conn.request("POST", PATH, body=payload, headers={"Content-Type": "application/json"})
    resp = conn.getresponse()
    data = json.loads(resp.read().decode("utf-8"))
    conn.close()
    
    print("[+] Response chars:", len(data.get("response", "")))

if __name__ == "__main__":
    main()
