#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PCB 看板 / CopperLens（桌面版 / 单 exe）

    · 打开老式 EDA 软件的设计库(.ddb)：自动把里面所有 PCB 抽出来，一次全带上，
      界面上用下拉框切换（★最新 排第一）
    · 打开单个 .pcb 板文件
    · 打开 KiCad 的 .kicad_pcb 板文件（6~10，含 4/5 的老写法）
    · 抽出来立刻在窗口里显示，可缩放、点一下就能顺着铜皮查整条线路

不需要安装任何 EDA 软件、不需要 Python，也不联网。
显示用系统里的 Edge（Win10/11 自带；Win7/8 装了 Chrome 也行）。
程序按 32 位打包，从 Win7 到 Win11、32 位和 64 位系统都能跑。

⚠ 这里不用 tkinter：32 位 Python 环境经常没装 Tcl/Tk，打进 exe 也缺
   运行库，结果就是"双击没反应"。所有对话框改用 Win32 API（comdlg32/user32），
   只依赖系统 DLL。
"""

import base64
import csv
import ctypes
import datetime as _dt
import http.server
import json
import os
import secrets
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
from ctypes import wintypes
from pathlib import Path

APP_TITLE = "PCB 看板 CopperLens"
VERSION = "1.15"

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


_HWND_CACHE = [None]


_HK_PROC = ctypes.windll.kernel32


def _proc_name(pid):
    """进程 exe 名（小写）。用来把"我们开的 --app 窗口"和用户自己的浏览器标签分开。"""
    try:
        h = _HK_PROC.OpenProcess(0x1000, False, int(pid))   # QUERY_LIMITED_INFORMATION
        if not h:
            return ""
        try:
            buf = ctypes.create_unicode_buffer(1024)
            n = wintypes.DWORD(1024)
            if not _HK_PROC.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(n)):
                return ""
            return buf.value.rsplit("\\", 1)[-1].lower()
        finally:
            _HK_PROC.CloseHandle(h)
    except Exception:
        return ""


# 只认这些进程的窗口：--app 窗口的类名和普通标签页一样，只能靠"进程 + 标题"分开。
_VIEWER_PROCS = ("msedge.exe", "chrome.exe", "chromium.exe",
                 "brave.exe", "opera.exe", "vivaldi.exe", "thorium.exe")


def _viewer_hwnd():
    """找到我们自己那个显示窗口（Edge/Chrome 的 --app 窗口），当文件对话框的父窗口。

    ⚠ 这里以前只看标题，认到过一次**错的句柄**，后果很吓人：
    父窗口不对时，通用对话框会退而把"当前前台窗口"当主体并把它
    EnableWindow(False)，关掉对话框时又还给那个错句柄 —— 用户看到的就是
    "窗口还在、页面也在动，但点 X 没反应、整窗变灰"。

    ⚠ 后来还发现：用户在**夸克/普通浏览器**里打开在线版（标题同样带
    "PCB 看板 CopperLens"）时，这函数会把那个标签页当成自己的窗口，
    于是给别人家的窗口发 EnableWindow / SetForegroundWindow。
    所以现在四重要求：可见 + 类名是浏览器窗口 + 进程是我们认的浏览器 +
    标题里**没有 " - "**（浏览器标签页会追加 " - Microsoft Edge" / " - 夸克"，
    而 --app 窗口的标题是干净的），多个候选取面积最大的，并缓存结果。
    """
    h = _HWND_CACHE[0]
    try:
        if h and _user32.IsWindow(h) and _user32.IsWindowVisible(h):
            return h
    except Exception:
        pass
    try:
        best = [None, 0]
        proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        rect = wintypes.RECT

        def cb(hwnd, _):
            try:
                if not _user32.IsWindowVisible(hwnd):
                    return True
                cls = ctypes.create_unicode_buffer(64)
                _user32.GetClassNameW(hwnd, cls, 64)
                if cls.value not in ("Chrome_WidgetWin_1", "MozillaWindowClass"):
                    return True
                ln = _user32.GetWindowTextLengthW(hwnd)
                if ln <= 0:
                    return True
                b = ctypes.create_unicode_buffer(ln + 1)
                _user32.GetWindowTextW(hwnd, b, ln + 1)
                t = b.value
                if "CopperLens" not in t and "PCB 看板" not in t:
                    return True
                if " - " in t:          # 浏览器标签页：标题后面挂着浏览器名
                    return True
                pid = wintypes.DWORD()
                _user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                if _proc_name(pid.value) not in _VIEWER_PROCS:
                    return True
                r = rect()
                if not _user32.GetWindowRect(hwnd, ctypes.byref(r)):
                    return True
                area = max(0, r.right - r.left) * max(0, r.bottom - r.top)
                if area > best[1]:
                    best[0], best[1] = hwnd, area
            except Exception:
                pass
            return True

        _user32.EnumWindows(proc(cb), 0)
        _HWND_CACHE[0] = best[0]
        return best[0]
    except Exception:
        return None


def _dialog_open():
    """当前是不是有通用文件对话框开着（类名 #32770）。解禁线程靠它避让。"""
    hit = [False]
    try:
        proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def cb(hwnd, _):
            try:
                if not _user32.IsWindowVisible(hwnd):
                    return True
                cls = ctypes.create_unicode_buffer(64)
                _user32.GetClassNameW(hwnd, cls, 64)
                if cls.value == "#32770":
                    hit[0] = True
                    return False
            except Exception:
                pass
            return True

        _user32.EnumWindows(proc(cb), 0)
    except Exception:
        pass
    return hit[0]


