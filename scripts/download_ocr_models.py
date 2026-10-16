"""Build-time only: fetch official PP-OCRv5 Korean models, verify pinned SHA256."""
import hashlib
import http.client
from pathlib import Path
import sys
from urllib.parse import urljoin, urlsplit

MODELS = (
    ("det.onnx", "PP-OCRv5_mobile_det_onnx", "inference.onnx", "a431985659dc921974177a95adcfbb90fd9e51989a5e04d70d0b75f597b6e61d"),
    ("rec_korean.onnx", "korean_PP-OCRv5_mobile_rec_onnx", "inference.onnx", "92f0b7785e64fc9090106a241cf4c1eb97472824558272751b88a2a4476d3a08"),
    ("rec_korean.yml", "korean_PP-OCRv5_mobile_rec_onnx", "inference.yml", "f757fa1c40e99edcf27e9cce879b93eb2a51fa46f5ef39095689b8c37dd75998"),
)


def _open_https(url, redirects=5):
    """HTTPS로만 내려받는다(file:// 등 다른 방식 불가). 넘겨주기(3xx)도 HTTPS 주소만 따라간다."""
    for _ in range(redirects + 1):
        parts = urlsplit(url)
        if parts.scheme != "https" or not parts.hostname:
            raise RuntimeError(f"HTTPS가 아닌 주소는 내려받지 않습니다: {url}")
        connection = http.client.HTTPSConnection(parts.hostname, parts.port or 443, timeout=120)
        connection.request("GET", parts.path + (f"?{parts.query}" if parts.query else ""))
        response = connection.getresponse()
        if response.status in (301, 302, 303, 307, 308):
            url = urljoin(url, response.getheader("Location") or "")
            response.read()
            connection.close()
            continue
        if response.status != 200:
            raise RuntimeError(f"OCR model download failed: HTTP {response.status}")
        return response
    raise RuntimeError("OCR model download redirected too many times")


def download(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name, repo, filename, expected in MODELS:
        target = folder / name
        url = f"https://huggingface.co/PaddlePaddle/{repo}/resolve/main/{filename}"
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            temporary = target.with_suffix(target.suffix + ".download")
            try:
                with _open_https(url) as source, temporary.open("wb") as output:
                    size = 0
                    while chunk := source.read(1024 * 1024):
                        size += len(chunk)
                        if size > 40 * 1024 * 1024:
                            raise RuntimeError("OCR model exceeds expected maximum size")
                        output.write(chunk)
                if hashlib.sha256(temporary.read_bytes()).hexdigest() != expected:
                    raise RuntimeError(f"OCR model SHA256 mismatch: {name}")
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
        print(f"Verified PP-OCRv5 {name}: {expected}")


if __name__ == "__main__":
    download(sys.argv[1])
