# HydroStar 原生与手册推荐的可视化流程

“原生软件图”限定为 HydroStar 自带 HyView、Visu5D/Visu4D、StarViewer 等查看器中生成并保存的画面。优先打开本次项目并实际验收这些查看器的保存/导出；ParaView、Gnuplot 的结果标为配套工具出图，原生计算数值来源另行记录。当前发布七种湿面构型和半潜平台二阶外部积分面的 Visu5D 原图。

当前交付优先静态网格、压力/荷载和响应原图及数值表。原生软件自身保存与官方配套工具导出分别注明实际工具；代表相位图记录工况与相位，峰值结论另有全周期数据支持。README 默认展示高清 PNG 和矢量曲线，在线报告的动画由用户主动播放。已有 GIF 作为可选资料保存。

网格、曲线、运动和场量展示首先采用当前版本手册默认、推荐的可视化路径，包括原生工具以及官方输出接配套查看器的流程。这是项目必须遵循的默认选择：官方链路可用并覆盖需求时，先完成查看、核对与导出，再组织科研排版和在线展示。

每项任务先查对应分析章节的手册、教程和当前版本帮助，再选择适用路径。下表列出已核对的常用入口；其他手册推荐路径采用同一优先原则。

## 按内容选择入口

| 展示内容 | 首选路径 | 核对内容 |
| --- | --- | --- |
| 求解网格与几何部件 | hview / HyView；本机 Visu5D，按版本核对 hvisu / Visu4D | 实际求解面元连接、湿面、水线面、干结构及其他部件的显示范围，坐标和单位 |
| 运动、荷载及其他响应曲线 | hsplt / StarViewer；按版本使用 gnplt 等官方绘图入口 | 对应原生输出、量纲、浪向、频率定义、幅值和相位，实际采样点 |
| 谱、极坐标、响应谱及时间重建 | 配套 StarViewer 中适用的结果视图 | 实际计算量、数据覆盖、选定浪向与频率、单位和时间设置 |
| 短期、长期及其他谱统计图 | StarSpec 手册的相应绘图流程 | 已完成的谱统计结果、海况、概率、持续时间、统计量定义和单位 |
| 刚体运动、波面与表面压力云图 | 本机版本提供的 hview / HyView 原生后处理 | 本次原生数据库或场量文件、工况、物理时间/相位、压力分量与波面定义 |
| 手册规定的 ParaView 场量动画 | HSprv 导出 → Anim/ 数据 → ParaView / Hstar2Paraview | .prv 设置、原生导出的数据索引及场量、查看器与宏版本兼容、色标和时间轴 |
| GIF、视频与展示帧 | 上述原生工具的实际导出功能 | 固定色标、单位、观察倍率、周期、帧率和数据来源；按版本核实可导出的格式 |

## 先确认当前版本的用法

先识别本机安装版本、HydroStar 工作目录和项目名，再按配套手册、教程或帮助确认入口。环境命令、GUI 程序和独立求解器分别记录；控制台命令通过其对应的 HydroStar 项目环境调用。入口尚未封装成 MCP 工具时，仍按文档中的实际命令或界面路径操作。

本机 8.2.0 安装包的《HstarManual.pdf》第 3.13.1 节（PDF 第 53–54 页）介绍在 HydroStar 项目环境中输入 hview 查看已读取的网格，并通过部件树控制显示。第 12 章介绍 hsplt；同一手册的版本修订说明（PDF 第 7 页）记录 hsplt 已改为调用 StarViewer，旧 gnuplot 入口为 gnplt。使用时结合当前版本帮助核对，保留实际采用的曲线数据及设置。

同一手册的版本修订说明记录 HyView 动画模块，本机 PythonWrap/ 中提供 HyView.exe、visu5d.exe 和 StarViewer.exe。可执行文件存在表示入口已发现；实际查看和导出的成功状态以打开本次数据、核对画面并验收输出为依据。HyView 的参数、场量依赖和导出选项按本机帮助确认。

《HstarManual.pdf》第 14 章（PDF 第 143–145 页）规定 HSprv 的 ParaView 动画输出和 Hstar2Paraview 导入流程：使用本次 .prv 输入生成 Anim/ 数据，再由配套查看器加载。该流程属于官方首选路径。本机提供 hsprv.exe 与 hstar2paraview.py；使用前核对 ParaView、宏和 Python 接口版本，按当前手册选择兼容的导入方式。

