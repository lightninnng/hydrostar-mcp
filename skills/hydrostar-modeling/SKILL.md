---
name: hydrostar-modeling
description: "Build and verify HydroStar hydrodynamic models from parameters, sections, CAD or meshes, using structure-aligned quadrilaterals and a default 3000-panel total budget. Use for geometry, meshing, quality checks, native single-body calculations and delivery of native mesh, load, parameter and result files."
---

# HydroStar 建模与验收

将资料、几何、物理参数、原生求解和结果来源连成可审阅的链路。MCP 与命令行使用同一套输入和验收；读取当前项目 AGENTS.md 后开展工作。

## 3000 面元预算

新模型默认使用 3000 个全体等效总面元预算，包含湿面、水线面与对称展开。计数采用 N_total=(N_wet+N_waterplane)×2^sym，其中 sym=0、1、2 分别表示全体、半体和四分之一体。独立自交检查内部使用的三角形数量另行记录。

保留 CaseConfig.recommended_max_panels=3000，GeometryRequest.max_panels 默认不高于 3000。初始网格从适合课程或简化分析的较低数量开始，为自动水线面预留预算；优先改善分区、对应关系、局部尺寸与模型简化。

预计或实测超出 3000 时，提出具体算例的湿面、水线面和全体总数，说明必要性以及时间/内存需求，再取得用户对该预算的明确授权。不得为通过检查自行抬高 recommended_max_panels、max_panels 或自动接受 confirmation_token。对同一算例、物理模型和面元预算已有的明确授权继续有效。

本项目保留的高密度参照例按其已授权配置复现；其预算属于特定研究记录。新建模型仍从 3000 默认预算规划，公开示例配置本身不构成其他用户的执行授权。

## 按结构选择拓扑

选择布局时阅读 [面元建模方法](references/panel-meshing.md)。

- 同轴圆柱、变截面 Spar 与扩底柱采用 ring_bands：轴向分环、周向等角对应、肩部径向分区及规则 O 型底面。
- 平顺船体采用 station_bands：沿 x 轴站位，与水线、最低点和两侧弧向对应，使用平顺纵向渐变及端部过渡。
- 等截面多边形外体和单一贯通开口采用 polygon_blocks：角点对应、环形底面及相容内外壁分块。
- 其余 CAD 采用 quad_dominant 分区离散；保留折角、接头、开口及共享边约束。已有表面网格保留有效四边形。

四边形保留到原生 HST，图示读取实际求解面元。局部三角形用于有说明的尖端、过渡和复杂连接，记录位置与数量。

## 资料与物理模型

使用 inspect_geometry_source 或 geometry-inspect 识别格式、单位和来源。型值表确认轮廓顺序与站位，CAD 确认闭合的外部排水实体。图像/PDF 经尺寸标定、独立检查点和经审阅描线后重建；缺失尺寸和形状假设写入来源说明。

显式给出质量、重心、惯性、约束、阻尼与环境。当前编排采用单刚体一阶频域分析。按目标问题说明 BEM 与 Morison 分工，保留实际几何、装载和耗散的证据状态。

## 验收与执行

build_geometry / geometry-build 产生独立几何包。检查原生面元比例、凸性、角度、翘曲、相邻尺度、CAD 体积/浮心、共享边、水线闭环、预期连通分量和全局自交。使用显式门限；超限先调整模型或离散，再复核。

将返回的 case_geometry 连同 source_manifest 用于 plan_case → prepare_case → start_case → case_status → read_rao，或对应 CLI。规划时检查估算总量，hslec 后复核实测总量。硬性门禁失败时完成具体诊断和修正，再进入后续步骤。

原生求解顺序执行并按机器内存选择 MPI 进程数。冻结输入与来源哈希；网格改变后，用新网格重算对应结果。比较离散时固定质量、重心、惯性、恢复、阻尼和环境，分别报告网格质量与响应敏感性。

## 原生文件属于正式交付物

每次交付同时提供可编辑、可检查、可继续计算的 HydroStar 原生文件。图表、动画和 JSON 报告与这些文件逐一对应。按当前安装版本的手册和教程核对文件格式及调用顺序，具体要求见[原生文件交付](references/native-delivery.md)。

| 文件 | 交付内容 |
| --- | --- |
| .hst | 实际求解网格的节点、面元连接、坐标和对称定义；保留曲面四边形 |
| .rdf | 辐射绕射的频率、浪向、水深、航速和结果文件设置 |
| .mcn | 质量、重心、惯性、恢复、阻尼及本次采用的附加构件与运动参数 |
| .rao | 结果提取指令文件，以及单独保存的原生响应/荷载 RAO 输出，附单位、浪向、频率和相位约定 |
| .spc | 教程或任务涉及 StarSpec 谱分析时的海况、谱型、方向、RAO 路径、积分与统计设置 |
| 其他实际使用的输入 | 如 .mri 建网指令、压力/场点输入、荷载与构件参数文件，以及几何源资料 |

同一算例使用一致的项目名、相对路径和文件引用；随包给出目录清单、关键参数与单位、执行顺序、质量门禁、文件哈希及结果来源。区分原生输入、求解器生成的中间文件和原生输出，保存复算或后续分析必需的文件。

逐项记录文件状态为已生成、已执行、已验证、待补充或本次不适用。包含谱统计的交付必须有实际 .spc；海况资料缺失时明确待补充参数，补齐后再完成该阶段。缺少本次分析需要的网格、荷载或参数文件时，交付尚未完成。已验证状态须有对应的实际执行与检查记录。

科研图采用清楚的单位、固定色标和观察倍率；云图和动画使用对应算例的真实场值。明确已完成的验证和目标用途精度所需的后续证据。
