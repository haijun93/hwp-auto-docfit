"""폴더를 '/' 경로 구분자의 ZIP으로 묶는다(Windows PowerShell 5.1 Compress-Archive 대체)."""
import os
import sys
import zipfile


def main(stage, output):
    with zipfile.ZipFile(output, "x", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for folder, dirs, files in os.walk(stage):
            dirs.sort()
            for name in sorted(files):
                path = os.path.join(folder, name)
                archive.write(path, os.path.relpath(path, stage).replace(os.sep, "/"))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