《StarViewer-UserGuide.pdf》介绍极坐标、谱面、时间重建及响应谱等结果视图。《StarSpec_Manual.pdf》第 4.12 节（PDF 第 56 页）列出 Starspec 的绘图入口，如 -sht、-lt、-rao 与 -ws，分别用于已计算的短期、长期、RAO 与波谱结果。StarSpec 的显示入口与配套 Gnuplot 分别记录为对应软件出图。具体项目参数与输出形式仍按当前帮助确认。

## 从实际计算到原生画面

优先复用已经完成且来源匹配的原生计算。网格与场量关联到同一项目的输入、质量记录和文件哈希；原生查看所需的数据库在对应算例工作目录加载。需要再生成文件时，列出已有输入和具体步骤，沿用原来的物理参数及面元预算。

原生图像和动画实际打开后，核对面元边界、显示部件、视角、单位、频率、浪向、波幅、水深、时间原点或相位。压力说明所显示的分量和参考状态；波面说明入射、散射或总场定义。绘制整个周期时保持统一色标，并分别标注运动与波高的观察倍率。原生画面中的图例、坐标和关键参数保持可读。

优先使用上述官方流程实际支持的图片、帧序列或视频导出。任务需要 GIF 而当前流程只提供帧或视频时，可以在导出之后编码为 GIF，保存原始帧/视频及转码参数，注明原生数据、查看器与编码工具。色标、场值、相位和面元连接与原生结果一致。

## 补充制图与受限情况

论文排版、跨算例叠图和在线交互可使用外部工具补充，同时保留官方查看与数值核对记录。优先核对本次内容可用的手册推荐路径；受版本、授权、数据兼容性或导出格式限制时，先记录具体限制及已经核实的尝试，再选择自定义制图路径。该记录与结果一起交付。ParaView、Gnuplot 等被手册纳入官方工作流时，按对应的官方路径记录。

可视化记录准确标明画面的生成方式：原生导出、官方配套查看器导出、已导出帧转码或自定义渲染，并分别列出官方核对状态。历史脚本绘图与动画继续保留其真实生成工具和来源；采用新流程后，根据实际完成的查看或导出更新状态。

## 当前发布图的命令复现

**已验证的原生软件图。** HydroStar 8.2.0 自带 Visu5D。切换算例先用 **File → Close** 清空旧模型（直接连续打开会叠加）；再用 **File → Open** 读取实际求解 `.hst`，在 **Mesh → Hull 1** 核对湿面面元边界。半体算例用 **Display xOz symmetry** 展开，核对两侧形状；二阶 `platform2.hst` 还可选 **Mesh → Free-surface**，倾斜视角检查外部环带和四个水线开口。旋转和缩放至完整构型后，由工具栏 **Save image to file** 保存 JPG。本机对话框仅列 `picture (*.jpg)`；发布图均为 1630×900，保留原始文件、HST 和图像哈希，详见[导出记录](../examples/visualization/viewer-exports.json)。HyView 加载同一月池项目时报告 `vtkDelaunay2D` 填充警告，月池发布图采用已验证的 Visu5D 路径。

**StarViewer 曲线。** 打开算例 `rao/`，在 **RAOs** 选六个运动文件，设幅值（**Module**）与单一 60° 浪向，关闭 **All-In-One**，用 **Tight layout** 整理坐标后从工具栏 **Save** 直接保存 SVG。二阶用 **QTF** 标签读取 `qtf_fz.qtf`，选 **Module**、**plot in w** 和三条差频；此视图的横轴是两波平均角频率。原表在无效配对处保留零值，发布图在 StarViewer 内缩放到约 0.50–1.05 rad/s，保留原表并避开补零段。已核对保存的两张 SVG 由矢量路径组成。五浪向叠图和六分量 QTF 继续提供 Gnuplot 配套版。

**HyView 带浪画面与压力。** 同一半潜平台的对称 HST 在此版本 HyView 中只显示文件中存储的半体。为获得完整场景，将已验收湿面沿 xOz 显式镜像、共面节点合并，保留面元类型和法向；不带入二阶外部积分面。固定物理参数重做 `HSlec → HSchk → HSrdf → HSmcn → HSrao`。共 1656 个湿面和 126 个水线面（1782 个全体总面元）。排水量、浮心和湿面积通过对称前后核对；在 60° 的 31 个共同频率上，五个自由度最大复数差异小于各自峰值的 0.002%，艏摇为 0.7553%。原二阶求解输入和 QTF 独立保留。

```powershell
python scripts/prepare_hyview_platform.py output/validation/native-views/platform-hyview
```

