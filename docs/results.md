# 公开计算结果

三个资料参照构型均使用 HydroStar 8.2.0 完成原生求解。公开包保存项目生成的输入与求解数值，可离线核查。展示曲线连接原始频率点，保持计算幅值与相位。

[交互结果页](https://lightninnng.github.io/hydrostar-mcp/)；离线打开 [index.html](index.html)。

## 计算设置

海水密度 1025 kg/m³，重力加速度 9.81 m/s²，船舶水深 80 m、半潜水深 200 m，零航速。浪向 0°–360°、步长 30°，频率步长 0.005 rad/s。

| 模型 | 频率点 | 半体湿面/水线面面板 | 原生横向 GM |
| --- | --- | --- | --- |
| 集装箱船 | 151（0.05–0.80 rad/s） | 727 / 128 | 0.598346 m |
| 丰满油船 | 111（0.05–0.60 rad/s） | 660 / 206 | 5.708755 m |
| 圆柱半潜 | 237（0.02–1.20 rad/s） | 828 / 63 | 7.229444 m |

三套均通过六项门禁，hschk 七项计数均为零。半潜总排水体积 13919.320 m³，包含面元 13556.758 m³ 与实体细杆 362.562 m³；总质量约 14267.303 t，按当前零静态预载假设配平。精确值见各 `summary.json`。

## 科研图与交互查看

静态六联图显示 0°、60°、90°、180° 四个浪向，采用色盲友好配色和不同线型。各自由度使用独立纵轴并保留实际量级；平移为 m/m，转角为 deg/m。PNG 为 300 dpi，PDF 为矢量格式。

| 图 | PNG | PDF |
| --- | --- | --- |
| 三类求解几何 | [查看](assets/reference-geometry.png) | [下载](assets/reference-geometry.pdf) |
| 集装箱船 | [查看](assets/container_kcs_style_rao.png) | [下载](assets/container_kcs_style_rao.pdf) |
| 丰满油船 | [查看](assets/tanker_kvlcc2_style_rao.png) | [下载](assets/tanker_kvlcc2_style_rao.pdf) |
| 圆柱半潜 | [查看](assets/semisub_oc4_style_rao.png) | [下载](assets/semisub_oc4_style_rao.pdf) |

交互页提供 13 个浪向、幅值/相位切换、网格旋转与原始点取值。相位跨越周期分界且相邻跳变超过 180° 时断开连线；幅值近零时结合幅值解释相位。蓝色为实际计算湿面，棕色为实体细杆，灰色为干柱示意。各模型内空间比例统一，G/B 分别标记组合重心/浮心。

[动态总波面与散射波面](wavefields.md)补充固定规则波工况的云图 GIF、六自由度运动及完整原生场点记录。

## 数据与复现

[结果索引](../examples/results/index.json)下每套数据包含：

~~~text
config.json          完整配置
inputs/              自行生成的 HST、RDF、MCN、RAO 指令
rao/                 六自由度原生数值
motions.json         幅值、相位、频率、浪向和单位
summary.json         执行摘要、门禁、来源和逐文件 SHA-256
~~~

`source_case_id` 标识实际求解记录；`computed_at_utc` 为完成时间。`backend.automation_version` 记录求解时程序版本，`publication_version` 记录公开整理版本。完整本机日志由重算流程另行生成。

~~~powershell
python scripts/check_release.py
python scripts/reference_form_study.py --run
python scripts/export_showcase.py
python scripts/build_gallery.py
~~~

第一条离线检查哈希、原生 RAO/展示数组、几何与文档链接；后三条重算、导出并重建展示，需要有效软件安装与授权。

## 适用范围

船型使用标量拟合的分段曲面，局部线型由项目重建。半潜尺度、质量、配载、约束和耗散按[模型说明](reference-forms.md)明确取值。结果适用于参数教学、流程复现及这些假设下的简化分析。

半潜低频水平运动峰值受假定刚度与耗散影响，应结合波幅、实际运动范围及线性适用性判断。0.005 rad/s 有助于定位峰值，峰高稳定性需针对峰区继续加密。本版对三套新构型保留网格/频率收敛研究事项。

`engineering_acceptance.ready=false` 列出目标用途、实际几何/装载、系泊预载、阻尼及基准响应等证据。方法基准的敏感性数值仅适用于其对应模型，见[验证说明](verification.md)。

[返回 README](../README.md)
