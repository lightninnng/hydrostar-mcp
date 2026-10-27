# 原生计算图与动画 / Native scientific figures and animations

响应曲线使用 Gnuplot 读取原生响应文件，云图使用经过完整复响应核对的 HSPRS 场量和面元压力，由 ParaView 命令保存。图注、单位、固定色标和观察倍率随图给出，GIF 由实际 ParaView 帧编码。

Response curves use Gnuplot and the native RAO files. Contours use independently checked HSPRS complex fields and panel pressure, exported by ParaView commands. Captions state units, fixed colour scales and display gains; GIFs encode actual ParaView frames.

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