def _reassert_enabled(h, tries=4):
    """把窗口重新启用，并分几次"补刀"。

    对话框的收尾不是同步的：我们这边 EnableWindow(True) 之后，系统还可能再
    关一次（实测就是这样），窗口于是停在禁用状态 —— 点 X 完全没反应。
    所以隔 0.3 秒再补几次，用户感觉不到窗口"灰一下"。
    """
    def run():
        for _ in range(tries):
            try:
                _user32.EnableWindow(h, True)
            except Exception:
                pass
            time.sleep(0.3)

    try:
        threading.Thread(target=run, daemon=True).start()
    except Exception:
        pass


def _unstick_guard():
    """保命线程：窗口被留在"禁用"状态时自动解禁。

    现象（真实发生过）：文件对话框关掉后，程序窗口还在、页面还在跑，但点 X、
    点任何按钮都没反应 —— 因为窗口还是 WS_DISABLED。这里每秒看一眼，
    只要"没有对话框开着 + 窗口却是禁用的"，就把它重新启用。
    """
    while True:
        time.sleep(1.2)
        try:
            h = _viewer_hwnd()
            if not h:
                continue
            if not _user32.IsWindowEnabled(h) and not _dialog_open():
                _user32.EnableWindow(h, True)
                _HWND_CACHE[0] = None          # 顺手让下次重新找一遍
                log("窗口卡在禁用状态（对话框没还回来），已自动解禁 hwnd=%r" % h)
        except Exception:
            pass


def _raise_window(h):
    """把窗口拽到最前面（单靠 SetForegroundWindow 常被系统"反抢焦点"规则挡掉）。"""
    try:
        HWND_TOPMOST, HWND_NOTOPMOST = -1, -2
        SWP = 0x0001 | 0x0002 | 0x0040          # NOSIZE | NOMOVE | SHOWWINDOW
        _user32.SetWindowPos(h, HWND_TOPMOST, 0, 0, 0, 0, SWP)
        _user32.SetWindowPos(h, HWND_NOTOPMOST, 0, 0, 0, 0, SWP)
        fg = _user32.GetForegroundWindow()
        tid_fg = _user32.GetWindowThreadProcessId(fg, None)
        tid_me = ctypes.windll.kernel32.GetCurrentThreadId()
        if tid_fg and tid_fg != tid_me:
            _user32.AttachThreadInput(tid_me, tid_fg, True)
            _user32.SetForegroundWindow(h)
            _user32.AttachThreadInput(tid_me, tid_fg, False)
        else:
            _user32.SetForegroundWindow(h)
        # 上面都失败时还有这一招（微软内部也在用，效果最硬）
        try:
            _user32.SwitchToThisWindow(h, True)
        except Exception:
            pass
    except Exception as e:
        log("对话框置前失败：%r" % e)


