# Third-party notices

## kordoc

The optional advanced document tools invoke `kordoc` version 4.x through npm.

- Project: https://gitlab.aigov.go.kr/chrisryugj/kordoc
- Copyright (c) 2026 chrisryugj
- License: MIT

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Optional kordoc features can load additional packages and models. Their own
license and notice files remain available in the installed kordoc package.

## Other components

| Component | Use | License |
|---|---|---|
| Hancom HWP automation security module sample (`MapoHwpAutoDocFitSecurity.dll`) | Approves HWP COM automation; Hancom sample binary renamed for this project | Hancom sample distribution terms |
| pywin32 | HWP COM bridge | PSF |
| tkinterdnd2 | Drag and drop | MIT |
| Pillow | Images | MIT-CMU (HPND) |
| defusedxml | Safe XML parsing | PSF |
| pywebview | Web UI window | BSD-3-Clause |
| Flutter | flutter_ui | BSD-3-Clause |
| Noto Sans KR | flutter_ui font (see `flutter_ui/assets/OFL.txt`) | SIL Open Font License 1.1 |
| PyInstaller | Executable build | GPL-2.0 with bootloader exception |
| Python / Tcl/Tk runtime | Bundled in the executable | PSF / Tcl/Tk License |

The HWP application itself (HWPFrame.HwpObject) is not bundled; the user's installed copy is used.
