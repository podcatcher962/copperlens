# PCB 看板 / CopperLens v1.16

**中文** ｜ [English](#english) ｜ [版本履历 Changelog](CHANGELOG.md)

维修查线路用的 **只读** 看板工具。点一下走线或焊盘 → 整条网络亮黄，状态栏直接写出
`U100-4 / C102-1` 这样的具体脚位。不装任何 EDA 软件，不联网。

单个 exe，**支持 x86 与 64 位 Windows**，Windows 7 / 8 / 10 / 11 双击即用，不用另装东西。

## 直接用

| | 地址 | 适合 |
|---|---|---|
| **在线版**（推荐先试） | <https://podcatcher962.github.io/copperlens/> | 浏览器直接打开，把板文件拖进去。**文件只在本机读取，不上传服务器**。读不了设计库（`.ddb`） |
| **桌面版 exe** | [Releases](../../releases) 里下载，约 9 MB | **支持 x86 与 64 位系统**，Win7 / 8 / 10 / 11 双击即用。**能读设计库 `.ddb`**（自动抽出里面所有板子） |

![查线](预览_查线.png)

> 格式名（`PCB 4.0 Binary File`）只出现在"能读什么"里，用来描述兼容性，不作商标使用；
> 详见文末《发布与合规》。

## 能读什么

| 文件 | 说明 |
|---|---|
| `.pcb`（`PCB 4.0 Binary`） | 单块板，1998–2000 年前后那一代设计文件 |
| `.ddb`（设计库） | 一次抽出库里所有板子，**每块板各占一个页签**，能并排对照 |
| `.kicad_pcb`（KiCad） | KiCad 6 / 7 / 8 / 9 / 10 的板文件（纯文本）；4、5 版的老格式也认。见「v1.14 重点」 |
| **Gerber + 钻孔**（`.gbr` `.gtl` `.gbl` `.gko` `.drl` `.xln` …） | 板厂给的那一包制造文件，**一层一个文件，整包一起拖进来合成一块板**；也可以直接给 `.zip`。见「v1.15 重点」 |
| 立创EDA **标准版** `.json` | 立创EDA 导出的板文件（纯文本 JSON）。见「v1.16 重点」 |
| 立创EDA **专业版** `.epro2` / `.epro` | 整个工程包直接拖进来，里面那份 `.epru` 设计日志会自己解开。见「v1.16 重点」 |

明确**不做**：原理图（`.sch`）、`PCB 3.0`（更早的 16 位版本，部分兼容、未逐一验证）。
宁可明确报错，也不给一张假图 —— 照假图查线是要出事的。

## 用法

双击 exe → 先过一段**海报**（几秒，点一下可跳过）→ 进**首页**；
首页点「打开文件」选 `.ddb` / `.pcb` / `.kicad_pcb` / 立创 `.json` / `.epro2` / Gerber（同一个对话框），
也可以把文件拖到 exe 图标上，或拖进窗口。**手上没文件也能打开程序看界面**。

点一下走线或焊盘 → 与之电气相连的整条铜亮黄，状态栏写出具体脚位。
**按 <kbd>H</kbd>（或顶栏「覆铜」按钮）→ 一键收起所有铺铜，细走线立刻看清。**

### 快捷键

| 键 | 作用 |
|---|---|
| <kbd>F</kbd> | 适合窗口（整板入画） |
| <kbd>H</kbd> | 覆铜显示 / 隐藏 |
| <kbd>K</kbd> | 两点通不通 |
| <kbd>D</kbd> | 量距 |
| <kbd>Ctrl</kbd>+<kbd>F</kbd> | 找元件 / 找网络 |
| <kbd>Esc</kbd> | 清高亮（量距过程中先退量距） |
| 方向键 | 平移（按住 <kbd>Shift</kbd> 走得更快） |
| <kbd>+</kbd> <kbd>-</kbd> | 缩放 |
| <kbd>0</kbd> | 回到板子中心 |
| 中键 | 关掉当前页签 |

鼠标：滚轮**以指针位置为锚点**缩放；**按住左键拖到画布边缘，画面自己往那个方向走**
（越靠边越快，松手就停）；放大后**左上角缩略图**里的黄框是当前视野，点一下跳过去；
板上**右键写一句话**就是一条标记，按板子存档。

## v1.16 重点

**立创EDA（EasyEDA）两种版本的板子都能看了。** 标准版是 `.json`，专业版是 `.epro2` / `.epro`
工程包 —— 国内打板圈最常用的就是这两样，对方给文件十有八九是它们。

![立创EDA 专业版：泰山派 1F 金手指核心板（RK3566）](预览_立创.png)

<sub>演示用板：**立创·泰山派 RK3566-1F 金手指核心板**，作者「立创开发板」（LCKFB），
来自[立创开源硬件平台](https://oshwhub.com/li-chuang-kai-fa-ban/tai-shan-pai-1f-jin-shou-zhi-he-xin-ban)，
按 **CC BY-NC-SA 4.0** 许可展示。截图由本程序渲染其公开的设计数据得出，未经修改；
本程序不附带该设计的任何工程文件。详见 [第三方组件与许可.txt](第三方组件与许可.txt)。</sub>

| 之前 | 现在 |
|---|---|
| 只有 Protel、KiCad、Gerber 三条路，**立创画的板打不开** | 标准版 `.json` 直接拖；专业版 `.epro2` 整个工程包直接拖 |
| — | 铜层按板子自己的名字列：`GND02` / `S03` / `POWER05` / `GND07`，不是笼统的"内层 1" |
| — | 焊盘带真实网络名（`I2C5_SCL_M0`、`VCC_3V3`），查线、清单照样按名字走 |
| — | 位号与型号从器件库里翻出来：`U6 = RK3566`、`R70 = 2.2kΩ` |

专业版那个包其实是 **zip**，里面除了一堆图片，真正的板子只有一份 `.epru` **设计日志**：
一行一条变更，形如 `{"type":"LINE","ticket":2414,"id":"e27"}||{"layerId":1,"startX":…}|`，
左边是流水号，右边才是内容 —— 所以读法是"按日志重建"，不是"按表取数"。

### 五个坑（都踩过）

1. **元件和它的属性分两行存，先后顺序不保证** —— 属性行可能排在同一条元件之前。
   边读边合会丢掉一半位号，得先全收着，扫完再统一并。
2. **封装 uuid 必须整串匹配。** 属性里的 `Footprint` 是 `49e9c3dbcc05e765_a816…` 这种整串；
   我一开始按 `_` 截断去前缀，结果把 8 个不同的封装并成同一个，单个元件摊出 2114 个焊盘，
   整板虚报 **17818** 个（实际 1963）。
3. **焊盘的孔是个对象，不是数字**：`{"holeType":"ROUND","width":40,"height":40}`。
   长圆孔（SLOT）要取短轴才是钻孔径，取 `width` 会把槽长当孔径。
4. **焊盘网络在 `PAD_NET` 里，而它的 `id` 是"字符串化了的数组"** ——
   `"[\"PAD_NET\",\"e0\",\"2\",\"e12\"]"`。不拆开这一层，所有焊盘的网络号都是 0。
5. **`REGION`（禁止布线区）用的是画布局部坐标**，跟板坐标不是一个原点。硬当铜画，
   板子下面会凭空多出一个菱形和一个大灰框 —— 现在直接丢掉。

验证用的是立创官方开源工程「泰山派1F 金手指核心板」（RK3566，8 层板，260 针金手指）：
**12995** 段走线 / **1963** 个焊盘 / **1078** 个过孔 / **347** 个元件 / **400** 个网络，
板框量出 **69.6 × 30.0 mm** —— 正好是 DDR4 内存条那个尺寸。
标准版另外两块真板（2 层 / 4 层）37 项断言、专业版 42 项断言（含 exe 传数据的两条通道），全过。

### 立创这两版的边界（先说清楚）

- **专业版的覆铜（POUR / POURED）不展开**：它存的是归一化坐标，跟板坐标不是一个原点，
  硬画整片错位。所以内层电地平面看起来是"空的 + 一片过孔"，这是实情，不是漏画。
- **只读 PCB**：工程包里的原理图、多板结构不读。
- **型号偶尔只有料号**：器件库里没填值的时候只能显示料号（比如屏蔽夹），长句会截短到 18 个字显示。
- **那份日志很大**：泰山派这块板的 `.epru` 有 18 MB。exe 把它压缩到 **14%** 再交给显示端
  （3.5 MB），双击打开照样是秒开；否则内嵌页面会胀到 24 MB。

## v1.15 重点

![Gerber：整包文件合成一块板](预览_Gerber.png)

**现在能看 Gerber 了 —— 也就是"板厂手里那一包文件"。** 这是唯一一种所有 EDA 都导得出的格式，
所以从此不论对方用什么软件画的板，只要能导制造文件，这里就能看。

| 之前 | 现在 |
|---|---|
| 只有对方愿意给原始工程文件（`.pcb` / `.kicad_pcb`）才看得了；**维修现场最常见的"只给一包 Gerber"完全打不开** | 一层一个文件，整包一起拖进来合成一块板；`.zip` 也行 |
| — | 光圈的直径当线宽 / 焊盘尺寸；钻孔按坐标套到铜皮上，套不上的当安装孔单独画 |
| — | 没有板框层就按铜皮外包补一圈，尺寸照样量得准 |
| — | 导出时勾了 X2 属性的，网络名和位号能接回来，查线和清单照样按名字走 |

三件必须按实情处理的地方：

- **零直径光圈**（`ADD10C,0.0000`）只是"抬笔挪位置"，不能落笔 —— 当真画成线，一块板会凭空多出几千条假线。
  板框层反过来：Altium 的机械层就是用 0 宽光圈画轮廓的，得给一个最小宽度，否则板子没边框、尺寸只能靠猜。
- **钻孔的小数位要跟着同批 Gerber 走**：RPI CAN Hat 的 Gerber 是 `FSLAX25`（5 位小数），钻孔 `X174291`
  就是 1.74291 英寸；DCF77 是 `FSLAX24`（4 位），同样的 `X26114` 是 2.6114 英寸。按固定 2:4 算会整整差 10 倍。
- **钻孔文件的名字各家各样**：Altium 叫 `.TXT`、Eagle 叫 `.drd`、KiCad 叫 `.drl`。所以只点中其中一层时，
  程序会按内容（有没有 `M48` 头）去同目录把同一块板的其它文件找齐 —— 不用按住 Ctrl 一个个点。

验证用的是两块真实板子（都取自开源仓库里的板厂成品包）：Raspberry Pi CAN HAT（Altium 导出，9 层 + 钻孔）
和 DCF77 时钟模块（Eagle 导出，含八角焊盘宏）。外形分别量出 **65.0 × 56.0 mm** 与 **99.0 × 74.5 mm**，
孔数与源文件的坐标行数逐个对上（106 / 98），33 项断言全过。

### Gerber 的边界（先说清楚）

Gerber 是**制造文件**，不是设计文件：它只描述形状，不写哪里是 GND、哪颗是 R1（除非导出时勾了 X2）。

- **清单里通常没有位号** —— 丝印上的字是被"描"成一条条线段的，没有文字语义，读不出 `R1`。
  只有 X2 属性里带了位号的才有。
- **查线变成"按铜皮连"**：没有网络号，就按几何接触去找相连的铜。结果通常是对的，
  但遇到大面积铺铜会一次点亮一大片 —— 因为它们在电气上确实连着。
- **过孔不单独统计**：Gerber 里的过孔就是铜层上的一个小圆，和圆焊盘长得一样，没法区分。
- **覆铜是"线填充"**：一大片铺铜在文件里是几千条密集的线，画出来就是满版实心色。想看清细走线，
  按 <kbd>H</kbd> 收起覆铜，或者在图层面板里关掉那一层。

## v1.14 重点

**现在也读 KiCad 的板子了。** 自己画的新板子（KiCad 6–10）不用再转成别的格式，直接拖进来。

| 之前 | 现在 |
|---|---|
| 只认 Protel / Altium 那一代的老文件，**自己画的 KiCad 板反而打不开** | `.kicad_pcb` 直接读：KiCad 6 / 7 / 8 / 9 / 10，连 4、5 版的老格式也认 |
| — | 走线、焊盘、过孔、覆铜、板框、丝印、位号、型号全部读出来；**查线、量距、清单定位、板子尺寸**一样能用 |
| — | 层名按 KiCad 的叫法显示（`F.Cu` / `B.Cu` / `Edge.Cuts`），不用记编号 |
| — | 板子外形量的是 `Edge.Cuts`，和 KiCad 里看到的一致 |

要过三道坎：KiCad 存**毫米**（本程序内部用 mil）、**Y 轴朝下**（本程序朝上）、
网络在 KiCad 10 里只存**名字**、6–9 存**编号**。三条都按文件版本分开处理。

验证用的是三块真实板子（KiCad 4 / 5 / 10）加一块最小 KiCad 8 板做板框精度校验：
22 项断言全过，同时把 Protel 那条老路径完整回归了一遍（14 项）。

## v1.13 重点

**点清单不再"怼脸"、同一个设计库里的多块板能并排开着，另外补了量距、板子尺寸、缩略导航和最近打开。**

![量距](预览_量距.png)

| 之前 | 现在 |
|---|---|
| 清单里点一颗 0402，画面直接怼到只剩两颗焊盘，得先滚轮缩小才认得出它在板子哪儿 | 元件占屏约三分之一，**周围留出位置感**；放大后左上角还有**整板缩略图**，黄框标出当前视野，点一下跳过去 |
| 想挪视角只能按方向键；拖到窗口边缘就拖不动了 | **拖到画布边缘，画面自己往那个方向走**（Protel 的手感），越靠边越快，松手就停 |
| 方位按钮被右侧清单抽屉盖住，找不到 | 方向盘搬到**左下角**，抽屉在右边，两个永远不抢位置 |
| 想知道两点差多少毫米，只能靠数格子和比例尺 | **量距**（<kbd>D</kbd>）：点两个点，黄虚线连着，读数同时给 `mm` 和 `mil`，落点自动吸到焊盘圆心 |
| 文件里明明有板子尺寸、最细线宽、最小孔径，界面一个都没显示 | 左栏「**板子**」：外形 mm、面积、铜层、元件/焊盘/过孔/网络数、最细线、最小孔；点元件多给一行**外形尺寸 + 脚数**，点网络给**布线总长 + 孔数** |
| 同一个 `.ddb` 换一块板，上一块就被冲掉了 | 下拉框选板 = **新开一个页签**，上一块原样留着，可以左右对照；已开过的那块再选是切过去，不重复解析 |
| 每次都要翻文件夹找上次那个 `.ddb` | 首页列出「**最近打开**」（只记本机路径，不上传），点一下直接开 |
| 窗口关了，exe 偶尔还在后台赖着 | 关窗时页面主动打招呼（`pagehide` → beacon），exe 立刻退；按 <kbd>F5</kbd> 刷新不会被误判成关闭 |

![清单定位](预览_清单定位.png)
![多板页签](预览_多板页签.png)
![首页：最近打开](预览_首页.png)

几个实现上的取舍（细节见 [CHANGELOG](CHANGELOG.md)）：

- **定位留白不是拍脑袋的比例**：按比例留白（目标占屏 ~1/3），并加了一条硬上限
  —— 屏幕短边至少装下 360 mil（约 9 mm），不然小料照样被放到看不见周围。
- **边缘平移用 `setTimeout` 自循环，不用 `requestAnimationFrame`**：窗口被别的窗口挡住、
  或页面在后台时，浏览器会把 rAF 挂起，指针贴在边上画面一动不动。
- **缩略图是离屏画的**：载入时画一次（只画走线和焊盘，跳过几千条覆铜填充线），
  之后每帧只是 `drawImage` + 一个黄框；整板都看得见时自动收起。

## 其它常用功能

| 功能 | 说明 |
|---|---|
| **查线** | 点走线/焊盘 → 整条网络亮黄，状态栏写脚位。点接地只亮焊盘与过孔，不把整板刷成一片黄 |
| **通不通**（<kbd>K</kbd>） | 点两点给结论：按网表 → 同片覆铜 → 实际铜皮连通，三层判据，老文件也能判 |
| **清单抽屉** | 右侧列出全部位号 + 型号、全部网络与脚数；点哪条跳哪条；一键复制清单 / 导出 CSV |
| **板上标记** | 右键写一句话（"这里烧过"），插旗存档，换板不串 |
| **图层** | 单击切换、双击只看这层；四个按钮：全选 / 全不选 / 顶底铜 / 反选 |
| **存图** | 当前画面（含位号、型号、高亮）一键存 PNG，文件名带板名和时间 |
| **多页签** | 一个文件一个页签，切回来缩放/平移/图层/高亮全部还原 |
| **中英双语** | 右上角 <kbd>🌐</kbd> 切换，按钮上写的是"对方"的语言 |

更多界面：`预览_全板标注.png`、`预览_清单_网络.png`、`预览_清单_脚位.png`、
`预览_标记.png`、`预览_多页签.png`、`预览_海报.png`、`预览_英文界面.png`、`预览_免责声明.png`。

## 隐私与安全

- **只读**：只读文件，**绝不修改、覆盖、删除**你的原始文件。
- **不联网**：显示内核跑在本机回环（`127.0.0.1` 随机端口 + 一次性令牌），
  **不监听网卡、不上外网、不写注册表**。在线版也是纯前端，文件不出浏览器。
- **不留痕**：只有两处写盘 —— 临时目录（读 `.ddb` 时的中转文件，退出即清）和
  首页「最近打开」的一份本地清单（只存路径、板名、时间，纯本地）。
- **无第三方库**：绘图与解析全部自己实现，没有运行时依赖注入。

## 兼容性

| 项 | 值 |
|---|---|
| 目标系统 | Windows 7 / 8 / 8.1 / 10 / 11，**x86 与 64 位都可** |
| exe PE 头 | `0x014c` = i386（32 位） |
| exe Subsystem | `2` = Windows GUI（无控制台窗口） |
| 运行库依赖 | 仅系统 DLL（comdlg32 / user32 / kernel32 + UCRT），无 tcl/tk、无 WebView2 |
| 浏览器要求 | 系统自带的 Edge / Chrome 任一（用于 `--app=` 独立窗口） |

## 已知限制

- **原理图（`.sch`）不做**：设计库里原理图是 OLE 复合文档且引用元件库，复杂度远高于 PCB。
- **DDB 内部结构直接读不做**：Jet 数据库的大字段跨 2KB 页存，页头会插进记录流，
  段一大就整段错位。宁可明确报错，也不给假图。
- 只支持 `PCB 4.0 Binary`；`PCB 3.0`（16 位版）部分兼容，未逐一验证。
- **KiCad 的自定义焊盘 / 梯形焊盘按矩形画**：外形接近，但不是逐点还原；
  圆弧按折线离散（每 8° 一段），放大到极限能看出棱角。
- **KiCad 的规则区（rule area）、3D 模型、尺寸标注不显示** —— 这些不影响查线。
- KiCad 4 / 5 的老文件里位号常常还是 `REF**`（没编号），那种板子的清单里就没有位号可找。
- **立创专业版的覆铜（POUR / POURED）不展开**：文件里存的是归一化坐标，跟板坐标不是一个原点，
  硬画整片错位，所以内层电地平面看起来是空的 + 一片过孔 —— 这是实情，不是漏画。
- **立创专业版的规则区（REGION / 禁止布线区）不画**：它同样用局部坐标，画出来会有一大块游离图形。
- 无代码签名，SmartScreen 可能提示"未知发布者"。

## 重新打包

```bash
py -3.12-32 -m pip install --target _py32 pyinstaller
py -3.12-32 _build32.py
```

**必须用 32 位解释器**，否则打出来是 64 位，32 位 Windows 上跑不起来。
`_build32.py` 会自动在环境变量 `PYI_TARGET` 或脚本旁的 `_py32/` 里找 PyInstaller。
可选参数：`_build32.py <输出目录>`（exe 正在运行时没法覆盖它，先出到旁边再换）。

## 仓库里有什么

```
PCB看板.exe              单文件程序（x86 32 位，走 Release 分发，不进源码树）
index.html               查线内核（单文件网页，中英双语，exe 里内嵌一份）
src/copperlens.py          exe 主程序（对话框文案随系统语言中/英）
src/mdbtools/              mdb-export.exe + DLL（读 .ddb 用，全是 32 位）
src/导出DDB.py             独立导出脚本（备用）
_build32.py               打包脚本（须用 32 位 Python，保证 x86）
使用说明.txt               随包说明
第三方组件与许可.txt        第三方组件、示例文件授权、GPL 源码书面要约
COPYING-GPL-2.0.txt        mdbtools 工具的 GPL 全文
COPYING-LGPL-2.1.txt       libmdb / libiconv 的 LGPL 全文
LICENSE-CERN-OHL-1.2.txt   预览截图所涉开源硬件的 CERN-OHL v1.2 全文
CHANGELOG.md              逐版改动记录
预览_*.png                 界面预览
```

`.pcb` / `.ddb` 设计文件与 `build/`、`_py32/`、`*.exe` 都不进源码树。

## 第三方组件与许可

| 组件 | 许可 | 用途 |
|---|---|---|
| mdbtools（`mdb-export.exe`） | GPL-2.0-or-later | 读 `.ddb`（设计库） |
| libmdb / libiconv（DLL） | LGPL-2.1 | 同上，动态链接 |
| 预览截图所涉开源硬件设计 ① | CERN-OHL v1.2 | 截图里展示的板子（© René Richard, 2017） |
| 预览截图所涉开源硬件设计 ② | **CC BY-NC-SA 4.0** | 立创·泰山派 RK3566-1F 金手指核心板（© 立创开发板 LCKFB，来自立创开源硬件平台） |

调用方式是**进程外调用 exe**，不与本程序链接成单一作品，因此不传染 GPL。
GPL-2.0 §3(b) 的三年书面源码要约写在 `第三方组件与许可.txt` 第 1 节。

## 发布与合规

分发（拷给同事、发群、放内网共享、上 GitHub）前逐条确认：

| # | 事项 | 现状 | 说明 |
|---|---|---|---|
| 1 | 产品名里不含任何厂商 / 软件名 | ✅ 已做 | 叫 `PCB 看板 / CopperLens`。窗口标题、图标名、exe 名、文件夹名都不带 |
| 2 | 厂商名只出现在"能读什么"的描述里 | ✅ 已做 | 只留格式自身魔数 `PCB 4.0 Binary File` 和扩展名 `.pcb / .ddb` —— 这是**描述性使用**（说明兼容性所必需），不是当商标用 |
| 3 | 不出现厂商图标 / 字体 / 界面素材 | ✅ 已做 | 全自绘，零外部资源 |
| 4 | 免责声明里写明"无隶属关系、商标归各自所有者" | ✅ 已做 | 免责声明第 5 节 + 关于 |
| 5 | mdbtools（GPL-2.0-or-later + LGPL）随附许可证 + 源码书面要约 | ✅ 已做 | 发行包内 `第三方组件与许可.txt` + `COPYING-GPL-2.0.txt` + `COPYING-LGPL-2.1.txt`。GPL-2.0 §3(b) 的三年 written offer 已写进 `第三方组件与许可.txt` 第 1 节 |
| 6 | 代码里不留任何第三方项目名 / 厂商名 | ✅ 已做 | 注释里原有的外部参考已删除，改为「由本人对样本文件做二进制差分实测得出」（这本来也是实际做法） |
| 7 | **PCB 设计文件一个都不分发** | ✅ 已做 | 预览截图用的两块板都来自开源硬件项目：PC-Henshin（© René Richard 2017, CERN-OHL v1.2）与立创·泰山派 1F（© 立创开发板 LCKFB, CC BY-NC-SA 4.0）。**这些文件一个都不进发行包、不进仓库、不进 Release** —— 不发出就不产生再分发义务。截图已随附 `LICENSE-CERN-OHL-1.2.txt` + 双重署名，并在 `第三方组件与许可.txt` 第 2 节写明（CC BY-NC-SA 的署名/非商业/相同方式共享三项义务逐条对应）。对外演示可换自画板 |
| 8 | 不要把公司真实板子 / 客户资料放进仓库 | ⚠️ 自己把关 | 生产板的 PCB 文件属公司资产，示例请用开源板或纯自制 |
| 9 | 免责声明写清"仅供参考、不得作生产依据、维修自负" | ✅ 已做 | 免责声明第 1/3/4 节，中英各一份 |
| 10 | 签名 / 证书 | — | 无代码签名，SmartScreen 可能提示"未知发布者"；内部分发属正常，对外分发可忽略或自行签 |
| 11 | 名字是否与在用品牌冲突 | ⚠️ 待定 | `CopperLens` 与一个同名海外 AI 服务重名（非 PCB 行业）。**品类不同、商标上难构成混淆**，但搜索会被对方占满。要清爽就换名 |
| 12 | exe / 源码里是否夹带本机信息 | ✅ 已验证 | 对 `PCB看板.exe` 与全部源文件检索**本机用户名、计算机名、工作目录路径（含工具名）、旧产品名**：**各 0 次**。通用盘符与 `Desktop`、`Program Files` 这类公共目录不算本机信息，代码里仍会出现 |
| 13 | 仓库里不要提交的东西 | ⚠️ 上传时注意 | 设计库 `.ddb`、`build/`、`_t/`、`_py32/`、`_archive/`、`*.exe` 走 Release 而非源码树 |

### 一句话总结风险

**能上传，风险很低。** 关键就三条：

1. **不拿别人名字当自己名字**（产品名、图标、快捷方式、窗口标题都不带）；
2. **提名字只为说明"能打开这种文件"**，并在免责声明里声明商标归属与无隶属关系；
3. **随包分发的第三方东西把许可证、署名、源码渠道一起给出去**（mdbtools 的 GPL / LGPL；
   截图所涉开源硬件的 CERN-OHL 与 CC BY-NC-SA）；**拿不到授权的文件干脆不放进包里**。
   带 **NC（非商业）** 条款的素材（如泰山派那块板）只用于展示，不改作卖点、不做广告。

格式兼容这件事本身，国内外都有大量工具在做（各类板图查看器、格式转换脚本），
属于事实上的行业惯例，不是在蹭品牌。而且本程序**只读**、不碰加密、不绕过任何授权机制，
属互操作性目的，这是各国判例里明确受保护的用途。

## 许可与署名

本程序自身的源码作者保留权利（仓库未附本项目级的开源许可）；随附的第三方组件
仍是各自的许可证 —— mdbtools 的 GPL-2.0-or-later / LGPL-2.1、截图所涉开源硬件的
CERN-OHL v1.2，全文见仓库根目录。第三方组件的完整清单与授权说明见 `第三方组件与许可.txt`。

**保持只读、不联网、不改原始文件**是这个项目的底线，不接受会破坏这条底线的改动。

© 永远的兰兰 Lanlan Eternal

---

# English

**English** ｜ [中文](#pcb-看板--copperlens-v116) ｜ [Changelog](CHANGELOG.md)

A **read-only** PCB viewer for repair work. Click a trace or a pad and the whole net lights
up in yellow, with the actual pin names right there in the status bar — `U100-4 / C102-1`,
not just "some copper". No EDA suite required. No network access.

One portable exe, **runs on both x86 and 64-bit Windows** — Windows 7 / 8 / 10 / 11,
double-click and go.

## Quick start

| | Where | Good for |
|---|---|---|
| **Web version** (try this first) | <https://podcatcher962.github.io/copperlens/> | Open in a browser, drop a `.pcb` in. **The file is read locally, never uploaded.** Cannot read design databases (`.ddb`) |
| **Desktop exe** | Download from [Releases](../../releases), ~9 MB | **x86 and 64-bit**, Windows 7–11, no install. **Reads `.ddb` design databases** (all boards inside, automatically) |

![Tracing a net](预览_查线.png)

> The format signature (`PCB 4.0 Binary File`) appears only in "What it reads", as a
> compatibility statement — not as a trademark. See *Compliance* below.

## What it reads

| File | Notes |
|---|---|
| `.pcb` (`PCB 4.0 Binary`) | A single board; the 1998–2000 era of design files |
| `.ddb` (design database) | Every board inside is extracted; **each board gets its own tab** so you can compare them side by side |
| `.kicad_pcb` (KiCad) | KiCad 6 / 7 / 8 / 9 / 10 board files (plain text); the older 4 and 5 formats work too. See "What's new in v1.14" |
| **Gerber + drill** (`.gbr` `.gtl` `.gbl` `.gko` `.drl` `.xln` …) | The fabrication set your board house sends: **one file per layer, drop the whole set in and it becomes one board**. A `.zip` works too. See "What's new in v1.15" |
| EasyEDA **standard** `.json` | The board file EasyEDA exports (plain-text JSON). See "What's new in v1.16" |
| EasyEDA **pro** `.epro2` / `.epro` | Drop the whole project file; the `.epru` design log inside is unpacked for you. See "What's new in v1.16" |

Explicitly **not supported**: schematics (`.sch`), and `PCB 3.0` (the earlier 16-bit
format) is only partially compatible and not verified case by case. A clear error beats a
wrong picture — tracing a fault off a wrong rendering is how people scrap boards.

## Usage

Double-click the exe → a short **poster** (a few seconds, click to skip) → **home**.
Click **Open file** and pick a `.ddb`, `.pcb`, `.kicad_pcb` or a Gerber set (one dialog for all), or
drag a file onto the exe icon or into the window. **You can open the program with no file at all** and just
look around.

Click a trace or pad → the whole electrically connected net lights up yellow and the status
bar names the pins. **Press <kbd>H</kbd> (or the "Pour" button) to hide every copper pour** —
the fastest way to see fine traces.

### Shortcuts

| Key | Action |
|---|---|
| <kbd>F</kbd> | Fit board to window |
| <kbd>H</kbd> | Copper pour on / off |
| <kbd>K</kbd> | Continuity between two points |
| <kbd>D</kbd> | Measure distance |
| <kbd>Ctrl</kbd>+<kbd>F</kbd> | Find part / net |
| <kbd>Esc</kbd> | Clear highlight (exits measuring first) |
| Arrows | Pan (<kbd>Shift</kbd> for a longer step) |
| <kbd>+</kbd> <kbd>-</kbd> | Zoom |
| <kbd>0</kbd> | Back to board centre |
| Middle click | Close current tab |

Mouse: the wheel zooms **anchored at the pointer**; **drag to the edge of the canvas and the
view keeps moving that way** (faster the closer you get, stops when you let go); once zoomed
in, the **mini-map in the top-left** shows your viewport as a yellow box — click to jump;
**right-click on the board writes a note**, saved per board.

## What's new in v1.16

**Both flavours of EasyEDA (LCEDA) boards now open.** The standard edition exports a `.json`;
the pro edition saves a `.epro2` / `.epro` project file. These two are what most Chinese
prototype houses hand you, so odds are this is the file you actually get.

The board in the screenshot is the **LCKFB Taishan Pi RK3566-1F gold-finger SoM**, published on the
EasyEDA open-hardware platform under **CC BY-NC-SA 4.0**; the image is this program rendering that
board's published design data, unmodified. No files from that design ship with this program.

| Before | Now |
|---|---|
| Protel, KiCad and Gerber only — **an EasyEDA board simply would not open** | Standard `.json` drops straight in; the pro `.epro2` project file goes in whole |
| — | Copper layers carry the board's own names — `GND02` / `S03` / `POWER05` / `GND07`, not a generic "inner 1" |
| — | Pads carry real net names (`I2C5_SCL_M0`, `VCC_3V3`), so tracing and the net list work by name |
| — | Designator and value come out of the device library: `U6 = RK3566`, `R70 = 2.2kΩ` |

The pro file is really a **zip**. Besides a pile of images it holds one `.epru` **design log**:
one change per line, `{"type":"LINE","ticket":2414,"id":"e27"}||{"layerId":1,"startX":…}|`,
ticket on the left, payload on the right — so the board is *rebuilt from a log*, not read from tables.

### Five traps, all of them hit

1. **A component and its attributes live on separate lines, in no guaranteed order.** The
   attribute line can come *before* the component it belongs to; merging on the fly loses half
   the designators. Collect first, merge after the scan.
2. **The footprint uuid must match in full.** The `Footprint` attribute is a whole string like
   `49e9c3dbcc05e765_a816…`. Splitting on `_` merged eight distinct footprints into one, which
   put 2114 pads on a single part and reported **17818** pads for the board (the real count is 1963).
3. **A pad's hole is an object, not a number**: `{"holeType":"ROUND","width":40,"height":40}`.
   For a slot, the short axis is the drill — taking `width` turns slot length into hole size.
4. **Pad nets live in `PAD_NET`, and its `id` is a stringified array** —
   `"[\"PAD_NET\",\"e0\",\"2\",\"e12\"]"`. Without unwrapping that, every pad has net 0.
5. **`REGION` (keep-out) uses a drawing-local coordinate frame**, not the board origin. Drawing it
   as copper adds a stray diamond and a big grey rectangle below the board — it is dropped now.

Verified on LCEDA's own open-source project "TaishanPi 1F gold-finger core board" (RK3566,
8 layers, 260-pin edge connector): **12995** trace segments / **1963** pads / **1078** vias /
**347** parts / **400** nets, outline measuring **69.6 × 30.0 mm** — exactly DDR4 SODIMM size.
37 assertions on two more real standard-edition boards plus 42 on the pro edition
(including both data channels the exe uses) all pass.

### Limits of the EasyEDA support (up front)

- **Pro-edition copper pours (POUR / POURED) are not expanded**: they use a normalised coordinate
  space that does not share the board origin, so drawing them shifts whole regions. Inner ground
  planes therefore look like bare vias and voids — that is the real data, not a miss.
- **PCB only**: the schematic and multi-board structure inside the project are not read.
- **Occasionally only a part number is available**: when the device library has no value, the part
  number is shown instead (e.g. a shield clip), trimmed to 18 characters.
- **That log is big**: the `.epru` for this board is 18 MB. The exe compresses it to **14%**
  (3.5 MB) before handing it to the viewer, so double-click still opens instantly; embedding it
  raw would bloat the page to 24 MB.

## What's new in v1.15

![Gerber: the whole set becomes one board](预览_Gerber.png)

**It reads Gerber now — the set of files your board house actually holds.** Gerber is the one
format every EDA can export, so from here on it does not matter what the other side drew with:
if they can hand over fabrication data, you can look at it.

| Before | Now |
|---|---|
| Only if they gave you the original project (`.pcb` / `.kicad_pcb`); **the most common case in repair — "all I have is a Gerber set" — did not open at all** | One file per layer; drop the whole set in and it becomes one board. A `.zip` works too |
| — | Aperture diameter becomes the trace width / pad size; drill hits are matched onto copper by coordinate, unmatched ones are drawn as mounting holes |
| — | No profile layer? The outline is closed from the copper extents, so board size still measures correctly |
| — | If the export carried X2 attributes, net names and refdes come back, and tracing / the parts list work by name |

Three things that had to be handled the way real files actually behave:

- **Zero-diameter apertures** (`ADD10C,0.0000`) only mean "pen up, move"; they must not draw.
  Treat them as lines and a single board grows thousands of phantom traces. The profile layer is
  the opposite case: Altium's mechanical layer draws its outline *with* a zero-width aperture,
  so it needs a minimum width or the board has no border and the size has to be guessed.
- **Drill decimal places must follow the Gerber of the same set.** The RPI CAN Hat Gerber is
  `FSLAX25` (5 decimals), so drill `X174291` is 1.74291 inch; DCF77 is `FSLAX24` (4 decimals),
  so the same-shaped `X26114` is 2.6114 inch. Assuming a fixed 2:4 is off by a factor of ten.
- **Drill files are named differently everywhere**: `.TXT` from Altium, `.drd` from Eagle,
  `.drl` from KiCad. So when you click just one layer, the program looks in the same folder for
  the rest of that board by content (does it carry an `M48` header) instead of by extension.

Verified against two real boards, both taken from finished fabrication sets in public repos:
a Raspberry Pi CAN HAT (Altium export, 9 layers + drill) and a DCF77 clock module (Eagle export,
including an octagonal pad macro). Outlines measure **65.0 × 56.0 mm** and **99.0 × 74.5 mm**;
hole counts match the source files' coordinate lines exactly (106 / 98). 33 assertions pass.

### Gerber's limits (stated up front)

Gerber is **fabrication data, not design data**: it describes shapes and never says which net is
GND or which part is R1 — unless the export carried X2 attributes.

- **The parts list usually has no refdes.** Text on the silkscreen is *stroked* into line segments
  with no character semantics, so `R1` cannot be read back. Only X2 tags give you refdes.
- **Tracing becomes "connected copper"**: with no net codes, connectivity is found by geometric
  contact. Usually correct, but a large pour will light up in one go — because it really is
  electrically continuous.
- **Vias are not counted separately**: in Gerber a via is just a small circle on a copper layer,
  indistinguishable from a round pad.
- **Pours are line-filled**: a large plane is thousands of closely spaced lines in the file, so it
  renders as a solid sheet. Press <kbd>H</kbd> to hide pours, or switch that layer off in the
  layer panel, to see fine traces.

## What's new in v1.14

**It reads KiCad boards now.** Boards you draw yourself (KiCad 6–10) go straight in — no
conversion step, no third-party tool.

| Before | Now |
|---|---|
| Only the 1998–2000 Protel/Altium generation — **the boards you drew yourself would not open** | `.kicad_pcb` directly: KiCad 6 / 7 / 8 / 9 / 10, plus the older 4 and 5 formats |
| — | Tracks, pads, vias, pours, board outline, silkscreen, refdes and values all come through; net tracing, measuring, list-locate and board stats work unchanged |
| — | Layers are named the KiCad way (`F.Cu` / `B.Cu` / `Edge.Cuts`) instead of numbers |
| — | Board size is measured off `Edge.Cuts`, matching what KiCad reports |

Three gaps had to be bridged: KiCad stores **millimetres** (this program works in mil),
**Y grows downwards** here it grows up, and **KiCad 10 dropped numeric net codes** in
favour of net names (6–9 still store numbers). Each case is handled per file version.

Verified against three real boards (KiCad 4 / 5 / 10) plus a minimal KiCad 8 board for
outline accuracy: 22 assertions pass, with the whole Protel path regressed alongside (14).

## What's new in v1.13

**Clicking a part in the list no longer slams the camera into it; several boards from one
database can stay open side by side; plus measuring, board facts, a mini-map and recent files.**

![Measuring](预览_量距.png)

| Before | Now |
|---|---|
| Clicking an 0402 in the list zoomed until only two pads were visible — you had to wheel out to work out where on the board you were | A part takes about a third of the screen, **with context around it**; the **mini-map** in the top-left frames your viewport, click to jump |
| To pan you had to press the arrow buttons; dragging to the window edge did nothing | **Drag to the canvas edge and the view keeps going** (the Protel feel), faster near the edge, stops on release |
| The pan buttons were buried under the right-hand list drawer | The pan pad moved to the **bottom-left**; the drawer is on the right, so they never fight for space |
| Distance between two points meant counting grid squares | **Measure** (<kbd>D</kbd>): two clicks, a dashed yellow line, readout in **mm and mil**, snapping to pad centres |
| The file knew the board size, thinnest trace and smallest hole — the UI showed none of it | **Board** block in the left panel: outline in mm, area, copper layers, parts / pads / vias / nets, thinnest trace, smallest hole. Selecting a part adds **body size + pin count**; selecting a net adds **total routed length + via count** |
| Switching boards inside one `.ddb` threw the previous one away | Picking a board from the dropdown **opens a new tab**; the previous one stays. Re-picking an open board just switches to it, no re-parse |
| Hunting through folders for last time's `.ddb` | **Recent files** on the home screen (local paths only, never uploaded) |
| The exe sometimes lingered after the window closed | The page says goodbye on `pagehide` (beacon) and the exe exits right away. <kbd>F5</kbd> is not mistaken for a close |

![Locating a part](预览_清单定位.png)
![Multiple board tabs](预览_多板页签.png)
![Home with recent files](预览_首页.png)

Design decisions worth knowing (details in the [CHANGELOG](CHANGELOG.md)):

- **Zoom headroom is not a guessed ratio**: the target gets about a third of the screen,
  and there is a hard cap — the short side of the viewport must hold at least 360 mil
  (~9 mm), otherwise small parts still get blown up past all context.
- **Edge panning uses a `setTimeout` loop, not `requestAnimationFrame`**: when the window is
  covered or the page is in the background, the browser suspends rAF and the view freezes
  with the pointer parked at the edge.
- **The mini-map is drawn off-screen once** (traces and pads only, skipping thousands of pour
  fill segments), then it is just a `drawImage` plus a yellow box per frame. It hides itself
  when the whole board is visible.

## Other everyday features

| Feature | Notes |
|---|---|
| **Net tracing** | Click a trace or pad → the whole net lights up, pins named in the status bar. Clicking ground lights pads and vias only, not the entire board |
| **Continuity** (<kbd>K</kbd>) | Two clicks → verdict, judged in three tiers: netlist → same pour → actual copper connectivity, so older files without net numbers still work |
| **List drawer** | All designators + values, all nets with pin counts; click any row to jump there; copy the list or export CSV |
| **Board notes** | Right-click, type a sentence ("this one burnt"), a flag is stored per board |
| **Layers** | Click to toggle, double-click to show only that layer; All / None / Top+Bot / Invert |
| **Save PNG** | The current view (designators, values, highlight included) as a PNG named after the board and time |
| **Tabs** | One tab per file; zoom, pan, layers and highlight are all restored when you come back |
| **Bilingual UI** | Toggle with <kbd>🌐</kbd>; the button always shows the *other* language |

## Privacy and security

- **Read-only**: files are only read. Your originals are **never modified, overwritten or
  deleted**.
- **No networking**: the renderer runs on a loopback-only local server (`127.0.0.1`, random
  port, one-time token). **Nothing listens on a network interface, nothing goes to the
  internet, nothing is written to the registry.** The web version is pure client-side — your
  file never leaves the browser.
- **Nothing left behind**: only two things touch the disk — a temp file used while parsing a
  `.ddb` (cleared on exit) and a local recent-files list (path, board name, time only).
- **No third-party runtime libraries**: parsing and drawing are implemented from scratch.

## Compatibility

| Item | Value |
|---|---|
| Target | Windows 7 / 8 / 8.1 / 10 / 11, **x86 and 64-bit** |
| exe PE machine | `0x014c` = i386 (32-bit) |
| exe subsystem | `2` = Windows GUI (no console window) |
| Runtime deps | System DLLs only (comdlg32 / user32 / kernel32 + UCRT); no tcl/tk, no WebView2 |
| Browser | Either bundled Edge or Chrome (used for the `--app=` window) |

## Known limitations

- **No schematics (`.sch`)**: inside a design database they are OLE compound documents that
  reference component libraries — far more complex than the PCB side.
- **No direct parsing of the database internals**: large fields span 2 KB pages and page
  headers get interleaved into the record stream, so big segments come out shifted. An
  explicit error is preferable to a plausible-looking wrong picture.
- `PCB 4.0 Binary` only; `PCB 3.0` (16-bit) is partially compatible, not verified.
- **KiCad custom and trapezoidal pads are drawn as rectangles** — close in shape, not
  point-for-point; arcs are flattened every 8°, so extreme zoom shows facets.
- **KiCad rule areas, 3D models and dimension annotations are not shown** — none of them
  matter for tracing a fault.
- In older KiCad 4 / 5 files, refdes are often still `REF**` (unannotated); those boards
  have nothing to search for in the parts list.
- Not code-signed, so SmartScreen may warn about an unknown publisher.

## Building from source

```bash
py -3.12-32 -m pip install --target _py32 pyinstaller
py -3.12-32 _build32.py
```

**A 32-bit interpreter is required**, otherwise you get a 64-bit binary that will not start
on 32-bit Windows. `_build32.py` looks for PyInstaller in `PYI_TARGET` or a sibling
`_py32/` directory. Optional argument: `_build32.py <output-dir>` (needed when the current
exe is running and cannot be overwritten).

## Third-party components

| Component | Licence | Purpose |
|---|---|---|
| mdbtools (`mdb-export.exe`) | GPL-2.0-or-later | Reading `.ddb` databases |
| libmdb / libiconv (DLLs) | LGPL-2.1 | Same, dynamically linked |
| Open-hardware design shown in screenshots ① | CERN-OHL v1.2 | PC-Henshin (© René Richard, 2017) |
| Open-hardware design shown in screenshots ② | **CC BY-NC-SA 4.0** | LCKFB Taishan Pi RK3566-1F gold-finger SoM (© 立创开发板 LCKFB, EasyEDA open-hardware platform) |

mdbtools is invoked **out of process**, not linked into a single work, so the GPL does not
propagate. The GPL-2.0 §3(b) three-year written offer is in section 1 of
`第三方组件与许可.txt` (Chinese).

## Compliance

Checked before any distribution (colleague, chat group, intranet share, GitHub):

| # | Item | Status | Note |
|---|---|---|---|
| 1 | Product name contains no vendor / software name | ✅ | It is `PCB 看板 / CopperLens`. Window title, icon name, exe name, folder name — all clean |
| 2 | Vendor names appear only in "what it reads" | ✅ | Only the format's own magic string `PCB 4.0 Binary File` and the extensions `.pcb / .ddb` — **descriptive use**, needed to state compatibility, not trademark use |
| 3 | No vendor icons / fonts / UI assets | ✅ | Everything hand-drawn, zero external assets |
| 4 | Disclaimer states non-affiliation and trademark ownership | ✅ | Disclaimer section 5 + About |
| 5 | mdbtools (GPL-2.0-or-later + LGPL) ships with licences and a written offer | ✅ | `第三方组件与许可.txt` + `COPYING-GPL-2.0.txt` + `COPYING-LGPL-2.1.txt`; GPL-2.0 §3(b) offer in section 1 |
| 6 | No third-party project names left in the code | ✅ | Original external references removed; the offsets were derived by binary diffing sample files, which is what was actually done |
| 7 | **No PCB design files are distributed at all** | ✅ | Both boards in the previews come from open-hardware projects: PC-Henshin (© René Richard 2017, CERN-OHL v1.2) and the LCKFB Taishan Pi 1F (© 立创开发板 LCKFB, CC BY-NC-SA 4.0). **None of those files are in the release package, the repo or any release asset** — not shipping them creates no redistribution obligation. Previews ship with `LICENSE-CERN-OHL-1.2.txt` and dual attribution, noted in section 2 of `第三方组件与许可.txt` (BY / NC / SA each addressed) |
| 8 | No real company boards or customer data in the repo | ⚠️ | Production PCB files belong to the employer; use open-hardware or self-made sample boards |
| 9 | Disclaimer: reference only, not for production, repair at your own risk | ✅ | Disclaimer sections 1 / 3 / 4, in both languages |
| 10 | Signing / certificate | — | Unsigned; SmartScreen may warn. Normal for internal use |
| 11 | Name collision with an existing brand | ⚠️ | `CopperLens` collides with an unrelated overseas AI service (not PCB). Different category, unlikely to confuse; search results will favour them. Rename if that matters |
| 12 | Machine paths / user names in the exe or source | ✅ | `PCB看板.exe` and every source file searched for the local user name, computer name, working-directory path (the one containing the tool name) and the old product name: **0 hits each**. Generic drive letters and common folders such as `Desktop` or `Program Files` are not personal data and do appear in code |
| 13 | What must not be committed | ⚠️ | Design databases, `build/`, `_t/`, `_py32/`, `_archive/`, `*.exe` — binaries go to Releases, not the source tree |

**Bottom line: safe to publish, very low risk.** Three rules: don't take someone else's name
as your own; mention names only to say "this file format can be opened", with trademark
ownership and non-affiliation stated; and ship licences, attribution and source routes with
any third-party component you distribute — or simply don't ship the file.

Format interoperability is common practice across many tools, and this program is
**read-only**: it does not touch encryption or circumvent any protection mechanism.

## Licence and credits

The program's own source is published here with all rights reserved by the author; this
repository carries no project-level open-source licence. Bundled third-party components keep
their own licences — mdbtools under GPL-2.0-or-later / LGPL-2.1, and the open-hardware design
shown in the screenshots under CERN-OHL v1.2. Full texts are in the repository root; the
complete component list and attribution are in `第三方组件与许可.txt` (Chinese).

**Read-only, offline, never touching your originals** is the non-negotiable baseline of this
project.

© 永远的兰兰 Lanlan Eternal