def _pop_dialog_forward(title, timeout=8.0):
    """文件对话框是工作线程弹的，没有父窗口焦点时会躲在浏览器后面。

    盯着 #32770（通用对话框类名），一出来就抓到最前面，并写一行记录。
    """
    end = time.time() + timeout
    proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    while time.time() < end:
        time.sleep(0.08)
        hits = []

        def cb(h, _):
            try:
                n = _user32.GetWindowTextLengthW(h)
                if n <= 0:
                    return True
                cls = ctypes.create_unicode_buffer(64)
                _user32.GetClassNameW(h, cls, 64)
                if cls.value != "#32770":
                    return True
                b = ctypes.create_unicode_buffer(n + 1)
                _user32.GetWindowTextW(h, b, n + 1)
                if b.value == title:
                    hits.append(h)
            except Exception:
                pass
            return True

        try:
            _user32.EnumWindows(proc(cb), 0)
        except Exception:
            return
        if hits:
            _raise_window(hits[0])
            log("对话框已置前 hwnd=%r" % hits[0])
            return


def ask_file():
    """原生"打开文件"对话框。返回路径或 None。"""
    if _comdlg32 is None:
        msgbox(L("系统缺少文件对话框组件（comdlg32.dll）。\n"
                 "可以改成把 .pcb / .ddb / .kicad_pcb 文件直接拖到本程序的图标上。",
                 "The file dialog component (comdlg32.dll) is missing.\n"
                 "Workaround: drag a .pcb / .ddb / .kicad_pcb file onto this "
                 "program's icon."))
        return None
    # 对话框是走 shell 的，从工作线程弹之前先把 COM 起起来（已起过会返回 S_FALSE，无害）
    try:
        ctypes.windll.ole32.CoInitializeEx(None, 0x2)
    except Exception:
        pass
    buf = ctypes.create_unicode_buffer(32768)
    filt = L("PCB 文件 (*.pcb;*.ddb;*.kicad_pcb;*.gbr;*.zip)"
             "\0*.pcb;*.ddb;*.kicad_pcb;*.gbr;*.gtl;*.gbl;*.gko;*.drl;*.zip\0"
             "设计库 (*.ddb)\0*.ddb\0"
             "板文件 (*.pcb)\0*.pcb\0"
             "KiCad 板文件 (*.kicad_pcb)\0*.kicad_pcb\0"
             "Gerber / 钻孔 (*.gbr;*.gtl;*.gbl;*.gko;*.drl;*.xln;*.zip)"
             "\0*.gbr;*.gtl;*.gbl;*.gts;*.gbs;*.gto;*.gbo;*.gko;*.drl;*.xln;*.zip\0"
             "所有文件 (*.*)\0*.*\0\0",
             "PCB files (*.pcb;*.ddb;*.kicad_pcb;*.gbr;*.zip)"
             "\0*.pcb;*.ddb;*.kicad_pcb;*.gbr;*.gtl;*.gbl;*.gko;*.drl;*.zip\0"
             "Design library (*.ddb)\0*.ddb\0"
             "Board file (*.pcb)\0*.pcb\0"
             "KiCad board (*.kicad_pcb)\0*.kicad_pcb\0"
             "Gerber / drill (*.gbr;*.gtl;*.gbl;*.gko;*.drl;*.xln;*.zip)"
             "\0*.gbr;*.gtl;*.gbl;*.gts;*.gbs;*.gto;*.gbo;*.gko;*.drl;*.xln;*.zip\0"
             "All files (*.*)\0*.*\0\0")
    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    owner = _viewer_hwnd()
    if owner:
        # 万一上一轮把窗口留在禁用状态，先解开再弹，否则对话框也会跟着"被禁用"
        try:
            _user32.EnableWindow(owner, True)
        except Exception:
            pass
    ofn.hwndOwner = owner
    ofn.lpstrFilter = filt
    ofn.nFilterIndex = 1
    ofn.lpstrFile = ctypes.cast(buf, wintypes.LPWSTR)
    ofn.nMaxFile = len(buf)
    title = L("选择要看的板子", "Open a board")
    ofn.lpstrTitle = title
    ofn.Flags = (OFN_EXPLORER | OFN_FILEMUSTEXIST | OFN_PATHMUSTEXIST |
                 OFN_NOCHANGEDIR)
    ofn.lpstrDefExt = "pcb"
    # 后台线程弹的对话框默认可能落在别的窗口后面；派个哨兵把它抓到最前面
    threading.Thread(target=_pop_dialog_forward, args=(title,),
                     daemon=True).start()
    try:
        ok = bool(_comdlg32.GetOpenFileNameW(ctypes.byref(ofn)))
    finally:
        # 不管用户是选了文件还是按了取消，父窗口都必须还回"可用"状态。
        # 踩过的坑：对话框关掉后窗口还是灰的，点 X 完全没反应。
        if owner:
            _reassert_enabled(owner)
    if not ok:
        return None
    path = buf.value
    return path or None


