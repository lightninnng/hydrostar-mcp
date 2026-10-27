# 原生算例文件 / Native case files

本算例保留实际计算使用的原生输入、六自由度幅值与相位及独立几何验收包。项目名为 `vessel_bands`。参数和明确的课程分析假设见 config.json；网格、计算和文件来源见 verification.json 与 delivery.json。

This case preserves the actual native inputs, six-DOF amplitude/phase outputs and accepted geometry bundle. The project name is `vessel_bands`. config.json records the physical parameters and study assumptions; verification.json and delivery.json record acceptance and provenance.

## 文件 / Files

- inputs/vessel_bands.hst：实际求解网格 / solved mesh。
- inputs/vessel_bands.rdf：辐射绕射工况 / radiation and diffraction settings。
- inputs/vessel_bands.mcn：质量、重心、惯性、阻尼与运动设置 / mechanics and motion settings。
- inputs/vessel_bands.rao：结果提取指令 / response extraction instructions。
- rao/*.rao：原生响应输出，含频率、浪向、幅值、相位与单位 / native response outputs。
- geometry/：源资料、参数、湿面和验收记录 / source, mesh and geometry acceptance。
- delivery.json：交付文件状态与哈希 / file status and hashes。

## 复算顺序 / Replay order

在本目录使用已配置和授权的 HydroStar 8.2.0 环境，按以下顺序运行。每一步通过日志与相应质量检查后进入下一步；hschk 使用交付网格生成的本项目数据库。中间二进制数据库由这些输入重新生成。

Run these commands in this directory using a configured, licensed HydroStar 8.2.0 environment. Verify the logs and quality gates at each step. These inputs regenerate the intermediate binary databases.

```text
hslec inputs/vessel_bands.hst vessel_bands
hschk - vessel_bands
hsrdf inputs/vessel_bands.rdf vessel_bands
hsmcn inputs/vessel_bands.mcn vessel_bands
hsrao inputs/vessel_bands.rao vessel_bands
```

本次为规则波一阶响应计算，谱统计阶段在 delivery.json 中标为本次不适用。需要 StarSpec 时，补充有来源的海况、谱型、方向和积分范围，交付实际 .spc，并以 `hspec input.spc project` 执行。This study covers regular-wave first-order responses. A StarSpec extension supplies the sea states, spectrum, directions, integration range and actual .spc file before spectral execution.

本参照例保留 14,962 个全体等效总面元（含水线面），MPI 进程数为 1。新模型按 3000 个总面元规划，增加预算按具体算例审阅。This retained reference has 14,962 full-equivalent total panels, including waterplane panels; new models use the 3000-panel default budget.

响应采样为 0.2–0.8 rad/s、间隔 0.1 rad/s，四个浪向。它支持建模与原生计算链路及网格策略敏感性研究；工程精度还需对应构型的空间、峰区频率与参考响应证据。The sampled grid supports workflow and panel-layout sensitivity studies; target-specific accuracy requires spatial, peak-frequency and reference-response evidence.
