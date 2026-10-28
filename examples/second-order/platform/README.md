# 半潜平台二阶差频计算包

本包保存原创平台的正式原生输入和 HydroStar 8.2.0beta 的真实计算输出。主网格总量为 2946，包含湿面、水线面、外部积分自由面及对称展开；sensitivity/coarse/ 为 2898 总面元的对照。两档的湿面和物理参数一致，外圈采用连续渐变环带。

水深为 200 m、航速为 0、浪向为 60°。QTF 第一波频为 0.50–1.10 rad/s、间隔 0.05 rad/s，差频为 0、0.05、0.10 rad/s。按 ω₂=ω₁+Δω 保留 36 对有效配对、216 个复数荷载系数。力单位 N/m²，力矩单位 N m/m²；原生实部与虚部保持完整。qtf.json 将未求解的边界配对记为 null。

| 位置 | 正式交付内容 |
| --- | --- |
| inputs/ | HST 实际网格、RDF 波频与工况、MCN 质量与物理参数、DFT 平均漂移、QTF 二阶设置、RAO 提取指令 |
| rao/ | 六自由度运动、近远场平均漂移及六分量复数 QTF |
| logs/ | 八阶段原生执行日志 |
| geometry/ | 共水线环带网格、覆盖与形状检查、实际 HSLEC 积分面元核对 |
| delivery.json | 文件用途、状态、哈希、单位、依赖与执行顺序 |
| verification.json | 一阶复响应、QTF 对角项、近远场及外域敏感性、分量适用范围与图形来源 |
| plots/ | 直接读取原生结果并导出 SVG 的 Gnuplot 科研排版脚本 |

三个力分量的外域敏感性最高为 0.406%，横摇和纵摇力矩最高为 0.083%。艏摇力矩的自身峰值归一差异为 23.374%，近远场平均漂移差异为 128.854%，该分量标记为需继续收敛研究。工程荷载用途须完成对应分量、湿面、外域范围、频率及参考结果验证。

复算时把 inputs/ 的六份文件复制至新的工作目录，在自己的已授权 HydroStar 安装中依次执行下列命令。MPI 启动和环境按本机版本配置；本次 RDF、DFT、AMG、QTF 使用 2 进程，许可串行调度。

~~~text
hslec platform2.hst platform2
hschk - platform2
hsrdf platform2.rdf platform2
hsmcn platform2.mcn platform2
hsdft drift.dft platform2
hsamg full.qtf platform2
hsqtf full.qtf platform2
hsrao results.rao platform2
~~~

bin/、hdf/ 由正式输入重新生成，rao/ 为提取输出。当前规则波研究的 SPC 谱统计文件记为本次不适用。需要波谱统计时提供独立海况与 .spc，再进行相应验收。

从仓库根目录执行 `python scripts/check_second_order.py` 可离线核对交付。绘图时在本目录为每幅图单独运行 `gnuplot plots/qtf.gp` 等脚本，导出原生 SVG。发布脚本使用 Svglib/ReportLab 转为矢量 PDF，并由 PDFium 转为 PNG，转换版本及来源随 verification.json 保存。图形位于 [docs/assets](../../../docs/assets)，详细方法见[二阶计算说明](../../../docs/second-order.md)。