# ---------------------------------------------------------------- 显示内核
def find_browsers():
    """找能当显示内核的浏览器（Chromium 内核，--app 打开像独立程序）。"""
    # 安装目录一律从环境变量取，源码里不写死任何盘符
    sys_drive = os.environ.get("SystemDrive", "C:") + os.sep
    pf = os.environ.get("ProgramFiles") or os.path.join(sys_drive, "Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)") or os.path.join(sys_drive, "Program Files (x86)")
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


def build_view_html(boards, file_name=""):
    """把查线器和板子数据塞进一个自包含的 HTML —— 不联网、不受跨域限制。
    boards = [(显示名, 字节)]，第一块默认打开，其余在下拉框里切换。

    窗口标题由页面自己拼：程序名（跟界面语言走） + __TITLE__（板子名）。
    Edge 用 --app 打开时，标题栏取的就是 document.title。
    file_name 给页签用（拖到图标上打开时，页签显示的是文件名而不是板名）。
    """
    tpl = res_path("index.html").read_text(encoding="utf-8")
    # boards 的每一项可以是 (名, 字节)，也可以是 (名, [(文件名, 字节), …]) ——
    # 后者是 Gerber：一堆图层文件合成一块板，交给页面里的 parseGerberSet 拼。
    data = []
    for nm, raw in boards:
        if isinstance(raw, list):
            data.append({"n": nm,
                         "g": [{"n": f, "d": base64.b64encode(r).decode("ascii")}
                               for f, r in raw]})
        else:
            data.append({"n": nm, "d": base64.b64encode(raw).decode("ascii")})
    inject = (
        "<script>window.__BOARDS__=" +
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) +
        ";window.__TITLE__=" +
        json.dumps(boards[0][0], ensure_ascii=False) +
        ";window.__FILE__=" +
        json.dumps(file_name or "", ensure_ascii=False) +
        ";</script>"
    )
    html = tpl.replace("</head>", inject + "</head>", 1)
    outdir = Path(tempfile.gettempdir()) / _APPDIR
    outdir.mkdir(exist_ok=True)
    out = outdir / "view.html"
    out.write_text(html, encoding="utf-8")
    return out


def open_viewer(target):
    """用系统里的 Edge/Chrome 以 --app 方式开一个像独立程序的窗口。

    target 可以是本地 html 路径，也可以是 http://127.0.0.1 的首页地址。
    成功返回浏览器进程对象（首页模式要靠它判断窗口是否还开着），失败返回 None。
    """
    t = str(target)
    is_url = t.startswith(("http://", "https://"))
    url = t if is_url else Path(target).resolve().as_uri()
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
            return p
    if not is_url:
        log("  改用系统默认程序打开")
        try:
            os.startfile(str(Path(target)))
            log("    startfile 成功")
            return None
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
    return None


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


# ---------------------------------------------------------------- 首页模式
"""双击 exe 不再直接弹"打开文件"，而是进首页：先海报，再欢迎页，用户自己点打开。

页面跑在 Edge 里，要让它叫起 Windows 原生选择框（.ddb 只有 Python 这侧解得开），
就需要一条"页面 → 程序"的通道。这里用最朴素的办法：在 127.0.0.1 上起一个只服务
本机的临时端口（端口随机），URL 里带一次性令牌。不监听网卡、不上外网、不写注册表。

为什么不用 pywebview 那类内嵌浏览器：那需要 WebView2 Runtime，Win7 和一部分 LTSC
机器没有、离线也装不上，一旦缺了程序就打不开。Edge --app + 本机回环没有这个前提。
"""

_home_html = [b""]
_last_ping = [0.0]
# 页面临走前打的招呼（时间戳）。窗口关掉时浏览器会发一次 pagehide，
# 收到就退出；但要留 2.5 秒宽限，免得"刷新一下"也被当成关闭。
_bye = [0.0]


def build_home_html(token):
    tpl = res_path("index.html").read_text(encoding="utf-8")
    inject = ("<script>window.__DESKTOP__=1;window.__TOKEN__=%s;"
              "window.__TITLE__=\"\";</script>") % json.dumps(token)
    return tpl.replace("</head>", inject + "</head>", 1).encode("utf-8")


