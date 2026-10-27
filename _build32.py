# -*- coding: utf-8 -*-
"""用 32 位 Python 打包成单文件 exe（x86；32 位系统直接跑，64 位系统向下兼容）。

PyInstaller 装在哪里，按这个顺序找：
  1. 环境变量 PYI_TARGET（推荐：pip install --target <那个目录> PyInstaller）
  2. 本脚本旁边的 _py32/ 目录
两步都没有就退回到「直接用当前解释器里已装的 PyInstaller」。
"""
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
for cand in (os.environ.get("PYI_TARGET"), os.path.join(ROOT, "_py32")):
    if cand and os.path.isdir(cand):
        sys.path.insert(0, cand)
        break

import PyInstaller.__main__  # noqa: E402

SRC = os.path.join(ROOT, "src", "copperlens.py")
NAME = "PCB看板"
# 可选：把产物放到别的目录。exe 正在运行时没法覆盖它，先出到旁边再换。
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else ROOT
if not os.path.isabs(OUTDIR):
    OUTDIR = os.path.join(ROOT, OUTDIR)
OUT = os.path.join(OUTDIR, NAME + ".exe")

print("python:", sys.version)
print("64bit :", sys.maxsize > 2 ** 32)

PyInstaller.__main__.run([
    SRC,
    "--onefile",
    "--windowed",
    "--noconfirm",
    "--clean",
    "--name", NAME,
    "--distpath", OUTDIR,
    "--workpath", os.path.join(ROOT, "build"),
    "--specpath", os.path.join(ROOT, "build"),
    "--add-data", os.path.join(ROOT, "index.html") + ";.",
    "--add-data", os.path.join(ROOT, "src", "mdbtools") + ";mdbtools",
    "--exclude-module", "tkinter",
    "--exclude-module", "unittest",
    "--log-level", "WARN",
])
print("DONE", OUT, os.path.getsize(OUT) if os.path.exists(OUT) else "MISSING")
