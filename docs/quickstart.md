# 快速开始

本项目在 Windows 上调用 HydroStar 原生命令。Python 层负责输入生成、验收、进程编排和结果回读。已发布结果与交互页面可在没有 HydroStar 的电脑上查看。

## 安装

~~~powershell
git clone https://github.com/lightninnng/hydrostar-mcp.git
cd hydrostar-mcp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[plot,test]"
$env:HSTAR_PATH7 = 'C:\path\to\Hstar4Experts\v8.2.0'
python -m hydrostar_mcp environment
~~~

`environment` 检查程序位置和能力。实际求解时各模块继续检查授权与运行状态。MPI 使用 HydroStar 安装环境支持的 `mpiexec`。

默认运行根目录是项目下的 `runs/`。可用 `HS_WORKSPACE` 设置独立目录，或在每条命令前加 `--workspace C:/HydroStarCases`。HST 来源根目录由 `HS_SOURCE_ROOT` 或 `--source-root` 指定，默认项目目录。

## 选择和审阅构型

~~~powershell
python -m hydrostar_mcp forms
python -m hydrostar_mcp reference semisub_oc4_style
python -m hydrostar_mcp plan examples/semisub_oc4_style.json
python -m hydrostar_mcp generate examples/semisub_oc4_style.json
~~~

`reference` 返回完整规划，包括参数、公开来源、几何标量比较和工程验收项；`plan` 读取给定 JSON。`generate` 在新目录生成可审阅输入，保留参数与生成来源。

| 示例配置 | 用途 |
| --- | --- |
| [container_kcs_style.json](../examples/container_kcs_style.json) | 分段剖面集装箱船 |
| [tanker_kvlcc2_style.json](../examples/tanker_kvlcc2_style.json) | 丰满裸船 |
| [semisub_oc4_style.json](../examples/semisub_oc4_style.json) | 圆柱扩底半潜 |
| [barge100.json](../examples/barge100.json) | 解析箱体与输入链路基准 |
| [barge_explicit.json](../examples/barge_explicit.json) | 显式质量和惯性 |
| [semisub.json](../examples/semisub.json) / [curved_hull.json](../examples/curved_hull.json) | 参数生成与敏感性方法示例 |
| [imported_mesh.json](../examples/imported_mesh.json) | 导入本项目生成的船体 HST |

## 完成求解

~~~powershell
python -m hydrostar_mcp prepare examples/semisub_oc4_style.json
$caseId = '<prepare 返回的 case_id>'
python -m hydrostar_mcp start $caseId
python -m hydrostar_mcp status $caseId
python -m hydrostar_mcp result $caseId --dof heave
python -m hydrostar_mcp plot $caseId --output runs/semisub-figure.png
~~~

每次 `prepare` 建立新目录。`start` 只能执行已准备且文件校验一致的算例；CLI 等待完成。输入修改后应重新准备。`result` 支持 surge、sway、heave、roll、pitch、yaw，返回数组及原生单位。

| 状态 | 含义 |
| --- | --- |
| `generated` | 离线输入已导出 |
| `prepared` | 网格和准备阶段检查完成 |
| `needs_confirmation` | 建模建议超出阈值，报告包含具体原因与 token |
| `queued` / `running` | 等待或执行原生模块 |
| `completed` | 六项门禁全部通过 |
| `failed` / `cancelled` / `interrupted` | 诊断与已有文件保留，后续依赖步骤停止 |

若返回 `needs_confirmation`，先审阅面板数量、波长和面元尺度，再修改参数或显式传回本次 token：

~~~powershell
python -m hydrostar_mcp prepare examples/barge100.json --confirmation-token '<plan token>'
python -m hydrostar_mcp start $caseId --confirmation-token '<measured-mesh token>'
~~~

规划确认与实测网格确认分别绑定参数和文件。硬性门禁必须通过；token 用于接受建模建议范围的选择。

## MCP 客户端与诊断

复制 [mcp-settings.json](../examples/mcp-settings.json)，使用虚拟环境 Python 的绝对路径。启动命令为 `python -m hydrostar_mcp.server`。客户端依次调用：

~~~text
list_reference_forms → make_reference_case → plan_case
→ prepare_case → start_case → case_status → read_rao
~~~

`start_case` 异步返回。轮询 `case_status` 至终态后读取结果；`cancel_case` 清理该服务启动的当前算例进程树。服务 stdout 保留给 MCP 协议。

算例目录包含配置、HST 或 MRI、RDF、MCN、RAO 指令、`report.json`、模块日志和 `rao/` 输出。失败时先看错误代码和对应日志，再检查单位、平衡、网格及环境。授权诊断按正常软件授权流程处理。

[返回 README](../README.md) · [建模与质量](modeling-guide.md) · [结果说明](results.md)