用 **File → Open** 选重算目录。随算例保存的 `hyview/parameters.json` 设置规则波 7.9 s、0.50 m、60°，自由面和湿面压力均选择 **Perturbed**。点 **Play** 后核对日志中刚体运动、自由面和随体压力重建成功。`fs.prs` 使用 `COEFHDS 0.0`，`hull_0.prs` 使用 `COEFHDS 1.0`；后者保留一阶随体扰动，不含静水基值。波面图关闭测速标记，水面设 **Surface**、透明度 0.5；压力图隐藏自由面，采用原生 Viridis 色标。压力色标是显示范围；水柱单位及 `p = ρgh` 换算见手册第 9 章及第 12.1.11 节。

本机通过 **Record → 再点 Record → Save recording** 得到 H.264/MKV（20 fps）；发布 PNG 从原生录制逐帧解码，未裁切、缩放或重绘。没有用桌面截图，也未从此版本确认单图直接保存入口。两图是同一工况的独立代表帧；录制帧号用于复现，HyView 未提供该帧的物理时刻，不能用帧号除以帧率推断求解相位。静帧提取命令为 `python scripts/extract_hyview_frame.py INPUT.mkv INDEX OUTPUT.png`（需 OpenCV）。[出图验收记录](../examples/visualization/result-viewer-exports.json)保存选帧、单位、色标和哈希；[原生输入与复算数据](../examples/visualization/hyview-platform)包括 HST、提取卡、HSPRS 场点和六个重算 RAO。原生录制留在本地工作目录。

HyView 波面与刚体运动是一阶结果，可与二阶荷载并列说明工况。空间压力云图同样是一阶水动力压力。二阶 QTF 表达的是整个浮体的差频荷载系数；计算二阶湿面压力、慢漂运动或结构应力时，分别提供对应原生求解证据。

**配套工具图。** 以下命令保留配套出图的来源及复现方法。

响应图通过 `scripts/export_native_curves.py` 读取原生 RAO，沿 Gnuplot 路径保存 PNG、PDF 和 SVG。场量由 HSPRS 与 HSRAO 提取完整复数系数，通过 ParaView 命令渲染，再由 `scripts/encode_native_media.py` 添加科研图注并编码为 GIF。公开目录保存原生输入、原始数值、HSprv 数据、图像来源、参数和实际执行记录。

本机 8.2.0 的旧格式 HSprv 导出经过独立核对：入射和绕射分量可以匹配，运动相关总波面与完整复响应存在差异。当前展示使用已通过 HSPRS 复场量核对的总波、入射与绕射；散射和辐射在复数域相减后按相同物理相位重建。原始 HSprv 导出继续作为诊断保存，复核包括六个单位速度辐射系数与完整复运动的乘积。具体数值和处理经验见[排错记录](../skills/hydrostar-modeling/references/troubleshooting.md)。

表面压力使用随体一阶扰动，保留平均湿表面的实际 HST 面元边界；静水基值另存。转为 kPa 时使用原生压力头、密度、重力和本次波幅。压力与波面颜色保持实际物理量，波高和运动采用 6 倍观察倍率，平均湿面压力图为 1 倍几何比例。纯绕射图固定于平均姿态，辐射图显示对应的运动贡献。

已有公开数据可以直接重建图片，无需再次调用求解器。在克隆的完整仓库中，按本机已安装的命令运行。例如：

```powershell
conda env create -f scripts/paraview-environment.yml
conda activate hydrostar-visuals
pvpython --force-offscreen-rendering scripts/render_native_views.py examples/visualization/fields/vessel --output tmp/pv-vessel
```

编码 GIF 使用安装了项目 plot 依赖的 Python 环境：

```powershell
python scripts/encode_native_media.py --case vessel
python scripts/export_native_curves.py --gnuplot C:/path/to/gnuplot.exe --case vessel
python scripts/build_gallery.py
```

环境文件记录了已实际执行的 Windows ParaView/VTK ABI 组合，完整依赖版本见[可视化数据目录](../examples/visualization)。原生场量重算按各数据目录的交付清单执行。详细扫频的动画采用同网格、同物理参数的单频配套计算，并与完整扫频的六自由度复响应逐项核对。

## README 网格总览与动图预览

中英文 README 展示四种已计算构型的实际湿面网格、压力与波面、绕射与辐射以及六自由度响应。网格总览直接使用通过验收的原生面元连接，几何倍率为 1，各视图独立取景；蓝色湿面与灰色干结构背景分别显示。

