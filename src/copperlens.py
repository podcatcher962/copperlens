#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCB 看板 / CopperLens（桌面版 / 单 exe）

    · 打开老式 EDA 软件的设计库(.ddb)：自动把里面所有 PCB 抽出来，一次全带上，
      界面上用下拉框切换（★最新 排第一）
    · 打开单个 .pcb 板文件
    · 抽出来立刻在窗口里显示，可缩放、点一下就能顺着铜皮查整条线路

不需要安装任何 EDA 软件、不需要 Python，也不联网。
显示用系统里的 Edge（Win10/11 自带；Win7/8 装了 Chrome 也行）。
程序按 32 位打包，从 Win7 到 Win11、32 位和 64 位系统都能跑。

⚠ 这里刻意不用 tkinter：32 位 Python 环境经常没装 Tcl/Tk，打进 exe 也缺
   运行库，结果就是"双击没反应"。所有对话框改用 Win32 API（comdlg32/user32），
   只依赖系统 DLL。
"""

import base64
import csv
import ctypes
import datetime as _dt
import json
import os
import subprocess
import sys
import tempfile
import time
from ctypes import wintypes
from pathlib import Path

APP_TITLE = "PCB 看板 CopperLens"
VERSION = "1.8"

_APPDIR = "CopperLens"
_LOG = Path(tempfile.gettempdir()) / _APPDIR / "last-run.log"


# ------------------------------------------------------------ 界面语言
def _ui_is_zh():
    """系统界面语言是不是中文。GetUserDefaultUILanguage 的低字节 0x04 = 中文。"""
    try:
        return (ctypes.windll.kernel32.GetUserDefaultUILanguage() & 0xFF) == 0x04
    except Exception:
        return True


_ZH = _ui_is_zh()


def L(zh, en):
    """按系统语言取文案。英文系统的人看到的就不是一堆看不懂的汉字。"""
    return zh if _ZH else en


def log(msg):
    """留一份运行记录：出问题时让用户把 last-run.log 发过来就能定位。"""
    try:
        _LOG.parent.mkdir(exist_ok=True)
        with open(_LOG, "a", encoding="utf-8") as f:
            f.write("%s  %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except Exception:
        pass


def res_path(*parts):
    """打包成 exe 后资源在 sys._MEIPASS；源码运行时在脚本旁边（或上一级）。"""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    p = base.joinpath(*parts)
    if p.exists():
        return p
    alt = base.parent.joinpath(*parts)
    return alt if alt.exists() else p


# ------------------------------------------------------------ Win32 对话框
_user32 = ctypes.windll.user32
try:
    _comdlg32 = ctypes.windll.comdlg32
except Exception:
    _comdlg32 = None


def msgbox(text, err=True):
    """不依赖 tkinter 的消息框（有控制台时同时打印）。"""
    log("对话框：%s" % str(text).replace("\n", " / "))
    try:
        print(text, file=sys.stderr)
    except Exception:
        pass
    try:
        flag = 0x00000010 if err else 0x00000040      # MB_ICONERROR / MB_ICONINFORMATION
        _user32.MessageBoxW(None, str(text), APP_TITLE, flag | 0x00040000)  # MB_TOPMOST
    except Exception as e:
        log("消息框也弹不出来：%r" % e)


class OPENFILENAMEW(ctypes.Structure):
    _fields_ = [
        ("lStructSize", wintypes.DWORD),
        ("hwndOwner", wintypes.HWND),
        ("hInstance", wintypes.HINSTANCE),
        ("lpstrFilter", wintypes.LPCWSTR),
        ("lpstrCustomFilter", wintypes.LPWSTR),
        ("nMaxCustFilter", wintypes.DWORD),
        ("nFilterIndex", wintypes.DWORD),
        ("lpstrFile", wintypes.LPWSTR),
        ("nMaxFile", wintypes.DWORD),
        ("lpstrFileTitle", wintypes.LPWSTR),
        ("nMaxFileTitle", wintypes.DWORD),
        ("lpstrInitialDir", wintypes.LPCWSTR),
        ("lpstrTitle", wintypes.LPCWSTR),
        ("Flags", wintypes.DWORD),
        ("nFileOffset", wintypes.WORD),
        ("nFileExtension", wintypes.WORD),
        ("lpstrDefExt", wintypes.LPCWSTR),
        ("lCustData", wintypes.LPARAM),
        ("lpfnHook", wintypes.LPVOID),
        ("lpTemplateName", wintypes.LPCWSTR),
        ("pvReserved", wintypes.LPVOID),
        ("dwReserved", wintypes.DWORD),
        ("FlagsEx", wintypes.DWORD),
    ]


OFN_READONLY = 0x00000001
OFN_NOCHANGEDIR = 0x00000008
OFN_PATHMUSTEXIST = 0x00000800
OFN_FILEMUSTEXIST = 0x00001000
OFN_EXPLORER = 0x00080000


def ask_file():
    """原生"打开文件"对话框。返回路径或 None。"""
    if _comdlg32 is None:
        msgbox(L("系统缺少文件对话框组件（comdlg32.dll）。\n"
                 "可以改成把 .pcb / .ddb 文件直接拖到本程序的图标上。",
                 "The file dialog component (comdlg32.dll) is missing.\n"
                 "Workaround: drag a .pcb / .ddb file onto this program's icon."))
        return None
    buf = ctypes.create_unicode_buffer(32768)
    filt = L("PCB 文件 (*.pcb;*.ddb)\0*.pcb;*.ddb\0"
             "设计库 (*.ddb)\0*.ddb\0"
             "板文件 (*.pcb)\0*.pcb\0"
             "所有文件 (*.*)\0*.*\0\0",
             "PCB files (*.pcb;*.ddb)\0*.pcb;*.ddb\0"
             "Design library (*.ddb)\0*.ddb\0"
             "Board file (*.pcb)\0*.pcb\0"
             "All files (*.*)\0*.*\0\0")
    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.hwndOwner = None
    ofn.lpstrFilter = filt
    ofn.nFilterIndex = 1
    ofn.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR)
    ofn.nMaxFile = len(buf)
    ofn.lpstrTitle = L("选择要看的板子", "Open a board")
    ofn.Flags = (OFN_EXPLORER | OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST |
                 OFN_NOCHANGEDIR)
    ofn.lpstrDefExt = "pcb"
    if not _comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
        return None
    path = buf.value
    return path or None


# ---------------------------------------------------------------- 显示内核
def find_browsers():
    """找能当显示内核的浏览器（Chromium 内核，--app 打开像独立程序）。"""
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    local = os.environ.get("LOCALAPPDATA", "")
    cands = [
        Path(pf86) / "Microsoft/Edge/Application/msedge.exe",
        Path(pf) / "Microsoft/Edge/Application/msedge.exe",
        Path(pf86) / "Microsoft/EdgeCore/Application/msedge.exe",
        Path(pf) / "Google/Chrome/Application/chrome.exe",
        Path(pf86) / "Google/Chrome/Application/chrome.exe",
    ]
    if local:
        cands += [Path(local) / "Microsoft/Edge/Application/msedge.exe",
                  Path(local) / "Google/Chrome/Application/chrome.exe"]
    # 注册表兜底：Edge / Chrome 装在非默认盘也能找到
    try:
        import winreg
        for root, key in ((winreg.HKEY_LOCAL_MACHINE,
                           r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe"),
                          (winreg.HKEY_LOCAL_MACHINE,
                           r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"),
                          (winreg.HKEY_CURRENT_USER,
                           r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe")):
            try:
                with winreg.OpenKey(root, key) as k:
                    p = winreg.QueryValue(k, None)
                    if p:
                        cands.append(Path(p.strip('"')))
            except OSError:
                pass
    except Exception:
        pass
    out, seen = [], set()
    for p in cands:
        try:
            k = str(p).lower()
            if k in seen:
                continue
            seen.add(k)
            if p.exists():
                out.append(p)
        except Exception:
            pass
    return out


def build_view_html(boards):
    """把查线器和板子数据塞进一个自包含的 HTML —— 不联网、不受跨域限制。
    boards = [(显示名, 字节)]，第一块默认打开，其余在下拉框里切换。

    窗口标题由页面自己拼：程序名（跟界面语言走） + __TITLE__（板子名）。
    Edge 用 --app 打开时，标题栏取的就是 document.title。
    """
    tpl = res_path("index.html").read_text(encoding="utf-8")
    data = [{"n": nm, "d": base64.b64encode(raw).decode("ascii")} for nm, raw in boards]
    inject = (
        "<script>window.__BOARDS__=" +
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) +
        ";window.__TITLE__=" +
        json.dumps(boards[0][0], ensure_ascii=False) +
        ";</script>"
    )
    html = tpl.replace("</head>", inject + "</head>", 1)
    outdir = Path(tempfile.gettempdir()) / _APPDIR
    outdir.mkdir(exist_ok=True)
    out = outdir / "view.html"
    out.write_text(html, encoding="utf-8")
    return out


def open_viewer(html_path):
    url = html_path.resolve().as_uri()
    log("open_viewer %s" % url)
    # 本程序是无控制台窗口的，子进程拿不到有效的标准句柄会直接启动失败，
    # 所以显式断开三个标准流。
    kw = dict(stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
              stderr=subprocess.DEVNULL, close_fds=True)
    browsers = find_browsers()
    if not browsers:
        log("  没找到 Edge/Chrome")
    for exe in browsers:
        log("  试 %s" % exe)
        try:
            p = subprocess.Popen([str(exe), "--app=" + url,
                                  "--window-size=1440,920",
                                  "--no-first-run",
                                  "--disable-features=Translate"], **kw)
        except OSError as e:
            log("    启动失败：%r" % e)
            continue
        # 还在跑 = 窗口开着；返回 0 = 复用了已有实例（窗口也已经打开）。
        for _ in range(15):
            if p.poll() is not None:
                break
            time.sleep(0.1)
        log("    退出码 %r" % p.poll())
        if p.poll() in (None, 0):
            log("    成功")
            return True
    log("  改用系统默认程序打开")
    try:
        os.startfile(str(html_path))
        log("    startfile 成功")
        return True
    except OSError as e:
        log("    startfile 失败：%r" % e)
    msgbox(L("没找到可以显示板子的浏览器。\n\n"
             "这台机器需要装有 Microsoft Edge 或 Google Chrome。\n"
             "Win10 / Win11 自带 Edge，不用另装；\n"
             "Win7 / Win8 没有自带，请先装一个。\n\n"
             "详细记录：\n",
             "No browser was found to display the board.\n\n"
             "This program needs Microsoft Edge or Google Chrome.\n"
             "Windows 10 / 11 ship with Edge; Windows 7 / 8 do not — "
             "install one first.\n\n"
             "Log file:\n") + str(_LOG))
    return False


# ---------------------------------------------------------------- 从 DDB 抽 PCB
MAX_EMBED = 28 * 1024 * 1024     # 一次最多带进界面 28MB 板数据
MAX_BOARDS = 8


def _name_score(t):
    """一串文字"像不像人话"的粗略打分，用来在几种编码里挑最合理的那个。

    判据很朴素：汉字、中文标点加分；拉丁重音字母（Â/Ã/µ/¥ 这类）扣分——
    真的西文文档名不会是这种拼法，出现它们基本就是编码没对上。
    """
    s = 0.0
    for ch in t:
        o = ord(ch)
        if o < 0x80:
            s += 1.0
        elif 0x4E00 <= o <= 0x9FFF:          # 常用汉字
            s += 3.0
        elif 0x3400 <= o <= 0x4DBF:          # 扩展 A
            s += 1.5
        elif 0x3000 <= o <= 0x303F or 0xFF01 <= o <= 0xFF5E:
            s += 2.0                          # 中文标点 / 全角字符
        elif 0xE000 <= o <= 0xF8FF or o == 0xFFFD:
            s -= 8.0                          # 私用区、替换符：铁定解错
        elif 0x80 <= o <= 0x24F:
            s -= 3.0                          # 拉丁扩展字母：铁定解错
        else:
            s -= 1.0
    return s


def _fix_text(s):
    """把从 CSV 里按 latin-1 读进来的字符串还原成它本来的样子。

    这里要剥两层错位，缺一层都还是乱码：

    ① mdbtools 导出文本字段时会自作主张按 CP1252 把它转成 UTF-8，
       于是原始 GBK 字节 B5 A5 变成 C2 B5 C2 A5 —— 先用 latin-1 还原成
       字节、再按 UTF-8 解一次，就退回每个字节一个字符的原始形态。
    ② 原始形态里 0x80 以上的是"某个单字节编码"的字节，简体中文机器建的
       库就是 GBK。用打分在 utf-8 / gb18030 / big5 / cp932 里挑最像人话的。

    纯 ASCII 完全不动，所以英文文档名一个字节都不会变。
    """
    if not s:
        return s
    try:
        raw = s.encode("latin-1")
    except UnicodeEncodeError:
        return s                              # 已经是正常 Unicode
    if raw.isascii():
        return s

    plain = None                              # ① 剥掉 mdbtools 的 UTF-8 化
    try:
        un = raw.decode("utf-8")
        if un and all(ord(c) <= 0xFF for c in un):
            cand = un.encode("latin-1")
            if cand != raw:
                plain, raw = un, cand
    except (UnicodeDecodeError, UnicodeEncodeError):
        pass

    best, best_sc = (plain or s), None        # ② 挑编码
    for enc in ("utf-8", "gb18030", "big5", "cp932"):
        try:
            t = raw.decode(enc)
        except UnicodeDecodeError:
            continue
        sc = _name_score(t)
        if best_sc is None or sc > best_sc:
            best, best_sc = t, sc
    return best


def extract_pcbs(ddb):
    """返回 [dict]，已排除回收站，按修改时间从新到旧。

    为什么不能只按 EditorName=='PCB' 抓：一个库里往往存着同一块板的多个
    历史版本（Rev b / Rev c / Rev d 各自一个文件夹），还有扔进回收站的旧图。
    全列出来维修的人根本分不清该看哪块，所以带上目录名和日期、最新那条标 ★。
    """
    mdb = res_path("mdbtools", "mdb-export.exe")
    if not mdb.exists():
        raise RuntimeError(L("找不到 mdbtools\\mdb-export.exe（程序不完整，请重新拷贝整个文件）",
                             "mdbtools\\mdb-export.exe is missing "
                             "(incomplete copy — please copy the whole file again)"))

    work = Path(tempfile.mkdtemp(prefix="copperlens_"))
    csv_path = work / "items.csv"
    try:
        with open(csv_path, "wb") as f:
            r = subprocess.run([str(mdb), "-b", "raw", str(ddb), "Items"],
                               stdout=f, stderr=subprocess.PIPE,
                               stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            msg = (r.stderr or b"").decode("utf-8", "replace").strip()[:300]
            raise RuntimeError(L("读不了这个设计库。\n",
                                 "Cannot read this design library.\n") +
                               (msg or L("可能是文件损坏或设了密码",
                                         "the file may be damaged or password-protected")))

        csv.field_size_limit(1 << 30)
        rows = []
        with open(csv_path, newline="", encoding="latin-1") as f:
            rd = csv.reader(f)
            try:
                head = next(rd)
            except StopIteration:
                return []
            col = {n: i for i, n in enumerate(head)}
            for need in ("ID", "ParentID", "Name", "EditorName", "Size"):
                if need not in col:
                    raise RuntimeError(L("这个库的结构不认识（缺少 %s 列）" % need,
                                         "Unrecognised library structure (missing column %s)"
                                         % need))
            width = len(head)
            for row in rd:
                if len(row) < width:
                    row = row + [""] * (width - len(row))
                rows.append({
                    "id": row[col["ID"]].strip(),
                    "pid": row[col["ParentID"]].strip(),
                    "name": _fix_text(row[col["Name"]].strip()),
                    "kind": row[col["EditorName"]].strip(),
                    "size": row[col["Size"]].strip(),
                    "mtime": row[col["Modified"]].strip() if "Modified" in col else "",
                    "data": row[col["Data"]],
                })
    finally:
        try:
            csv_path.unlink()
        except OSError:
            pass
        try:
            work.rmdir()
        except OSError:
            pass

    if not rows:
        return []

    byid = {x["id"]: x for x in rows}

    # 回收站整棵子树都要排除
    trash = set()
    for x in rows:
        if x["kind"] == "RecycleBin":
            stack = [x["id"]]
            while stack:
                cur = stack.pop()
                if cur in trash:
                    continue
                trash.add(cur)
                stack.extend(y["id"] for y in rows if y["pid"] == cur)

    def path_of(pid):
        parts, cur, seen = [], byid.get(pid), set()
        while cur and cur["id"] not in seen:
            seen.add(cur["id"])
            nm = cur["name"].strip()
            if nm and nm not in ("Documents", "root", "rootparent"):
                parts.append(nm)
            cur = byid.get(cur["pid"])
        return list(reversed(parts))

    def fmt_time(s):
        s = (s or "").strip()
        for f in ("%m/%d/%y %H:%M:%S", "%m/%d/%Y %H:%M:%S"):
            try:
                return _dt.datetime.strptime(s, f)
            except ValueError:
                pass
        return None

    boards = []
    for x in rows:
        if x["kind"] != "PCB" or x["id"] in trash:
            continue
        try:
            size = int(x["size"])
        except ValueError:
            size = 0
        if size <= 0 or not x["data"]:
            continue
        raw = x["data"].encode("latin-1").replace(b"\r\n", b"\r")
        if len(raw) < 64 or not raw.lstrip(b"\x00")[:24].count(b"PCB"):
            continue
        folder = path_of(x["pid"])
        base = x["name"]
        for bad in '\\/:*?"<>|':
            base = base.replace(bad, "_")
        if not base.lower().endswith(".pcb"):
            base += ".pcb"
        boards.append({
            "path": " / ".join(folder),
            "name": base,
            "bytes": raw,
            "kb": len(raw) / 1024.0,
            "time": fmt_time(x["mtime"]),
        })

    # 新的排前面：维修时通常要看最后改过的那块
    boards.sort(key=lambda b: (b["time"] is not None, b["time"] or 0), reverse=True)

    out, total = [], 0
    for b in boards:
        if len(out) >= MAX_BOARDS:
            break
        if out and total + len(b["bytes"]) > MAX_EMBED:
            continue
        total += len(b["bytes"])
        when = b["time"].strftime("%Y-%m-%d") if b["time"] else ""
        star = L("★最新 ", "★latest ") if not out and len(boards) > 1 else ""
        tag = "%s%s" % (star, b["name"])
        if b["path"]:
            tag += L("（%s）", " (%s)") % b["path"]
        if when:
            tag += " " + when
        out.append({"label": tag, "name": b["name"], "bytes": b["bytes"],
                    "kb": b["kb"], "when": when})
    if len(out) < len(boards):
        log("库里共 %d 块板，界面只带了前 %d 块（避免文件过大）" % (len(boards), len(out)))
    return out


# ---------------------------------------------------------------- 主流程
def handle(path):
    p = Path(path)
    if not p.exists():
        msgbox(L("找不到文件：\n", "File not found:\n") + str(p))
        return False

    ext = p.suffix.lower()
    log("handle %s (%d 字节)" % (p, p.stat().st_size))

    if ext == ".pcb":
        html = build_view_html([(p.name, p.read_bytes())])
        return open_viewer(html)

    if ext == ".ddb":
        boards = extract_pcbs(p)
        if not boards:
            msgbox(L("这个设计库里没有 PCB。\n（它可能只存了原理图或元件库。）",
                     "This design library contains no PCB.\n"
                     "(It may only hold schematics or component libraries.)"))
            return False
        log("抽出 %d 块板：%r" % (len(boards), [b["label"] for b in boards]))
        html = build_view_html([(b["label"], b["bytes"]) for b in boards])
        return open_viewer(html)

    msgbox(L("只认 .ddb 和 .pcb 两种文件。\n你选的是：",
             "Only .ddb and .pcb files are supported.\nYou picked: ") + p.name)
    return False


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    targets = [a for a in args if a.lower().endswith((".ddb", ".pcb"))]
    log("==== 启动 v%s  参数=%r  浏览器=%r  py=%s %d 位  zh=%s" %
        (VERSION, targets, [str(x) for x in find_browsers()],
         sys.version.split()[0], 64 if sys.maxsize > 2**32 else 32, _ZH))

    if not targets:
        f = ask_file()
        if not f:
            log("用户取消了文件选择")
            return 0
        targets = [f]

    ok = False
    for t in targets:
        try:
            ok = handle(t) or ok
        except Exception as e:
            log("处理失败：%s" % e)
            import traceback
            log(traceback.format_exc())
            msgbox(L("处理失败：\n", "Failed:\n") + "%s\n\n" +
                   L("详细记录：\n", "Log file:\n") + str(_LOG))
    return 0 if ok else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception:
        import traceback
        log("未捕获异常：\n" + traceback.format_exc())
        msgbox(L("程序出错：\n", "Program error:\n") +
               traceback.format_exc()[-1200:] + "\n\n" +
               L("详细记录：\n", "Log file:\n") + str(_LOG))
        sys.exit(1)
