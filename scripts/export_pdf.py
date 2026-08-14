# -*- coding: utf-8 -*-
"""用本机 PowerPoint 将 PPTX 导出为同名 PDF。

用法：python scripts/export_pdf.py [pptx路径]
默认处理 submission/TeachOps_GOAI_初赛方案.pptx。
路径经 base64 编码传给 PowerShell，避免中文路径编码问题。
"""
import base64
import os
import subprocess
import sys


def export(pptx: str, pdf: str) -> None:
    pptx = os.path.abspath(pptx)
    pdf = os.path.abspath(pdf)
    ps = (
        "$ErrorActionPreference = 'Stop'\n"
        "$app = New-Object -ComObject PowerPoint.Application\n"
        f'$pres = $app.Presentations.Open("{pptx}", -1, 0, 0)\n'  # ReadOnly=msoTrue, Untitled/WithWindow=msoFalse
        f'$pres.SaveAs("{pdf}", 32)\n'  # 32 = ppSaveAsPDF
        "$pres.Close()\n"
        "$app.Quit()\n"
    )
    enc = base64.b64encode(ps.encode("utf-16-le")).decode()
    r = subprocess.run(
        ["powershell.exe", "-NoProfile", "-EncodedCommand", enc],
        capture_output=True, text=True, timeout=180,
    )
    if r.returncode != 0 or not os.path.exists(pdf):
        print("EXPORT FAILED", r.returncode)
        print(r.stdout)
        print(r.stderr)
        sys.exit(1)
    print("saved:", pdf)


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "submission", "TeachOps_GOAI_初赛方案.pptx")
    export(src, os.path.splitext(src)[0] + ".pdf")
