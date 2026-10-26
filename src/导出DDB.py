#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出DDB —— 把老式设计库(.ddb)里的 PCB 抽成独立的 .pcb 文件。

为什么需要它：
    DDB 是 Access 数据库，PCB 以长二进制字段存在里面，而且大段数据是跨 2KB 页
    存的。浏览器直接读会错位，所以先用本工具转成 .pcb，再用 index.html（PCB 看板）看。

用法：
    ① 把 .ddb 拖到 导出DDB.exe 的图标上；
    ② 或者双击 导出DDB.exe，再把 .ddb 拖进窗口、按回车；
    ③ 或者把 .ddb 放在 exe 旁边，双击 exe 即可。
    输出：在 DDB 同目录下生成 <DDB名>_pcb/ 文件夹，里面是抽出来的 .pcb

依赖：无。mdbtools 已打进 exe（源码运行时则用同目录 mdbtools/ 下的 mdb-export.exe）。
"""

import csv
import os
import re
import subprocess
import sys
from pathlib import Path

# 打包成 exe 后，随附文件被解到 sys._MEIPASS；源码运行时就在脚本旁边
_BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
MDB = _BASE / "mdbtools" / "mdb-export.exe"

# 该格式的文档类型 -> 扩展名
KIND_EXT = {"PCB": ".pcb", "SCH": ".sch", "Text": ".txt"}


def find_mdbexport():
    if MDB.exists():
        return MDB
    p = Path(__file__).resolve().parent / "mdbtools" / "mdb-export.exe"
    if p.exists():
        return p
    for name in ("mdb-export", "mdb-export.exe"):
        from shutil import which
        q = which(name)
        if q:
            return Path(q)
    return None


def export_table(ddb, exe):
    """把 Items 表导成 CSV（二进制原样），返回 CSV 路径。"""
    out = ddb.with_suffix(".items.csv")
    with open(out, "wb") as f:
        r = subprocess.run([str(exe), "-b", "raw", str(ddb), "Items"],
                           stdout=f, stderr=subprocess.PIPE)
    if r.returncode != 0:
        try:
            out.unlink()
        except OSError:
            pass
        raise RuntimeError("读不了这个库 —— " +
                           (r.stderr or b"").decode("utf-8", "replace").strip()[:300])
    return out


def extract(ddb, exe):
    ddb = Path(ddb)
    csv_path = export_table(ddb, exe)
    outdir = ddb.with_name(ddb.stem + "_pcb")
    outdir.mkdir(exist_ok=True)

    csv.field_size_limit(1 << 30)
    made = []

    with open(csv_path, newline="", encoding="latin-1") as f:
        rd = csv.reader(f)
        try:
            head = next(rd)
        except StopIteration:
            return made
        col = {name: i for i, name in enumerate(head)}
        need = ("ID", "Name", "Data", "Size", "EditorName")
        if not all(k in col for k in need):
            raise RuntimeError("Items 表结构不认识，缺少：" +
                               ", ".join(k for k in need if k not in col))
        width = len(head)
        for row in rd:
            if len(row) < width:
                row = row + [""] * (width - len(row))
            kind = row[col["EditorName"]].strip()
            ext = KIND_EXT.get(kind)
            if not ext:
                continue
            data = row[col["Data"]]
            if not data:
                continue
            raw = data.encode("latin-1")

            # ★ 关键一步：mdbtools 把二进制字段当文本导出，会把数据里的
            #   0x0D 自动补成 0x0D 0x0A。PCB 二进制里所有 0x0A 都紧跟在
            #   0x0D 后面，所以整块替换回来就能精确复原。
            fixed = raw.replace(b"\r\n", b"\r") if kind == "PCB" else raw

            name = row[col["Name"]].strip() or ("doc" + row[col["ID"]])
            for bad in '\\/:*?"<>|':
                name = name.replace(bad, "_")
            if not name.lower().endswith(ext):
                name += ext
            p = outdir / name
            n = 2
            while p.exists():
                p = outdir / (Path(name).stem + "_%d%s" % (n, ext))
                n += 1
            p.write_bytes(fixed)

            note = ""
            if kind == "PCB":
                size_col = row[col["Size"]].strip()
                if size_col.isdigit() and int(size_col) > 0:
                    want = int(size_col)
                    note = ("ok:%d" % len(fixed)) if len(fixed) == want \
                           else ("BAD:%d/%d" % (len(fixed), want))
            made.append((p, len(fixed), note))

    try:
        csv_path.unlink()
    except OSError:
        pass
    return made


def process_one(exe, ddb):
    print("\n处理：" + Path(ddb).name)
    try:
        made = extract(ddb, exe)
    except Exception as e:
        print("  失败：" + str(e))
        print("  （如果这个库设了打开密码，需要先解除密码）")
        return 0

    pcbs = 0
    for p, size, note in made:
        if p.suffix.lower() != ".pcb":
            continue
        pcbs += 1
        kb = "%.1f" % (size / 1024.0)
        tail = ""
        if note.startswith("ok:"):
            tail = "   √ 长度与数据库记录一致"
        elif note.startswith("BAD:"):
            tail = "   ! 长度不符(%s)，可能不完整" % note[4:]
        print("  抽出 %-30s %8s KB%s" % (p.name, kb, tail))
    print("  完成：%d 个 PCB，输出到 %s" % (pcbs, Path(ddb).with_name(
        Path(ddb).stem + "_pcb")))
    if pcbs == 0:
        print("  注意：这个库里没有 PCB（可能只有原理图或元件库）。")
    return pcbs


def parse_paths(line):
    out = []
    for m in re.finditer(r'"([^"]+)"|(\S+)', line or ""):
        p = m.group(1) or m.group(2)
        if p and p.lower().endswith(".ddb"):
            out.append(p)
    return out


def pause():
    try:
        if sys.stdin and sys.stdin.isatty():
            input("\n按回车键退出…")
    except (EOFError, KeyboardInterrupt, OSError):
        pass


def main(argv):
    # 控制台中文输出
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    print("================================================")
    print("  老式设计库( DDB )  ->  独立 PCB 文件")
    print("================================================\n")

    exe = find_mdbexport()
    if not exe:
        print("找不到 mdb-export.exe。")
        print("请确认 mdbtools 文件夹就在本程序旁边（里面应有 mdb-export.exe）。")
        pause()
        return 2

    here = Path(getattr(sys, "_MEIPASS", Path(argv[0]).resolve().parent))

    files = [a for a in argv[1:] if a.lower().endswith(".ddb")]
    if not files:
        files = sorted(str(p) for p in here.glob("*.ddb"))
    if not files:
        print("把 .ddb 文件拖到这个窗口里，然后按回车。")
        print("（也可以把 .ddb 直接拖到本程序的图标上）\n")
        try:
            files = parse_paths(input("> "))
        except (EOFError, KeyboardInterrupt):
            files = []

    if not files:
        print("\n没有拿到 .ddb 文件，什么也没做。")
        pause()
        return 2

    total = 0
    for ddb in files:
        if not Path(ddb).exists():
            print("\n找不到文件：" + ddb)
            continue
        total += process_one(exe, ddb)

    print("\n全部完成，共 %d 个 PCB。" % total)
    print("把生成的 .pcb 拖进 index.html（PCB 看板）就能查线了。")
    pause()
    return 0 if total > 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
