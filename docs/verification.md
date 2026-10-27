# 验证与复现

验证分别覆盖软件行为、几何/物理一致性、原生执行与目标用途证据；结论按各部分的实际证据给出。

## 离线验证

~~~powershell
python -m pip install -e ".[dev,plot]"
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

## 动态场验证

`python scripts/check_wavefields.py` 逐条核对压缩包内的原生场点 RAO、导出复数值、坐标网格、解析入射波、输入/数据哈希、GIF 帧数与循环时长。相位重建和运动坐标另有单元测试，详见[动态场说明](wavefields.md)。

## 按工程用途验收

`engineering_acceptance` 保存目标用途/海况、实际几何、装载/惯性、约束/预载、耗散和周期/RAO 对照等证据项。以目标资料替换假设后重新完成静力和全链路检查，声明精度指标与适用范围。

本版三套算例六项数值执行门禁全部通过，`engineering_acceptance.ready=false` 如实保留目标对象的后续证据工作。

[返回 README](../README.md) · [公开结果](results.md)
