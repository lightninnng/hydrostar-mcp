# 曲线船体 / Curved station hull

原创型值表建立的平顺曲面船体，保留站位、龙骨与水线对应的四边形网格。总长 120 m，最大宽度约 22 m，最大吃水约 7 m；精确尺寸、质量、重心、惯性与建模假设见 [参数](config.json)。

An original station-defined curved hull with feature-aligned quadrilateral bands. Length is 120 m, maximum beam approximately 22 m and maximum draft approximately 7 m; [parameters](config.json) record the exact geometry, mass properties and assumptions.

湿面 2029 个面元，其中四边形 2018 个、端部三角形 11 个；水线面 844 个，全体合计 2873 个，满足默认 3000 个总面元预算。CAD 体积与浮心、面元形状、翘曲、尺度过渡及完整拓扑均已验收，原生计算的六项质量门禁全部通过。

The solved mesh has 2029 wet panels, including 2018 quadrilaterals and 11 end-cap triangles, plus 844 waterplane panels. The full-equivalent total is 2873 within the 3000-panel default budget. Geometry acceptance and all six native execution gates passed.

计算采用 0.05–1.20 rad/s、间隔 0.005 rad/s，共 231 个频率和 13 个浪向。水深 80 m、零航速、自由单刚体，附加横摇阻尼为 5%。质量、重心和惯性沿用密网格参照例的显式课程假设。该例用于课程研究与简化一阶分析；对应工程精度仍需空间收敛和参照响应证据。

The sweep covers 231 frequencies from 0.05 to 1.20 rad/s at 0.005 rad/s spacing and 13 headings. It assumes 80 m water depth, zero speed, a free rigid body and 5% additional roll damping. Mass properties retain the explicit course assumptions of the dense reference. The case supports teaching and simplified first-order studies; target-specific engineering accuracy requires spatial convergence and reference-response evidence.

实际计算使用的 [原生网格和参数](inputs)、[响应输出](rao)、[独立几何验收](geometry/geometry-report.json)、[计算验收](verification.json)和[交付清单](delivery.json)随包保存。

Actual [native inputs](inputs), [response outputs](rao), [geometry acceptance](geometry/geometry-report.json), [execution verification](verification.json) and [delivery manifest](delivery.json) are included.

在已配置且获得授权的 HydroStar 8.2.0 项目环境中，先建立 bin、hdf、rao、tmp 目录，再依次执行以下命令。每步通过日志与质量检查后继续。From a configured, licensed HydroStar 8.2.0 environment, create bin, hdf, rao and tmp directories, then execute these commands in order, verifying each stage.

```text
hslec inputs/vessel.hst vessel
hschk - vessel
hsrdf inputs/vessel.rdf vessel
hsmcn inputs/vessel.mcn vessel
hsrao inputs/vessel.rao vessel
```

也可以在仓库根目录运行 `python -m hydrostar_mcp prepare examples/vessel/config.json`，再对返回的算例执行 `start`。The MCP/CLI workflow can prepare this configuration from the repository root and start the returned case.
