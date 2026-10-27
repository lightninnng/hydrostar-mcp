# 资料参照构型与假设

内置模型从一手资料提取主尺度、静水标量、部件布置及部分质量/阻力参数，再由项目生成节点与面板。名称保留 `style`，明确资料参照层级。来源、几何重建和物理假设随配置与报告保存。

机器可读资料见[构型目录](references/basic-form-catalog.json)和[来源索引](references/sources.json)。

## 集装箱船：KCS 参照

[SIMMAN KCS](https://simman2014.dk/ship-data/moeri-container-ship/geometry-and-conditions-moeri-container-ship/)给出 Lpp=230 m、B=32.2 m、T=10.8 m、排水体积 52030 m³、CM=0.985、LCB/L=-1.48%、GM=0.6 m、kxx/B=0.4、kzz/L=0.25。

项目以平底圆舭剖面、平行中体、不同艏艉丰满度、球鼻艏和艉封板重建湿面，以排水量和 LCB 拟合丰满度。局部剖面和球鼻形状按参数化假设生成；当前离散体积较来源约低 0.485%，LCB 误差约 -0.025%L。

质量按离散排水配平，Gx 跟随浮心，Gz 由水线面和目标 GM 反算。kyy/L=0.25 为假设；裸船、零航速、5% 临界参考附加阻尼随配置声明。

[配置](../examples/container_kcs_style.json) · [计算记录](../examples/results/container_kcs_style/summary.json)

## 丰满油船：KVLCC2 参照

[SIMMAN KVLCC2](https://simman2014.dk/ship-data/moeri-kvlcc2-tanker/geometry-and-conditions-moeri-kvlcc2-tanker/)给出 Lpp=320 m、T=20.8 m、排水体积 312622 m³、CB=0.8098、CM=0.998、LCB/L=+3.48%、GM=5.71 m。B 取 58 m：原页面全尺度 Bwl 单元格为 580；1:100 模型宽 0.5800 m，以及体积/方形系数关系共同支持 58 m，目录保留了这项资料异常。

采用丰满中体、宽平底、小圆舭和艏艉收缩。离散体积约低 0.477%，LCB 误差约 -0.048%L。质量与 GM 的设置同船舶参照族；惯性和附加阻尼来源/假设见 `source_note`。

[配置](../examples/tanker_kvlcc2_style.json) · [计算记录](../examples/results/tanker_kvlcc2_style/summary.json)

## 圆柱扩底半潜：OC4 参照

固定版本 OpenFAST r-test 提供几何、部分质量与阻力标量：

- [HydroDyn 部件和阻力输入](https://github.com/OpenFAST/r-test/blob/dd5feaaaa500ba7283140107806300d551cff0a7/glue-codes/openfast/5MW_OC4Semi_WSt_WavesWN/NRELOffshrBsline5MW_OC4DeepCwindSemi_HydroDyn.dat)
- [ElastoDyn 结构质量输入](https://github.com/OpenFAST/r-test/blob/dd5feaaaa500ba7283140107806300d551cff0a7/glue-codes/openfast/5MW_OC4Semi_WSt_WavesWN/NRELOffshrBsline5MW_OC4DeepCwindSemi_ElastoDyn.dat)
- [HydroDyn 建模说明](https://openfast.readthedocs.io/en/main/source/user/hydrodyn/modeling_considerations.html)

| 项目 | 参数与处理 |
| --- | --- |
| 布置 | 中心柱 + 三偏置柱，柱心三角形边长 50 m |
| 主尺度 | 吃水 20 m；中心柱直径 6.5 m；偏置上柱 12 m、基柱 24 m；基柱高 6 m |
| 面元 | 四柱及扩底肩部，圆周多边形面积守恒 |
| 实体细杆 | 15 根直径 1.6 m 连接/斜撑，Cm=2 为假设，Cd=0.63 引自资料；排水计入平衡 |
| 柱阻力 | 7 段 Cm=0 补充，Cd=0.56/0.61/0.68，柱体积仅计一次 |
| 结构 | 未压载质量 3852180 kg、Gz=-8.6588 m 与给定惯性引自资料 |
| 压载 | 内径 11.88/23.88 m 与填高来自资料，增加对称底配载形成零预载平衡 |
| 上部质量 | 塔架 250 t、Gz=45 m；RNA 350 t、Gz=90 m，均为课程简化假设 |
| 约束 | K11=K22=50 kN/m，K66=80 MN·m/rad，为当前假设 |
| 阻力线性化 | 波幅 0.5 m；底板轴向 Cd=9.6，假定相对速度幅值 0.25 m/s |

底板耗散采用 `B=4ρCdA Vrel/(3π)`，以向量 `[0,0,1,y,-x,0]` 汇总为 heave/roll/pitch 阻尼矩阵。相对速度幅值与系泊刚度应按目标工况做敏感性和标定。

总排水相对 13917 m³ 参照约高 0.0167%。本次对称配载近似处理原系统静态系泊预载；目标浮式风机还应补充整机载荷、预载、柔性与耦合动力学。

[配置](../examples/semisub_oc4_style.json) · [计算记录](../examples/results/semisub_oc4_style/summary.json)

## 来源与权利

公开湿面网格来自项目生成器。第三方完整网格、商业软件和培训资料由各自权利方提供，引用见 [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md)。代码可在 [forms_geometry.py](../hydrostar_mcp/forms_geometry.py) 和 [reference_forms.py](../hydrostar_mcp/reference_forms.py) 复核。

[返回 README](../README.md) · [建模流程](modeling-guide.md)
