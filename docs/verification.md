# 验证与复现

验证分别覆盖软件行为、几何/物理一致性、原生执行与目标用途证据；结论按各部分的实际证据给出。

## 离线验证

~~~powershell
python -m pip install -e ".[dev,plot,geometry]"
python -m ruff check hydrostar_mcp scripts tests
python -m pytest -q -m "not integration" --basetemp .pytest-tmp
python scripts/check_release.py
python scripts/check_local.py
python -m build
~~~

测试覆盖几何、组合质量、硬门禁、文件完整性、日志异常、失败停止、状态、取消/超时进程树清理和真实 MCP stdio。编排测试使用明确标注的合成网格与模拟输出；物理数值证据由原生计算单独提供。

`check_release.py` 检查公开文件、本地文档链接、逐文件哈希、原生 RAO 与展示数组、网格积分及页面嵌入数据。`check_local.py` 离线生成全部示例并记录本机诊断。GitHub Actions 在 Windows 的 Python 3.10/3.12 上执行离线测试与构建。

## 原生复现

~~~powershell
$env:HSTAR_PATH7 = 'C:\path\to\Hstar4Experts\v8.2.0'
python scripts/check_local.py --solver
python scripts/reference_form_study.py --run
python scripts/export_showcase.py
python scripts/build_gallery.py
~~~

研究脚本可复用相同配置的已完成记录；配置变化时建立新算例。独立重算可直接对示例 JSON 执行 `prepare` / `start`。链路包含 hslec/hschk、MPI hsrdf、hsmcn、hsrao 与六自由度验收，报告保留退出码、耗时、网格、GM、平衡及哈希。

~~~powershell
$env:HS_RUN_INTEGRATION = '1'
python -m pytest -q -m integration
~~~

该集成测试需要本机安装与授权。授权不可用时明确记为 xfail，应与已完成数值验收分开解释。

## 网格与频率敏感性

~~~powershell
python scripts/mesh_study.py --run
python scripts/parametric_study.py --run
python scripts/frequency_study.py
python scripts/peak_study.py
~~~

这些脚本分别研究箱体、原创方柱半潜和解析曲面体。固定质量、惯性、刚度、阻尼及环境，结合幅值与相位比较复数 RAO，再加密峰区频率。

三套资料参照构型发布了 0.005 rad/s 网格的原生结果和标量核查。方法基准的收敛数值仅适用于对应基准；新构型应另做三档空间网格和峰区频率研究，形成自身误差证据。

## 多来源几何验证

`python scripts/check_geometry.py` 核对三类原创复杂几何的源包、CAD 体积与浮心误差、求解湿面、六项原生门禁、完整 RAO 数组和图像哈希。单元测试覆盖毫米制 STEP/IGES、显式单位 BREP、DXF 角点、STL/OBJ/PLY/HST、全局面自交、图纸独立尺寸点及源包修改拦截；MCP 测试通过真实 stdio 调用几何构建。

三类新增构型采用 0.2–0.8 rad/s、步长 0.1 rad/s 及四个浪向，验证的是几何转换、原生求解和数据追溯链路。其响应峰区和工程误差应按目标用途另做空间与频率研究。

当前站位带、月池分块和 Spar 环带均保留原生四边形，并单独记录用于检查的内部三角化数量。Spar 另保存 6800 个湿面元的原生参照，与 9312 个湿面元结果比较；各策略固定 v0.4.0 基线的质量、重心、惯性、恢复设置、阻尼和环境。`scripts/export_mesh_comparison.py` 从原始数组重新计算幅值、相位及复数差，`check_geometry.py` 复核全部指标和固定物理参数。两档环带的采样最大复升沉差除以较粗网格升沉峰值为 3.70%，对应的空间收敛与峰区频率证据仍按目标用途补充。

## 动态场验证

`python scripts/check_wavefields.py` 逐条核对压缩包内的原生场点 RAO、导出复数值、坐标网格、解析入射波、输入/数据哈希、GIF 帧数与循环时长。相位重建和运动坐标另有单元测试，详见[动态场说明](wavefields.md)。

## 按工程用途验收

`engineering_acceptance` 保存目标用途/海况、实际几何、装载/惯性、约束/预载、耗散和周期/RAO 对照等证据项。以目标资料替换假设后重新完成静力和全链路检查，声明精度指标与适用范围。

本版三套资料参照构型与三套多来源几何算例的六项数值执行门禁全部通过，`engineering_acceptance.ready=false` 保留目标对象的后续证据工作。

按[原生文件交付规范](native-delivery.md)核对实际网格、工况、荷载/参数及输出。文件清单保留用途、执行顺序、状态与哈希；采用 StarSpec 的任务还保存实际 .spc 及对应谱统计记录。

[返回 README](../README.md) · [公开结果](results.md)

## 二阶差频交付检查

`python scripts/check_second_order.py` 从正式原生输入和复数输出复核两档环带外域、区域覆盖与形状、36 对有效波频、216 个复数荷载系数、QTF 对角项、近远场结果、积分离散敏感性、媒体和来源。该检查已并入发布门禁。艏摇力矩按自身尺度记录需继续收敛，当前通过状态针对所列主要分量；[二阶研究说明](second-order.md)给出具体范围及原生复算方法。

二阶系数动画另验收原生复数来源、虚部符号、零差频恒定性、均值/RMS 与周期闭合；两组各保留 80 个相位。GIF 解码后逐帧像素与固定调色板输入一致，并在排除时钟和图注后复核每个荷载面板的变化，检查已并入发布门禁。