# ---------------- Gerber / Excellon ----------------
# 各家 EDA 导出的后缀五花八门（.gbr .gtl .gbl .gko .drl .xln .pho …），
# 这里只当作线索；真正的判据是文件内容（%FS / %MO / %ADD / M48）。
GER_SUFFIX = (".gbr", ".gtl", ".gbl", ".gts", ".gbs", ".gto", ".gbo",
              ".gko", ".gm1", ".gml", ".gmb", ".gpt", ".gbp", ".pho",
              ".art", ".drl", ".xln", ".nc", ".ncd", ".exc",
              # 钻孔文件专门有下面这两个叫法：Altium 用 .TXT、Eagle 用 .drd。
              # 后缀宽一点没关系，真正决定收不收的是 _looks_gerber 看内容。
              ".drd", ".txt")


def _looks_gerber(name, head):
    """看内容不看后缀 —— 板厂给的包里经常压根没有后缀。"""
    if b"\x00" in head:
        return False                      # 带 NUL 的是二进制（.pcb / .ddb）
    if b"%FS" in head or b"%MO" in head or b"%ADD" in head or b"M48" in head:
        return True
    return Path(name).suffix.lower() in GER_SUFFIX


def _gerber_members(p):
    """把一个文件或压缩包里的 Gerber / 钻孔成员取出来：[(文件名, 字节)]"""
    if p.suffix.lower() == ".zip":
        import zipfile
        try:
            z = zipfile.ZipFile(p)
        except Exception:
            return []
        out, total = [], 0
        with z:
            for info in z.infolist():
                if info.is_dir() or info.file_size > 40 * 1024 * 1024:
                    continue
                try:
                    data = z.read(info)
                except Exception:
                    continue
                if not _looks_gerber(info.filename, data[:4096]):
                    continue
                total += len(data)
                if total > 200 * 1024 * 1024:
                    break
                out.append((Path(info.filename).name, data))
        return out
    try:
        with p.open("rb") as f:
            head = f.read(4096)
    except OSError:
        return []
    if not _looks_gerber(p.name, head):
        return []
    try:
        return [(p.name, p.read_bytes())]
    except OSError:
        return []


def _head(p, n=4096):
    try:
        with p.open("rb") as f:
            return f.read(n)
    except OSError:
        return b""


def _gerber_auto(p):
    """只选了一层时，把同目录里同一块板的其它层一起带上。

    板厂给的包通常是 board.GTL / board.GBL / board.GTO / board.GKO / board.TXT
    平铺在一个文件夹里，维修现场只可能点中其中一个 —— 让它自己找齐，比让
    用户按住 Ctrl 一个个点实在。

    注意钻孔文件的名字千奇百怪：Altium 叫 .TXT、Eagle 叫 .drd、KiCad 叫 .drl，
    所以不能只看后缀，得看内容里有没有 M48（Excellon 的头）。
    """
    if p.suffix.lower() == ".zip":
        return _gerber_members(p)
    memb = _gerber_members(p)
    if not memb:
        return []
    group = [p]
    try:
        stem = p.stem.lower()
        for q in sorted(p.parent.iterdir()):
            if not q.is_file() or q.name == p.name:
                continue
            if q.stem.lower() != stem:
                continue
            if not _looks_gerber(q.name, _head(q)):
                continue
            group.append(q)
            if len(group) >= 30:
                break
    except OSError:
        pass
    if len(group) == 1:
        return memb
    out = []
    for q in group:
        for name, data in _gerber_members(q):
            out.append((name, data))
    return out


