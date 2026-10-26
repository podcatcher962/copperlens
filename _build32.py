# -*- coding: utf-8 -*-
"""用 32 位 Python 打包成单文件 exe（x86，Win10 32 位可直接运行）。"""
import os
import sys

sys.path.insert(0, r"E:\workbuddy\2026-10-26-18-39-43\_py32")

import PyInstaller.__main__  # noqa: E402

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src", "copperlens.py")
NAME = "PCB看板"
OUT = os.path.join(ROOT, NAME + ".exe")

print("python:", sys.version)
print("64bit :", sys.maxsize > 2 ** 32)

PyInstaller.__main__.run([
    SRC,
    "--onefile",
    "--windowed",
    "--noconfirm",
    "--clean",
    "--name", NAME,
    "--distpath", ROOT,
    "--workpath", os.path.join(ROOT, "build"),
    "--specpath", os.path.join(ROOT, "build"),
    "--add-data", os.path.join(ROOT, "index.html") + ";.",
    "--add-data", os.path.join(ROOT, "src", "mdbtools") + ";mdbtools",
    "--exclude-module", "tkinter",
    "--exclude-module", "unittest",
    "--log-level", "WARN",
])
print("DONE", OUT, os.path.getsize(OUT) if os.path.exists(OUT) else "MISSING")
