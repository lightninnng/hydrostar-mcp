# 原生计算图与动画 / Native scientific figures and animations

半潜平台的 [StarViewer 和 HyView 原生结果图](result-viewer-exports.json)包括六自由度 RAO、垂向二阶 QTF、HSMCN 带浪运动及湿面压力。[HyView 复算包](hyview-platform)保存显式全体 HST、同工况场量设置、重算响应与对照记录。

The [bundled StarViewer and HyView exports](result-viewer-exports.json) cover the semisubmersible RAOs, vertical-load QTF, HSMCN motion in waves and wet-surface pressure. The [HyView replay package](hyview-platform) records the explicit full-body HST, field settings, recomputed RAOs and comparisons.

配套曲线使用 Gnuplot 读取原生响应文件，配套云图使用经过完整复响应核对的 HSPRS 场量和面元压力，由 ParaView 命令保存。图注、单位、固定色标和观察倍率随图给出，GIF 由实际 ParaView 帧编码。

Companion curves use Gnuplot and the native RAO files. Companion contours use independently checked HSPRS complex fields and panel pressure, exported by ParaView commands. Captions state units, fixed colour scales and display gains; GIFs encode actual ParaView frames.

每个 fields 子目录保存原生网格与参数、场量输入、完整复数数据、原始响应归档、查看设置、数值验收、可视化记录和正式交付清单。HSprv 的原始 PVD 数据另行归档，旧格式总场差异保留为诊断；公开动画指向通过独立复数核对的场量。

Each fields directory contains native inputs, field cards, full complex values, original RAO archives, settings, numerical verification, rendering records and delivery status. Original HSprv PVD data are also archived. The old-format total-field discrepancy remains a diagnostic; displayed fields use the independently verified complex results.

| 构型 / Configuration | 原生数据 / Fields | 响应绘图 / Curves |
| --- | --- | --- |
| 曲线船体 / Curved hull | [场量与原生输入](fields/vessel) | [Gnuplot 数据与设置](curves/vessel) |
| 集装箱船 / Container hull | [场量与原生输入](fields/container) | [Gnuplot 数据与设置](curves/container) |
| 丰满油船 / Tanker | [场量与原生输入](fields/tanker) | [Gnuplot 数据与设置](curves/tanker) |
| 半潜平台 / Semisubmersible | [场量与原生输入](fields/platform) | [Gnuplot 数据与设置](curves/platform) |

完整复现命令见[可视化方法](../../docs/native-visualization.md)。工具依赖独立安装；[ParaView 版本清单](paraview-versions.json)及仓库中的环境文件记录了实际可用的 Windows 组合。

See [visualization methods](../../docs/native-visualization.md) for replay commands. Tools are installed separately; the [version record](paraview-versions.json) and repository environment file identify the tested Windows combination.

七种湿面构型及二阶外部积分面的 [Visu5D 原图记录](viewer-exports.json)保存所用 HST、对称显示、导出步骤及哈希。四构型 ParaView 配套总览记录见 [readme-meshes.json](readme-meshes.json)，八组动态预览记录见 [readme-media.json](readme-media.json)。预览保留原动图的全部相位、时间、固定调色板与图例，点击后可查看原始高清导出。

The [Visu5D export record](viewer-exports.json) lists the solved HST files, symmetry settings, export steps and hashes for the seven wet meshes and the exterior integration mesh. See [readme-meshes.json](readme-meshes.json) for the four-model ParaView companion plate and [readme-media.json](readme-media.json) for the eight dynamic previews. Previews retain every source phase, timing, fixed palette and legend, with links to the original full-resolution exports.