def _payload_for_path(p):
    """把选中的文件读成前端要的结构：{boards:[{n,d}], ddb:bool}"""
    ext = p.suffix.lower()
    if ext == ".pcb":
        raw = p.read_bytes()
        return {"boards": [{"n": p.name,
                            "d": base64.b64encode(raw).decode("ascii")}],
                "ddb": False, "file": p.name}
    if ext == ".kicad_pcb":
        # KiCad 从 6.0 起是纯文本 S 表达式，浏览器那侧自己解析（index.html 的
        # parseKicad）。这里只负责原样送过去，不做任何转换。
        raw = p.read_bytes()
        return {"boards": [{"n": p.name,
                            "d": base64.b64encode(raw).decode("ascii")}],
                "ddb": False, "file": p.name, "kicad": True}
    if ext == ".ddb":
        boards = extract_pcbs(p)
        if not boards:
            return {"error": L("这个设计库里没有 PCB。\n（它可能只存了原理图或元件库。）",
                               "This design library contains no PCB "
                               "(it may only hold schematics or part libraries).")}
        return {"boards": [{"n": b["label"],
                            "d": base64.b64encode(b["bytes"]).decode("ascii")}
                           for b in boards],
                "ddb": True, "file": p.name}
    # Gerber / Excellon：一堆文件合成一块板（浏览器那侧按层拼）
    memb = _gerber_auto(p)
    if memb:
        label = p.stem if ext == ".zip" else p.name
        return {"boards": [{"n": label,
                            "g": [{"n": n, "d": base64.b64encode(b).decode("ascii")}
                                  for n, b in memb]}],
                "gerber": True, "file": p.name}

    return {"error": L("只认 .pcb / .ddb / .kicad_pcb / Gerber / .zip。",
                       "Only .pcb, .ddb, .kicad_pcb, Gerber and .zip are supported.")}


def _payload_for_bytes(name, data):
    """拖进窗口的文件走这里：落到临时目录再按扩展名照常处理。"""
    suffix = Path(name).suffix or ".pcb"
    work = Path(tempfile.mkdtemp(prefix="copperlens_up_"))
    tmp = work / ("upload" + suffix)
    try:
        tmp.write_bytes(data)
        res = _payload_for_path(tmp)
        if not res.get("ddb") and res.get("boards"):
            for b in res["boards"]:
                b["n"] = name           # 别把临时文件名漏给用户看
            res["file"] = name
        return res
    finally:
        try:
            tmp.unlink()
        except OSError:
            pass
        try:
            work.rmdir()
        except OSError:
            pass


# ------------------------------------------------------ 最近打开（本机记录）
# 存在 %LOCALAPPDATA%\CopperLens\recent.json，只记路径 / 文件名 / 板名 / 时间。
# 不记文件内容，不联网，删掉这个 json 就等于清空列表。
def _recent_path():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return Path(base) / _APPDIR / "recent.json"


def _load_recent():
    try:
        data = json.loads(_recent_path().read_text(encoding="utf-8"))
        items = data.get("items") if isinstance(data, dict) else data
        return [x for x in (items or []) if isinstance(x, dict) and x.get("path")]
    except Exception:
        return []


def _save_recent(items):
    try:
        p = _recent_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"items": items[:12]}, ensure_ascii=False),
                     encoding="utf-8")
    except Exception as e:
        log("最近打开的记录写不进去：%r" % e)


def _remember(path, res):
    """打开成功后记一笔。同一个文件再打开就挪到最前面，不会重复。"""
    try:
        path = str(Path(path).resolve())
        items = [x for x in _load_recent()
                 if os.path.normcase(str(x.get("path", ""))) != os.path.normcase(path)]
        items.insert(0, {
            "path": path,
            "name": Path(path).name,
            "boards": [b.get("n") for b in (res.get("boards") or [])][:12],
            "ts": time.time(),
        })
        _save_recent(items)
    except Exception as e:
        log("最近打开记录失败：%r" % e)


def _recent_when(ts):
    """时间只给数字，不写"昨天"——界面有中英两种语言，数字两边都读得懂。"""
    try:
        if not ts:
            return ""
        t = time.localtime(ts)
        now = time.localtime()
        if (t.tm_year, t.tm_yday) == (now.tm_year, now.tm_yday):
            return time.strftime("%H:%M", t)
        if t.tm_year == now.tm_year:
            return time.strftime("%m-%d", t)
        return time.strftime("%Y-%m-%d", t)
    except Exception:
        return ""


def _recent_listing():
    out = []
    for it in _load_recent():
        p = str(it.get("path") or "")
        out.append({
            "name": it.get("name") or Path(p).name,
            "boards": it.get("boards") or [],
            "when": _recent_when(it.get("ts")),
            "gone": not Path(p).exists(),
        })
    return {"items": out}