```powershell
pvpython --disable-registry --force-offscreen-rendering scripts/render_readme_meshes.py
python scripts/export_readme_media.py
python scripts/export_readme_media.py --check
```

预览从已验收的高清 ParaView 动图按原固定调色板缩放，完整保留 40 个物理相位、逐帧时长、色标、单位和观察倍率。点击 README 图片可以打开高清动图或矢量响应 PDF。发布检查核对原始图、预览、脚本与验收来源的一致性，并在排除时间标题后检查每个场量视窗的 40 个物理相位均有像素变化。导出与复核记录见 `examples/visualization/readme-meshes.json` 和 `readme-media.json`。

## 交付记录

三种复杂几何的当前总览使用各自新网格完成原生重算，再由 HSprv 的 SHIP 输出进入 ParaView PVDReader。每个原生三角形或四边形与验收 HST 按节点坐标及完整连接关系逐面核对；显示平均湿面，关闭 deformation，几何倍率为 1。原始 PVD、两帧 VTU、实际 mesh-view.prv、执行日志与来源记录保存于各算例 visualization/ 和 logs/。本总览只验收网格，HSprv 诊断输出中的场量不用于该图。

```powershell
pvpython --disable-registry --force-offscreen-rendering scripts/render_geometry_meshes.py
python scripts/export_native_curves.py --gnuplot C:/path/to/gnuplot.exe --case lofted_vessel --case moonpool_caisson --case cad_spar
python scripts/export_geometry.py --gnuplot C:/path/to/gnuplot.exe
python scripts/build_gallery.py
python scripts/check_geometry.py
```

总览、各模型三维图与正交投影全部来自 HSprv → ParaView 离屏文件导出，单模型 PNG 为 3000×1700。每个模型的三页 PDF 分别保存三维、纵向和俯视图；总览 PDF 为每个模型一页。GL2PS 导出前将视图移出分割布局，显式设置两倍视图像素，避免默认 400×400 窗口裁切。检查实际 PDF 对象后确认本机 ParaView 6.2 仍会将三维几何栅格化，即使 Rasterize3Dgeometry=0；这些 PDF 为高清原生视图，不宣称矢量网格。PDFium 仅复制原生页对象。

响应和两档网格对照通过原始 RAO、hsrao 生成的 .gnu 宏与 Gnuplot 文件终端导出 PNG、矢量 PDF/SVG。宏中的列号逐项与原表浪向核对；原表已存储而宏省略的对称浪向使用其实际列，不作插值。原始宏、数据副本、脚本与输出哈希随包保存。记录见 `examples/geometry/native-mesh-views.json`、各例 visualization/verification.json 和 sensitivity/visualization/verification.json。独立批量导出方法见 [skill 导出说明](../skills/hydrostar-modeling/references/direct-export.md)。

交付清单保存手册依据、工具名称和版本、项目名、相对数据路径、输入及数据库哈希、命令或界面操作、视图设置、场量与工况、色标、单位、倍率、时间/帧率、导出格式和媒体哈希。原生绘图设置、场点输入、实际 .prv、所用 Anim/ 索引及数据、宏/会话设置、原始导出文件和必要的转码设置按采用的路径交付；数据库可随包保存，或清楚记录由交付输入再生成的方法。

原生及官方配套可视化状态按实际证据记为待查看、已查看、已导出、已验证或受限并采用补充方案。已验证须具备来源匹配、实际输出与视觉检查。求解质量门禁与可视化验收分别保留，各自完成相应阶段。

[原生文件交付](native-delivery.md)　[面元建模方法](panel-meshing.md)

## 二阶差频荷载系数的动态图

`scripts/animate_second_order.py` 使用手册配套的 Gnuplot 路径，直接读取实际原生 .qtf 的实部、虚部和有效频率配对，按明确的正时间谐波基底导出 SVG 帧，再转为 PNG 编码 GIF。两组分别展示频率域系数矩阵和选定频率对的六分量谐波。它们使用归一化荷载系数单位，独立于前述一阶空间场量动画；实际双频荷载合成、二阶面压力和慢漂位移需要对应原生计算。

保持各分量的色标与纵轴范围固定，记录物理周期、相位数、播放时长、单位、倍率、配对掩码及艏摇分量范围。排除时间与图注后检查各数值面板确实变化，零差频项另验收为恒定。原生绘图脚本、数值验证、转换与 GIF 设置随二阶计算包保存。
