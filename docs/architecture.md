# 架构与数据流

CLI 和 MCP 共享 `CaseService`。统一输入模型约束单位、有限数值、几何类型、质量和运行参数；每次生成与准备使用独立目录。

多来源前处理由 `GeometryService` 管理。CAD、剖面和网格在独立子进程中转换，使用明确单位和水线产生全体湿面 HST；图片与 PDF 返回标定工作区。几何包保存源文件、请求、湿面、独立验收与哈希。`CaseService` 核验该包后复制到新的计算目录，并将这些资料纳入启动前的输入冻结检查。

~~~mermaid
flowchart LR
    A[JSON / MCP 参数] --> B[Pydantic 语义校验]
    B --> C[几何与质量预检]
    C --> D[MRI / HST / RDF / MCN / RAO]
    D --> E[hslec + hschk]
    E --> F[MPI hsrdf]
    F --> G[hsmcn]
    G --> H[hsrao]
    H --> I[完整性与哈希验收]
    I --> J[数组 / 科研图 / 交互展示]
~~~

| 模块 | 职责 |
| --- | --- |
| [models.py](../hydrostar_mcp/models.py) | 配置与物理约束 |
| [geometry_sources.py](../hydrostar_mcp/geometry_sources.py) | 多来源请求、剖面和格式契约 |
| [geometry_workflow.py](../hydrostar_mcp/geometry_workflow.py) | 来源边界、快照、独立进程和包哈希 |
| [geometry_kernel.py](../hydrostar_mcp/geometry_kernel.py) | CAD、曲线放样、网格转换和水线裁剪 |
| [surface_checks.py](../hydrostar_mcp/surface_checks.py) | 全体湿面拓扑、方向与全局自交 |
| [drawing.py](../hydrostar_mcp/drawing.py) | 图像与 PDF 渲染、米制描线工作区 |
| [geometry.py](../hydrostar_mcp/geometry.py) | 基准几何、拓扑、组合质量 |
| [forms_geometry.py](../hydrostar_mcp/forms_geometry.py) | 分段船型和圆柱半潜 |
| [reference_forms.py](../hydrostar_mcp/reference_forms.py) | 来源、假设、构型工厂和标量对照 |
| [core.py](../hydrostar_mcp/core.py) | 原生文件、积分、日志和进程 |
| [workflow.py](../hydrostar_mcp/workflow.py) | 状态机、门禁、异步作业与追溯 |
| [server.py](../hydrostar_mcp/server.py) / [cli.py](../hydrostar_mcp/cli.py) | MCP 与命令行 |
| [visualization.py](../hydrostar_mcp/visualization.py) | 科研格式绘图 |

`report.json` 保存参数、来源、源码哈希、日志路径、验收与工程证据项。准备完成后冻结输入哈希，启动前复核，读取时验证输出。Windows Job Object 管理当前模块与 MPI 派生进程；超时和取消终止该进程树。

[export_showcase.py](../scripts/export_showcase.py)读取已完成且门禁通过的算例，导出便携输入、数值与质量摘要。[build_gallery.py](../scripts/build_gallery.py)将网格和完整响应数组嵌入静态 HTML。图与页面共享同批数据，公开包以逐文件 SHA-256 校验一致性。

[返回 README](../README.md)