class _HomeServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def _make_handler(token, home_html):
    class H(http.server.BaseHTTPRequestHandler):
        server_version = "CopperLensHome"

        def log_message(self, fmt, *args):
            log("  http " + (fmt % args))

        def _send(self, code, body, ctype):
            if isinstance(body, str):
                body = body.encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            try:
                self.wfile.write(body)
            except OSError:
                pass

        def _json(self, obj, code=200):
            self._send(code, json.dumps(obj, ensure_ascii=False),
                       "application/json; charset=utf-8")

        def _gate(self):
            u = urllib.parse.urlparse(self.path)
            q = urllib.parse.parse_qs(u.query)
            if (q.get("t") or [""])[0] != token:
                self._json({"error": "forbidden"}, 403)
                return None
            return u

        def do_GET(self):
            # 浏览器自动要图标，它不带令牌；直接回空，别在记录里刷 403
            if urllib.parse.urlparse(self.path).path.startswith("/favicon"):
                return self._send(204, b"", "image/x-icon")
            u = self._gate()
            if u is None:
                return
            if u.path in ("/", "/index.html"):
                return self._send(200, home_html, "text/html; charset=utf-8")
            if u.path == "/api/ping":
                _last_ping[0] = time.time()
                return self._json({"ok": True})
            if u.path == "/api/recent":
                return self._json(_recent_listing())
            if u.path == "/api/bye":
                # sendBeacon 有时走 GET，两个方法都认
                _bye[0] = time.time()
                return self._json({"ok": True})
            self._json({"error": "not found"}, 404)

        def do_POST(self):
            u = self._gate()
            if u is None:
                return
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n) if n > 0 else b""
            if u.path == "/api/bye":
                _bye[0] = time.time()
                return self._json({"ok": True})
            if u.path == "/api/open":
                log("弹出文件对话框（父窗口=%r）" % _viewer_hwnd())
                path = ask_file()
                log("对话框返回：%r" % path)
                if not path:
                    return self._json({"cancel": True})
                try:
                    res = _payload_for_path(Path(path))
                    if res.get("boards"):
                        _remember(path, res)
                    return self._json(res)
                except Exception as e:
                    log("打开失败：%r" % e)
                    return self._json({"error": str(e)})
            if u.path == "/api/upload":
                q = urllib.parse.parse_qs(u.query)
                name = (q.get("name") or ["board.pcb"])[0]
                if len(body) > 64 * 1024 * 1024:
                    return self._json({"error": L("文件太大（超过 64MB）",
                                                  "File too large (over 64 MB)")})
                try:
                    return self._json(_payload_for_bytes(name, body))
                except Exception as e:
                    log("拖入文件解析失败：%r" % e)
                    return self._json({"error": str(e)})
            if u.path == "/api/recent":
                # 只认记录里已有的路径，前端传不了任意路径过来
                q = urllib.parse.parse_qs(u.query)
                try:
                    i = int((q.get("i") or ["-1"])[0])
                except ValueError:
                    i = -1
                items = _load_recent()
                if not (0 <= i < len(items)):
                    return self._json({"error": L("没有这条最近打开的记录。",
                                                  "No such recent entry.")})
                p = Path(items[i].get("path") or "")
                if not p.exists():
                    return self._json({"error": L("文件已经不在原处了：\n",
                                                  "The file is gone:\n") + str(p)})
                try:
                    res = _payload_for_path(p)
                    if res.get("boards"):
                        _remember(str(p), res)
                    return self._json(res)
                except Exception as e:
                    log("从最近打开里打开失败：%r" % e)
                    return self._json({"error": str(e)})
            self._json({"error": "not found"}, 404)

    return H


