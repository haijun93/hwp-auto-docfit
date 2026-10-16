"""Build-time only: fetch official PP-OCRv5 Korean models, verify pinned SHA256."""
import hashlib
from pathlib import Path
import sys
import urllib.request

MODELS = (
    ("det.onnx", "PP-OCRv5_mobile_det_onnx", "inference.onnx", "a431985659dc921974177a95adcfbb90fd9e51989a5e04d70d0b75f597b6e61d"),
    ("rec_korean.onnx", "korean_PP-OCRv5_mobile_rec_onnx", "inference.onnx", "92f0b7785e64fc9090106a241cf4c1eb97472824558272751b88a2a4476d3a08"),
    ("rec_korean.yml", "korean_PP-OCRv5_mobile_rec_onnx", "inference.yml", "f757fa1c40e99edcf27e9cce879b93eb2a51fa46f5ef39095689b8c37dd75998"),
)


def download(folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for name, repo, filename, expected in MODELS:
        target = folder / name
        url = f"https://huggingface.co/PaddlePaddle/{repo}/resolve/main/{filename}"
        if not target.is_file() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
            temporary = target.with_suffix(target.suffix + ".download")
            try:
                with urllib.request.urlopen(url, timeout=120) as source, temporary.open("wb") as output:
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
