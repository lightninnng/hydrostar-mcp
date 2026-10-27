# Full-form tanker

本目录交付当前工况的原生输入、完整复场量与命令导出设置。规则波幅 0.5 m，角频率 0.4 rad/s，浪向 60.0°，水深 80.0 m。压力和高程的颜色采用实际物理单位；运动和波高的观察倍率均为 6，平均湿面压力图的几何倍率为 1。

This package delivers actual native inputs, full complex fields and command-render settings. Wave amplitude is 0.5 m, frequency 0.4 rad/s, heading 60.0° and depth 80.0 m. Colours retain physical pressure/elevation units. Motion and wave height use a stated 6× gain; mean pressure geometry uses 1×.

[交付清单 / Delivery](delivery.json)保存执行顺序与文件状态，[场量 / Complex fields](waves.json)保留完整复数，[验收 / Verification](verification.json)记录解析入射波、完整复辐射及压力检查，[导出 / Rendering](render.json)记录实际帧、图像、GIF 与视觉验收。

平均静水压力另存，云图采用随体一阶扰动。自由面采样以平均水线为边界，纯绕射视图固定船体，辐射视图显示对应运动。The pressure is the body-following first-order perturbation, with mean hydrostatic pressure stored separately. Free-surface sampling follows the mean waterline; diffraction uses a fixed body and radiation displays the associated motion.

克隆完整仓库后，按[可视化方法](../../../../docs/native-visualization.md)命令重建。波面与压力的实际来源见交付清单，原始 HSprv 导出作为版本诊断保存。Clone the complete repository and follow the [command workflow](../../../../docs/native-visualization.md). The delivery manifest identifies the accepted wave/pressure sources; original HSprv output remains a version diagnostic.

原生重算先建立 bin、hdf、rao 和 tmp 目录，再按交付清单逐步执行，各步核对日志与门禁。谱统计阶段在本例标为不适用。For native replay, create bin, hdf, rao and tmp directories and execute the manifest sequence, checking logs and gates. Spectral statistics are outside this regular-wave case.