def run_home():
    """双击启动：海报 → 首页 → 自己点"打开文件"。"""
    threading.Thread(target=_unstick_guard, daemon=True).start()
    token = secrets.token_hex(16)
    _home_html[0] = build_home_html(token)
    try:
        srv = _HomeServer(("127.0.0.1", 0), _make_handler(token, _home_html[0]))
    except OSError as e:
        # 端口被安全软件挡住之类：退回老做法，宁可弹个框也不能打不开
        log("本机服务起不来：%r —— 回退到直接弹文件对话框" % e)
        f = ask_file()
        return handle(f) if f else True

    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    url = "http://127.0.0.1:%d/?t=%s" % (port, token)
    log("首页地址：%s" % url)

    proc = open_viewer(url)
    if proc is None:
        srv.shutdown()
        return False

    # 窗口关掉就退出，别在后台留进程。
    # 三条判据，按可靠性排：
    #   ① 页面自己说"我走了"（pagehide → /api/bye）：最准，留 2.5 秒宽限，
    #      这样用户按 F5 刷新时（会先 pagehide 再重新 ping）不会被误杀；
    #   ② 页面心跳静默 120 秒：兜底（页面被强杀、浏览器崩了）；
    #   ③ 浏览器进程退出且从没收到过心跳：浏览器复用了别的实例时用这条。
    start = time.time()
    while True:
        time.sleep(0.6)
        now = time.time()
        if _bye[0] and now - _bye[0] > 2.5 and now - _last_ping[0] > 2.0:
            log("页面报告已关闭（bye），退出")
            break
        if _last_ping[0]:
            if now - _last_ping[0] > 120:
                log("页面已关闭（心跳静默），退出")
                break
        elif proc.poll() is not None and now - start > 8:
            log("浏览器已退出，退出")
            break
        elif now - start > 300:
            # 5 分钟一次心跳都没收到，说明页面根本没连上（浏览器复用了别的实例、
            # 或者开着的是个错误页）。这种情况下别再后台挂着，直接退。
            log("页面从未连上（无心跳），退出")
            break
        elif now - start > 6 * 3600:
            log("已运行 6 小时，退出")
            break
    try:
        srv.shutdown()
    except Exception:
        pass
    return True


# ---------------------------------------------------------------- 主流程
def handle(path):
    p = Path(path)
    if not p.exists():
        msgbox(L("找不到文件：\n", "File not found:\n") + str(p))
        return False

    ext = p.suffix.lower()
    log("handle %s (%d 字节)" % (p, p.stat().st_size))

    if ext in (".pcb", ".kicad_pcb"):
        html = build_view_html([(p.name, p.read_bytes())], p.name)
        _remember(str(p), {"boards": [{"n": p.name}]})
        return open_viewer(html) is not None

    if ext == ".ddb":
        boards = extract_pcbs(p)
        if not boards:
            msgbox(L("这个设计库里没有 PCB。\n（它可能只存了原理图或元件库。）",
                     "This design library contains no PCB.\n"
                     "(It may only hold schematics or component libraries.)"))
            return False
        log("抽出 %d 块板：%r" % (len(boards), [b["label"] for b in boards]))
        html = build_view_html([(b["label"], b["bytes"]) for b in boards], p.name)
        _remember(str(p), {"boards": [{"n": b["label"]} for b in boards]})
        return open_viewer(html) is not None

    memb = _gerber_auto(p)
    if memb:
        label = p.stem if ext == ".zip" else p.name
        log("Gerber：%d 个文件合成一块板" % len(memb))
        html = build_view_html([(label, memb)], p.name)
        _remember(str(p), {"boards": [{"n": label}]})
        return open_viewer(html) is not None

    msgbox(L("只认 .ddb / .pcb / .kicad_pcb / Gerber / .zip。\n你选的是：",
             "Only .ddb, .pcb, .kicad_pcb, Gerber and .zip are supported.\nYou picked: ")
           + p.name)
    return False


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    targets = [a for a in args
               if a.lower().endswith((".ddb", ".pcb", ".kicad_pcb", ".zip")
                                     + GER_SUFFIX)]
    log("==== 启动 v%s  参数=%r  浏览器=%r  py=%s %d 位  zh=%s" %
        (VERSION, targets, [str(x) for x in find_browsers()],
         sys.version.split()[0], 64 if sys.maxsize > 2**32 else 32, _ZH))

    if not targets:
        # 双击启动：进首页（海报 → 欢迎页 → 自己点"打开文件"），不再直接弹框
        return 0 if run_home() else 1

    # 一堆 Gerber 一起拖到图标上：合成一块板看，而不是弹一堆窗口
    plain = [t for t in targets
             if not t.lower().endswith((".ddb", ".pcb", ".kicad_pcb"))]
    if len(plain) >= 2:
        memb = []
        for t in plain:
            memb += _gerber_members(Path(t))
        if memb:
            label = L("Gerber 板", "Gerber board") + " · %d %s" % (
                len(memb), L("个文件", "files"))
            log("Gerber 板：命令行 %d 个参数合成 %d 个文件" % (len(plain), len(memb)))
            html = build_view_html([(label, memb)], "")
            return 0 if open_viewer(html) is not None else 1

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
