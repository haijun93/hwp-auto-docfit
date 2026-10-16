"""Build-time only: fetch official PP-OCRv5 Korean models, verify pinned SHA256."""
import hashlib
from pathlib import Path
import sys
import urllib.request

MODELS = (
    ("det.onnx", "a431985659dc921974177a95adcfbb90fd9e51989a5e04d70d0b75f597b6e61d"),
    ("rec_korean.onnx", "92f0b7785e64fc9090106a241cf4c1eb97472824558272751b88a2a4476d3a08"),
    ("rec_korean.yml", "f757fa1c40e99edcf27e9cce879b93eb2a51fa46f5ef39095689b8c37dd75998"),
)


def _open(name):
    """모델마다 고정된 HTTPS 주소만 연다(주소를 조립하지 않음: GitLab Semgrep dynamic-urllib 규칙, 2026-10-17)."""
    if name == "det.onnx":
        return urllib.request.urlopen(
            "https://huggingface.co/PaddlePaddle/PP-OCRv5_mobile_det_onnx/resolve/main/inference.onnx", timeout=120)
    if name == "rec_korean.onnx":
        return urllib.request.urlopen(
            "https://huggingface.co/PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx/resolve/main/inference.onnx", timeout=120)
    if name == "rec_korean.yml":
        return urllib.request.urlopen(
            "https://huggingface.co/PaddlePaddle/korean_PP-OCRv5_mobile_rec_onnx/resolve/main/inference.yml", timeout=120)
    raise ValueError(f"unknown OCR model: {name}")


def download(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name, expected in MODELS:
        target = folder / name
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            temporary = target.with_suffix(target.suffix + ".download")
            try:
                with _open(name) as source, temporary.open("wb") as output:
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
