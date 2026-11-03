# 原生算例文件 / Native case files

项目名 `cad_spar_rings_fine`，湿面 2832，水线面 132，全体等效总面元 **2964/3000**，MPI 进程数 2。

实际求解网格及 .rdf/.mcn/.rao 输入保存在 inputs/，六自由度原生响应保存在 rao/。config.json 保存质量、重心、惯性、阻尼、环境和单位；geometry/ 保存源资料、网格及独立验收。budget-preflight.json 记录相同 HST 的原生预算实测；verification.json、logs/ 和 delivery.json 保存执行、质量门禁及哈希。

The solved native inputs are in inputs/, the six-DOF outputs in rao/, and the accepted source geometry in geometry/. Physical parameters are held fixed for the sampled panel-layout comparison. The total includes automatic waterplane panels and symmetry expansion.

## 复算顺序 / Replay order

在本目录使用已配置且获许可的 HydroStar 8.2.0 环境，逐步核对日志和门禁。以下输入重新生成二进制数据库；确保 bin/、hdf/、tmp/、logs/、rao/ 工作目录存在。

```text
hslec inputs/cad_spar_rings_fine.hst cad_spar_rings_fine
hschk - cad_spar_rings_fine
hsrdf inputs/cad_spar_rings_fine.rdf cad_spar_rings_fine
hsmcn inputs/cad_spar_rings_fine.mcn cad_spar_rings_fine
hsrao inputs/cad_spar_rings_fine.rao cad_spar_rings_fine
```

响应采样为 0.2–0.8 rad/s、间隔 0.1 rad/s，四个浪向。本次完成几何及原生计算链路验收；工程精度仍需对应构型的空间、峰区频率和参考响应证据。The two nearby Spar discretizations measure local sampled sensitivity; they do not establish spatial convergence. Regular-wave first-order analysis uses no .spc; a StarSpec extension supplies sea states and an actual spectral input.
